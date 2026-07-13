#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from vlm_bench.validation import validate_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a prepared capability manifest")
    parser.add_argument("--manifest", type=Path, default=Path("data/processed/manifests/all.jsonl"))
    parser.add_argument("--data-root", type=Path, default=Path("data/processed"))
    parser.add_argument("--skip-hashes", action="store_true")
    args = parser.parse_args()
    result = validate_manifest(args.manifest, args.data_root, verify_hashes=not args.skip_hashes)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
