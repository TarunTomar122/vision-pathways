# Where Does Visual Grounding Die in Vision-Language Models?

**A scoped pre-MSc mechanistic research project (about 2 months, single RTX 4090)**
Author: Tarun Tomar
Target fit: Edoardo Ponti / Pasquale Minervini / multimodal research; secondary fit to ML systems if connected to efficient inference failure modes
Last updated: Jul 2026

---

## TL;DR

Modern VLMs can describe complex images but still fail at simple grounded tasks:
counting objects, reading changed digits, understanding left/right, or following a UI
instruction. The interesting question is not just *whether* they fail. It is:

> Where does the visual signal disappear: the vision encoder, the projector, early LLM
> layers, or late language-generation attention?

This project studies that question causally. Instead of only reporting accuracy, it uses
attention analysis, activation patching, component-wise probes, and a small intervention
to test a mechanism.

Safe version:

1. Pick **two grounded skills**: counting + OCR/layout or counting + spatial relations.
2. Build controlled image pairs where the answer changes for a known visual reason.
3. Localize where the answer-relevant signal is preserved, degraded, or ignored.
4. Test one lightweight intervention: attention redistribution, visual-attention floor,
   projector patching, or targeted synthetic fine-tuning.

This is less job-systems-aligned than the KV-cache idea, but it is much more genuinely
research-shaped.

---

## The Core Hypothesis

VLM grounding failures are not one phenomenon.

Possible mechanism:

> Counting fails because visual evidence exists early but gets ignored by later language
> layers. OCR may fail because fine-grained patch information is lost in the
> vision-to-language projector. Spatial layout may fail because 2D structure is flattened
> into weak 1D positional signals.

The project should test whether that claim is true.

If it is false, that is still useful. For example, maybe all failures reduce to bad
attention allocation in the LLM decoder. Or maybe small VLMs fail at the vision encoder,
while larger VLMs fail at the language stage. A real research project allows that answer.

---

## Why This Is Not Just Benchmarking

A benchmark-shaped project asks:

> Which model gets the highest score on counting or spatial reasoning?

This project asks:

> Which internal component causally carries the visual signal, where is it lost, and can
> a minimal intervention recover it?

That gives you:

- A hypothesis that could be false.
- A mechanism, not just a leaderboard.
- Causal tests via activation patching or intervention.
- A clearer contribution even if the final accuracy gain is small.

---

## Research Questions

1. **RQ1: Stage localization**
   - For a grounded skill, is the relevant signal present in the vision encoder,
     after the projector, in early LLM layers, or in late LLM layers?

2. **RQ2: Skill-specific failure**
   - Do counting, OCR, and spatial layout fail at the same stage, or at different
     stages?

3. **RQ3: Causal components**
   - Are there specific attention heads/layers that route visual evidence into the
     answer token?

4. **RQ4: Minimal intervention**
   - Can a small intervention restore the lost signal without retraining the full model?

---

## Related Work Map

| Area | What exists | Remaining gap |
|---|---|---|
| Counting circuits | Counting heads and visual activation patching have been studied | Mostly counting-only; unclear if the same circuit explains OCR/layout |
| Visual attention sink | Some visual tokens absorb attention despite being irrelevant | Needs task-specific causal analysis |
| Projector information loss | Connectors distort visual embedding geometry | Needs downstream causal link to specific grounded failures |
| Spatial architecture failures | CLIP encoders, 1D flattening, and weak 2D position hurt spatial reasoning | Needs component-level causal localization |
| VLM mech-interp tooling | Spectra and custom activation patching code now exist | Few complete small-scale project recipes |

---

## The Most Useful Papers

### 1. Counting Circuits: Mechanistic Interpretability of Visual Reasoning in LVLMs

Link: https://arxiv.org/html/2603.18523v1

What it does:

- Studies counting as a simple but powerful visual reasoning task.
- Introduces **Visual Activation Patching** and **HeadLens**.
- Finds functional head categories:
  - visual grounding
  - cross-modal routing
  - counting aggregation
  - difficulty/existence detection
- Shows targeted counting fine-tuning also improves broader visual reasoning slightly.

Why it matters:

This is the closest prior art. It proves that VLM visual reasoning can have identifiable
circuits rather than being completely opaque.

Gap for this project:

It focuses heavily on counting. You can ask whether OCR, spatial layout, and UI grounding
reuse the same heads or fail elsewhere.

---

### 2. Counting to Four is still a Chore for VLMs

Link: https://arxiv.org/html/2604.10039

What it does:

- Builds controlled counting cases.
- Shows count-relevant evidence is strongest around the modality projection stage.
- Shows this evidence degrades in later LLM layers, where text priors dominate.
- Proposes **Modality Attention Share (MAS)**: force a minimum budget of visual attention.

