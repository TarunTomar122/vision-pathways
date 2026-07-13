# Task-Aware Vision-Encoder Pruning for Edge VLMs

**A scoped mechanistic efficiency project (about 2 months, single RTX 4090)**
Author: Tarun Tomar
Target areas: efficient multimodal inference, mechanistic analysis, edge VLMs
Last updated: Jul 2026

---

## TL;DR

Vision-language models normally execute the same complete vision encoder for OCR, counting,
spatial reasoning, and object questions. This project tests whether those capabilities depend
on different encoder blocks and whether that difference can support task-specific execution.

The project will:

1. Benchmark one open VLM on balanced OCR, counting, spatial, and object/attribute buckets.
2. Bypass individual vision-encoder blocks and contiguous block groups without fine-tuning.
3. Measure task-specific accuracy changes, answer flips, latency, and memory.
4. Verify promising patterns with graded interventions, activation probes, and repeated samples.
5. Build task-specific pruned variants and apply lightweight recovery training.
6. Attempt prompt-conditioned block execution only if task-specific pathways are genuinely
   different.

The intended contribution is not merely a smaller model. It is evidence about which visual
capabilities require which parts of the encoder, followed by a practical use of that evidence.

---

## Core Question

> Do OCR, counting, spatial reasoning, and recognition require measurably different subsets or
> depths of a VLM's vision encoder, and can those differences reduce edge inference cost without
> unacceptable task degradation?

## Hypotheses

- **H1: Task-specific sensitivity.** Bypassing a block changes some capability buckets more
  than others.
- **H2: Structured redundancy.** Several blocks or contiguous spans can be removed with little
  degradation, but the safe spans differ by task.
- **H3: Recoverability.** Lightweight distillation or adapter tuning recovers much of the loss
  caused by task-specific pruning.
- **H4: Conditional execution.** A task-aware pathway gives a better accuracy/latency frontier
  than one equally sized generic pruned encoder.

Each hypothesis may be false. If sensitivity maps are almost identical across tasks, the result
supports generic rather than task-aware pruning.

---

## What The Map Means

The first output is a **task-by-block sensitivity map**:

```text
sensitivity(task, block) = score(full model, task) - score(block bypassed, task)
```

This is evidence that a block is necessary under a particular intervention. It does **not** by
itself prove that the block stores a capability. A bypass can hurt because later blocks receive
an unfamiliar activation distribution. We therefore reserve the term **causal capability map**
for patterns that survive additional controls:

- graded residual suppression rather than only hard bypass;
- contiguous and combinatorial block removal;
- activation probing to test whether task-relevant information is decodable;
- activation patching or replacement where practical;
- recovery training to separate missing computation from distribution shift;
- replication across seeds and preferably a second model.

---

## Research Questions

1. **RQ1: Layer sensitivity**
   Which vision-encoder blocks are necessary for each capability bucket?
2. **RQ2: Capability specificity**
   Are differences between task maps larger than sampling and prompt variance?
3. **RQ3: Interactions**
   Do apparently redundant blocks become necessary when removed together?
4. **RQ4: Compression**
   Can capability-aware pruning beat generic pruning at the same measured latency or FLOPs?
5. **RQ5: Dynamic execution**
   Can the question select a safe encoder pathway at runtime without expensive routing?

---

## Novelty Boundary

Existing work already includes generic layer pruning, domain-aware decoder pruning, dynamic
layer skipping, visual-token pruning, resolution routing, and mixture-of-experts routing. The
project must not claim that task-aware pruning itself is new.

The narrower underexplored combination is:

> Fine-grained visual capability mapping across standard image-encoder blocks, causal validation
> of the map, and use of that map for task-specific or prompt-conditioned encoder execution.

The closest comparison is domain-aware layer selection. The distinction is that this project
targets the **vision encoder**, uses fine-grained visual capabilities rather than broad domains,
and requires interventions that establish more than activation similarity.

---

## Scope

### Minimum publishable unit

- One open VLM.
- Four balanced capability buckets.
- All single-block bypasses and selected contiguous-span bypasses.
- Statistical task-by-block comparison.
- Generic versus capability-aware pruning at matched compute.
- One recovery method.
- Real latency and peak-memory measurements on the RTX 4090.

### Stretch work

- Replication on a second architecture.
- Prompt-conditioned runtime routing.
- Evaluation on a lower-power edge device.
- Joint block and visual-token routing.

### Explicitly out of scope initially

- Pruning the language decoder.
- Training a VLM from scratch.
- Unstructured weight pruning and quantization research.
- Claiming neuron-level circuits from block-level ablations.
- Supporting every possible visual capability.

---

## Model Strategy

**Primary candidate: Qwen2.5-VL-3B-Instruct.** It fits a 24 GB RTX 4090 for inference and
lightweight tuning, is strong enough on OCR and general visual tasks, and has accessible open
implementations. Phase 0 must verify that its vision blocks can be bypassed cleanly and timed
without changing image preprocessing.

**Replication candidate: SmolVLM2 or another compact open VLM with a different vision tower.**
The second model is optional until the complete pipeline works on the primary model.

Model choice is governed by hookability, reproducible generation, memory use, benchmark support,
and licensing, not leaderboard rank.

---

## Dataset Strategy

The finalized benchmark has two suites. MME supplies a controlled yes/no protocol across OCR,
count, position, existence, and color. The external suite contains 300 examples each from direct
OCRBench text recognition, TallyQA counting, VSR spatial relations, and POPE object existence.
This balances natural capability coverage while retaining MME as an answer-format control.

