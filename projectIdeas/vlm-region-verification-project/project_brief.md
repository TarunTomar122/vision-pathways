# Region-Grounded Verification for VLM OCR and Document Answers

**A scoped pre-MSc research project (about 2 months, single RTX 4090)**
Author: Tarun Tomar
Target fit: ML reliability, document AI, VLM grounding, production ML systems
Last updated: Jul 2026

---

## TL;DR

Vision-language models are increasingly used as OCR and document-understanding engines, but
they often produce answers that are **plausible** rather than visually verifiable. Existing
risk-control methods catch many unstable OCR hallucinations by checking whether the same
answer appears across multiple crops/views. But they admit one major residual failure:

> **stable-but-wrong consensus**: the model confidently repeats the same wrong answer across
> multiple views, so a cross-view agreement system accepts it.

This project targets that specific gap.

Instead of asking "is the answer stable across views?", ask:

> Is the answer locally supported by a specific image region?

The project builds a small verification layer that ties a candidate answer to localized visual
evidence using crops, OCR specialists, string/structure checks, and possibly a VLM verifier. It
then measures whether region-grounded verification catches errors that cross-view consensus
misses.

---

## Why This Is Different From The First Two Projects

| Project | Main question | Flavor |
|---|---|---|
| KV-cache reuse | Can we reuse/compress visual context safely? | ML systems + reliability |
| Grounding mechanisms | Where does visual signal die inside the model? | Mechanistic interpretability |
| **Region verification** | Can we prove a generated answer is visually supported? | Deployment reliability + document AI |

This third idea is less about model internals and more about an **external reliability contract**:
answer, abstain, or acquire local evidence.

---

## The Core Hypothesis

Cross-view consistency is a useful risk signal, but not proof of correctness.

Hypothesis:

> Stable-but-wrong OCR/document errors happen because global VLM generation optimizes semantic
> plausibility, while OCR/document extraction needs local geometric support. A region-grounded
> verifier should catch a subset of errors that cross-view consensus accepts.

This could be false. If stable-but-wrong errors remain visually supported under all local checks,
then region verification may not help. That is still a useful negative result.

---

## Why This Is Not Just Benchmarking

Benchmark-shaped:

> Run VLMs on DocVQA/OCRBench and compare scores.

Research-shaped:

> Identify a residual failure mode of current risk-control systems, build a targeted verifier for
> that failure, and quantify the coverage-risk trade-off.

The key object is not accuracy. It is **exposed risk**:

- accepted wrong answers
- catastrophic OCR substitutions
- over-generation
- unsupported answer spans
- abstention/coverage trade-off

---

## Related Work Map

| Area | What exists | Remaining gap |
|---|---|---|
| Generative OCR risk control | GRC uses multi-view consensus and structural checks | Fails on stable-but-wrong consensus; suggests region-level verification as next step |
| Latent abstention probes | LRP/HALP detect uncertainty from hidden states | Requires access to internals; not always tied to local visual evidence |
| OCR hallucination mitigation | KIE-HVQA, PAR, VISTA reduce hallucinations | Often improves generation, but not always an auditable accept/abstain contract |
| Region-aware verification | R-CoV/CoReVe verify object hallucinations with regions | Mostly object hallucination, not OCR/document answer support |
| Document grounding | DocVAL, LAT, ARIAL, M3Grounder ground answers to regions | Often training-heavy or dataset-building; a small frozen-model controller is still open |

---

## Main Research Questions

1. **RQ1: Residual failure**
   - How often does cross-view consensus accept stable-but-wrong OCR/document answers?

2. **RQ2: Local evidence**
   - Can region-level verification detect errors that global/multi-view consistency misses?

3. **RQ3: Verifier design**
   - Which verifier is most useful under a small budget?
     - specialist OCR on crop
     - VLM crop verifier
     - string/format constraints
     - cross-view crop consistency
     - internal confidence/hidden-state probe

4. **RQ4: Coverage-risk trade-off**
   - How much coverage is sacrificed to reduce exposed catastrophic errors?

---

## The Proposed Method

### Baseline: Geometric Risk Controller style

1. Query a frozen VLM on multiple transformed views/crops.
2. Apply structural checks.
3. Accept if outputs are stable enough.
4. Abstain otherwise.

This catches unstable hallucinations.

### New layer: region-grounded verification

For each accepted answer:

1. **Localize candidate evidence**
   - Use OCR boxes, document layout boxes, text search, or VLM-predicted region.

2. **Crop and re-read**
   - Run a specialist OCR engine or smaller VLM on the candidate region.

3. **Check support**
   - Does the crop-level transcription support the global answer?
   - Does the answer appear in the expected local region?
   - Is the string stable under local crop perturbations?

