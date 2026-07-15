# Freeze matched-K robust route controls

## Intended commit subject

`Freeze matched-K robust route controls`

## Problem and decision

The robust search selects one generic and five capability-specific routes at K4, K6, and K8, but
those evolved routes still require fair same-compute comparisons. This commit freezes all control
routes before control inference and before inspecting evolved-route selection results. Controls are
comparison-only and cannot alter which evolved route is selected.

## Files and behavior changed

- `configs/robust_route_controls.json` records exact generic-independent,
  capability-conditional-independent, contiguous, and three random routes at every K.
- `scripts/run_robust_route_controls.py` waits for a frozen evolved-route registry, verifies the
  selection-manifest hash, runs each condition resumably on the same 876 rows, and records state.
- `decision-log/2026-07-15-freeze-robust-route-controls.md` documents this commit boundary.

The independent routes are the first K blocks from the previously committed single-block
rankings. The contiguous route minimizes the sum of generic single-block drops over every
contiguous K-block window. K4 and K8 random seeds reproduce the existing controls; K6 uses the
interpolated deterministic seeds `20261314` through `20261316`.

## Alternatives considered

- Selecting controls after viewing evolved-route results was rejected because it permits an
  artificially weak comparator.
- Comparing only against the old generic K8 route was rejected because it would omit K4 and K6 and
  would not characterize random-route variance.
- Running task-independent routes over all capabilities was rejected as unnecessary compute; the
  conditional policy evaluates each route only on its assigned capability while still covering
  every selection row exactly once.

## Verification evidence

- The registry defines exactly six controls for each of K4, K6, and K8.
- Every fixed and conditional route contains exactly K unique block indices in `[0, 31]`.
- K4 and K8 generic, task, contiguous, and random definitions match the previously committed route
  registry.
- `python3 -m py_compile scripts/run_robust_route_controls.py` passed.
- No control predictions were generated before this commit.

## Limitations and unsupported claims

- The controls use the consumed method-selection partition, not a new sealed source-transfer set.
- Random-route coverage is three repetitions per K and does not estimate the full route-space
  distribution.
- The contiguous comparator is defined from single-block proxy scores and is not exhaustively
  selected by combination accuracy.
- Control inference measures accuracy at fixed K; latency differences between routes at the same K
  should be negligible and are not a route-selection objective.

## Next action enabled

After all six evolved route families are frozen, run the control registry once, then produce
matched-K full/generic/task/independent/contiguous/random comparisons on identical selection rows.
