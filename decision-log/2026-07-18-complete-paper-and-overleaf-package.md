# Complete Manuscript And Add Verified Overleaf Package

## Intended Commit Subject

`Complete manuscript and add verified Overleaf package`

## Problem Or Decision

The research repository had a substantially complete Markdown draft and generated paper assets, but
it did not have a submission-ready LaTeX manuscript, a rendered bibliography, a downloadable PDF, or
an archive that could be imported directly into Overleaf. The paper also needed an end-to-end render
check so broken image paths, clipped figures, missing citations, and table overflow would be found
before publication work continued.

## Exact Changes

- Expanded `paper/draft.md` into the complete manuscript and linked its references section to the
  canonical bibliography and compiled paper.
- Added `paper/main.tex` with the abstract, numbered sections, mathematical method, experiments,
  limitations, related work, conclusion, 22 cited references, eight vector figures, and the generated
  main-results table.
- Added `paper/main.pdf`, the verified 14-page rendering of the manuscript.
- Added `paper/overleaf-package.zip` containing the LaTeX source, BibTeX database, eight PDF figures,
  and generated LaTeX table with working relative paths.
- Added `paper-pdf`, `overleaf-package`, and `clean-paper-latex` targets to `Makefile`.
- Updated `paper/README.md` with local build and Overleaf import instructions.
- Updated `.gitignore` to exclude LaTeX intermediate files while retaining the distributable PDF and
  ZIP archive.

## Alternatives Considered

- Keeping Markdown as the only manuscript source was rejected because it leaves figure placement,
  cross-references, and bibliography rendering unverified until late in submission preparation.
- Generating LaTeX only through Pandoc on every build was rejected because the generated figure and
  table markup required deliberate placement, captions, labels, and layout correction.
- Shipping only `main.tex` was rejected because Overleaf would then be missing the bibliography,
  generated table, and figure dependencies.
- Using raster PNG figures in the paper package was rejected in favor of the existing vector PDF
  figures for sharper text and plots.

## Verification Evidence

- `make PYTHON=/tmp/vlm-paper-venv/bin/python submission` regenerated all eight figure sets and passed
  frozen-result, table, research-document, and GitHub Pages verification.
- `make PYTHON=/tmp/vlm-paper-venv/bin/python overleaf-package` compiled the paper and created the ZIP.
- The ZIP was extracted into `/tmp/vlm-overleaf-test` and compiled independently with
  `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`.
- The independent build produced a 14-page PDF, rendered all 22 bibliography entries, and emitted no
  unresolved citation, unresolved reference, overfull box, underfull box, or LaTeX warning matched by
  the verification audit.
- Every rendered page was inspected as a PNG, including the title, all eight figures, the main table,
  equations, conclusion, and both reference pages.
- `git diff --check` passed.

## Known Limitations And Unsupported Claims

- The manuscript remains a working paper rather than a claim of peer review or acceptance.
- The author and repository metadata are intentionally minimal and may need affiliation, email,
  acknowledgements, venue style, and anonymous-review changes before submission.
- The 876-example partition is method-selection evidence, not a pristine sealed benchmark; only the
  250-example IIIT5K audit is a fresh post-freeze source-transfer test.
- SmolVLM2 has a completed four-block study only, and its latency result is an unlocked same-VM RTX
  4090 comparison. The paper does not claim fixed-clock, edge-device, energy, or complete Qwen
  final-route latency evidence.
- Identity skipping reduces executed vision depth but does not physically remove checkpoint weights.

## Next Action Enabled

Import `paper/overleaf-package.zip` into Overleaf, edit `paper/main.tex` for venue and author metadata,
and use the verified `paper/main.pdf` as the baseline when revising the manuscript.
