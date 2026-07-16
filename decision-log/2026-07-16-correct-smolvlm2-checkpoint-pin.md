# Correct SmolVLM2 Checkpoint Pin

## Intended Commit Subject

`Pin SmolVLM2 replication to downloaded checkpoint`

## Problem And Decision

The initial protocol used a preliminary SmolVLM2 revision from model-page research. Before any
inference, the GPU host resolved and downloaded the model through the Hugging Face API. The
authoritative resolved snapshot is `482adb537c021c86670beed01cd58990d01e72e4`. The experiment must
pin that actual immutable checkpoint rather than an unverified preliminary hash.

## Files And Behavior Changed

- `configs/baseline_smolvlm2_2b.json` now pins the exact Hugging Face snapshot downloaded on the
  RTX 4090. All subsequent processor and model loads use this revision.

## Alternatives Considered

- Retaining the preliminary revision was rejected because it would make the checkpoint provenance
  ambiguous.
- Using the floating `main` revision was rejected because later model updates could change results.

## Verification Evidence

- Remote command: `PYTHONPATH=src .venv/bin/python scripts/download_models.py
  HuggingFaceTB/SmolVLM2-2.2B-Instruct --output results/smolvlm2-model-snapshot.json`.
- The download output recorded the exact snapshot path and revision above before any benchmark
  inference began.

## Limitations And Non-Claims

- This updates provenance only and reports no accuracy, latency, or pruning results.
- The replication protocol remains otherwise unchanged.

## Next Action Enabled

Load the pinned model, validate full and one-block identity inference, then launch the frozen
baseline and development-only one-block sweep.
