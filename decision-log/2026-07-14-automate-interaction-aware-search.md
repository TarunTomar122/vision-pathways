# Decision: Automate interaction-aware route search and pairwise block analysis

- Date: 2026-07-14
- Intended commit subject: `Automate interaction-aware vision route search`
- Status: Accepted for Phase 3 development evaluation

## Problem And Decision

The fixed one-block ranking produced acceptable four-block routes but failed at eight removals:
target-capability losses ranged from 10.18 to 37.30 percentage points. Phase 2 final-boundary
low-rank repair reduced feature error without reliably restoring answers. Repeating larger fixed
routes or increasing bridge rank would not test the observed failure mechanism.

The decision is to test conditional block importance directly. Starting from each useful
four-block task route, Phase 3 adds blocks one at a time, reevaluates all allowed additions after
every removal, and retains a width-three beam through eight removed blocks. A separate pairwise
map quantifies non-additivity among independently safe blocks.

## Files And Behavior Changed

- `src/vlm_bench/benchmark.py`
  - Adds validated dynamic vision-route switching.
  - Retains original vision blocks outside the active model tree so one loaded checkpoint can
    evaluate hundreds of identity routes.
  - Recomputes active parameter accounting for every route.
  - Exposes a one-row prediction method for resumable orchestration.
- `src/vlm_bench/phase3.py`
  - Adds deterministic seed selection, candidate pools, beam expansion and deduplication, paired
    metrics, route keys, and pairwise interaction calculation.
- `scripts/run_phase3_interaction_search.py`
  - Builds a 500-row search and 404-row image-disjoint development validation split.
  - Runs conditional beam search from budget four through eight.
  - Freezes search rank 1 before validation and measures all three beam survivors.
  - Reuses saved independent, generic, contiguous, and random controls.
  - Evaluates all 45 pairs among ten low-sensitivity blocks per capability.
  - Writes append-only predictions, stage state, summaries, and a readable report.
- `configs/phase3_interaction_search.json`
  - Freezes seed, split size, beam width, candidate pool, pairwise pool, and budgets.
- `tests/test_phase3.py`
  - Covers route validation, beam deduplication, paired flips, interaction arithmetic, and seed
    selection.
- `docs/phase3_interaction_search_protocol.md`
  - Documents the question, split, algorithm, controls, runtime, stopping rule, and claim limits.
- `README.md` and `docs/current_status.md`
  - Mark Phase 3 as the active experiment and link its protocol.
- `decision-log/2026-07-14-automate-interaction-aware-search.md`
  - Documents this commit.

## Alternatives Considered

- Full width-three search over all 32 blocks. Rejected because it requires approximately 131,000
  search predictions before validation. Restricting expansion to the 16 least-sensitive blocks
  reduces compute while preserving the conditional-interaction test.
- Pure greedy search. Rejected because one early tie or noisy choice would be irreversible. A beam
  of three is a modest robustness improvement.
- Search from zero removals. Rejected because the four-block routes are already measured and useful;
  the unresolved question is whether conditional selection fixes the fifth-through-eighth choices.
- Tune a target-plus-collateral objective. Rejected for this phase because its coefficient would be
  an arbitrary development-set hyperparameter. Search uses target accuracy and reports collateral
  damage separately.
- Select the best beam route on development validation. Rejected because that would leak validation
  outcomes into route choice. Search rank 1 remains primary regardless of validation performance.
- Refit a higher-rank final-boundary bridge. Rejected because ranks 8, 32, and 128 already produced
  nearly identical reconstruction and weak behavioral recovery.
- Run recovery training immediately. Rejected until route search establishes that an eight-block
  route is a defensible training target.

## Verification Evidence

- Local Python compilation passed for all changed Python files.
- GPU unit suite passed: 15 tests in 4.29 seconds.
- Full smoke pipeline completed search, validation, and 30 pairwise configurations.
- Smoke outputs returned the GPU to 1 MiB allocated memory with no remaining process.
- A second complete smoke invocation left the aggregate prediction hash unchanged:
  `be4829a12c2a53b613b09f55b666515b0b4e96d045b6b4dc238c55e43d86e7ae`.
- The full development split was verified at 500 search and 404 validation rows with zero image
  overlap.
- Run JSON parsing, all tests, documentation-link checks, and `git diff --check` before commit.

## Limitations, Risks, And Unsupported Claims

- The original one-block ranking used the larger discovery data, so the 404-row validation
  remainder is not fully untouched by method development.
- Candidate search excludes 16 blocks per capability and cannot claim a globally optimal route.
- Search accuracy has one-percentage-point resolution on 100 examples and can contain ties.
- The pairwise interaction statistic is descriptive and does not establish direct communication
  or causal storage between two blocks.
- Original blocks remain resident during dynamic switching; search peak VRAM does not represent a
  physically compact checkpoint.
- No training, second-model replication, edge-device measurement, or external held-out evaluation
  is included.
- The experiment does not establish that eight-block pruning will work or merit recovery training.

## Next Action Enabled

Run the full resumable pipeline on the RTX 4090. If the search-selected primary eight-block routes
materially outperform existing independent eight-block routes on the development validation
remainder, freeze a recovery-training configuration using LoRA plus answer/logit distillation. If
they do not, stop pure route-selection work and document the interaction limit rather than tuning
on the sealed external benchmark.
