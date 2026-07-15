"""Frozen external-evaluation routing and paired accuracy helpers."""

from __future__ import annotations

import random
import statistics


def validate_protocol(protocol: dict) -> None:
    capabilities = set(protocol["capabilities"])
    conditions = protocol["conditions"]
    if "full" not in conditions:
        raise ValueError("The frozen protocol must include a full-model condition")
    for name, condition in conditions.items():
        kind = condition.get("kind")
        if kind == "fixed":
            routes = [condition["blocks"]]
        elif kind == "conditional":
            if set(condition["routes"]) != capabilities:
                raise ValueError(f"{name} does not define exactly one route per capability")
            routes = condition["routes"].values()
        else:
            raise ValueError(f"Unsupported condition kind for {name}: {kind!r}")
        for blocks in routes:
            if blocks != sorted(set(blocks)) or any(block < 0 or block >= 32 for block in blocks):
                raise ValueError(f"Invalid blocks in condition {name}: {blocks}")


def condition_blocks(protocol: dict, condition_name: str, capability: str) -> list[int]:
    condition = protocol["conditions"][condition_name]
    if condition["kind"] == "fixed":
        return list(condition["blocks"])
    return list(condition["routes"][capability])


def prediction_map(rows: list[dict]) -> dict[str, dict]:
    mapped = {}
    for row in rows:
        if row["id"] in mapped:
            raise ValueError(f"Duplicate prediction ID: {row['id']}")
        mapped[row["id"]] = row
    return mapped


def paired_accuracy(baseline: dict[str, dict], candidate: dict[str, dict], ids: list[str]) -> dict:
    if not ids:
        raise ValueError("Cannot compare an empty set")
    baseline_values = [float(bool(baseline[row_id]["correct"])) for row_id in ids]
    candidate_values = [float(bool(candidate[row_id]["correct"])) for row_id in ids]
    baseline_accuracy = statistics.fmean(baseline_values)
    candidate_accuracy = statistics.fmean(candidate_values)
    return {
        "examples": len(ids),
        "baseline_accuracy": baseline_accuracy,
        "candidate_accuracy": candidate_accuracy,
        "accuracy_drop_pp": 100 * (baseline_accuracy - candidate_accuracy),
        "lost_correct": sum(base > candidate for base, candidate in zip(baseline_values, candidate_values)),
        "recovered_correct": sum(base < candidate for base, candidate in zip(baseline_values, candidate_values)),
    }


def bootstrap_advantage(
    left: dict[str, dict], right: dict[str, dict], ids: list[str], seed: int, iterations: int = 10_000,
) -> dict:
    """Return paired accuracy(left - right) in percentage points."""
    values = [
        float(bool(left[row_id]["correct"])) - float(bool(right[row_id]["correct"]))
        for row_id in ids
    ]
    rng = random.Random(seed)
    count = len(values)
    estimates = sorted(
        statistics.fmean(values[rng.randrange(count)] for _ in range(count))
        for _ in range(iterations)
    )
    return {
        "examples": count,
        "mean_pp": 100 * statistics.fmean(values),
        "ci95_low_pp": 100 * estimates[int(0.025 * iterations)],
        "ci95_high_pp": 100 * estimates[int(0.975 * iterations)],
    }
