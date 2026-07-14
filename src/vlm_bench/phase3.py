"""Pure helpers for interaction-aware vision-route search."""

from __future__ import annotations

from collections.abc import Iterable


CAPABILITIES = ("attribute", "counting", "object", "ocr", "spatial")


def route_key(blocks: Iterable[int]) -> str:
    normalized = tuple(sorted(int(block) for block in blocks))
    return "-".join(f"b{block:02d}" for block in normalized)


def select_task_seed(routes: list[dict], capability: str, budget: int = 4) -> tuple[int, ...]:
    matches = []
    for route in routes:
        if len(route["skip_vision_blocks"]) != budget:
            continue
        for assignment in route.get("assignments", []):
            if assignment.get("route_type") == "task_specific" and assignment.get("capability") == capability:
                matches.append(tuple(sorted(route["skip_vision_blocks"])))
    if len(matches) != 1:
        raise ValueError(f"Expected one {capability} task seed at budget {budget}; found {len(matches)}")
    return matches[0]


def capability_pool(sensitivity: dict, capability: str, size: int) -> tuple[int, ...]:
    ranking = sensitivity["capability_rankings_least_to_most_sensitive"][capability]
    if not 0 < size <= len(ranking):
        raise ValueError(f"Invalid candidate-pool size {size}")
    return tuple(int(block) for block in ranking[:size])


def expand_beam(beam: list[tuple[int, ...]], candidate_pool: tuple[int, ...]) -> list[dict]:
    """Expand every retained route by one block and deduplicate convergent children."""
    children = {}
    for parent in beam:
        parent_set = set(parent)
        for block in candidate_pool:
            if block in parent_set:
                continue
            child = tuple(sorted((*parent, block)))
            record = children.setdefault(child, {"blocks": child, "parents": [], "added_blocks": []})
            record["parents"].append(parent)
            record["added_blocks"].append(block)
    return [children[key] for key in sorted(children)]


def paired_metrics(baseline: dict[str, dict], variant: dict[str, dict], ids: list[str]) -> dict:
    missing = [row_id for row_id in ids if row_id not in baseline or row_id not in variant]
    if missing:
        raise ValueError(f"Missing paired predictions for {missing[:5]}")
    baseline_correct = [bool(baseline[row_id]["correct"]) for row_id in ids]
    variant_correct = [bool(variant[row_id]["correct"]) for row_id in ids]
    base_accuracy = sum(baseline_correct) / len(ids)
    variant_accuracy = sum(variant_correct) / len(ids)
    return {
        "examples": len(ids),
        "baseline_accuracy": base_accuracy,
        "variant_accuracy": variant_accuracy,
        "accuracy_drop_pp": 100 * (base_accuracy - variant_accuracy),
        "lost_correct": sum(base and not candidate for base, candidate in zip(baseline_correct, variant_correct)),
        "recovered_correct": sum(not base and candidate for base, candidate in zip(baseline_correct, variant_correct)),
    }


def interaction_pp(single_i_drop: float, single_j_drop: float, pair_drop: float) -> float:
    return pair_drop - single_i_drop - single_j_drop
