# Add Fixed-Clock SmolVLM2 Latency Audit

## Intended Commit Subject

`Add fixed-clock SmolVLM2 latency audit`

## Problem And Decision

Accuracy-only route comparisons do not establish an edge-efficiency result. Add a separate,
post-selection latency audit for full versus frozen generic K4/K6/K8 routes. The GPU must run under
fixed graphics and memory clocks, and controls must be bracketed by repeated full-model baselines
to distinguish route effects from clock drift.

## Files And Behavior Changed

- `scripts/run_smolvlm2_fixed_clock_latency.py` freezes the generic routes, locks the RTX 4090 at
  2700 MHz graphics and 10501 MHz memory, invokes the existing randomized/bracketed latency audit
  for K4/K6/K8, records clock-control commands, and restores normal clock control in `finally`.
- `scripts/supervise_smolvlm2_replication.py` runs latency only after all route analysis, fresh OCR
  transfer, and cross-model reporting are complete.

## Alternatives Considered

- Measuring latency during parallel search was rejected because concurrent model workers distort
  timing and power/clock behavior.
- Using floating clocks was rejected because the VPS GPU can boost dynamically between conditions.
- Measuring conditional task policies was deferred because their route changes with capability;
  this initial audit isolates the practical generic compressed checkpoints at K4/K6/K8.

## Verification Evidence

- The RTX 4090 reports supported graphics clocks including 2700 MHz and a maximum memory clock of
  10501 MHz.
- `sudo -n` succeeds on the VPS, allowing the script to set and reset GPU clocks without prompt.
- The underlying audit uses 20 warmups, five repeats, 10 examples per capability, randomized route
  order, and three bracketed full-model baselines.

## Limitations And Non-Claims

- This is batch-size-one RTX 4090 latency, not a measurement on a mobile edge device.
- It reports generic-route latency only; conditional routing needs a separate workload-aware audit.

## Next Action Enabled

After all accuracy evidence is frozen and summarized, run reproducible K4/K6/K8 fixed-clock speed
measurements and add their results to the final cross-model report.
