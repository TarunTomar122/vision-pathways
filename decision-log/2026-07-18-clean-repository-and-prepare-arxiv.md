# Clean Repository And Prepare arXiv Submission

## Intended Commit Subject

`Clean paper artifacts and document arXiv submission`

## Problem Or Decision

The repository tracked a reproducible Overleaf ZIP and two duplicate figure formats in addition to
the PDF figures consumed by LaTeX and the PNG figures consumed by GitHub Pages. The website linked to
the paper directory instead of the current PDF, its artifact count and method alt text were stale,
and the submission checklist did not describe the current arXiv 1.5 workflow or the human-review
obligations created by substantial AI assistance.

## Exact Changes

- Removed the committed `paper/overleaf-package.zip`; it remains reproducible with
  `make overleaf-package` and is now ignored by Git.
- Removed the 16 duplicate `paper/figures/generated-*.png` and `*.svg` files. The eight canonical PDF
  figures remain tracked for LaTeX, and the eight website PNGs remain tracked once under
  `docs/assets/`.
- Updated `.gitignore` for local Overleaf/arXiv ZIPs and duplicate paper figure formats.
- Added `make arxiv-package`, which creates an ignored source archive containing `main.tex`,
  `references.bib`, eight PDF figures, and the generated LaTeX table.
- Updated `README.md` and `paper/README.md` with direct paper/site/source links, the canonical tracked
  artifact policy, and the distinction between submission sources and writing-history documents.
- Updated `docs/index.html` with a direct current-PDF link, LaTeX-source link, submission status,
  corrected seven-stage figure alt text, and the correct 24 generated figure-file count.
- Corrected `CITATION.cff` from the old `vlm-bench` URL to `vision-pathways` and advanced its release
  date/version metadata.
- Expanded `paper/submission-checklist.md` with the current arXiv upload sequence, endorsement,
  metadata, license, source-bundle, preview, correction, post-announcement, human review, citation
  verification, and AI-assistance disclosure checks.
- Changed model revision hashes in `paper/main.tex` to breakable monospace URLs and enabled `flafter`
  so floats cannot appear before their source location; rebuilt `paper/main.pdf`.

## Alternatives Considered

- Keeping every generated format was rejected because the paper PNGs duplicated website assets and
  the SVGs were not consumed by either delivery path.
- Removing the compiled PDF was rejected because it is the repository's easiest stable paper link and
  is useful for readers who do not build LaTeX.
- Removing Markdown drafts, protocol notes, or aggregate evidence was rejected because they are small,
  provide research history, and support auditability even though `main.tex` is canonical.
- Deleting ignored raw prediction caches was rejected because they are not uploaded to GitHub and may
  still be useful for local reanalysis; this cleanup does not destroy experiment evidence.
- Adding an AI disclosure directly to the manuscript was deferred because its claim that the human
  author reviewed everything must become true first. The checklist contains proposed wording and a
  hard human-review gate.

## Verification Evidence

- `make PYTHON=/tmp/vlm-paper-venv/bin/python submission` regenerated all 24 figure formats, tables,
  website assets, and paper data, then passed frozen-result and publication verification.
- `make PYTHON=/tmp/vlm-paper-venv/bin/python arxiv-package` built the intended source archive.
- The archive was extracted into `/tmp/vlm-arxiv-clean` and compiled independently with
  `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` under TeX Live 2025.
- The clean build produced 15 pages and 22 references with no matched LaTeX warnings, unresolved
  citations, unresolved references, overfull boxes, or underfull boxes.
- Rendered pages 6 through 11 were inspected after the hash and float-order fixes.
- A standard-library HTML audit confirmed unique IDs, valid fragment links, and all local website
  assets present.
- `git diff --check`, the README/site dash audit, and stale repository-link/count checks passed.

## Known Limitations And Unsupported Claims

- arXiv submission is not complete; the website intentionally says submission is pending.
- The human author must still supply or confirm affiliation, email, ORCID, acknowledgements, funding,
  license, metadata, category, endorsement status, and final AI disclosure.
- arXiv's official guide did not expose a separate generative-AI disclosure field when checked on
  2026-07-18, but a target conference, journal, employer, or funder may impose stricter rules.
- The arXiv license choice is irrevocable and was not selected by this commit.
- Removing files from the current tree does not erase their historical Git objects; no history rewrite
  was attempted or needed for this small repository.

## Next Action Enabled

Complete every unchecked human/AI item in `paper/submission-checklist.md`, reconcile the final
Overleaf manuscript with `paper/main.tex`, generate or export one final source ZIP, and upload it as a
new `cs.CV` submission. After arXiv announces the paper, replace the pending status with its identifier
and create a release tag from the submitted commit.