4. **Decision**
   - accept if region support passes
   - abstain if unsupported
   - optionally acquire more evidence (zoom/crop)

### Main comparison

| System | What it catches | What it misses |
|---|---|---|
| Output confidence | cheap but miscalibrated | overconfident hallucinations |
| Cross-view consensus | unstable wrong answers | stable-but-wrong consensus |
| Region verification | unsupported local evidence | stable but locally plausible errors |
| Region + specialist OCR | many OCR hallucinations | OCR engine errors / ambiguous visual evidence |

---

## Datasets

### Start with controlled synthetic docs

Generate simple documents/forms/receipts with known fields:

- invoice number
- amount
- date
- name
- ID
- table cell

Then create perturbations:

- `30` vs `80`
- `approved` vs `denied`
- missing/blurred character
- overlaid glare/occlusion
- row inserted or shifted
- repeated template with one changed field

Why synthetic first:

- exact ground truth
- can create stable-but-wrong traps
- can separate OCR, localization, and reasoning failures
- cheap to generate

### Real validation datasets

Use one or two:

- **DocVQA**: standard document VQA baseline.
- **MP-DocVQA**: multi-page document QA.
- **OCRBench / TextVQA / ST-VQA**: OCR-heavy VQA.
- **KIE-HVQA** if available: degraded document hallucination benchmark.
- **MMLongBench-Doc** only as a later stretch, not the starting point.

---

## Models and Tools

### Frozen VLM generators

| Model | Role |
|---|---|
| Qwen2.5-VL-3B | main local model |
| SmolVLM2 | small/edge model |
| LLaVA / Idefics-style model | optional comparison |

### Verifiers

| Verifier | Why |
|---|---|
| PaddleOCR / PP-OCR | specialist OCR baseline, cheap |
| crop-level VLM prompt | tests whether VLM is better as verifier than generator |
| string/format validator | catches impossible outputs |
| local perturbation consistency | detects unstable visual support |
| latent probe (optional) | tests whether internals know uncertainty |

### Existing code to inspect

- GRC repository: https://github.com/phare111/GRC
- PaddleOCR / PaddleOCR-VL docs: https://www.paddleocr.ai/
- TinyDoc-VLM: https://github.com/eulogik/TinyDoc-VLM

---

## Related Papers

### 1. From Plausibility to Verifiability: Risk-Controlled Generative OCR for VLMs

Link: https://arxiv.org/html/2603.19790v3

What it does:

- Treats frozen-VLM OCR as selective accept/abstain.
- Uses multiple geometric views.
- Accepts only when outputs are stable.
- Reduces catastrophic OCR errors at predictable coverage cost.

Why it matters:

This is the direct foundation.

Gap:

The paper explicitly says its residual failure is **stable-but-wrong consensus** and that a
natural next step is **region-level verification**.

---

### 2. Reading Between the Lines: Abstaining from VLM-Generated OCR Errors via Latent Representation Probes

Link: https://arxiv.org/html/2511.19806v1

What it does:

- Trains lightweight probes on hidden states/attention patterns.
- Detects when the model should abstain from OCR/STVQA answers.
- Finds uncertainty signals in intermediate layers rather than output probabilities.

Why it matters:

Useful comparison: internal uncertainty vs external local evidence.

Gap:

It detects uncertainty, but does not directly prove local visual support.

---

### 3. HALP: Detecting Hallucinations in VLMs without Generating a Single Token

Link: https://aclanthology.org/2026.eacl-long.287.pdf

What it does:

- Predicts hallucination risk before generation using internal representations.
- Works across several VLMs.

Why it matters:

Another internal-probe baseline.

Gap:

Pre-generation risk is useful, but document/OCR applications often need answer-specific
evidence after generation.

---

### 4. Seeing is Believing? Mitigating OCR Hallucinations in MLLMs

Link: https://arxiv.org/html/2506.20168v2

What it does:

- Introduces degraded document/OCR hallucination setting.
- Uses uncertainty-aware grounding and refusal behaviors.

Why it matters:

Good benchmark/task inspiration for visually ambiguous OCR.

Gap:

More model-training oriented; not a lightweight frozen-model verifier.

---

### 5. PAR: Training-Free Positional Perturbation and Attention Recycling for Faithful OCR

Link: https://aclanthology.org/2026.acl-long.1065.pdf

What it does:

- Finds long OCR generation drifts from visual reading to language reciting.
- Uses positional perturbation and attention recycling to force the model to look back.

Why it matters:

Mechanism inspiration: OCR hallucination is partly attention drift.

Gap:

It improves generation; it does not build a region-grounded accept/abstain contract.

---

### 6. R-CoV / CoReVe: Region-Aware Chain-of-Verification

Link: https://arxiv.org/html/2604.20696v1

