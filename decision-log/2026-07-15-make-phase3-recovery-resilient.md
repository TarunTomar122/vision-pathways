# Make Phase 3 Recovery Resilient

## Intended Commit Subject

Make Phase 3 recovery resilient to missing raw artifacts

## Problem Or Decision

The original GPU instance was terminated before the in-progress Phase 3 raw predictions were
copied off-machine. Raw JSONL predictions are intentionally excluded from Git, so a new instance
must regenerate the V2 baseline, one-block discovery predictions, and validation controls. The
existing validation implementation required historical route-control files and the one-block
runner used fixed aggregate filenames, preventing safe concurrent recovery workers.

The recovery must preserve the frozen development protocol and must not inspect the sealed
external held-out benchmark.

## Files And Behavior Changed

- `scripts/run_layer_ablation.py` adds `--summary-stem`. Concurrent workers using non-overlapping
  block ranges can share one output directory while writing separate summary JSON, heatmap CSV,
  and heatmap PNG files. Default filenames remain unchanged when the option is omitted.
- `scripts/run_phase3_interaction_search.py` now uses historical validation-control predictions
  when available and otherwise regenerates the same frozen routes on the image-disjoint
  development validation rows. The summary records the prediction source.
- `docs/phase3_interaction_search_protocol.md` documents recovery semantics and safe concurrent
  one-block workers.
- `scripts/run_phase3_recovery.sh` validates V2 data, resumes the baseline, runs two disjoint
  one-block shards, runs search/validation and pairwise analysis as two workers, verifies every
  prerequisite block output, and merges final state only after all workers succeed. A one-example
  GPU smoke gate prevents expensive work from starting when model inference is broken. The
  one-block sweep is restricted to the deterministic 500-row search split because those raw
  predictions are used only by search-set pairwise analysis.
- `scripts/restore_frozen_v2.py` reconstructs the exact V2 rows from the committed V1 manifest and
  stable VQAv2 slice, materializes only absent TallyQA/POPE/VSR images, verifies every restored
  image digest, and rejects any development manifest other than the recorded frozen SHA-256.
- `docs/protocol_v2.md` records the frozen manifest hash and restoration procedure.

## Alternatives Considered

- Reconstructing metrics from compact summaries was rejected because paired per-example metrics
  require raw predictions.
- Re-running the entire historical task-route benchmark was rejected because Phase 3 validation
  needs only the frozen controls on its validation rows.
- Running all one-block interventions on the 404-row validation remainder was rejected because
  Phase 3 never consumes those predictions; omitting them reduces prerequisite inference by 44.7%.
- Accepting the clean rebuild's 877-row development split was rejected because it does not match
  the frozen 904-row method-development split used by prior phases.
- Letting concurrent ablation workers overwrite `summary.json` was rejected because the final
  aggregate would depend on process completion order even though block directories are disjoint.
- Evaluating the sealed external benchmark during recovery was rejected because it would leak
  method-development information into the final evaluation set.

## Verification Evidence

- `PYTHONPATH=src .venv/bin/pytest -q` passed all 15 tests on the replacement RTX 4090 instance.
- `python -m py_compile` passed for the modified Python launchers and restoration utility.
- `bash -n scripts/run_phase3_recovery.sh` and `git diff --check` passed.
- An invalid `--summary-stem bad/stem` exited nonzero with the declared validation error.
- A clean upstream rebuild produced 1,780 examples but the wrong 877/903 split and development
  manifest hash, confirming that pinned source revisions alone did not recover the frozen split.
- `scripts/restore_frozen_v2.py` restored 68 absent POPE, 70 absent TallyQA, and 64 absent VSR image
  files after accounting for images already shared with rebuilt rows. Every restored payload matched
  the digest recorded in the frozen manifest.
- The restored dataset has 1,780 examples, 1,431 unique images, a 904/876 development/test split,
  and development SHA-256 `b7c097e8cea30d5c070d9ef03bacfb853b5967756d5282ba78c8575354e4ffae`.
- Full `validate_dataset.py` verification passed all 1,780 restored rows and image hashes.
- The one-example GPU smoke gate answered correctly in 183.39 ms total, measured 68.60 ms in the
  vision encoder, and reserved 7,676 MiB peak GPU memory.
- The off-instance backup service completed more than five consecutive one-minute sync cycles
  without restart before inference began.

## Limitations And Risks

- Regeneration costs additional GPU time and does not recover the terminated instance's raw files.
- Concurrent workers are safe only when their block ranges do not overlap.
- Frozen-image restoration depends on the pinned upstream datasets and COCO URLs remaining
  available; payload hashes prevent silent substitution but cannot prevent an upstream outage.
- The change does not claim that development validation is external held-out evidence.
- The change does not evaluate or unseal the external benchmark.

## Next Action Enabled

Regenerate the V2 prerequisites with two RTX 4090 workers, run Phase 3 search/validation and
pairwise analysis concurrently, and continuously replicate raw outputs off the GPU instance.
