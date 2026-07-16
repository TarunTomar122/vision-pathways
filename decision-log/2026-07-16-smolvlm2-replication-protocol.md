# SmolVLM2 Replication Protocol

## Intended Commit Subject

`Add frozen SmolVLM2 route-search replication protocol`

## Problem And Decision

The completed Qwen2.5-VL route-search result is one-model evidence. The next valid step is a
same-protocol replication on an architecturally different VLM, not reuse of Qwen-selected blocks.
SmolVLM2 has a 27-block SigLIP vision encoder whose block calls return tuples, unlike Qwen's
32-block vision tower whose blocks return tensors. The benchmark runner must preserve those
different output contracts while applying the identical identity intervention.

## Files And Behavior Changed

- `src/vlm_bench/benchmark.py` adds explicit Qwen and SmolVLM vision adapters. The runner now
  resolves the model-specific vision module and block list, validates the configured block count,
  and returns the correct identity-block output type.
- `scripts/run_layer_ablation.py` requires an explicit block range, validates it against the model
  configuration, and filters the baseline by the requested split before computing ablation drops.
- `scripts/build_single_block_priors.py` creates capability and generic development-only rankings
  plus deterministic independent, contiguous, and random route candidates for arbitrary block
  counts.
- `scripts/freeze_matched_controls.py` freezes K4/K6/K8 controls from those rankings before control
  inference.
- `scripts/run_robust_route_controls.py` validates controls against an explicit allowed-block set.
- `scripts/run_robust_route_search.py` rejects duplicate or insufficient allowed-block pools.
- `configs/baseline_smolvlm2_2b.json` pins SmolVLM2-2.2B-Instruct, 27 vision blocks, deterministic
  greedy decoding, bf16, and SDPA.
- `configs/robust_route_search_smolvlm2_2b.json` freezes the same processed-v2 split, budgets,
  scouts, evolutionary settings, and source-aware objectives as the completed Qwen search while
  requiring SmolVLM2-only development discovery and forbidding use of the consumed external set.

## Alternatives Considered

- Reusing the Qwen routes was rejected because it would test cross-model route transfer rather than
  replicate the route-selection method.
- Keeping a 32-block assumption was rejected because it can silently produce invalid Smol routes.
- Treating Smol's tuple-returning blocks as Qwen tensors was rejected because downstream encoder
  code expects the first tuple element to be hidden states.
- Fine-tuning or feature repair was deferred. This replication isolates no-training identity
  pruning and matched compute first.

## Verification Evidence

- `python3 -m py_compile src/vlm_bench/benchmark.py scripts/run_layer_ablation.py
  scripts/run_robust_route_search.py scripts/run_robust_route_controls.py
  scripts/build_single_block_priors.py scripts/freeze_matched_controls.py`
- `git diff --check`
- The next pre-launch gate is a remote full-model and one-skipped-block SmolVLM2 smoke test on the
  pinned model revision, followed by the full 27-block development sweep.

## Limitations And Non-Claims

- This commit contains protocol and code only; it does not yet establish SmolVLM2 accuracy,
  latency, or a replication result.
- The image-disjoint processed-v2 test partition is method-selection evidence only because it was
  used by the earlier Qwen discovery work. Smol's own discovery remains development-only.
- The fresh OCR source-transfer set and fixed-clock latency measurements are separate downstream
  stages and are not claimed here.

## Next Action Enabled

Download or verify the pinned SmolVLM2 snapshot on the RTX 4090, run an identity-substitution
smoke test, then execute the baseline, 27 one-block development sweep, source-aware route search,
matched controls, analysis, fresh OCR transfer, and fixed-clock latency audit.
