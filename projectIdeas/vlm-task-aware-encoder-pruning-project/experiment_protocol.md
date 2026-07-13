# Experiment Protocol

This document is the implementation contract. Changes to model, prompts, datasets, scoring, or
generation settings must be versioned in the run configuration.

## 1. Experimental Units

- Unit of analysis: one image-question-answer example.
- Intervention target: a vision-encoder transformer block or contiguous block span.
- Treatment: hard bypass, residual scaling, or activation replacement.
- Control: the same model, input, prompt, preprocessing, and decoding settings with all blocks.

## 2. Phase 0 Smoke Test

Before a full benchmark:

1. Load Qwen2.5-VL-3B-Instruct on the RTX 4090.
2. Enumerate named vision blocks and record tensor shapes.
3. Run 20 fixed examples from each capability bucket.
4. Bypass one early, middle, and late block independently.
5. Verify that no preprocessing, token count, or decoding setting changes.
6. Run each condition twice and compare outputs and timing variance.

Exit condition: all interventions produce valid outputs and repeated baseline scores match.

## 3. Data Manifest

Every example should have:

```json
{
  "id": "dataset/split/example-id",
  "image": "path-or-dataset-reference",
  "question": "...",
  "answers": ["..."],
  "capability": "ocr|counting|spatial|object|attribute",
  "subtype": "dataset-specific subtype",
  "metadata": {}
}
```

Create separate development and final-evaluation manifests. Do not select block pathways using
the final-evaluation examples.

## 4. Fixed Inference Settings

Record at minimum:

- model and exact revision;
- dtype and quantization;
- image resizing/dynamic-resolution settings;
- prompt template;
- maximum generated tokens;
- greedy or sampling parameters;
- software versions and GPU model;
- intervention specification;
- warm-up count and timing repetitions.

Use greedy decoding for the primary sweep unless a benchmark requires another setting.

## 5. Intervention Matrix

### Screening

- Full model.
- One hard bypass per vision block.
- Optional uniform baselines removing every nth block.

### Validation

- Residual scale `alpha` in `{1.0, 0.75, 0.5, 0.25, 0.0}` for selected blocks.
- Contiguous spans of lengths 2, 4, and 6.
- Same-sized random spans.
- Selected non-contiguous combinations.

For residual blocks represented as `x + F(x)`, scale only `F(x)` where the implementation allows
it. If the architecture differs, document the exact intervention rather than assuming identity
bypass is equivalent.

## 6. Measurements

Store one row per example and condition:

```text
run_id, example_id, capability, intervention, prediction, normalized_prediction,
correct, full_model_correct, answer_flipped, vision_latency_ms, total_latency_ms,
peak_memory_mb, visual_tokens
```

Aggregate only after preserving these paired example-level results.

## 7. Analysis

For each task and intervention calculate:

- native task score;
- score delta from full model;
- answer-flip rate;
- harmful flips: correct to incorrect;
- beneficial flips: incorrect to correct;
- paired bootstrap 95% confidence interval;
- median/p95 vision and end-to-end latency.

Compare task sensitivity vectors with correlation and distance metrics. A visually different
heatmap is not sufficient; estimate uncertainty on between-task differences.

## 8. Pruning Search

Use the development manifest only.

1. Generic ranking: average normalized sensitivity across tasks.
2. Task ranking: sensitivity within one capability.
3. Uniform baseline: evenly spaced block removal.
4. Random baseline: multiple subsets for each budget.
5. Greedy interaction-aware search: repeatedly remove the block with the smallest measured
   marginal damage.

Evaluate each method at identical executed-block budgets and then compare measured latency.

## 9. Recovery Training

Start with one method, not several:

- freeze the language decoder;
- retain the selected encoder pathway;
- distill final visual features from the full encoder;
- optionally combine feature loss with supervised answer loss;
- train on data disjoint from final evaluation;
- compare before and after recovery at the same architecture and compute.

Record whether recovery restores only benchmark performance or also the intermediate feature
geometry of the teacher.

## 10. Dynamic Router Gate

Build a runtime router only when both conditions hold:

- at least two task-specific pathways differ materially; and
- each beats the generic pathway for its target task at matched cost.

The simplest router is deterministic classification from the question into known capability
labels. Report oracle routing first, then predicted routing. This separates pathway quality from
router mistakes.

## 11. Reproducibility Checklist

- Fixed example manifests committed.
- Exact model revision recorded.
- Full run configuration saved with every result.
- Raw predictions retained.
- Baseline repeated after code changes.
- Warm-up excluded from timing.
- Confidence intervals generated from paired examples.
- Failed or malformed generations counted, not silently removed.
- Development and final evaluation kept separate.
