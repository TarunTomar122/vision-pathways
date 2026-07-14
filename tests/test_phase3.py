from vlm_bench.benchmark import validate_skip_blocks
from vlm_bench.phase3 import expand_beam, interaction_pp, paired_metrics, route_key, select_task_seed


def test_validate_skip_blocks_normalizes_and_rejects_invalid_values() -> None:
    assert validate_skip_blocks([4, 1], 5) == [1, 4]
    for invalid in ([1, 1], [-1], [5]):
        try:
            validate_skip_blocks(invalid, 5)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected route to be rejected: {invalid}")


def test_expand_beam_deduplicates_children_from_multiple_parents() -> None:
    expanded = expand_beam([(1, 2), (1, 3)], (1, 2, 3, 4))
    by_key = {route_key(item["blocks"]): item for item in expanded}
    shared = by_key["b01-b02-b03"]
    assert len(shared["parents"]) == 2
    assert set(shared["added_blocks"]) == {2, 3}


def test_paired_metrics_counts_harmful_and_beneficial_flips() -> None:
    baseline = {"a": {"correct": True}, "b": {"correct": False}}
    variant = {"a": {"correct": False}, "b": {"correct": True}}
    result = paired_metrics(baseline, variant, ["a", "b"])
    assert result["accuracy_drop_pp"] == 0
    assert result["lost_correct"] == 1
    assert result["recovered_correct"] == 1


def test_interaction_and_seed_selection() -> None:
    assert interaction_pp(1.0, 2.0, 6.5) == 3.5
    routes = [{
        "skip_vision_blocks": [9, 2, 10, 30],
        "assignments": [{"route_type": "task_specific", "capability": "object", "budget": 4}],
    }]
    assert select_task_seed(routes, "object") == (2, 9, 10, 30)
