#!/usr/bin/env python3
"""Restore the frozen V2 manifest and images after rebuilding sources changes row selection."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import time
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

from vlm_bench.dataset_builder import SEED, _stable_int
from vlm_bench.io import read_jsonl, sha256_file, write_json, write_jsonl


TALLYQA_REVISION = "2636200d9845bf54d545ed9e66b2957532c5bf13"


def encode_png(image: Image.Image) -> bytes:
    converted = image.convert("RGB")
    try:
        buffer = io.BytesIO()
        converted.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()
    finally:
        converted.close()
        image.close()


def write_verified_image(row: dict, payload: bytes, data_root: Path) -> None:
    actual = hashlib.sha256(payload).hexdigest()
    if actual != row["image_sha256"]:
        raise ValueError(f"Image hash mismatch for {row['id']}: expected {row['image_sha256']}, got {actual}")
    destination = data_root / row["image"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)


def download_image(url: str, attempts: int = 3) -> Image.Image:
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return Image.open(io.BytesIO(response.read()))
        except Exception:
            if attempt == attempts:
                raise
            time.sleep(attempt * 2)
    raise AssertionError("unreachable")


def materialize_url_row(row: dict, data_root: Path) -> str:
    if row["source"] == "vsr":
        url = row["metadata"]["image_url"]
    elif row["source"] == "pope":
        image_source = row["metadata"]["image_source"]
        filename = image_source if image_source.lower().endswith(".jpg") else f"{image_source}.jpg"
        url = f"https://s3.amazonaws.com/images.cocodataset.org/val2014/{filename}"
    else:
        raise ValueError(f"Unsupported URL source: {row['source']}")
    write_verified_image(row, encode_png(download_image(url)), data_root)
    return row["id"]


def materialize_tallyqa(rows: list[dict], data_root: Path) -> None:
    if not rows:
        return
    from datasets import load_dataset

    by_index = {
        int(row["id"].split("/", 1)[1].split("-", 1)[0]): row
        for row in rows
    }
    dataset = load_dataset(
        "vikhyatk/tallyqa-test",
        split="test",
        revision=TALLYQA_REVISION,
        streaming=True,
    )
    remaining = set(by_index)
    for index, source in enumerate(dataset):
        if index in remaining:
            write_verified_image(by_index[index], encode_png(source["image"]), data_root)
            remaining.remove(index)
            print(f"[tallyqa] restored {len(by_index) - len(remaining)}/{len(by_index)}", flush=True)
        if not remaining:
            break
    if remaining:
        raise ValueError(f"TallyQA indices were not found: {sorted(remaining)[:10]}")


def frozen_rows(v1_manifest: Path, rebuilt_v2_manifest: Path) -> list[dict]:
    v1_rows = list(read_jsonl(v1_manifest))
    vqav2_rows = [row for row in read_jsonl(rebuilt_v2_manifest) if row["source"] == "vqav2_color"]
    if len(v1_rows) != 1480 or len(vqav2_rows) != 300:
        raise ValueError(f"Expected 1480 frozen V1 rows and 300 VQAv2 rows, got {len(v1_rows)} and {len(vqav2_rows)}")
    rows = sorted([*v1_rows, *vqav2_rows], key=lambda row: row["id"])
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Recovered V2 rows contain duplicate IDs")
    return rows


def write_manifests(rows: list[dict], manifest_root: Path, rebuilt_summary: dict) -> dict:
    write_jsonl(manifest_root / "all.jsonl", rows)
    for suite in sorted({row["suite"] for row in rows}):
        write_jsonl(manifest_root / f"{suite}.jsonl", [row for row in rows if row["suite"] == suite])
    for split in sorted({row["split"] for row in rows}):
        write_jsonl(manifest_root / f"{split}.jsonl", [row for row in rows if row["split"] == split])
    smoke = []
    for capability in sorted({row["capability"] for row in rows}):
        candidates = [row for row in rows if row["capability"] == capability and row["split"] == "development"]
        candidates.sort(key=lambda row: _stable_int(row["id"]))
        smoke.extend(candidates[:20])
    write_jsonl(manifest_root / "smoke.jsonl", sorted(smoke, key=lambda row: row["id"]))
    summary = {
        **rebuilt_summary,
        "seed": SEED,
        "total_examples": len(rows),
        "unique_images": len({row["image_sha256"] for row in rows}),
        "counts_by_suite": dict(Counter(row["suite"] for row in rows)),
        "counts_by_capability": dict(Counter(row["capability"] for row in rows)),
        "counts_by_source": dict(Counter(row["source"] for row in rows)),
        "counts_by_split": dict(Counter(row["split"] for row in rows)),
    }
    summary["manifest_sha256"] = sha256_file(manifest_root / "all.jsonl")
    write_json(manifest_root / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1-manifest", type=Path, default=Path("data/processed/manifests/all.jsonl"))
    parser.add_argument("--data-root", type=Path, default=Path("data/processed-v2"))
    parser.add_argument(
        "--expected-development-sha256",
        default="b7c097e8cea30d5c070d9ef03bacfb853b5967756d5282ba78c8575354e4ffae",
    )
    args = parser.parse_args()
    manifest_root = args.data_root / "manifests"
    rebuilt_manifest = manifest_root / "all.jsonl"
    rebuilt_summary = json.loads((manifest_root / "summary.json").read_text(encoding="utf-8"))
    rows = frozen_rows(args.v1_manifest, rebuilt_manifest)

    missing = [row for row in rows if not (args.data_root / row["image"]).exists()]
    by_source = Counter(row["source"] for row in missing)
    unsupported = set(by_source) - {"tallyqa", "pope", "vsr"}
    if unsupported:
        raise ValueError(f"Cannot restore missing image sources: {sorted(unsupported)}")
    print(f"Missing frozen images: {dict(by_source)}", flush=True)

    url_rows = [row for row in missing if row["source"] in {"pope", "vsr"}]
    with ThreadPoolExecutor(max_workers=8) as executor:
        for index, _ in enumerate(executor.map(lambda row: materialize_url_row(row, args.data_root), url_rows), start=1):
            if index == 1 or index % 25 == 0 or index == len(url_rows):
                print(f"[url images] restored {index}/{len(url_rows)}", flush=True)
    materialize_tallyqa([row for row in missing if row["source"] == "tallyqa"], args.data_root)

    summary = write_manifests(rows, manifest_root, rebuilt_summary)
    development_sha = sha256_file(manifest_root / "development.jsonl")
    if development_sha != args.expected_development_sha256:
        raise ValueError(
            f"Recovered development manifest mismatch: expected {args.expected_development_sha256}, got {development_sha}"
        )
    print(json.dumps({**summary, "development_manifest_sha256": development_sha}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
