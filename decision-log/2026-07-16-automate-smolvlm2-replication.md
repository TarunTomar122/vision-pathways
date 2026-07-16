# Automate SmolVLM2 Replication

## Intended Commit Subject

`Automate resumable SmolVLM2 replication`

## Problem And Decision

The second-model experiment contains many dependent, long-running stages. Manual launches create
idle GPU gaps and risk a missed transition after a temporary SSH disconnect. Use a small supervisor
that starts a stage only after its immutable prerequisite artifact exists, preserves each runner's
own checkpointing, and limits every stage to two launch attempts.

## Files And Behavior Changed

- `scripts/supervise_smolvlm2_replication.py` advances baseline-complete work through two
  non-overlapping development ablation workers, development-only priors, two ordered robust-search
  lanes, route finalization, frozen controls, and analysis.
- It writes a compact supervisor state under the result root and per-stage logs under `logs/`.

## Alternatives Considered

- A one-shot shell pipeline was rejected because it cannot safely resume partially completed route
  caches after host interruption.
- Launching all six search families at once was rejected because duplicated model processes could
  exceed 24 GB VRAM. The supervisor runs at most two family workers at a time.
- Human-driven launch transitions were rejected because they waste GPU time during long jobs.

## Verification Evidence

- The script is syntax-checked before deployment.
- It relies on existing atomic per-route caches and state files from the robust-search runner.
- The initial baseline and manifest preparation were independently launched and observed running
  before the supervisor was introduced.

## Limitations And Non-Claims

- This supervisor does not declare an experiment successful; it only launches frozen stages.
- It intentionally leaves fresh OCR source transfer and fixed-clock latency as separately gated
  post-analysis work, so those cannot affect route selection.

## Next Action Enabled

Deploy the supervisor to the GPU host and let it advance the full second-model replication without
manual stage handoffs.
