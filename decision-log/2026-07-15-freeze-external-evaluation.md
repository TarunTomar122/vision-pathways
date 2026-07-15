# Intended commit subject

Freeze the external route evaluation before inference

# Problem or decision

Development validation did not settle whether capability-conditional routes transfer better than
the generic eight-block route. The existing 1,250-example external benchmark has never been used
for model evaluation, so its routes and analysis must be committed before predictions are exposed.

# Exact changes

- Added `configs/external_frozen_evaluation.json` with the exact manifest hash, model revision,
  four conditions, route blocks, identity operation, and no-repair decision.
- Added `src/vlm_bench/external_eval.py` for protocol validation, route dispatch, paired accuracy,
  and paired bootstrap intervals.
- Added `scripts/run_external_frozen_evaluation.py`, which verifies the protocol and manifest,
  resumes condition-specific JSONL predictions, and supports disjoint concurrent workers.
- Added `scripts/analyze_external_frozen_evaluation.py`, which requires complete matched IDs and
  compares each route with the full model and conditional routes with generic K8.
- Added unit tests and clarified the external protocol's first frozen evaluation.

# Alternatives considered

- Reusing the V2 test split was rejected because the independent block ranking had already seen
  all 1,780 V2 examples and source families overlap development.
- Selecting new routes from external outcomes was rejected because it would destroy the held-out
  claim.
- Running every condition sequentially was rejected because two Qwen 3B workers fit the 24 GB GPU;
  concurrency reduces wall time. Timing from this run is explicitly excluded from speed claims.
- Adding repaired or random conditions was deferred because no repair method is currently supported
  by positive development evidence, and the immediate question is conditional versus generic routing.

# Verification

Run the unit tests, compile the new scripts, and verify that the frozen manifest SHA-256 is
`c01c93a9f8f007bb21a11c1952ca50fa51bfdaa5232ebbd681a979156cca5a77` before committing.

# Limitations and unsupported claims

- Dataset identity remains confounded with capability because each capability uses a different
  external source family.
- Public benchmark examples may have appeared during model pretraining.
- Concurrent timings do not support latency or speedup claims.
- This protocol tests only Qwen2.5-VL-3B-Instruct and identity block removal.
- Freezing the protocol does not imply that task-specific routing will outperform generic pruning.

# Next action

Materialize and hash-validate the external images on the GPU VPS, run all four frozen conditions,
then publish paired held-out accuracy and confidence intervals without modifying the routes.
