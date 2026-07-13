#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

from vlm_bench.io import write_json


DEFAULT_MODELS = [
    "Qwen/Qwen2.5-VL-3B-Instruct",
    "HuggingFaceTB/SmolVLM2-2.2B-Instruct",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Download pinned model snapshots into the HF cache")
    parser.add_argument("models", nargs="*", default=DEFAULT_MODELS)
    parser.add_argument("--output", type=Path, default=Path("results/model_snapshots.json"))
    args = parser.parse_args()
    api = HfApi()
    resolved = {}
    for model_id in args.models:
        revision = api.model_info(model_id).sha
        path = snapshot_download(repo_id=model_id, revision=revision)
        resolved[model_id] = {"revision": revision, "cache_path": path}
        print(json.dumps({model_id: resolved[model_id]}, indent=2), flush=True)
    write_json(args.output, resolved)


if __name__ == "__main__":
    main()
