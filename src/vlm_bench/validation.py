from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

from .io import read_jsonl, sha256_file


REQUIRED_FIELDS = {
    "id",
    "image",
    "image_sha256",
    "question",
    "answers",
    "answer_format",
    "capability",
    "subtype",
    "source",
    "source_split",
    "suite",
    "split",
    "metadata",
}


def validate_manifest(manifest: Path, data_root: Path, verify_hashes: bool = True) -> dict:
    rows = list(read_jsonl(manifest))
    if not rows:
        raise ValueError("Manifest is empty")

    ids = Counter(row.get("id") for row in rows)
    duplicate_ids = [key for key, count in ids.items() if count > 1]
    if duplicate_ids:
        raise ValueError(f"Duplicate IDs: {duplicate_ids[:5]}")

    image_splits: dict[str, set[str]] = defaultdict(set)
    checked_images: set[str] = set()
    for index, row in enumerate(rows):
        missing = REQUIRED_FIELDS - row.keys()
        if missing:
            raise ValueError(f"Row {index} is missing fields: {sorted(missing)}")
        if not row["question"].strip() or not row["answers"]:
            raise ValueError(f"Row {row['id']} has an empty question or answers")
        if row["answer_format"] not in {"binary", "integer", "short_text"}:
            raise ValueError(f"Row {row['id']} has an invalid answer format")
        image_splits[row["image_sha256"]].add(row["split"])
        image_path = data_root / row["image"]
        if not image_path.is_file():
            raise FileNotFoundError(f"Missing image for {row['id']}: {image_path}")
        if row["image_sha256"] not in checked_images:
            with Image.open(image_path) as image:
                image.verify()
            if verify_hashes and sha256_file(image_path) != row["image_sha256"]:
                raise ValueError(f"Image hash mismatch for {image_path}")
            checked_images.add(row["image_sha256"])

    leaked = [digest for digest, splits in image_splits.items() if len(splits) > 1]
    if leaked:
        raise ValueError(f"Images occur across development/test splits: {leaked[:5]}")

    return {
        "examples": len(rows),
        "unique_images": len(checked_images),
        "counts_by_source": dict(Counter(row["source"] for row in rows)),
        "counts_by_capability": dict(Counter(row["capability"] for row in rows)),
        "counts_by_suite": dict(Counter(row["suite"] for row in rows)),
        "counts_by_split": dict(Counter(row["split"] for row in rows)),
        "manifest_sha256": sha256_file(manifest),
    }
