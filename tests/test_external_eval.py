from vlm_bench.external_eval import (
    bootstrap_advantage,
    condition_blocks,
    paired_accuracy,
    validate_protocol,
)


def protocol() -> dict:
    return {
        "capabilities": ["ocr", "spatial"],
        "conditions": {
            "full": {"kind": "fixed", "blocks": []},
            "generic": {"kind": "fixed", "blocks": [1, 3]},
            "task": {"kind": "conditional", "routes": {"ocr": [2], "spatial": [4]}},
        },
    }


def test_protocol_validation_and_route_dispatch() -> None:
    value = protocol()
    validate_protocol(value)
    assert condition_blocks(value, "generic", "ocr") == [1, 3]
    assert condition_blocks(value, "task", "spatial") == [4]


def test_paired_accuracy_reports_percentage_point_drop_and_flips() -> None:
    baseline = {"a": {"correct": True}, "b": {"correct": True}, "c": {"correct": False}}
    candidate = {"a": {"correct": False}, "b": {"correct": True}, "c": {"correct": True}}
    result = paired_accuracy(baseline, candidate, ["a", "b", "c"])
    assert result["accuracy_drop_pp"] == 0
    assert result["lost_correct"] == 1
    assert result["recovered_correct"] == 1


def test_bootstrap_advantage_uses_paired_outcomes() -> None:
    left = {"a": {"correct": True}, "b": {"correct": True}}
    right = {"a": {"correct": False}, "b": {"correct": False}}
    result = bootstrap_advantage(left, right, ["a", "b"], seed=1, iterations=100)
    assert result["mean_pp"] == 100
    assert result["ci95_low_pp"] == 100
    assert result["ci95_high_pp"] == 100
