# arXiv Submission Metadata

This sheet is the canonical copy for the arXiv form. It matches the frozen manuscript source. Review every
field in the arXiv preview before submitting.

## Paper

- **Title:** Searching for Task-Specific Vision Paths: Evolutionary Block Pruning Across Vision-Language Models
- **Authors:** Tarun Tomar
- **Primary category:** `cs.CV`
- **Cross-list:** None proposed
- **Submission processor:** pdfLaTeX
- **Top-level file:** `main.tex`
- **Source candidate tag:** `arxiv-v1-candidate`
- **Comments:** 14 pages, 8 figures. Code and aggregate evidence: https://github.com/TarunTomar122/vision-pathways

## Abstract

Vision-language models normally execute the same complete vision encoder for every question, even when OCR,
counting, object, attribute, and spatial queries may not require identical computation. We study whether
fixed-budget combinations of vision blocks can be skipped without fine-tuning. A shared K-block route skips one
searched set of exactly K blocks for every question, while a capability-specific K-block policy selects one
same-size route using a known capability label. We introduce a source-balanced evolutionary search and compare
it with independent ranking, contiguous removal, and random routes at matched budgets. Experiments use
Qwen2.5-VL-3B-Instruct, SmolVLM2-2.2B-Instruct, and an 876-example image-disjoint selection split. Search
transfers across architectures: on SmolVLM2, the searched shared four-block route beats independent construction
by 4.91 percentage points. Capability specialization is less stable. On Qwen, the six-block capability policy
beats the shared route by 2.17 points, driven by a 7.10-point OCR gain. On sealed IIIT5K, however, the SmolVLM2
OCR-specific route trails its shared route by 13.6 points. Combinatorial search reliably improves route
construction, but capability labels do not define universally transferable vision pathways.

## Author Decisions Still Required

- **Affiliation:** Supply only a current, accurate affiliation. Leave blank if there is none.
- **Email and ORCID:** Confirm these in the arXiv account and author fields. They are not embedded in the paper.
- **Funding disclosure:** Confirm whether there is funding to disclose. None is asserted by this repository.
- **License:** Choose in arXiv after checking future venue and funder requirements. The choice is irrevocable.
- **Endorsement:** Confirm whether the arXiv account is already endorsed for `cs.CV`.
- **Submission agreement:** The human author must read and accept it.

## Upload

Upload `paper/arxiv-source.zip`. The archive contains only the TeX source, bibliography, generated table, and
eight PDF figures. Do not upload the repository or `paper/main.pdf` as the source package.

The acknowledgement discloses AI assistance for code, orchestration, figures, manuscript organization, and
language editing. The human author must review the complete PDF and accept responsibility before submission.
