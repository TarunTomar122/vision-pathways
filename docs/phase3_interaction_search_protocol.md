# Phase 3: Interaction-Aware Route Search

## Question

The existing task routes rank every vision block once and then remove the first 4, 8, 12, or 16
blocks in that fixed order. Four removals are useful, but every capability loses at least 10.18
percentage points at eight removals. Phase 3 tests the specific failure mechanism:

> Does recomputing block importance after every removal produce a materially better eight-block
> route than composing independent one-block scores?

This is method-development work. It does not use the sealed external benchmark.

## Data Separation

The 904-row V2 development manifest is deterministically divided by image identity:

- Search: exactly 100 examples from each capability, 500 total.
- Development validation: the remaining 404 examples.
- Image overlap: zero.

The search objective uses only the 100 target-capability examples. The 404-row remainder measures
target preservation and collateral damage only after the search beam is fixed.

This is not a true held-out split. The original single-block rankings used the larger discovery
set, which includes these examples. The split prevents combination-level selection on validation
answers but does not remove the earlier one-block selection bias.

## Conditional Beam Search

Each capability starts from its existing four-block task route. Candidate additions are restricted
to that capability's 16 least-sensitive blocks from the completed one-block sweep. The existing
four blocks are included in this pool.

For depths five through eight:

1. Add each remaining candidate block to every retained route.
2. Deduplicate identical routes reached from different parents.
3. Evaluate every child on the fixed 100-example target search set.
4. Rank by paired target-capability accuracy drop from the full model.
5. Retain the best three routes, breaking exact ties by sorted block indices.
6. Recompute all additions from those three routes at the next depth.

The primary route is rank 1 on search data. All three final routes are measured on development
validation, but those validation results do not change which route is primary.

The objective deliberately has no collateral-loss coefficient. Introducing such a coefficient
would add an arbitrary development-tuned hyperparameter. Collateral damage is reported separately
for all five capabilities.

## Matched Comparisons

On the same image-disjoint development validation rows, compare the search-selected eight-block
route against already completed predictions for:

- the independent-ranking task route;
- generic macro-ranked pruning;
- the least-damaging contiguous route;
- three deterministic random routes.

This avoids rerunning controls and preserves exact paired example comparisons.

## Pairwise Interaction Map

For each capability, use its ten least-sensitive single blocks and evaluate all 45 pairs on the
100-example search set. Existing one-block predictions provide the matched single effects.

For blocks `i` and `j`:

```text
interaction(i, j)
    = pair accuracy drop
    - single-i accuracy drop
    - single-j accuracy drop
```

- Positive: the pair is more harmful than the sum of its individual effects.
- Near zero: effects are approximately additive at the measured sample size.
- Negative: the pair is more compatible than expected from individual effects.

The map is descriptive and can motivate later mechanistic work. It is not proof that the blocks
directly communicate or store a named capability.

## Runtime And Recovery

The runner loads Qwen once and swaps original blocks and identity modules in place. Original block
modules remain resident in GPU memory, so this optimization saves checkpoint-loading time rather
than peak VRAM. Every route writes one JSONL row per completed prediction and can resume after an
interruption without duplicating rows.

Expected RTX 4090 runtime:

- Conditional beam search: 3–4 hours.
- Development validation: 20–30 minutes.
- Pairwise map: 1–1.5 hours.
- Total: approximately 5–6 hours.

Run a smoke test:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_phase3_interaction_search.py \
  --smoke \
  --output-dir results/phase3-interaction-search-smoke
```

Run or resume the full pipeline:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_phase3_interaction_search.py
```

The full output is `results/phase3-interaction-search-qwen25-vl-3b`. Raw predictions remain
ignored by Git; compact summaries and the generated report are committed after completion.

## Decision Rule

Proceed to LoRA plus answer/logit distillation only if the primary interaction-aware eight-block
route materially improves target accuracy over the existing independent eight-block route on the
development validation remainder. The practical recovery target is within 1–3 percentage points
of the full-model target accuracy.

If conditional search does not materially improve eight-block preservation, do not train an
arbitrarily selected eight-block route. Conclude that route selection alone cannot make aggressive
block pruning viable and either pivot to mechanistic interaction analysis or combine mild
four-block pruning with token pruning, quantization, and decoder compression.

## Unsupported Claims

Phase 3 cannot establish:

- external generalization;
- globally optimal routes outside the 16-block candidate pool;
- edge-device speedup;
- recovery from training;
- causal localization of a capability to a block or block pair;
- transfer to another VLM architecture.
