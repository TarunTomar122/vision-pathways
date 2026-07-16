# Use Shared Baseline For K4 Analysis

## Intended Commit Subject

`Use shared baseline for K4 analysis`

## Problem And Decision

The K4 protocol intentionally writes route artifacts to a new directory while reusing the completed
SmolVLM2 baseline in its original directory. The analysis script assumed every route root contained
its own `baseline/predictions.jsonl`, so automatic analysis failed after all K4 controls completed.
Accept an explicit baseline-predictions path and pass the shared baseline from the supervisor.

## Files And Behavior Changed

- `scripts/analyze_robust_route_search.py` accepts `--baseline-predictions` and retains the old
  root-local baseline as its default.
- The K4 supervisor passes the immutable shared SmolVLM2 baseline path to analysis.

## Alternatives Considered

- Copying baseline predictions into the K4 result directory was rejected because it duplicates a
  large artifact and obscures that K4 reused the original baseline.
- Changing the K4 root layout was rejected because its route and control artifacts are already
  complete and correctly isolated.

## Verification Evidence

- The failed analysis log reports only a missing
  `results/robust-route-search-smolvlm2-2b-k4/baseline/predictions.jsonl` path.
- The shared baseline exists at
  `results/robust-route-search-smolvlm2-2b/baseline/predictions.jsonl` and was used for every K4
  route and control comparison.

## Limitations And Non-Claims

- This fixes orchestration only; it does not change K4 predictions, routes, controls, scoring, or
  the frozen selection manifest.
- Existing supervisor attempt counters require restarting from the repaired analysis artifact.

## Next Action Enabled

Run K4 analysis with the shared baseline, then resume sealed IIIT5K transfer, latency, and the
cross-model report.
