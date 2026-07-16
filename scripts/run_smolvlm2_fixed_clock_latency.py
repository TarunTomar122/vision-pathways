#!/usr/bin/env python3
"""Lock GPU clocks and audit full versus frozen generic SmolVLM2 routes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from vlm_bench.io import write_json


def run(command: list[str]) -> dict:
    completed = subprocess.run(command, check=True, text=True, capture_output=True)
    return {"command": command, "stdout": completed.stdout, "stderr": completed.stderr}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-routes", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("results/fixed-clock-latency-smolvlm2-2b"))
    parser.add_argument("--graphics-mhz", type=int, default=2700)
    parser.add_argument("--memory-mhz", type=int, default=10501)
    args = parser.parse_args()
    frozen = json.loads(args.frozen_routes.read_text(encoding="utf-8"))
    if frozen.get("status") != "frozen":
        raise ValueError("Routes must be frozen before latency measurement")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    candidates = [
        {"name": f"frozen-generic-k{k}", "skip_vision_blocks": frozen["families"]["generic"]["budgets"][str(k)]["blocks"], "assignments": [{"route_type": "frozen_generic", "budget": k}]}
        for k in (4, 6, 8)
    ]
    candidate_path = args.output_dir / "candidates.json"
    write_json(candidate_path, candidates)
    clock_log = {"requested_graphics_mhz": args.graphics_mhz, "requested_memory_mhz": args.memory_mhz, "set": [], "restore": []}
    write_json(args.output_dir / "clock-control.json", clock_log)
    try:
        clock_log["set"].append(run(["sudo", "-n", "nvidia-smi", "-pm", "1"]))
        clock_log["set"].append(run(["sudo", "-n", "nvidia-smi", "-lgc", f"{args.graphics_mhz},{args.graphics_mhz}"]))
        clock_log["set"].append(run(["sudo", "-n", "nvidia-smi", "-lmc", f"{args.memory_mhz},{args.memory_mhz}"]))
        clock_log["set"].append(run(["nvidia-smi", "--query-gpu=name,clocks.current.graphics,clocks.current.memory", "--format=csv,noheader,nounits"]))
        write_json(args.output_dir / "clock-control.json", clock_log)
        for budget in (4, 6, 8):
            destination = args.output_dir / f"k{budget}"
            if (destination / "summary.json").exists():
                continue
            subprocess.run([
                sys.executable, "scripts/audit_route_latency.py",
                "--config", "configs/baseline_smolvlm2_2b.json",
                "--candidate-config", str(candidate_path),
                "--manifest", "data/processed-v2/manifests/development.jsonl",
                "--data-root", "data/processed-v2",
                "--output-dir", str(destination),
                "--budget", str(budget),
                "--per-capability", "10",
                "--repeats", "5",
            ], check=True)
    finally:
        for command in (["sudo", "-n", "nvidia-smi", "-rgc"], ["sudo", "-n", "nvidia-smi", "-rmc"]):
            try:
                clock_log["restore"].append(run(command))
            except subprocess.CalledProcessError as error:
                clock_log["restore"].append({"command": command, "returncode": error.returncode, "stdout": error.stdout, "stderr": error.stderr})
        write_json(args.output_dir / "clock-control.json", clock_log)


if __name__ == "__main__":
    main()
