# Switch SmolVLM2 Primary Protocol To K4

## Intended Commit Subject

`Switch SmolVLM2 primary replication to K4`

## Problem And Decision

The partial K6 SmolVLM2 search showed that six skipped vision blocks are too destructive for this
model: the completed generic K6 route lost 21.80 percentage points of overall selection accuracy
and 62.58 points on OCR. Continue with a new K4-only primary replication, which directly tests the
smaller, deployment-relevant skip budget requested after observing that failure mode.

## Files And Behavior Changed

- `configs/robust_route_search_smolvlm2_2b_k4_lean.json` freezes the source-balanced K4 protocol
  in new output and prepared-manifest directories.
- The route runner now accepts a single targeted K4 protocol.
- Fresh OCR transfer and cross-model reporting accept the frozen K budget rather than assuming K6.
- The supervisor launches K4 search, controls, transfer, latency, and reporting into K4-specific
  paths. It does not resume or extend the K6 run.

## Alternatives Considered

- Continuing K6 controls and external transfer was rejected because K6 is no longer the selected
  deployment setting and would spend inference budget on a known destructive route budget.
- Reusing partial K6 results as K4 evidence was rejected because the routes and compute budgets
  differ.
- Reducing held-out selection or matched controls was rejected because that would weaken the K4
  comparison more than the K6-to-K4 budget change reduces runtime.

## Verification Evidence

- All 27 SmolVLM2 single-block ablations completed before this decision.
- Five K6 family searches had sufficient selection predictions for a diagnostic comparison; K6
  generic accuracy was 60.84% versus 82.65% full-model accuracy on 876 selection examples.
- K6 workers and supervisor were stopped before controls, fresh IIIT5K inference, latency, or a
  frozen K6 registry were produced.

## Limitations And Non-Claims

- The partial K6 artifacts are diagnostic-only and must not be reported as a completed,
  matched-control, or external-transfer result.
- This commit does not establish that K4 is safe; it schedules the experiment needed to measure it.
- The K4 result is a targeted replication, not a complete K4/K6/K8 SmolVLM2 sweep.

## Next Action Enabled

Prepare the deterministic K4 manifests and automatically run all six K4 route families, frozen
matched controls, sealed IIIT5K transfer, fixed-clock latency, and the K4 cross-model report.
