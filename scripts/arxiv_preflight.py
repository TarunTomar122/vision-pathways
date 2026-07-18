#!/usr/bin/env python3
"""Compile and audit the exact arXiv source archive in a clean directory."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "paper" / "arxiv-source.zip"
EXPECTED_FILES = {
    "main.tex",
    "references.bib",
    "tables/generated-main-results.tex",
    "figures/generated-cross-model-capability-heatmap.pdf",
    "figures/generated-efficiency-summary.pdf",
    "figures/generated-fresh-ocr-transfer.pdf",
    "figures/generated-matched-k4-controls.pdf",
    "figures/generated-method-overview.pdf",
    "figures/generated-qwen-accuracy-by-budget.pdf",
    "figures/generated-route-stability.pdf",
    "figures/generated-single-block-sensitivity.pdf",
}
FORBIDDEN_SOURCE = re.compile(
    r"TODO|TBD|FIXME|PLACEHOLDER|/home/|/Users/|password|private[_ -]?key|secret[_ -]?key",
    re.IGNORECASE,
)
BAD_LOG = re.compile(
    r"undefined citations?|undefined references?|multiply defined|"
    r"overfull \\|underfull \\|LaTeX Warning|Package .* Warning|! LaTeX Error",
    re.IGNORECASE,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    archive = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ARCHIVE
    require(archive.is_file(), f"Missing archive: {archive}")

    with zipfile.ZipFile(archive) as package:
        names = package.namelist()
        require(len(names) == len(set(names)), "Archive contains duplicate paths")
        require(set(names) == EXPECTED_FILES, "Archive file set differs from the frozen package")
        for name in names:
            require(re.fullmatch(r"[A-Za-z0-9_+.,=/\-]+", name) is not None, f"Invalid arXiv filename: {name}")
            require(not name.startswith("/") and ".." not in Path(name).parts, f"Unsafe archive path: {name}")
        source = "\n".join(
            package.read(name).decode("utf-8")
            for name in ("main.tex", "references.bib", "tables/generated-main-results.tex")
        )
        require(FORBIDDEN_SOURCE.search(source) is None, "Submission source contains a forbidden marker or local path")

        main_tex = package.read("main.tex").decode("utf-8")
        references = package.read("references.bib").decode("utf-8")
        require("\\title{" in main_tex and "\\author{" in main_tex, "Title or author is missing")
        require("\\today" not in main_tex, "Do not use a rebuild-dependent date")
        require("\\appendix" in main_tex and "Reproducibility Details" in main_tex, "Reproducibility appendix is missing")
        require("AI-assisted tools were used" in main_tex, "AI-assistance acknowledgement is missing")

        abstract_match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", main_tex, re.DOTALL)
        require(abstract_match is not None, "Abstract is missing")
        abstract = re.sub(r"\s+", " ", abstract_match.group(1)).strip()
        require(len(abstract) <= 1920, f"Abstract has {len(abstract)} characters; arXiv permits at most 1920")

        cited = set()
        for match in re.finditer(r"\\cite[pt]?\{([^}]+)\}", main_tex):
            cited.update(key.strip() for key in match.group(1).split(","))
        bibliography = set(re.findall(r"^@\w+\{([^,]+),", references, re.MULTILINE))
        require(cited <= bibliography, f"Missing BibTeX entries: {sorted(cited - bibliography)}")
        require(bibliography <= cited, f"Unused BibTeX entries: {sorted(bibliography - cited)}")

        referenced = set(re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", main_tex))
        referenced.update(re.findall(r"\\input\{([^}]+)\}", main_tex))
        require(referenced <= set(names), f"Missing included files: {sorted(referenced - set(names))}")

        with tempfile.TemporaryDirectory(prefix="arxiv-preflight-") as temporary:
            destination = Path(temporary)
            package.extractall(destination)
            result = subprocess.run(
                ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                cwd=destination,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            require(result.returncode == 0, f"Clean LaTeX build failed:\n{result.stdout[-4000:]}")

            log = (destination / "main.log").read_text(encoding="utf-8", errors="replace")
            bad_log_lines = [line for line in log.splitlines() if BAD_LOG.search(line)]
            require(not bad_log_lines, "Final LaTeX log contains warnings:\n" + "\n".join(bad_log_lines))

            pdf = destination / "main.pdf"
            info = subprocess.run(
                ["pdfinfo", str(pdf)], check=True, text=True, stdout=subprocess.PIPE
            ).stdout
            require("Encrypted:       no" in info, "Generated PDF is encrypted")
            pages_match = re.search(r"^Pages:\s+(\d+)$", info, re.MULTILINE)
            require(pages_match is not None, "Could not determine generated page count")

            fonts = subprocess.run(
                ["pdffonts", str(pdf)], check=True, text=True, stdout=subprocess.PIPE
            ).stdout
            require(" no " not in fonts, "Generated PDF contains an unembedded or incomplete font")

    print(
        f"arXiv preflight passed: {len(names)} source files, {len(cited)} citations, "
        f"{pages_match.group(1)} pages, abstract {len(abstract)} characters"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
