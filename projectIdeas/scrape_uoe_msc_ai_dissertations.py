#!/usr/bin/env python3
"""Scrape UoE Informatics MSc dissertation metadata and filter AI programme."""

from __future__ import annotations

import csv
import io
import re
import ssl
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path

from pypdf import PdfReader

BASE_URL = "https://project-archive.inf.ed.ac.uk/msc"
OUTSTANDING_PAGES = {
    "2023-2024": "2024-outstanding.html",
    "2024-2025": "2025-outstanding.html",
    "2022-2023": "2023-outstanding.html",
}
TARGET_ACADEMIC_YEARS = {"2023-2024", "2024-2025"}
OUTPUT_CSV = Path(__file__).parent / "uoe_msc_ai_dissertations.csv"
OUTPUT_ALL_CSV = Path(__file__).parent / "uoe_msc_all_outstanding_dissertations.csv"
OUTPUT_EXTENDED_AI_CSV = Path(__file__).parent / "uoe_msc_ai_dissertations_extended.csv"
MAX_WORKERS = 8
REQUEST_TIMEOUT = 45

AI_PROGRAM_PATTERNS = [
    r"master\s+of\s+science\s+artificial\s+intelligence",
    r"msc\s+artificial\s+intelligence",
    r"artificial\s+intelligence\s+school\s+of\s+informatics",
]

OTHER_PROGRAM_PATTERNS = [
    r"computer\s+science",
    r"data\s+science",
    r"design\s+informatics",
    r"cognitive\s+science",
    r"speech\s+and\s+language\s+processing",
    r"cyber\s+security",
    r"blockchain",
    r"informatics\s+\(?\s*general",
    r"advanced\s+technology",
    r"statistics",
    r"operational\s+research",
]

ctx = ssl.create_default_context()


@dataclass
class Dissertation:
    academic_year: str
    author: str
    title: str
    project_id: str
    pdf_url: str
    degree_program: str
    is_msc_ai: bool
    submission_year: str
    abstract_snippet: str
    source: str


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research scraper)"})
    with urllib.request.urlopen(req, context=ctx, timeout=REQUEST_TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research scraper)"})
    with urllib.request.urlopen(req, context=ctx, timeout=REQUEST_TIMEOUT) as resp:
        return resp.read()


def parse_outstanding_page(html: str, academic_year: str) -> list[dict]:
    rows = re.findall(
        r"<tr><td>\s*([^<]+)</td><td><a href=\"([^\"]+)\">\s*([^<]+)</a></td></tr>",
        html,
        flags=re.IGNORECASE,
    )
    projects = []
    for author, rel_path, title in rows:
        author = re.sub(r"\s+", " ", author).strip()
        title = re.sub(r"\s+", " ", title).strip()
        project_id = rel_path.split("/")[0]
        projects.append(
            {
                "academic_year": academic_year,
                "author": author,
                "title": title,
                "project_id": project_id,
                "pdf_url": f"{BASE_URL}/{rel_path}",
            }
        )
    return projects


def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_program(text: str) -> tuple[str, bool]:
    lowered = normalize_text(text).lower()

    if any(re.search(p, lowered) for p in AI_PROGRAM_PATTERNS):
        return "MSc Artificial Intelligence", True

    for pattern in OTHER_PROGRAM_PATTERNS:
        if re.search(pattern, lowered):
            label = pattern.replace(r"\s+", " ").replace("\\", "")
            return f"MSc {label.title()}", False

    if "master of science" in lowered:
        # Cover pages sometimes split programme name across PDF text lines.
        cover_block = lowered.split("abstract", 1)[0]
        if re.search(r"artificial\s+intelligence", cover_block):
            return "MSc Artificial Intelligence", True

        match = re.search(
            r"master of science\s+([a-z][a-z\s/&-]{2,60}?)(?:school of informatics|university of edinburgh)",
            lowered,
        )
        if match:
            program = normalize_text(match.group(1)).title()
            is_ai = "artificial intelligence" in program.lower()
            return f"MSc {program}", is_ai

        if re.search(
            r"master of science.+?school of informatics",
            cover_block,
            flags=re.DOTALL,
        ):
            return "MSc School Of Informatics", False

    return "Unknown", False