Why it matters:

This directly supports the "the model sees it early, then loses/ignores it later" story.

Gap for this project:

Counting only. The next question is whether visual-evidence decay also explains OCR,
spatial relations, or document/UI grounding.

---

### 3. See What You Are Told: Visual Attention Sink in Large Multimodal Models

Link: https://arxiv.org/abs/2503.03321

What it does:

- Finds **visual attention sink** tokens: visual tokens that receive high attention even
  when irrelevant.
- Shows these sink tokens can often be removed without hurting performance.
- Proposes **Visual Attention Redistribution (VAR)** to move attention toward useful
  visual tokens.

Why it matters:

This gives a concrete internal failure mode: the model may not be lacking visual
information; it may be spending attention budget badly.

Gap for this project:

It is broad. It does not deeply explain why some skills break while others survive.

---

### 4. Lost in Embeddings: Information Loss in Vision-Language Models

Link: https://aclanthology.org/2025.findings-emnlp.1235/

What it does:

- Studies the connector/projector between the vision encoder and LLM.
- Finds k-nearest-neighbor relationships diverge by 40-60% after projection.
- Shows patch-level embedding loss can predict where models struggle.

Why it matters:

This suggests grounding may die before the LLM reasoning stack: at the projector.

Gap for this project:

It studies representation distortion, but not a complete causal chain from information
loss -> wrong answer -> intervention.

---

### 5. Spatial Reasoning is Not a Free Lunch: A Controlled Study on LLaVA

Link: https://arxiv.org/pdf/2603.12545

What it does:

- Tests spatial reasoning failures in LLaVA-style VLMs.
- Argues failures are tied to CLIP-style encoders, 1D flattening of image patches, and
  weak 2D positional structure.
- Compares encoder choices and 2D positional encoding variants.

Why it matters:

It frames spatial failure as architectural, not just "more data needed."

Gap for this project:

It is more diagnostic than causal. You can ask which layer/head/component loses the
spatial signal.

---

### 6. Beyond Semantics: Rediscovering Spatial Awareness in VLMs

Link: https://arxiv.org/html/2503.17349

What it does:

- Studies why VLMs underuse spatial cues.
- Proposes tools:
  - Position Sensitivity Index
  - Cross-Modality Balance
  - RoPE Sensitivity probe
- Finds visual token norms and text token norms can be imbalanced, suppressing positional
  signals.
- Tests targeted interventions that restore positional sensitivity.

Why it matters:

This is a good bridge between diagnosis and intervention.

Gap for this project:

Needs broader testing across models and grounded skills.

---

### 7. Spectra: A Mechanistic Interpretability Library for VLMs

Link: https://aclanthology.org/2026.acl-demo.78.pdf

What it does:

- Provides VLM-specific mech-interp tooling.
- Supports Qwen2.5-VL, Qwen3-VL, LLaVA 1.5, and SmolVLM.
- Exposes activation caching, activation patching, and attention analysis.

Why it matters:

This may save weeks. It turns the project from "build interpretability plumbing" into
"run experiments."

---

## Methods You Would Use

### Behavioral controls

Build or use synthetic controlled cases:

- Counting: 1-6 repeated shapes, clutter, overlap, adversarial wording.
- OCR: same template with one digit/word changed.
- Spatial: left/right, above/below, between, nearest/farthest.
- Optional UI: identify a button after a small layout change.

Controlled pairs matter because activation patching needs clean/corrupted examples:

- Clean image: answer is "3".
- Corrupted image: answer is "4".
- Same prompt, only the relevant visual evidence changes.

### Probes and localization

For each skill:

- Probe vision encoder features for the answer.
- Probe projected visual tokens.
- Probe residual stream across LLM layers.
- Measure attention from answer token to visual tokens.
- Measure cross-modality balance: visual vs text attention share.

### Causal tests

Use activation patching:

- Run clean input and corrupted input.
- Patch activations from clean into corrupted at specific layers/heads/token positions.
- If the answer recovers, that component carried causal information.

Useful patch points:

- visual token embeddings after projector
- early LLM residual stream
- specific attention head outputs
- attention patterns from answer token to image tokens

### Interventions

Pick one:

- **MAS-style visual attention floor:** force minimum visual attention during answer
  generation.
- **VAR-style attention redistribution:** remove visual sink tokens and redistribute
  attention to image-centric heads.
- **Projector-side patching:** preserve/reinject high-loss patch embeddings.
- **Small targeted fine-tune:** synthetic counting or spatial data only, then test
  out-of-distribution transfer.

---

## Datasets

### Best for a 2-month scope

1. **Synthetic counting / spatial dataset**
   - You generate it yourself.
   - Full control.
   - Perfect for causal patching because clean/corrupted pairs are exact.

