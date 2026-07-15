#!/usr/bin/env python3
"""Run one or more conditions from the immutable external-evaluation protocol."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from vlm_bench.benchmark import BaselineRunner, summarize
from vlm_bench.external_eval import condition_blocks, prediction_map, validate_protocol
from vlm_bench.io import read_jsonl, sha256_file, write_json


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=Path("configs/external_frozen_evaluation.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/external-frozen-qwen25-vl-3b"))
    parser.add_argument("--conditions", nargs="+", required=True)
    parser.add_argument("--worker-name", required=True)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    unknown = set(args.conditions) - set(protocol["conditions"])
    if unknown:
        raise ValueError(f"Unknown conditions: {sorted(unknown)}")

    manifest = Path(protocol["manifest"])
    if sha256_file(manifest) != protocol["manifest_sha256"]:
        raise ValueError("External manifest hash differs from the frozen protocol")
    rows = list(read_jsonl(manifest))
    if len(rows) != protocol["examples"]:
        raise ValueError(f"Expected {protocol['examples']} rows, found {len(rows)}")
    expected_ids = {row["id"] for row in rows}
    model_config = json.loads(Path(protocol["model_config"]).read_text(encoding="utf-8"))
    if model_config["model_id"] != protocol["model_id"] or model_config["revision"] != protocol["model_revision"]:
        raise ValueError("Model configuration differs from the frozen protocol")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    state_path = args.output_dir / f"worker-{args.worker_name}.json"
    write_json(state_path, {
        "status": "running",
        "started_at": now(),
        "worker": args.worker_name,
        "conditions": args.conditions,
        "protocol_sha256": sha256_file(args.protocol),
    })
    runner = BaselineRunner(model_config, manifest, args.output_dir / f"runner-{args.worker_name}", manifest.parent.parent)
    try:
        for condition_name in args.conditions:
            condition_dir = args.output_dir / condition_name
            condition_dir.mkdir(parents=True, exist_ok=True)
            predictions_path = condition_dir / "predictions.jsonl"
            existing_rows = list(read_jsonl(predictions_path)) if predictions_path.exists() else []
            existing = prediction_map(existing_rows)
            if not set(existing) <= expected_ids:
                raise ValueError(f"Unexpected prediction IDs in {predictions_path}")
            pending = [row for row in rows if row["id"] not in existing]
            active_blocks = None
            mode = "a" if predictions_path.exists() else "w"
            with predictions_path.open(mode, encoding="utf-8", buffering=1) as handle:
                for index, row in enumerate(pending, start=1):
                    blocks = condition_blocks(protocol, condition_name, row["capability"])
                    if blocks != active_blocks:
                        runner.set_skip_vision_blocks(blocks)
                        active_blocks = blocks
                    prediction = runner.predict(row)
                    prediction["condition"] = condition_name
                    prediction["skip_vision_blocks"] = blocks
                    handle.write(json.dumps(prediction, sort_keys=True) + "\n")
                    existing[row["id"]] = prediction
                    if index == 1 or index % 25 == 0 or index == len(pending):
                        print(
                            f"[{condition_name}] {index}/{len(pending)} pending; "
                            f"{len(existing)}/{len(rows)} saved",
                            flush=True,
                        )
            completed = [existing[row["id"]] for row in rows]
            write_json(condition_dir / "summary.json", summarize(completed))
            write_json(condition_dir / "run_metadata.json", {
                "condition": condition_name,
                "condition_spec": protocol["conditions"][condition_name],
                "completed_at": now(),
                "examples_completed": len(completed),
                "manifest_sha256": protocol["manifest_sha256"],
                "model_config": model_config,
                "protocol_sha256": sha256_file(args.protocol),
                "timing_valid_for_speed_claims": False,
            })
    finally:
        runner.close()
    write_json(state_path, {
        "status": "complete",
        "completed_at": now(),
        "worker": args.worker_name,
        "conditions": args.conditions,
        "protocol_sha256": sha256_file(args.protocol),
    })


if __name__ == "__main__":
    main()
