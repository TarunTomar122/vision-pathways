# Resume Completed Single-Block Ablations

## Intended Commit Subject

`Resume completed single-block ablations`

## Problem And Decision

The live SmolVLM2 sweep showed that each block reloads the checkpoint, adding about 110 seconds
of model-load time. To safely increase from two to three non-overlapping workers, completed blocks
must be skipped and partially written prediction files must be resumed instead of discarded.

## Files And Behavior Changed

- `scripts/run_layer_ablation.py` now detects a compatible completed `ablation_record.json`, reuses
  it, and skips re-running that block. Incomplete blocks retain their existing prediction files;
  `BaselineRunner.run` already resumes by prediction ID.
- `scripts/supervise_smolvlm2_replication.py` schedules three non-overlapping ablation partitions
  (`0-8`, `9-17`, and `18-26`) so it does not relaunch the obsolete two-partition commands.

## Alternatives Considered

- Allowing the two existing workers to finish avoids a restart but leaves measured VRAM capacity
  unused and keeps the longer wall-clock schedule.
- Deleting partial predictions was rejected because each record is append-only and resumable.
- Reusing a model across blocks would save additional load time but requires a larger runner
  lifecycle refactor; this narrow change is lower risk while jobs are live.

## Verification Evidence

- Block 0 and block 14 completed with 904 predictions each and have ablation records.
- Blocks 1 and 15 have partial append-only prediction caches, which `BaselineRunner` filters by ID.
- The new guard rejects records whose block index or example count does not match the current run.

## Limitations And Non-Claims

- This change improves only job resumption and wall-clock utilization; it does not alter scores,
  data, block identity intervention, or route-selection protocol.

## Next Action Enabled

Restart the remaining single-block work as three disjoint partitions on the 24 GB GPU, retain all
completed and partial work, then let the supervisor continue to priors and robust search.
