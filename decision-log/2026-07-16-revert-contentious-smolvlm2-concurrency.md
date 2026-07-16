# Revert Contentious SmolVLM2 Concurrency

## Intended Commit Subject

`Revert contentious SmolVLM2 concurrency`

## Problem And Decision

Three SmolVLM2 workers fit in 24 GB VRAM but did not improve throughput. Live ablation progress
measured roughly 0.45 examples/second per worker at three workers, while the preceding two-worker
run delivered about 1.1 examples/second per worker. GPU contention therefore made three workers
slower in aggregate.

## Files And Behavior Changed

- `scripts/supervise_smolvlm2_replication.py` returns to two ordered search lanes and two
  non-overlapping ablation ranges (`0-13` and `14-26`). The resume guard preserves completed blocks
  and partial prediction files across the restart.

## Alternatives Considered

- Continuing with three workers was rejected because it reduces total examples/second despite
  available VRAM.
- Reducing to one worker was rejected because the two-worker preflight had higher aggregate
  throughput and remained well within memory limits.
- Altering search budgets was rejected because it changes the frozen research protocol rather than
  addressing a hardware-scheduling issue.

## Verification Evidence

- Three-worker live measurement: 17,654 MiB used, 6,428 MiB free, with approximately 149 and 144
  new examples completed by two fresh workers over 333 seconds.
- Earlier two-worker completed blocks measured about 0.655 seconds median inference latency per
  worker and completed 904 examples per block substantially faster.

## Limitations And Non-Claims

- This measurement is specific to this RTX 4090, input mix, and batch-size-one generation.
- The change affects wall-clock scheduling only, not route selection, scoring, data, or model
  configuration.

## Next Action Enabled

Resume the remaining ablations and later robust families with two workers, then estimate remaining
search time from the first completed scout batch rather than theoretical candidate counts.
