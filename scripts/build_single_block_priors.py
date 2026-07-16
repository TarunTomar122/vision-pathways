#!/usr/bin/env python3
"""Derive deterministic route priors from a development-only one-block sweep."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from vlm_bench.io import read_jsonl, write_json, write_jsonl


CAPABILITIES = ("attribute", "counting", "object", "ocr", "spatial")


def prediction_map(path: Path) -> dict[str, dict]:
    rows = list(read_jsonl(path))
    mapped = {str(row["id"]): row for row in rows}
    if len(mapped) != len(rows):
        raise ValueError(f"Duplicate prediction IDs in {path}")
    return mapped


def accuracy(rows: list[dict]) -> float:
    if not rows:
        raise ValueError("Cannot score an empty group")
    return sum(bool(row["correct"]) for row in rows) / len(rows)


def drops(baseline: dict[str, dict], variant: dict[str, dict]) -> dict[str, float]:
    if baseline.keys() != variant.keys():
        raise ValueError("Baseline and intervention IDs differ")
    return {
        capability: accuracy([baseline[row_id] for row_id in baseline if baseline[row_id]["capability"] == capability])
        - accuracy([variant[row_id] for row_id in baseline if baseline[row_id]["capability"] == capability])
        for capability in CAPABILITIES
    }


def add_route(routes: dict[tuple[int, ...], dict], blocks: list[int], assignment: dict) -> None:
    key = tuple(sorted(blocks))
    record = routes.setdefault(
        key,
        {"name": f"route-{len(routes):03d}-k{len(key):02d}", "skip_vision_blocks": list(key), "assignments": []},
    )
    record["assignments"].append(assignment)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--ablation-dir", type=Path, required=True)
    parser.add_argument("--development-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--blocks", required=True, help="e.g. 0-26")
    parser.add_argument("--budgets", default="4,6,8")
    parser.add_argument("--random-repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260716)
    args = parser.parse_args()

    if "-" in args.blocks:
        first, last = (int(value) for value in args.blocks.split("-", 1))
        blocks = tuple(range(first, last + 1))
    else:
        blocks = tuple(int(value) for value in args.blocks.split(",") if value)
    if not blocks or min(blocks) < 0 or len(set(blocks)) != len(blocks):
        raise ValueError("--blocks must contain unique non-negative block indexes")
    budgets = tuple(int(value) for value in args.budgets.split(","))
    if any(value <= 0 or value >= len(blocks) for value in budgets):
        raise ValueError("Each budget must be between 1 and the number of available blocks minus one")

    development_rows = list(read_jsonl(args.development_manifest))
    ids = {str(row["id"]) for row in development_rows}
    baseline_all = prediction_map(args.baseline_dir / "predictions.jsonl")
    if not ids <= baseline_all.keys():
        raise ValueError("Baseline does not cover the development manifest")
    baseline = {row_id: baseline_all[row_id] for row_id in ids}
    block_drops = {}
    for block in blocks:
        predicted = prediction_map(args.ablation_dir / f"block-{block:02d}" / "predictions.jsonl")
        if not ids <= predicted.keys():
            raise ValueError(f"Block {block} does not cover the development manifest")
        block_drops[block] = drops(baseline, {row_id: predicted[row_id] for row_id in ids})

    rankings = {
        capability: sorted(blocks, key=lambda block: (block_drops[block][capability], block))
        for capability in CAPABILITIES
    }
    macro_drop = {block: sum(block_drops[block].values()) / len(CAPABILITIES) for block in blocks}
    generic_ranking = sorted(blocks, key=lambda block: (macro_drop[block], block))
    routes: dict[tuple[int, ...], dict] = {}
    for budget in budgets:
        add_route(routes, generic_ranking[:budget], {"route_type": "generic_macro", "budget": budget})
        start = min(
            range(len(blocks) - budget + 1),
            key=lambda start: sum(macro_drop[blocks[index]] for index in range(start, start + budget)),
        )
        add_route(routes, list(blocks[start:start + budget]), {"route_type": "contiguous_macro", "budget": budget})
        for capability in CAPABILITIES:
            add_route(routes, rankings[capability][:budget], {"route_type": "task_specific", "capability": capability, "budget": budget})
        for repeat in range(args.random_repeats):
            seed = args.seed + budget * 100 + repeat
            add_route(routes, random.Random(seed).sample(blocks, budget), {"route_type": "random", "budget": budget, "repeat": repeat, "seed": seed})

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "sensitivity.json", {
        "schema_version": 1,
        "evidence_status": "development-only one-block discovery for the current model",
        "allowed_blocks": list(blocks),
        "discovery_examples": len(baseline),
        "capability_counts": {capability: sum(row["capability"] == capability for row in baseline.values()) for capability in CAPABILITIES},
        "single_block_accuracy_drops": {str(block): block_drops[block] for block in blocks},
        "capability_rankings_least_to_most_sensitive": rankings,
        "generic_macro_ranking_least_to_most_sensitive": generic_ranking,
    })
    write_json(args.output_dir / "routes.json", list(routes.values()))
    write_jsonl(args.output_dir / "development-baseline" / "predictions.jsonl", [baseline[str(row["id"])] for row in development_rows])


if __name__ == "__main__":
    main()
