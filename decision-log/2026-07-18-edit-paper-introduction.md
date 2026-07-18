# Edit the Paper Introduction and Add a Motivation Figure

## Intended commit subject

`Edit paper introduction and add motivation figure`

## Problem and decision

The author drafted the first manuscript Introduction using ShortGPT's compact rhetorical structure.
The draft had the intended voice and section order, but it named the wrong Qwen model, framed the
problem as a model-performance ceiling rather than inference cost, overstated capability-routing
success, and incorrectly said the Smol OCR route transferred to IIIT5K. It also lacked citations and
a motivating figure.

The decision is to preserve the author's direct ShortGPT-style progression while correcting facts,
adding citation keys, defining matched-K route terminology, and generating a first figure from the
committed Qwen single-block ablation evidence. Later manuscript sections remain empty for the author
to write.

## Files and behavior changed

- `paper/draft.md`: retained the author's title, compact Introduction structure, research questions,
  and contribution list; corrected the model and evidence claims; added route terminology, matched
  budgets, source-transfer language, ten citation keys, and the generated Figure 1 with a restrained
  screening-evidence caption.
- `paper/references.bib`: added scaling-law references and the closest layer-pruning competitor,
  Short-LVLM.
- `scripts/generate_paper_assets.py`: added a deterministic single-block capability heatmap sourced
  from `results/ablation-qwen25-vl-3b/capability_accuracy_drops.csv`, included that CSV in the paper
  data provenance hashes, copied the PNG into Pages assets, and updated the generated-figure count.
- `scripts/verify_submission.py`: requires the new figure in PNG, PDF, and SVG and computes the
  verified figure-file count from the expected set.
- `paper/README.md`: documents the eighth figure and its recommended Introduction/Motivation use.
- `paper/data/paper-data.json`: regenerated with the single-block CSV source path and hash.
- `paper/figures/generated-single-block-sensitivity.{png,pdf,svg}`: generated publication assets.
- `docs/assets/generated-single-block-sensitivity.png`: generated web-resolution copy.

No model inference, route search, aggregate result, or later manuscript prose changed.

## Alternatives considered

- Replace the Introduction with a new polished version. Rejected because the author explicitly wants
  to write the paper and asked that their tone remain visible.
- Preserve the original claims exactly. Rejected because the 7B model name and positive IIIT5K
  transfer statement contradicted committed evidence.
- Put equations in the Introduction. Rejected to match the selected ShortGPT structure; equations
  remain reserved for Methodology.
- Reuse the old raster heatmap directly. Rejected because a paper asset should regenerate from
  committed numeric evidence and be available in vector formats.
- Add a two-panel headline-results figure. Deferred because the single-block heatmap provides the
  cleanest transition into the author's Motivation section without prematurely crowding the
  Introduction with final results.

## Verification evidence

- `MPLCONFIGDIR=/tmp/vlm-mpl make PYTHON=/tmp/vlm-paper-venv/bin/python submission`
  - Generated eight figure sets.
  - Verified frozen results, 24 figure files, tables, research documents, and the Pages site.
- Citation audit against `paper/references.bib`
  - All ten citation keys used by the draft exist in the bibliography.
- `python3 -m py_compile scripts/generate_paper_assets.py scripts/verify_submission.py`
  - Passed.
- `git --git-dir=.git-data --work-tree=. diff --check`
  - Passed.
- Visually inspected `paper/figures/generated-single-block-sensitivity.png` at original resolution.
  - Capability labels, all 32 block labels, title, and color scale are readable and unclipped.

## Limitations and unsupported claims

- The Introduction is an author draft, not a completed or externally reviewed manuscript.
- Scaling-law citations motivate model growth but do not establish that the vision tower alone is the
  dominant VLM deployment bottleneck.
- The single-block heatmap is screening evidence and does not show that capabilities are stored in
  individual blocks or that low-damage blocks compose safely.
- Capability-specific routing remains conditional; the edit does not claim a learned router,
  universal route map, global optimum, edge-device result, or complete Qwen latency curve.
- No confidence intervals are shown in Figure 1 because it visualizes the earlier screening sweep,
  not the final matched-policy comparisons.

## Next action enabled

The author can now draft Section 2, Motivation, directly under a factually correct Introduction and
use Figure 1 to explain the transition from individual block redundancy to combinatorial route
search.
