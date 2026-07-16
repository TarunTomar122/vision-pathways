#!/usr/bin/env python3
"""Analyze frozen robust routes and matched-K controls on method selection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics

from vlm_bench.external_eval import bootstrap_advantage
from vlm_bench.io import read_jsonl, write_json
from vlm_bench.phase3 import route_key
from vlm_bench.robust_search import (
    generic_robust_objective,
    source_balanced_paired_metrics,
)


CAPABILITIES = ("attribute", "counting", "object", "ocr", "spatial")


def prediction_map(path: Path) -> dict[str, dict]:
    mapped = {}
    for row in read_jsonl(path):
        row_id = str(row["id"])
        if row_id in mapped:
            raise ValueError(f"Duplicate prediction ID {row_id} in {path}")
        mapped[row_id] = row
    return mapped


def cached_route(path: Path, blocks: list[int], wanted_ids: set[str]) -> dict[str, dict]:
    key = route_key(blocks)
    mapped = {}
    for record in read_jsonl(path):
        if record["route_key"].removeprefix(f"k{len(blocks):02d}-") != key:
            continue
        prediction = record["prediction"]
        row_id = str(prediction["id"])
        if row_id in wanted_ids:
            if row_id in mapped:
                raise ValueError(f"Duplicate cached route prediction {key}/{row_id}")
            mapped[row_id] = prediction
    missing = sorted(wanted_ids - mapped.keys())
    if missing:
        raise ValueError(f"Route {blocks} is missing {len(missing)} selection IDs: {missing[:5]}")
    return mapped


def conditional_policy(
    rows: list[dict],
    routes: dict[str, list[int]],
    cache_paths: dict[str, Path],
) -> dict[str, dict]:
    policy = {}
    for capability in CAPABILITIES:
        ids = {str(row["id"]) for row in rows if row["capability"] == capability}
        predictions = cached_route(cache_paths[capability], routes[capability], ids)
        policy.update(predictions)
    if len(policy) != len(rows):
        raise ValueError("Conditional evolved policy does not cover selection exactly")
    return policy


def aggregate(rows: list[dict], predictions: dict[str, dict], baseline: dict[str, dict]) -> dict:
    def one(items: list[dict]) -> dict:
        ids = [str(row["id"]) for row in items]
        accuracy = statistics.fmean(bool(predictions[row_id]["correct"]) for row_id in ids)
        baseline_accuracy = statistics.fmean(bool(baseline[row_id]["correct"]) for row_id in ids)
        return {
            "examples": len(ids),
            "accuracy": accuracy,
            "baseline_accuracy": baseline_accuracy,
            "accuracy_drop_pp": 100 * (baseline_accuracy - accuracy),
        }

    by_capability = {
        capability: one([row for row in rows if row["capability"] == capability])
        for capability in CAPABILITIES
    }
    sources = sorted({row["source"] for row in rows})
    by_source = {
        source: one([row for row in rows if row["source"] == source])
        for source in sources
    }
    paired = source_balanced_paired_metrics(
        {str(row["id"]): baseline[str(row["id"])] for row in rows},
        {str(row["id"]): predictions[str(row["id"])] for row in rows},
    )
    objective = generic_robust_objective(paired)
    return {
        "overall": one(rows),
        "capabilities": by_capability,
        "sources": by_source,
        "source_balanced": {
            "mean_drop_pp": objective.mean_drop_pp,
            "worst_source_drop_pp": objective.worst_source_drop_pp,
            "source_variability_pp": objective.source_variability_pp,
            "selection_score": objective.selection_score,
        },
    }


def compare(
    left: dict[str, dict],
    right: dict[str, dict],
    rows: list[dict],
    seed: int,
) -> dict:
    overall_ids = [str(row["id"]) for row in rows]
    return {
        "overall": bootstrap_advantage(left, right, overall_ids, seed),
        "capabilities": {
            capability: bootstrap_advantage(
                left,
                right,
                [str(row["id"]) for row in rows if row["capability"] == capability],
                seed + index + 1,
            )
            for index, capability in enumerate(CAPABILITIES)
        },
    }


def write_report(output_dir: Path, analysis: dict) -> None:
    lines = [
        "# Robust Route Search Results",
        "",
        "These are processed-v2 method-selection results, not a new sealed external evaluation.",
        "All route comparisons at a given K skip exactly the same number of vision blocks.",
        "",
        "## Matched-K Summary",
        "",
        "| K | Full | Evolved generic | Evolved task policy | Task vs generic | Generic independent | Task independent | Contiguous | Random mean (range) |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    full = analysis["full"]["overall"]["accuracy"]
    for raw_k, result in sorted(analysis["budgets"].items(), key=lambda item: int(item[0])):
        conditions = result["conditions"]
        random_values = [conditions[f"random-{index}"]["overall"]["accuracy"] for index in range(3)]
        advantage = result["comparisons"]["evolved_task_minus_evolved_generic"]["overall"]
        lines.append(
            f"| {raw_k} | {100 * full:.2f}% | "
            f"{100 * conditions['evolved-generic']['overall']['accuracy']:.2f}% | "
            f"{100 * conditions['evolved-task']['overall']['accuracy']:.2f}% | "
            f"{advantage['mean_pp']:+.2f} pp | "
            f"{100 * conditions['generic-independent']['overall']['accuracy']:.2f}% | "
            f"{100 * conditions['task-independent']['overall']['accuracy']:.2f}% | "
            f"{100 * conditions['contiguous']['overall']['accuracy']:.2f}% | "
            f"{100 * statistics.fmean(random_values):.2f}% "
            f"({100 * min(random_values):.2f}-{100 * max(random_values):.2f}%) |"
        )
    lines.extend(["", "## Capability-Specific Advantage", ""])
    for raw_k, result in sorted(analysis["budgets"].items(), key=lambda item: int(item[0])):
        lines.extend([
            f"### K{raw_k}",
            "",
            "| Capability | Evolved task | Evolved generic | Advantage | 95% interval |",
            "|---|---:|---:|---:|---:|",
        ])
        for capability in CAPABILITIES:
            task = result["conditions"]["evolved-task"]["capabilities"][capability]["accuracy"]
            generic = result["conditions"]["evolved-generic"]["capabilities"][capability]["accuracy"]
            comparison = result["comparisons"]["evolved_task_minus_evolved_generic"]["capabilities"][capability]
            lines.append(
                f"| {capability} | {100 * task:.2f}% | {100 * generic:.2f}% | "
                f"{comparison['mean_pp']:+.2f} pp | "
                f"[{comparison['ci95_low_pp']:.2f}, {comparison['ci95_high_pp']:.2f}] |"
            )
        lines.append("")
    lines.extend([
        "## Evidence Boundary",
        "",
        "The development/test image split is disjoint, but both partitions informed earlier",
        "single-block discovery. These results can compare frozen route-construction methods; they",
        "cannot establish untouched source transfer. The previously consumed external benchmark",
        "was not accessed by this search or analysis.",
        "",
    ])
    (output_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("results/robust-route-search-qwen25-vl-3b"))
    parser.add_argument("--manifest", type=Path, default=Path("data/processed-v2/robust-route-search/prepared/selection.jsonl"))
    parser.add_argument(
        "--baseline-predictions",
        type=Path,
        help="Optional shared baseline predictions; defaults to ROOT/baseline/predictions.jsonl",
    )
    parser.add_argument("--budgets", default="4,6,8", help="Comma-separated frozen K values")
    parser.add_argument("--bootstrap-iterations", type=int, default=10_000)
    args = parser.parse_args()
    # external_eval currently freezes 10,000 iterations; reject a misleading CLI override.
    if args.bootstrap_iterations != 10_000:
        raise ValueError("bootstrap iterations are frozen to 10,000")

    rows = list(read_jsonl(args.manifest))
    wanted_ids = {str(row["id"]) for row in rows}
    baseline_path = args.baseline_predictions or args.root / "baseline" / "predictions.jsonl"
    baseline_all = prediction_map(baseline_path)
    baseline = {row_id: baseline_all[row_id] for row_id in wanted_ids}
    frozen = json.loads((args.root / "frozen_routes.json").read_text(encoding="utf-8"))
    controls_state = json.loads((args.root / "controls" / "state.json").read_text(encoding="utf-8"))
    if frozen.get("status") != "frozen" or controls_state.get("status") != "complete":
        raise ValueError("Frozen routes and controls must both be complete")
    family_caches = {
        family: args.root / "families" / family / "route-predictions.jsonl"
        for family in ("generic", *CAPABILITIES)
    }
    analysis = {
        "schema_version": 1,
        "evidence_status": "processed-v2 method-selection; external heldout not accessed",
        "examples": len(rows),
        "full": aggregate(rows, baseline, baseline),
        "budgets": {},
    }
    budgets = tuple(int(value) for value in args.budgets.split(",") if value)
    if not budgets or len(set(budgets)) != len(budgets):
        raise ValueError("--budgets must contain unique positive integers")
    for k in budgets:
        generic_blocks = frozen["families"]["generic"]["budgets"][str(k)]["blocks"]
        evolved_generic = cached_route(family_caches["generic"], generic_blocks, wanted_ids)
        task_routes = {
            capability: frozen["families"][capability]["budgets"][str(k)]["blocks"]
            for capability in CAPABILITIES
        }
        evolved_task = conditional_policy(rows, task_routes, family_caches)
        condition_maps = {
            "evolved-generic": evolved_generic,
            "evolved-task": evolved_task,
        }
        for name in ("generic-independent", "task-independent", "contiguous", "random-0", "random-1", "random-2"):
            condition_maps[name] = prediction_map(args.root / "controls" / f"k{k:02d}-{name}" / "predictions.jsonl")
        metrics = {name: aggregate(rows, values, baseline) for name, values in condition_maps.items()}
        analysis["budgets"][str(k)] = {
            "routes": {
                "evolved-generic": generic_blocks,
                "evolved-task": task_routes,
            },
            "conditions": metrics,
            "comparisons": {
                "evolved_task_minus_evolved_generic": compare(evolved_task, evolved_generic, rows, 20260715 + k),
                "evolved_generic_minus_generic_independent": compare(evolved_generic, condition_maps["generic-independent"], rows, 20260815 + k),
                "evolved_task_minus_task_independent": compare(evolved_task, condition_maps["task-independent"], rows, 20260915 + k),
            },
        }
    output_dir = args.root / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "analysis.json", analysis)
    write_report(output_dir, analysis)
    print(output_dir / "analysis.json")


if __name__ == "__main__":
    main()