def extract_submission_year(text: str) -> str:
    match = re.search(r"university of edinburgh\s+(\d{4})", text.lower())
    return match.group(1) if match else ""


def extract_abstract_snippet(reader: PdfReader) -> str:
    chunks: list[str] = []
    for page in reader.pages[:3]:
        page_text = page.extract_text() or ""
        chunks.append(page_text)
    joined = normalize_text(" ".join(chunks))
    match = re.search(r"abstract[:\s]+(.{120,600}?)(?:keywords|contents|chapter|introduction|\d+\s+introduction)",
                     joined, flags=re.IGNORECASE)
    if match:
        return match.group(1)[:500]
    return joined[:400]


def enrich_project(project: dict) -> Dissertation:
    pdf_url = project["pdf_url"]
    degree_program = "Unknown"
    is_msc_ai = False
    submission_year = ""
    abstract_snippet = ""

    try:
        pdf_bytes = fetch_bytes(pdf_url)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        first_pages = []
        for page in reader.pages[:2]:
            first_pages.append(page.extract_text() or "")
        cover_text = "\n".join(first_pages)
        degree_program, is_msc_ai = detect_program(cover_text)
        submission_year = extract_submission_year(cover_text)
        abstract_snippet = extract_abstract_snippet(reader)
    except Exception as exc:  # noqa: BLE001 - keep scraping on individual failures
        abstract_snippet = f"PDF parse error: {exc}"

    return Dissertation(
        academic_year=project["academic_year"],
        author=project["author"],
        title=project["title"],
        project_id=project["project_id"],
        pdf_url=pdf_url,
        degree_program=degree_program,
        is_msc_ai=is_msc_ai,
        submission_year=submission_year,
        abstract_snippet=abstract_snippet,
        source="UoE Informatics Outstanding MSc Archive",
    )


def write_csv(path: Path, rows: list[Dissertation]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(asdict(rows[0]).keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def main() -> None:
    all_projects: list[dict] = []
    for academic_year, page in OUTSTANDING_PAGES.items():
        print(f"Fetching {page} ({academic_year})...")
        html = fetch_text(f"{BASE_URL}/{page}")
        projects = parse_outstanding_page(html, academic_year)
        print(f"  Found {len(projects)} listed projects")
        all_projects.extend(projects)

    # Deduplicate by project_id
    deduped: dict[str, dict] = {}
    for project in all_projects:
        deduped[project["project_id"]] = project
    projects = list(deduped.values())
    print(f"Total unique projects to process: {len(projects)}")

    dissertations: list[Dissertation] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(enrich_project, p): p for p in projects}
        for i, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            dissertations.append(result)
            status = "AI" if result.is_msc_ai else result.degree_program
            print(f"[{i}/{len(projects)}] {result.author[:30]:30} | {status}")
            time.sleep(0.05)

    dissertations.sort(key=lambda d: (d.academic_year, d.author.lower()))

    recent = [d for d in dissertations if d.academic_year in TARGET_ACADEMIC_YEARS]
    ai_recent = [d for d in recent if d.is_msc_ai]
    ai_all_years = [d for d in dissertations if d.is_msc_ai]
    write_csv(OUTPUT_ALL_CSV, recent)
    write_csv(OUTPUT_CSV, ai_recent)
    write_csv(OUTPUT_EXTENDED_AI_CSV, ai_all_years)

    print("\nDone.")
    print(f"Recent outstanding dissertations ({', '.join(sorted(TARGET_ACADEMIC_YEARS))}): {len(recent)} -> {OUTPUT_ALL_CSV}")
    print(f"MSc AI dissertations (last 2 academic years): {len(ai_recent)} -> {OUTPUT_CSV}")
    print(f"MSc AI dissertations (all scraped years):      {len(ai_all_years)} -> {OUTPUT_EXTENDED_AI_CSV}")


if __name__ == "__main__":
    main()