All 1,480 examples are fixed by a manifest at revision-specific source commits. Images are hashed,
and development/test assignment is performed by image hash so paired questions and duplicate
images cannot cross splits. Dataset-native source scores are reported separately rather than
merging incompatible metrics into an unqualified leaderboard score.

Also create controls:

- shuffled-image questions;
- image-free questions where supported;
- prompt paraphrases;
- simple synthetic cases with exact labels;
- category and answer-frequency stratification.

---

## Method

### Stage 1: Full-model baseline

- Freeze model, decoding settings, image resolution policy, prompts, and random seeds.
- Cache example IDs and full-model outputs.
- Record per-bucket score, per-example correctness, latency, peak memory, and visual-token count.

### Stage 2: Screening map

- Replace one vision block at a time with an identity path.
- Run every block against the same examples.
- Record score delta and answer-flip rate relative to the full model.
- Bootstrap confidence intervals over examples.
- Plot task-by-block heatmaps and pairwise distances between task sensitivity profiles.

### Stage 3: Causal validation

- Scale a block's residual contribution through several values between full and bypassed.
- Remove selected contiguous spans of 2, 4, and 6 blocks.
- Test combinations predicted to be safe and unsafe by the screening map.
- Train simple probes on intermediate features as supporting, not causal, evidence.
- Patch or replace activations on a controlled subset where implementation permits.

### Stage 4: Pruned variants

Compare at matched latency or executed-block count:

1. generic pruning based on average sensitivity;
2. random or uniform-depth pruning;
3. capability-aware pruning from each task map;
4. full model and simple early-exit baselines.

Apply one lightweight recovery method: feature distillation from the full encoder, LoRA/adapters,
or limited supervised fine-tuning with the decoder mostly frozen.

### Stage 5: Dynamic routing, conditional on evidence

If capability-aware variants use meaningfully different pathways, infer a task label from the
question and select the corresponding path. Include router errors and routing overhead in the
final evaluation. If pathways are nearly identical, stop at static variants rather than forcing
a dynamic result.

---

## Evaluation

### Quality

- Dataset-native task score.
- Absolute and relative score drop from the full model.
- Per-example answer-flip rate.
- Worst-bucket degradation.
- Calibration or confidence where outputs expose it reliably.

### Efficiency

- Median and p95 end-to-end latency after warm-up.
- Vision-encoder latency separately from decoding.
- Peak allocated GPU memory.
- Executed blocks, estimated FLOPs, and model parameters actually removed.
- Throughput for batch size 1 and one practical batched setting.

Model file size is relevant only for physically pruned static variants. Runtime block skipping
reduces compute but does not reduce stored parameters unless unused weights are removed.

### Statistical tests

- Paired bootstrap confidence intervals over fixed examples.
- McNemar-style paired comparisons for binary correctness where appropriate.
- Multiple-comparison correction across blocks.
- Replication over prompt variants and at least three sampling/order seeds when stochasticity is
  present.

---

## Success Criteria

The project is successful if it produces a defensible answer, including a negative one.

Evidence supporting task-aware pruning should include:

- statistically different sensitivity profiles for at least two capabilities;
- a capability-aware variant that improves the worst-task or target-task score over generic
  pruning at matched measured cost;
- a real latency reduction, not only theoretical FLOPs;
- conclusions that survive at least one causal-validation control.

Strong negative result:

- capability maps are highly similar or unstable;
- generic pruning matches task-aware pruning;
- routing overhead or distribution shift removes the expected benefit.

---

## Risks

| Risk | Mitigation |
|---|---|
| A bypass causes distribution shift rather than information loss | Use graded suppression, spans, patching, and recovery training |
| Benchmark buckets contain language shortcuts | Use shuffled/image-free controls and controlled subsets |
| Single-layer effects are tiny because blocks are redundant | Test contiguous and optimized combinations |
| Search over block subsets becomes combinatorial | Use screening scores, greedy search, and a fixed evaluation budget |
| Claimed speedup does not appear in wall-clock timing | Benchmark compiled and eager paths; report measured latency honestly |
| Results are architecture-specific | Present as a case study; replicate only after the primary pipeline is stable |
| Dynamic router adds complexity without benefit | Make runtime routing a gated stretch goal |

---

## Eight-Week Plan

| Week | Output |
|---|---|
| 1 | Environment, model hooks, deterministic baseline, small smoke dataset |
| 2 | Dataset adapters, scoring, controls, full-model benchmark |
| 3 | Complete single-block bypass sweep |
| 4 | Heatmaps, confidence intervals, contiguous-span experiments |
| 5 | Generic and task-specific pruning search |
| 6 | Lightweight recovery tuning and distillation |
| 7 | Latency/memory benchmark; dynamic routing only if justified |
| 8 | Ablations, replication subset, report, and clean release |

---

## Deliverables

- Reproducible evaluation harness with fixed manifests.
- Vision-block intervention API.
- Task-by-block sensitivity and validated capability maps.
- Generic and capability-aware pruning baselines.
- Accuracy/latency/memory Pareto curves.
- Recovery-tuned checkpoints or adapters.
- Short research report documenting positive and negative findings.

## Immediate Next Step

The full-model baseline and pipeline checks are complete. Implement identity bypasses for one
early, middle, and late block on the 100-example smoke manifest, verify tensor/output invariants,
then launch the complete 32-block screening sweep against the fixed development manifest.