2. **COUNTINGTRICKS / counting datasets from the counting papers**
   - Link from paper: https://github.com/leduy99/-CVPRW26-Modality-Attention-Share
   - Useful if released and runnable.

3. **CountBench / TallyQA-style data**
   - More natural counting evaluation.
   - Use after synthetic controls.

4. **Synthetic OCR/doc templates**
   - Generate invoices/forms/screenshots with one changed digit or label.
   - This tests "tiny visual change, big semantic change."

5. **ScreenSpot-v2 or simple UI grounding**
   - Optional later.
   - Useful if you want a UI-agent angle.

### Do not start with

- Full MMLongBench-Doc.
- Full GUI-agent trajectories.
- Real robotics/VLA sim.

Those are too broad for this mechanistic version.

---

## Models

Recommended starting point:

| Model | Why |
|---|---|
| **Qwen2.5-VL-3B** | strong, modern, supported by Spectra, fits 4090 |
| **SmolVLM** | small, fast, supported by Spectra, good for quick patching experiments |
| **LLaVA 1.5 7B** | older but very studied; supported by Spectra |

Do not start with a closed model. You need hooks.

Recommended order:

1. SmolVLM for pipeline/debugging.
2. Qwen2.5-VL-3B for main results.
3. Optional LLaVA 1.5 as cross-architecture comparison.

---

## Scoped 2-Month Plan

### Phase 0: Reproduce and choose task (Week 1)

- Get Spectra or equivalent hooks running.
- Run one counting task on SmolVLM/Qwen2.5-VL.
- Confirm you can cache activations and patch layers.
- Decide the two skills:
  - counting + spatial, or
  - counting + OCR.

### Phase 1: Controlled dataset (Week 2)

- Generate 500-2000 clean/corrupted image pairs.
- Keep prompts fixed.
- Make failures interpretable:
  - one object added
  - one digit changed
  - one object moved left/right

### Phase 2: Localization (Weeks 3-4)

- Probe stage-wise signal:
  - vision encoder
  - projector
  - early LLM layers
  - late LLM layers
- Plot signal strength across the stack.
- Identify whether each skill dies in the same place.

### Phase 3: Causal patching (Weeks 5-6)

- Patch clean activations into corrupted runs.
- Find layers/heads where patching recovers the correct answer.
- Identify visual grounding/routing/aggregation components.

### Phase 4: Intervention (Week 7)

- Implement one lightweight intervention:
  - MAS visual attention floor, or
  - VAR attention redistribution, or
  - projector-side correction.
- Measure whether it improves the specific failure without hurting general behavior.

### Phase 5: Write-up (Week 8)

- Produce:
  - mechanism diagram
  - layer-wise signal plots
  - patching heatmaps
  - intervention ablation
  - concise report/blog

---

## Expected Outcomes

### Minimum viable result

> Counting and OCR/spatial signals degrade at different stages of the VLM stack.

Even if no intervention works, this is useful if backed by causal patching.

### Strong result

> A specific class of heads/layers causally mediates grounded reasoning, and a cheap
> intervention recovers failures on controlled examples.

### Very strong result

> The same visual grounding/routing circuit transfers across tasks, or alternatively,
> counting/OCR/spatial use separable circuits. Either answer is publishable-style.

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Activation patching is slow | Start with SmolVLM; patch coarse layers first |
| Spectra has rough edges | Fall back to HuggingFace hooks on Qwen/LLaVA |
| Synthetic data looks toy-ish | Use it for causal analysis, then validate on CountBench/TallyQA |
| No intervention improves accuracy | Negative result still okay if localization is strong |
| Too many skills | Pick only two skills |

---

## Critical Read

This is the most research-shaped option so far.

Strengths:

- Real mechanism, not leaderboard work.
- Clear causal methods.
- Good for building research muscle.
- Feasible with a 4090 if scoped.
- Strong intellectual link to VLM grounding, multimodal reasoning, and interpretability.

Weaknesses:

- Less directly aligned with ML systems jobs than KV-cache or edge VLM work.
- Needs careful experimental design.
- Synthetic data can look small unless validated on real benchmarks.
- Mechanistic claims are easy to overclaim; must stay modest.

Best framing:

> A mechanistic study of where different grounded visual skills are preserved, lost, or
> ignored inside modern VLMs, with a lightweight intervention to test the diagnosis.

---

## Open Decisions

1. Which pair of skills?
   - Recommendation: **counting + OCR** if you want docs/UI relevance.
   - Alternative: **counting + spatial layout** if you want pure multimodal reasoning.

2. Which model first?
   - Recommendation: **SmolVLM for debugging, Qwen2.5-VL-3B for main results**.

3. What intervention?
   - Recommendation: start with **MAS-style visual attention floor** because it is easy
     and directly tests the "language layers ignore vision" hypothesis.

