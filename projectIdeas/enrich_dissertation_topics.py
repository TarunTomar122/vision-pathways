#!/usr/bin/env python3
"""Add lightweight topic buckets to dissertation CSV for analysis."""

from __future__ import annotations

import csv
import re
from pathlib import Path

INPUT = Path(__file__).parent / "uoe_msc_ai_dissertations.csv"
OUTPUT = Path(__file__).parent / "uoe_msc_ai_dissertations_with_topics.csv"
FULL_INPUT = Path(__file__).parent / "uoe_msc_ai_dissertations_extended.csv"
FULL_OUTPUT = Path(__file__).parent / "uoe_msc_ai_dissertations_extended_with_topics.csv"

TOPIC_RULES: list[tuple[str, list[str]]] = [
    ("LLMs & NLP", [r"\bllm\b", r"language model", r"text-to", r"discourse", r"translation", r"semantic", r"rag\b", r"prompt"]),
    ("Generative AI & Diffusion", [r"generative", r"diffusion", r"latent", r"pixel-based", r"storytelling"]),
    ("Computer Vision", [r"vision", r"image", r"3d object", r"segmentation", r"detection", r"nerf", r"polyp", r"satellite", r"tree species", r"mirror"]),
    ("Reinforcement Learning", [r"reinforcement", r"decision transformer", r"decision mamba", r"policy", r"atari", r"planning"]),
    ("Speech & Audio", [r"speech", r"audio", r"prosody", r"decipherment", r"spoken language"]),
    ("Recommender Systems", [r"recommend", r"sequential recommendation"]),
    ("Healthcare & Biology", [r"protein", r"medical", r"health", r"polyp", r"stroke", r"gesture", r"head gesture"]),
    ("Fairness, Ethics & Society", [r"fair", r"stereotype", r"gender", r"radicalization", r"privacy", r"ethic"]),
    ("Robotics & Autonomous Systems", [r"autonomous", r"autoware", r"lidar", r"driving", r"road user"]),
    ("Agents & Tool Use", [r"agent", r"multi-agent", r"tool-use", r"api call"]),
    ("Probabilistic ML", [r"probabilistic", r"tractable", r"quantiz", r"bayesian", r"einet", r"circuit"]),
    ("Efficiency & Systems", [r"efficient", r"caching", r"compression", r"low-rank", r"distributed", r"raspberry"]),
    ("Education & HCI Tools", [r"educational", r"gallery", r"game", r"visual solver", r"systematic review"]),
    ("Graph & Knowledge", [r"graph neural", r"knowledge graph", r"census", r"network"]),
    ("Finance & Industry", [r"financial", r"credit risk", r"insurance", r"startup"]),
]


def tag_topics(text: str) -> str:
    lowered = text.lower()
    hits: list[str] = []
    for topic, patterns in TOPIC_RULES:
        if any(re.search(p, lowered) for p in patterns):
            hits.append(topic)
    return "; ".join(hits) if hits else "Other / General AI"


def enrich(path_in: Path, path_out: Path, ai_only: bool) -> int:
    rows = list(csv.DictReader(path_in.open(encoding="utf-8")))
    if ai_only:
        rows = [r for r in rows if r.get("is_msc_ai") == "True"]

    for row in rows:
        blob = f"{row.get('title', '')} {row.get('abstract_snippet', '')}"
        row["topic_buckets"] = tag_topics(blob)

    if not rows:
        path_out.write_text("", encoding="utf-8")
        return 0

    fieldnames = list(rows[0].keys())
    with path_out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    n1 = enrich(INPUT, OUTPUT, ai_only=False)
    n2 = enrich(FULL_INPUT, FULL_OUTPUT, ai_only=False)
    print(f"Wrote {n1} rows -> {OUTPUT}")
    print(f"Wrote {n2} rows (all years, AI only) -> {FULL_OUTPUT}")


if __name__ == "__main__":
    main()
