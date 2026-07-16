# Add Cross-Model Replication Report

## Intended Commit Subject

`Add cross-model replication report`

## Problem And Decision

The Qwen and SmolVLM2 route searches must be interpreted together without conflating their
method-selection split with the fresh OCR transfer set. Add a small deterministic report that puts
same-K generic-versus-task values for both models beside the separately sealed Smol OCR transfer
result and states the evidence boundary directly.

## Files And Behavior Changed

- `scripts/analyze_cross_model_replication.py` reads the two frozen robust analyses plus the
  sealed Smol IIIT5K analysis and writes JSON, Markdown, and a static HTML view.
- `scripts/supervise_smolvlm2_replication.py` invokes the report only after the fresh OCR analysis
  has completed.

## Alternatives Considered

- Manually comparing terminal output was rejected because it is easy to mix K budgets or evidence
  partitions.
- Pooling Qwen and Smol predictions into a combined confidence interval was rejected because they
  are different models and their examples/predictions are not paired across model families.

## Verification Evidence

- The report consumes only completed analysis JSON files produced by existing frozen pipelines.
- It preserves each model's own paired bootstrap interval and does not rerun or reselect routes.

## Limitations And Non-Claims

- The report is a synthesis, not a new statistical test.
- It cannot establish a broad replication result if either model's interval crosses zero.

## Next Action Enabled

After the automated SmolVLM2 pipeline completes, inspect one committed report with comparable
matched-K and untouched OCR transfer evidence.
