# Protocol V2: Capability-Pruning Evaluation

V1 is exploratory: its 1,480 examples and all combined-path results informed analysis. Do not report its combined-path test accuracy as a held-out result.

V2 separates selection from evaluation and increases attribute coverage.

## Dataset

Build a new manifest without modifying V1:

```bash
.venv/bin/python scripts/prepare_dataset.py \
  --output-root data/processed-v2 \
  --external-per-capability 300 \
  --attribute-per-capability 300
```

V2 retains the existing five sources and adds 300 VQAv2 validation color questions. The VQAv2 slice uses the official question and annotation archives, only questions beginning `What color is/are...`, a 9-of-10 annotator consensus requirement, and balanced counts across 11 common color answers. It downloads only selected COCO images. The manifest remains grouped by image hash before assignment to `development` or `test`.

The frozen V2 development manifest contains 904 rows and has SHA-256
`b7c097e8cea30d5c070d9ef03bacfb853b5967756d5282ba78c8575354e4ffae`. Rebuilding upstream
datasets can change sampled row order even at pinned dataset revisions. If a clean rebuild does not
produce this hash, restore V2 from the committed V1 manifest plus the stable VQAv2 slice:

```bash
PYTHONPATH=src .venv/bin/python scripts/restore_frozen_v2.py
PYTHONPATH=src .venv/bin/python scripts/validate_dataset.py \
  --manifest data/processed-v2/manifests/development.jsonl \
  --data-root data/processed-v2
```

The restoration utility downloads only frozen images absent from the rebuild and verifies each
image digest before replacing manifests.

## Selection And Evaluation

1. Run the unmodified baseline on development and test separately.
2. Run all one-block identity interventions on development only.
3. Select blocks with `scripts/select_development_candidates.py`.
4. Fix the multi-block candidates before reading test predictions.
5. Run only those fixed paths on test, with repeated paired latency trials.

The development selector's defaults allow at most a 1.0 percentage-point overall development drop and at most three net-correct losses per capability. These are a screening rule, not a statistical significance claim; report paired counts and uncertainty in the final study.
