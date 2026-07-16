#!/usr/bin/env python3
"""Run frozen matched-K controls after robust routes have been selected."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from vlm_bench.benchmark import BaselineRunner
from vlm_bench.io import read_jsonl, sha256_file, write_json
from vlm_bench.robust_search import normalize_route


CAPABILITIES = ("attribute", "counting", "object", "ocr", "spatial")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_map(path: Path) -> dict[str, dict]:
    rows = {}
    if not path.exists():
        return rows
    for row in read_jsonl(path):
        row_id = str(row["id"])
        if row_id in rows:
            raise ValueError(f"Duplicate prediction ID {row_id} in {path}")
        rows[row_id] = row
    return rows


def validate_config(config: dict, manifest: Path) -> None:
    if sha256_file(manifest) != config["selection_manifest_sha256"]:
        raise ValueError("Selection manifest does not match the frozen control config")
    expected_k_values = sorted(int(value) for value in config.get("k_values", [4, 6, 8]))
    if sorted(int(value) for value in config["conditions"]) != expected_k_values:
        raise ValueError(f"Control config must define exactly K values {expected_k_values}")
    allowed_blocks = tuple(int(value) for value in config.get("allowed_blocks", range(32)))
    if not allowed_blocks:
        raise ValueError("Control config must define at least one allowed vision block")
    for raw_k, conditions in config["conditions"].items():
        k = int(raw_k)
        required = {"generic-independent", "task-independent", "contiguous", "random-0", "random-1", "random-2"}
        if set(conditions) != required:
            raise ValueError(f"K{k} controls do not match the frozen registry")
        for name, condition in conditions.items():
            routes = condition.get("routes", {}).values() if condition["kind"] == "conditional" else [condition["blocks"]]
            if condition["kind"] == "conditional" and set(condition["routes"]) != set(CAPABILITIES):
                raise ValueError(f"{name} K{k} does not define all capabilities")
            for route in routes:
                normalize_route(route, k=k, allowed_blocks=allowed_blocks)


def run_condition(
    runner: BaselineRunner,
    rows: list[dict],
    condition: dict,
    output_dir: Path,
    label: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = output_dir / "predictions.jsonl"
    existing = load_map(predictions_path)
    mode = "a" if predictions_path.exists() else "w"
    with predictions_path.open(mode, encoding="utf-8", buffering=1) as handle:
        grouped = (
            [(None, rows)]
            if condition["kind"] == "fixed"
            else [
                (capability, [row for row in rows if row["capability"] == capability])
                for capability in CAPABILITIES
            ]
        )
        for capability, group in grouped:
            blocks = condition["blocks"] if capability is None else condition["routes"][capability]
            runner.set_skip_vision_blocks(blocks)
            pending = [row for row in group if str(row["id"]) not in existing]
            for index, row in enumerate(pending, start=1):
                prediction = runner.predict(row)
                handle.write(json.dumps(prediction, sort_keys=True) + "\n")
                existing[str(row["id"])] = prediction
                if index == 1 or index % 25 == 0 or index == len(pending):
                    suffix = f" {capability}" if capability else ""
                    print(f"[{label}{suffix}] {index}/{len(pending)} new predictions", flush=True)
    expected = {str(row["id"]) for row in rows}
    if set(existing) != expected:
        raise RuntimeError(f"{label} cache does not exactly cover the selection manifest")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/robust_route_controls.json"))
    parser.add_argument("--frozen-routes", type=Path, default=Path("results/robust-route-search-qwen25-vl-3b/frozen_routes.json"))
    args = parser.parse_args()

    if not args.frozen_routes.exists():
        raise FileNotFoundError("Robust routes must be finalized before control inference")
    frozen_routes = json.loads(args.frozen_routes.read_text(encoding="utf-8"))
    if frozen_routes.get("status") != "frozen":
        raise ValueError("Robust route registry is not frozen")

    config = json.loads(args.config.read_text(encoding="utf-8"))
    manifest = Path(config["selection_manifest"])
    validate_config(config, manifest)
    rows = list(read_jsonl(manifest))
    model_config_path = Path(config["model_config"])
    model_config = json.loads(model_config_path.read_text(encoding="utf-8"))
    output_root = Path(config["output_dir"])
    state = {
        "status": "running",
        "started_at": now(),
        "config_sha256": sha256_file(args.config),
        "frozen_routes_sha256": sha256_file(args.frozen_routes),
        "selection_manifest_sha256": sha256_file(manifest),
        "conditions": {},
    }
    write_json(output_root / "state.json", state)
    runner = BaselineRunner(model_config, manifest, output_root / "runtime", Path(config["data_root"]))
    try:
        for _ in range(int(model_config.get("warmup_examples", 0))):
            runner.predict(rows[0])
        for raw_k, conditions in config["conditions"].items():
            for name, condition in conditions.items():
                key = f"k{int(raw_k):02d}-{name}"
                run_condition(runner, rows, condition, output_root / key, key)
                state["conditions"][key] = {"status": "complete", "completed_at": now()}
                write_json(output_root / "state.json", state)
        state["status"] = "complete"
        state["completed_at"] = now()
    except Exception as error:
        state["status"] = "failed"
        state["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        runner.close()
        write_json(output_root / "state.json", state)


if __name__ == "__main__":
    main()
