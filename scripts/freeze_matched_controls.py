#!/usr/bin/env python3
"""Freeze independent, contiguous, and random matched-K controls from a prior sweep."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from vlm_bench.io import sha256_file, write_json


CAPABILITIES = ("attribute", "counting", "object", "ocr", "spatial")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-config", type=Path, required=True)
    parser.add_argument("--selection-manifest", type=Path, required=True)
    parser.add_argument("--sensitivity", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--budgets", default="4,6,8")
    parser.add_argument("--seed", type=int, default=20260716)
    args = parser.parse_args()

    sensitivity = json.loads(args.sensitivity.read_text(encoding="utf-8"))
    blocks = tuple(int(value) for value in sensitivity["allowed_blocks"])
    rankings = {name: [int(value) for value in values] for name, values in sensitivity["capability_rankings_least_to_most_sensitive"].items()}
    generic = [int(value) for value in sensitivity["generic_macro_ranking_least_to_most_sensitive"]]
    drops = {int(key): value for key, value in sensitivity["single_block_accuracy_drops"].items()}
    macro = {block: sum(float(value) for value in drops[block].values()) / len(CAPABILITIES) for block in blocks}
    budgets = tuple(int(value) for value in args.budgets.split(","))
    if any(value <= 0 or value >= len(blocks) for value in budgets):
        raise ValueError("Invalid matched-control budget")
    conditions = {}
    for k in budgets:
        start = min(range(len(blocks) - k + 1), key=lambda index: sum(macro[blocks[item]] for item in range(index, index + k)))
        records = {
            "generic-independent": {"kind": "fixed", "blocks": generic[:k]},
            "task-independent": {"kind": "conditional", "routes": {capability: rankings[capability][:k] for capability in CAPABILITIES}},
            "contiguous": {"kind": "fixed", "blocks": list(blocks[start:start + k])},
        }
        for repeat in range(3):
            seed = args.seed + 10_000 + k * 100 + repeat
            records[f"random-{repeat}"] = {"kind": "fixed", "blocks": sorted(random.Random(seed).sample(blocks, k)), "seed": seed}
        conditions[str(k)] = records
    write_json(args.output, {
        "schema_version": 1,
        "status": "frozen before matched-control inference",
        "model_config": str(args.model_config),
        "selection_manifest": str(args.selection_manifest),
        "selection_manifest_sha256": sha256_file(args.selection_manifest),
        "data_root": "data/processed-v2",
        "output_dir": str(args.output_dir),
        "allowed_blocks": list(blocks),
        "k_values": list(budgets),
        "source_sensitivity_sha256": sha256_file(args.sensitivity),
        "seed_policy": "deterministic independent ranking, contiguous, and three random controls at each K",
        "selection_role": "comparison only; controls cannot change evolved route selection",
        "conditions": conditions,
    })


if __name__ == "__main__":
    main()
