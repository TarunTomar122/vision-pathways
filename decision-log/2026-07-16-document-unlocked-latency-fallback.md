# Document Unlocked Latency Fallback

## Intended Commit Subject

`Document unlocked latency fallback`

## Problem And Decision

The cloud provider denied GPU clock-control changes even under non-interactive sudo, so the planned
fixed-clock latency command failed before inference. Use an explicit same-idle-VM unlocked fallback
instead of fabricating a fixed-clock measurement or abandoning the latency comparison.

## Files And Behavior Changed

- The latency runner can continue only when `--allow-unlocked-fallback` is explicitly supplied;
  it records the failed lock command and `unlocked_same_vm_fallback` measurement mode.
- The K4 supervisor opts into that fallback because this VM denies clock control.
- The cross-model report exposes the measurement mode and states the resulting limitation.

## Alternatives Considered

- Reporting the result as fixed-clock latency was rejected because the provider denied the lock.
- Omitting latency entirely was rejected because a same-VM, idle comparison still measures the
  relative K4 route speed with a clear caveat.
- Requesting further privileges was rejected because the tenant-level GPU permission cannot be
  changed from this VM.

## Verification Evidence

- `sudo -n nvidia-smi -lgc 2700,2700` returns that the current user lacks permission to change
  GPU clocks, although 2700 MHz appears in the GPU's supported clock list.
- The GPU was idle when the failed clock-lock attempt was inspected.

## Limitations And Non-Claims

- Unlocked clock values can vary with thermal and power state, so these results are weaker than
  fixed-clock measurements and do not establish device-level latency.
- The fallback changes only latency measurement metadata and execution, not route selection or
  accuracy results.

## Next Action Enabled

Run the K4 same-VM latency audit, produce the final report, and label its measurement mode clearly.
