#!/usr/bin/env python3
"""Run resumable conditional beam search and pairwise block-interaction analysis."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from vlm_bench.benchmark import BaselineRunner
from vlm_bench.io import read_jsonl, write_json, write_jsonl
from vlm_bench.phase2 import split_by_image
from vlm_bench.phase3 import (
    CAPABILITIES,
    capability_pool,
    expand_beam,
    interaction_pp,
    paired_metrics,
    route_key,
    select_task_seed,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_map(paths: list[Path]) -> dict[str, dict]:
    merged = {}
    for path in paths:
        for row in read_jsonl(path):
            if row["id"] in merged:
                raise ValueError(f"Duplicate prediction ID {row['id']} across {paths}")
            merged[row["id"]] = row
    return merged


def rows_by_capability(rows: list[dict]) -> dict[str, list[dict]]:
    return {
        capability: [row for row in rows if row["capability"] == capability]
        for capability in CAPABILITIES
    }


def run_route(
    runner: BaselineRunner,
    blocks: tuple[int, ...],
    rows: list[dict],
    output_dir: Path,
    label: str,
) -> dict[str, dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = output_dir / "route.json"
    expected_metadata = {"blocks": list(blocks), "route_key": route_key(blocks)}
    if metadata_path.exists():
        existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if existing_metadata != expected_metadata:
            raise ValueError(f"Route metadata mismatch in {output_dir}")
    else:
        write_json(metadata_path, expected_metadata)

    predictions_path = output_dir / "predictions.jsonl"
    existing = load_map([predictions_path]) if predictions_path.exists() else {}
    pending = [row for row in rows if row["id"] not in existing]
    runner.set_skip_vision_blocks(list(blocks))
    mode = "a" if predictions_path.exists() else "w"
    with predictions_path.open(mode, encoding="utf-8", buffering=1) as handle:
        for index, row in enumerate(pending, start=1):
            prediction = runner.predict(row)
            handle.write(json.dumps(prediction, sort_keys=True) + "\n")
            existing[row["id"]] = prediction
            if index == 1 or index % 25 == 0 or index == len(pending):
                print(
                    f"[{label}] {index}/{len(pending)} pending; {len(existing)}/{len(rows)} saved",
                    flush=True,
                )
    expected_ids = {row["id"] for row in rows}
    if not expected_ids <= set(existing):
        raise RuntimeError(f"Incomplete route {label}")
    return {row_id: existing[row_id] for row_id in expected_ids}


def prepare(
    manifest: Path,
    output_dir: Path,
    per_capability: int,
    seed: int,
) -> tuple[list[dict], list[dict]]:
    rows = list(read_jsonl(manifest))
    search, validation = split_by_image(rows, per_capability, seed)
    search_hashes = {row["image_sha256"] for row in search}
    validation_hashes = {row["image_sha256"] for row in validation}
    if search_hashes & validation_hashes:
        raise RuntimeError("Phase 3 search and validation images overlap")
    prepared = output_dir / "prepared"
    write_jsonl(prepared / "search.jsonl", search)
    write_jsonl(prepared / "validation.jsonl", validation)
    write_json(prepared / "summary.json", {
        "source_manifest": str(manifest.resolve()),
        "search_examples": len(search),
        "validation_examples": len(validation),
        "search_counts": {capability: sum(row["capability"] == capability for row in search) for capability in CAPABILITIES},
        "validation_counts": {
            capability: sum(row["capability"] == capability for row in validation)
            for capability in CAPABILITIES
        },
        "image_overlap": 0,
        "seed": seed,
    })
    return search, validation


def search_routes(
    runner: BaselineRunner,
    search_rows: list[dict],
    baseline: dict[str, dict],
    route_design: list[dict],
    sensitivity: dict,
    output_dir: Path,
    candidate_pool_size: int,
    beam_width: int,
    start_budget: int,
    target_budget: int,
) -> dict:
    grouped = rows_by_capability(search_rows)
    summary = {"objective": "target capability accuracy only", "capabilities": {}}
    for capability in CAPABILITIES:
        target_rows = grouped[capability]
        target_ids = [row["id"] for row in target_rows]
        seed = select_task_seed(route_design, capability, start_budget)
        pool = capability_pool(sensitivity, capability, candidate_pool_size)
        if not set(seed) <= set(pool):
            raise ValueError(f"{capability} seed is not contained in its candidate pool")
        beam = [seed]
        capability_summary = {
            "seed": list(seed),
            "candidate_pool": list(pool),
            "depths": [],
        }
        for depth in range(start_budget + 1, target_budget + 1):
            candidates = expand_beam(beam, pool)
            evaluated = []
            for index, candidate in enumerate(candidates, start=1):
                blocks = candidate["blocks"]
                predictions = run_route(
                    runner,
                    blocks,
                    target_rows,
                    output_dir / "search" / capability / f"k{depth:02d}" / route_key(blocks),
                    f"search {capability} k{depth} route {index}/{len(candidates)}",
                )
                metrics = paired_metrics(baseline, predictions, target_ids)
                evaluated.append({
                    "blocks": list(blocks),
                    "parents": [list(parent) for parent in candidate["parents"]],
                    "added_blocks": sorted(set(candidate["added_blocks"])),
                    "metrics": metrics,
                })
            evaluated.sort(key=lambda item: (item["metrics"]["accuracy_drop_pp"], item["blocks"]))
            retained = evaluated[:beam_width]
            beam = [tuple(item["blocks"]) for item in retained]
            capability_summary["depths"].append({
                "budget": depth,
                "candidates_evaluated": len(evaluated),
                "retained": retained,
            })
            summary["capabilities"][capability] = capability_summary
            write_json(output_dir / "search_summary.json", summary)
            print(
                f"[search {capability}] retained k{depth}: "
                + ", ".join(f"{item['blocks']} ({item['metrics']['accuracy_drop_pp']:.2f} pp)" for item in retained),
                flush=True,
            )
    return summary


def assignment_routes(route_design: list[dict], route_type: str, budget: int, capability: str | None) -> list[dict]:
    selected = []
    for route in route_design:
        for assignment in route.get("assignments", []):
            if assignment.get("route_type") != route_type or assignment.get("budget") != budget:
                continue
            if capability is not None and assignment.get("capability") != capability:
                continue
            selected.append(route)
            break
    return selected


def validation_metrics(
    baseline: dict[str, dict],
    predictions: dict[str, dict],
    grouped_ids: dict[str, list[str]],
) -> dict:
    by_capability = {
        capability: paired_metrics(baseline, predictions, ids)
        for capability, ids in grouped_ids.items()
    }
    all_ids = [row_id for ids in grouped_ids.values() for row_id in ids]
    return {
        "overall": paired_metrics(baseline, predictions, all_ids),
        "capabilities": by_capability,
        "macro_drop_pp": sum(item["accuracy_drop_pp"] for item in by_capability.values()) / len(by_capability),
    }


def validate_routes(
    runner: BaselineRunner,
    validation_rows: list[dict],
    baseline: dict[str, dict],
    search_summary: dict,
    route_design: list[dict],
    existing_benchmark_root: Path,
    output_dir: Path,
    target_budget: int,
) -> dict:
    grouped_ids = {
        capability: [row["id"] for row in validation_rows if row["capability"] == capability]
        for capability in CAPABILITIES
    }
    summary = {
        "selection_rule": "primary route is rank 1 on search data; validation results do not change selection",
        "beam_routes": {},
        "existing_controls": {},
    }
    for capability in CAPABILITIES:
        final_depth = search_summary["capabilities"][capability]["depths"][-1]
        retained = final_depth["retained"]
        summary["beam_routes"][capability] = []
        for rank, item in enumerate(retained, start=1):
            blocks = tuple(item["blocks"])
            predictions = run_route(
                runner,
                blocks,
                validation_rows,
                output_dir / "validation" / capability / f"rank-{rank}-{route_key(blocks)}",
                f"validation {capability} rank {rank}",
            )
            summary["beam_routes"][capability].append({
                "search_rank": rank,
                "blocks": list(blocks),
                "search_metrics": item["metrics"],
                "validation_metrics": validation_metrics(baseline, predictions, grouped_ids),
            })

        controls = []
        controls.extend(assignment_routes(route_design, "task_specific", target_budget, capability))
        controls.extend(assignment_routes(route_design, "generic_macro", target_budget, None))
        controls.extend(assignment_routes(route_design, "contiguous_macro", target_budget, None))
        controls.extend(assignment_routes(route_design, "random", target_budget, None))
        unique_controls = {route["name"]: route for route in controls}
        summary["existing_controls"][capability] = []
        for route in unique_controls.values():
            predictions = load_map([existing_benchmark_root / route["name"] / "predictions.jsonl"])
            summary["existing_controls"][capability].append({
                "name": route["name"],
                "blocks": route["skip_vision_blocks"],
                "assignments": route["assignments"],
                "validation_metrics": validation_metrics(baseline, predictions, grouped_ids),
            })
        write_json(output_dir / "validation_summary.json", summary)
    return summary


def pairwise_analysis(
    runner: BaselineRunner,
    search_rows: list[dict],
    baseline: dict[str, dict],
    sensitivity: dict,
    single_ablation_roots: list[Path],
    output_dir: Path,
    pairwise_pool_size: int,
) -> dict:
    grouped = rows_by_capability(search_rows)
    summary = {"definition": "pair_drop - single_i_drop - single_j_drop", "capabilities": {}}
    single_maps = {
        block: load_map([root / f"block-{block:02d}" / "predictions.jsonl" for root in single_ablation_roots])
        for block in range(32)
    }
    for capability in CAPABILITIES:
        rows = grouped[capability]
        ids = [row["id"] for row in rows]
        pool = capability_pool(sensitivity, capability, pairwise_pool_size)
        singles = {block: paired_metrics(baseline, single_maps[block], ids) for block in pool}
        pairs = []
        combinations = [(pool[i], pool[j]) for i in range(len(pool)) for j in range(i + 1, len(pool))]
        for index, (first, second) in enumerate(combinations, start=1):
            blocks = tuple(sorted((first, second)))
            predictions = run_route(
                runner,
                blocks,
                rows,
                output_dir / "pairwise" / capability / route_key(blocks),
                f"pairwise {capability} pair {index}/{len(combinations)}",
            )
            pair_metrics = paired_metrics(baseline, predictions, ids)
            interaction = interaction_pp(
                singles[first]["accuracy_drop_pp"],
                singles[second]["accuracy_drop_pp"],
                pair_metrics["accuracy_drop_pp"],
            )
            pairs.append({
                "blocks": list(blocks),
                "single_i_drop_pp": singles[first]["accuracy_drop_pp"],
                "single_j_drop_pp": singles[second]["accuracy_drop_pp"],
                "pair_metrics": pair_metrics,
                "interaction_pp": interaction,
            })
        pairs.sort(key=lambda item: (-item["interaction_pp"], item["blocks"]))
        summary["capabilities"][capability] = {
            "candidate_pool": list(pool),
            "single_metrics": {str(block): metrics for block, metrics in singles.items()},
            "pairs_most_harmful_first": pairs,
        }
        write_json(output_dir / "pairwise_summary.json", summary)
    return summary


def write_report(output_dir: Path) -> None:
    lines = [
        "# Phase 3 Interaction-Aware Route Search",
        "",
        "This is a development-set search. It is not external held-out evidence.",
    ]
    search_path = output_dir / "search_summary.json"
    if search_path.exists():
        search = json.loads(search_path.read_text(encoding="utf-8"))
        lines.extend(["", "## Search-Selected Routes", "", "| Capability | Blocks | Search drop |", "|---|---|---:|"])
        for capability in CAPABILITIES:
            retained = search["capabilities"][capability]["depths"][-1]["retained"][0]
            lines.append(f"| {capability} | `{retained['blocks']}` | {retained['metrics']['accuracy_drop_pp']:.2f} pp |")
    validation_path = output_dir / "validation_summary.json"
    if validation_path.exists():
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        lines.extend(["", "## Image-Disjoint Development Validation", "", "| Capability | Primary blocks | Target drop | Macro drop |", "|---|---|---:|---:|"])
        for capability in CAPABILITIES:
            primary = validation["beam_routes"][capability][0]
            metrics = primary["validation_metrics"]
            lines.append(
                f"| {capability} | `{primary['blocks']}` | "
                f"{metrics['capabilities'][capability]['accuracy_drop_pp']:.2f} pp | {metrics['macro_drop_pp']:.2f} pp |"
            )
    pairwise_path = output_dir / "pairwise_summary.json"
    if pairwise_path.exists():
        pairwise = json.loads(pairwise_path.read_text(encoding="utf-8"))
        lines.extend(["", "## Strongest Harmful Pair Interaction", "", "| Capability | Blocks | Interaction |", "|---|---|---:|"])
        for capability in CAPABILITIES:
            strongest = pairwise["capabilities"][capability]["pairs_most_harmful_first"][0]
            lines.append(f"| {capability} | `{strongest['blocks']}` | +{strongest['interaction_pp']:.2f} pp |")
    lines.extend([
        "",
        "The search/validation split is image-disjoint, but the original one-block ranking used the",
        "larger discovery set. These results therefore remain method-development evidence. The sealed",
        "external benchmark must not be used until the route and recovery method are frozen.",
        "",
    ])
    (output_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/baseline_qwen25_vl_3b.json"))
    parser.add_argument("--phase3-config", type=Path, default=Path("configs/phase3_interaction_search.json"))
    parser.add_argument("--manifest", type=Path, default=Path("data/processed-v2/manifests/development.jsonl"))
    parser.add_argument("--data-root", type=Path, default=Path("data/processed-v2"))
    parser.add_argument("--baseline-predictions", type=Path, default=Path("results/task-route-design-qwen25-vl-3b/development-baseline/predictions.jsonl"))
    parser.add_argument("--route-design", type=Path, default=Path("results/task-route-design-qwen25-vl-3b/routes.json"))
    parser.add_argument("--sensitivity", type=Path, default=Path("results/task-route-design-qwen25-vl-3b/sensitivity.json"))
    parser.add_argument("--existing-benchmark-root", type=Path, default=Path("results/task-route-benchmark-qwen25-vl-3b"))
    parser.add_argument("--single-ablation-roots", type=Path, nargs="+", default=[Path("results/ablation-qwen25-vl-3b"), Path("results/ablation-vqav2-color-qwen25-vl-3b")])
    parser.add_argument("--output-dir", type=Path, default=Path("results/phase3-interaction-search-qwen25-vl-3b"))
    parser.add_argument("--stages", default="search,validate,pairwise")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    phase3_config = json.loads(args.phase3_config.read_text(encoding="utf-8"))
    if args.smoke:
        phase3_config.update({
            "beam_width": 2,
            "candidate_pool_size": 6,
            "pairwise_pool_size": 4,
            "search_examples_per_capability": 2,
            "target_budget": 5,
        })
    stages = [stage.strip() for stage in args.stages.split(",") if stage.strip()]
    invalid_stages = set(stages) - {"search", "validate", "pairwise"}
    if invalid_stages:
        raise ValueError(f"Unknown stages: {sorted(invalid_stages)}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    search_rows, validation_rows = prepare(
        args.manifest,
        args.output_dir,
        int(phase3_config["search_examples_per_capability"]),
        int(phase3_config["seed"]),
    )
    if args.smoke:
        grouped_validation = rows_by_capability(validation_rows)
        validation_rows = [
            row
            for capability in CAPABILITIES
            for row in grouped_validation[capability][:2]
        ]
        write_jsonl(args.output_dir / "prepared" / "validation-smoke.jsonl", validation_rows)
    baseline = load_map([args.baseline_predictions])
    required_ids = {row["id"] for row in [*search_rows, *validation_rows]}
    if not required_ids <= set(baseline):
        raise ValueError("Baseline predictions do not cover the Phase 3 development split")
    route_design = json.loads(args.route_design.read_text(encoding="utf-8"))
    sensitivity = json.loads(args.sensitivity.read_text(encoding="utf-8"))

    state = {
        "status": "running",
        "started_at": now(),
        "config": phase3_config,
        "stages_requested": stages,
        "stages": {},
    }
    write_json(args.output_dir / "pipeline_state.json", state)
    runner = BaselineRunner(json.loads(args.config.read_text(encoding="utf-8")), args.manifest, args.output_dir / "runtime", args.data_root)
    try:
        for _ in range(int(runner.config.get("warmup_examples", 0))):
            runner.predict(search_rows[0])
        for stage in stages:
            state["stages"][stage] = {"status": "running", "started_at": now()}
            write_json(args.output_dir / "pipeline_state.json", state)
            if stage == "search":
                search_routes(
                    runner, search_rows, baseline, route_design, sensitivity, args.output_dir,
                    int(phase3_config["candidate_pool_size"]), int(phase3_config["beam_width"]),
                    int(phase3_config["start_budget"]), int(phase3_config["target_budget"]),
                )
            elif stage == "validate":
                search_summary_path = args.output_dir / "search_summary.json"
                if not search_summary_path.exists():
                    raise ValueError("Validation requires a completed search summary")
                validate_routes(
                    runner, validation_rows, baseline,
                    json.loads(search_summary_path.read_text(encoding="utf-8")),
                    route_design, args.existing_benchmark_root, args.output_dir,
                    int(phase3_config["target_budget"]),
                )
            else:
                pairwise_analysis(
                    runner, search_rows, baseline, sensitivity, args.single_ablation_roots,
                    args.output_dir, int(phase3_config["pairwise_pool_size"]),
                )
            state["stages"][stage] = {**state["stages"][stage], "status": "complete", "completed_at": now()}
            write_report(args.output_dir)
            write_json(args.output_dir / "pipeline_state.json", state)
        state["status"] = "complete"
        state["completed_at"] = now()
    except Exception as error:
        state["status"] = "failed"
        state["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        runner.close()
        write_json(args.output_dir / "pipeline_state.json", state)


if __name__ == "__main__":
    main()