What it does:

- Uses region-level descriptions to verify object hallucinations.
- Checks whether entities in generated text are supported by the proposed regions.

Why it matters:

This is the closest region-verification method.

Gap:

Mainly object hallucination, not OCR/document field extraction. OCR needs stricter string and
geometric evidence.

---

### 7. DocVAL / Look as You Think / ARIAL / M3Grounder

Links:

- DocVAL: https://arxiv.org/html/2511.22521v2
- Look as You Think: https://doi.org/10.1609/aaai.v40i38.40488
- ARIAL: https://arxiv.org/html/2511.18192v2
- M3Grounder: https://openaccess.thecvf.com/content/CVPR2026/papers/Venna_M3Grounder_Mask-Based_Multi-Span_and_Multi-Granular_Grounding_for_Document_QA_CVPR_2026_paper.pdf

What they do:

- Ground document answers to boxes/masks/evidence.
- Improve interpretability and answer provenance.

Why they matter:

They show document grounding is an active and valuable direction.

Gap:

Many are training-heavy, dataset-heavy, or agent-heavy. This project stays small: frozen VLM +
external verifier + coverage-risk analysis.

---

## Scoped 2-Month Plan

### Phase 0: Reproduce baseline (Week 1)

- Run Qwen2.5-VL-3B or SmolVLM on synthetic OCR/doc prompts.
- Implement or fork a GRC-style multi-view consensus baseline.
- Measure accepted wrong answers.

### Phase 1: Build stable-but-wrong testbed (Week 2)

- Generate synthetic forms/receipts with visually similar fields.
- Add degradations: blur, glare, occlusion, compression, small fonts.
- Create cases where global generation is likely to produce plausible but wrong answers.

### Phase 2: Region verifier (Weeks 3-4)

- Localize likely evidence with OCR/layout boxes or text search.
- Crop candidate region.
- Re-read with specialist OCR and/or crop-level VLM.
- Define support score and accept/abstain rule.

### Phase 3: Coverage-risk evaluation (Weeks 5-6)

Compare:

- confidence threshold
- cross-view consensus
- region verification
- region verification + specialist OCR
- optional latent probe

Metrics:

- accepted-error rate
- catastrophic substitution rate
- coverage
- abstention rate
- cost / number of model calls
- stable-but-wrong catch rate

### Phase 4: Real-data validation (Week 7)

- Validate on DocVQA/OCRBench/TextVQA or a small curated real-doc subset.
- Keep this small; the synthetic testbed is the main controlled evidence.

### Phase 5: Write-up (Week 8)

- Failure taxonomy.
- Risk-coverage curves.
- Examples of stable-but-wrong consensus.
- Verifier ablation.
- Short report/blog and clean repo.

---

## Expected Outcomes

### Minimum viable result

> Cross-view consensus accepts a measurable class of stable-but-wrong OCR/document errors.

### Strong result

> Region-grounded verification catches a meaningful fraction of those errors at an acceptable
> coverage cost.

### Very strong result

> A small frozen-model verifier plus specialist OCR creates an auditable accept/abstain contract
> that beats confidence, self-consistency, and global cross-view agreement on catastrophic error
> reduction.

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Too close to GRC | Focus on its stated residual failure: stable-but-wrong consensus |
| Region localization is hard | Use synthetic boxes first; then OCR/layout boxes |
| Specialist OCR makes it "not VLM research" | Frame it as a verifier/control layer for frozen VLM deployment |
| Real datasets are messy | Use synthetic for causal evidence, real data for validation only |
| Too document-specific | This is okay; document AI is a real deployment use case |

---

## Critical Read

Strengths:

- Concrete, small, buildable.
- Has a very specific gap named by existing work.
- Strong production/reliability framing.
- Lets you build a real system, not only analyze internals.
- Useful for document AI and enterprise ML workflows.

Weaknesses:

- Less novel if someone publishes region-level OCR verification soon.
- More engineering/control-layer than core model research.
- Needs careful evaluation to avoid becoming "OCR pipeline beats VLM."

Best framing:

> A deployment-level verifier for frozen VLM document/OCR systems that catches stable-but-wrong
> errors by requiring localized visual support, not just global answer consistency.

---

## Open Decisions

1. Primary scope:
   - word/field-level OCR extraction, or
   - document VQA answer verification.

2. Verifier stack:
   - specialist OCR only,
   - VLM crop verifier only,
   - hybrid.

3. Main model:
   - Qwen2.5-VL-3B for realistic local VLM,
   - SmolVLM2 for fast iteration.

Recommendation:

Start with **field-level OCR extraction on synthetic forms**, then validate on a small real
document/OCR benchmark. Use a hybrid verifier: OCR boxes + crop OCR + VLM crop check.

