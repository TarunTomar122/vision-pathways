#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from vlm_bench.benchmark import BaselineRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the deterministic unpruned VLM baseline")
    parser.add_argument("--config", type=Path, default=Path("configs/baseline_qwen25_vl_3b.json"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--suite", choices=["controlled", "external"])
    parser.add_argument("--split", choices=["development", "test"])
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    runner = BaselineRunner(config, args.manifest, args.output_dir, args.data_root)
    try:
        summary = runner.run(limit=args.limit, suite=args.suite, split=args.split)
        print(json.dumps(summary, indent=2, sort_keys=True))
    finally:
        runner.close()


if __name__ == "__main__":
    main()
