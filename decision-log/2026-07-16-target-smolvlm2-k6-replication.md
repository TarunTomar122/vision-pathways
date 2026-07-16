# Target SmolVLM2 K6 Replication

## Intended Commit Subject

`Target SmolVLM2 replication at K6`

## Problem And Decision

The full K4/K6/K8 SmolVLM2 replication would require a large combinatorial route-search budget.
The completed Qwen experiment's only clear capability-level matched-K result was at K6: OCR
capability routing improved over generic routing by 7.10 percentage points with a paired interval
above zero. Target the new model replication at K6, preserving the essential source-aware
selection, held-out method-selection, and matched-control logic.

## Files And Behavior Changed

- `configs/robust_route_search_smolvlm2_2b_k6_lean.json` freezes a K6-only protocol: all source
  quotas, objectives, three seeds, finalists, controls, and decoding remain fixed; the population
  changes from 16 to 12 and generations from 3 to 2.
- Search, controls, analysis, latency, cross-model reporting, and the Smol supervisor now support a
  K6-only run while retaining compatibility with the full Qwen K4/K6/K8 protocol.
- The supervisor uses the completed full Smol baseline but writes all targeted-route artifacts to
  new K6-specific directories, prepares those manifests before search, and leaves the unused
  full-search configuration untouched.
- The frozen control configuration records its allowed K values so K6-only controls cannot be
  rejected by the full-protocol K4/K6/K8 validator.

## Alternatives Considered

- Keeping K4/K6/K8 was rejected because it triples the number of budget-specific searches without
  directly testing the strongest Qwen result.
- Reducing source-balanced scout or selection examples was rejected because it would make the
  source-aware objective and held-out comparison substantially noisier.
- Removing seeds entirely was rejected because route instability is a central risk; three seeds
  remain part of the targeted replication.

## Verification Evidence

- The Qwen robust analysis records K6 task-minus-generic +2.17 pp overall and OCR +7.10 pp with
  paired 95% interval [0.65, 14.19].
- The new K6 protocol reduces scout evolutionary evaluations by half after removing K4/K8, while
  retaining final development and selection evaluations plus all six K6 matched controls.
- No SmolVLM2 route-search predictions had started when this protocol was frozen.

## Limitations And Non-Claims

- This cannot claim K4 or K8 replication on SmolVLM2.
- The smaller population and generation count mean this is a targeted replication, not a bitwise
  copy of Qwen's optimizer budget.

## Next Action Enabled

Complete the current model-specific one-block sweep, prepare the K6 manifests, and run the targeted
source-aware K6 search, controls, fresh OCR transfer, fixed-clock latency, and report automatically.
