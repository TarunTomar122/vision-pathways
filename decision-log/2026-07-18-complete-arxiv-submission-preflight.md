# Prepare Audited arXiv Submission Candidate

## Intended Commit Subject

`Prepare audited arXiv submission candidate`

## Problem Or Decision

The manuscript rendered and had an arXiv source archive, but it was not yet a defensible submission candidate.
The paper lacked an appendix containing exact routes and frozen hashes, Figure 8 occupied a poorly composed page,
several bibliography records were stale, the arXiv form fields were not recorded in one place, and the existing
package check did not compile the exact ZIP in a clean directory. The decision is to complete every automatable
preflight step while leaving irreversible or identity-dependent actions to the human author.

## Files And Behavior Changed

- `paper/main.tex` now keeps Figure 8 with its explanatory text, includes exact frozen routes, seeds, search
  settings, artifact hashes, repository tag, and an AI-assistance acknowledgement, and exposes the full title in
  PDF metadata.
- `paper/main.pdf` is rebuilt from the updated source as a 14-page reference render.
- `paper/references.bib` corrects OCRBench and VScan metadata and links FlowCut to the official NeurIPS record.
- `paper/arxiv-metadata.md` supplies the exact title, author, category, comments, abstract, processor, and upload
  instructions while identifying author-only fields.
- `paper/citation-audit.md` maps all 22 citations to primary sources and states how each is used.
- `paper/submission-checklist.md` distinguishes completed machine-verifiable work from human review, identity,
  endorsement, license, agreement, upload, and preview obligations.
- `scripts/arxiv_preflight.py` audits the exact archive file set, source hygiene, metadata constraints, citations,
  includes, clean compilation, TeX log, PDF encryption, page count, and font embedding.
- `Makefile` adds `arxiv-preflight`; `paper/README.md` documents the metadata, citation, package, and audit workflow.

## Alternatives Considered

- Uploading only `paper/main.pdf` was rejected because arXiv requires TeX source for TeX-authored submissions.
- Treating the existing repository build as sufficient was rejected because missing package files or hidden local
  dependencies can appear only when the exact archive is compiled in isolation.
- Inventing an affiliation, selecting a default license, or claiming human citation review was rejected because
  those are factual, irreversible, or author-responsibility decisions.
- Moving Figure 8 to its own forced page was rejected because it created unnecessary whitespace. Holding only
  Figure 8 in place and moving Figure 1 earlier preserve reading order, remove a sparse page, and keep the paper
  at 14 pages without overflow.

## Verification Evidence

- `make PYTHON=/tmp/vlm-paper-audit-venv/bin/python arxiv-preflight`
- `make PYTHON=/tmp/vlm-paper-audit-venv/bin/python verify-paper`
- `python3 -m py_compile scripts/arxiv_preflight.py`
- `pdfinfo paper/main.pdf`
- `pdffonts paper/main.pdf`
- Visual inspection of all final pages, with focused inspection of the Figure 8 and reproducibility pages.
- `rg -n '[–—]' README.md docs` to preserve the repository and website punctuation rule.
- The clean archive contains 11 expected files, cites 22 bibliography entries, builds to 14 pages, has a
  1,283-character abstract, emits no final TeX warnings, is unencrypted, and embeds every font.

## Known Limitations And Unsupported Claims

- This audit does not certify novelty, acceptance, or compliance with a future conference or journal policy.
- Agent-assisted metadata checking does not replace the author's reading and validation of every citation.
- No affiliation, funding status, email, ORCID, arXiv endorsement state, or distribution license is inferred.
- The repository cannot accept the submission agreement or inspect arXiv's server-generated preview.
- The paper does not evaluate a learned per-question router, edge hardware, compact checkpoint export, final Qwen
  route latency, or SmolVLM2 skip budgets above K4.

## Next Action Enabled

The author can upload `paper/arxiv-source.zip`, paste the reviewed fields from `paper/arxiv-metadata.md`, choose a
license, inspect the arXiv-generated PDF, and submit after completing the remaining human-review checklist items.
