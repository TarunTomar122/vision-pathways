# Reliability-Aware KV-Cache Reuse for Vision-Language Models

**A scoped pre-MSc research project (≈2 months, single RTX 4090)**
Author: Tarun Tomar · Target supervisor fit: Luo Mai (ML Systems), Edoardo Ponti (efficient inference)
Last updated: Jul 2026

---

## TL;DR

VLMs turn a single image into hundreds–thousands of "visual tokens," which blow up the
KV cache and make serving slow and expensive (**UI-TARS-1.5-7B needs 76 GB of GPU memory
for just 5 screenshots**). People reuse/compress this cache to save cost — but they only
ever report **aggregate accuracy**, which hides *which capability quietly broke*. This project:

1. **Measures the reliability of KV reuse/compression, sliced by capability** (OCR, tables,
   spatial grounding) + instance-flip rate + hallucination rate. → *guaranteed result.*
2. **Builds a similarity-gated reuser for near-duplicate images** (docs/UI screenshots that
   differ slightly), borrowing the "position-independent caching" recipe from text-RAG. → *stretch upside.*

---

## The idea in one paragraph

When a VLM sees an image it has *already seen* (or nearly so), can we skip recomputing its
expensive KV cache and reuse the stored one — and if so, **how similar is "similar enough"
before the model silently starts getting things wrong?** Exact-match reuse already ships
(vLLM, LMCache). Same-image smart reuse just landed (VLCache). Video-frame similarity reuse
exists (InfiniPot-V, Sali-Cache). The **open seam** is (a) *near-duplicate cross-request*
reuse for documents/UI (not temporal video frames), and (b) the **capability-sliced
reliability** of any of it. That intersection is this project.

---

## Why it matters

- **Cost:** image tokens dominate the KV cache. Screenshot/document VLMs are the worst case.
  76 GB for 5 screenshots (UI-TARS-1.5-7B) is not deployable — reuse/compression is mandatory.
- **Real use cases with real volume:** document AI (invoices, forms, contracts), UI/computer-use
  agents, retail visual search. All send *near-duplicate* images at scale (same template, same
  screen, same product at a slightly different angle).
- **The blind spot:** every reuse/compression paper reports one aggregate accuracy number.
  A quantized/reused model can drop ~1% on average while **flipping ~20% of individual answers**
  and destroying a *specific* capability (e.g. reading a changed digit). In documents, the one
  flipped digit is the whole point.

---

## The research gap (what's solved vs open)

| Sub-problem | Status | What it means for this project |
|---|---|---|
| Reuse KV for a **byte-identical** image | **Solved / shipping** (vLLM, LMCache) | Baseline to beat |
| Reuse the **same image** in a new context (position changed) | **Recent** (VLCache, Dec 2025) | Borrow the layer-aware recompute idea |
| Reuse KV despite **position shift** (text) | **Solved** (CacheBlend EuroSys'25, EPIC ICML'25) | Port the "recompute ~15% highest-deviation tokens" recipe to vision |
| Exploit **video-frame** redundancy | **Active** (InfiniPot-V, Sali-Cache) | Only works with a temporal stream + aligned patches |
| Compress KV **within one GUI trajectory** | **Active** (GUI-KV, STaR-KV) | Fork the code; still intra-session, still aggregate metrics |
| **Near-duplicate cross-request** reuse (docs/UI) | **OPEN** | Core contribution |
| **Capability-sliced reliability** of reuse | **OPEN** | Core contribution (safe result) |

**Why video methods don't transfer to docs/UI:** they compare patch (x,y) at frame *t* to patch
(x,y) at frame *t+1* — they assume a single ordered stream + smooth motion + aligned patches.
Documents/UI break all three: no stream (different users/requests), near-duplicates are *reflowed*
(insert a row → everything shifts to new positions), and a tiny visual change can be a huge
semantic change (a `0` → `8`). So you need a *content* similarity gate + an alignment step, not
an optical-flow temporal diff.

---

## Research questions

1. **RQ1 (reliability):** When we reuse/compress the KV cache of VLMs, *which capabilities
   degrade first* (OCR/text, tables, charts, spatial grounding), and how much does the aggregate
   accuracy number hide it (instance-flip rate, hallucination rate)?
2. **RQ2 (gating):** For near-duplicate (non-identical) images, what cheap signal (perceptual
   hash, CLIP/ViT-embedding distance) best predicts whether KV reuse is *safe*, and is the safe
   threshold **task-dependent**?
3. **RQ3 (method, stretch):** Can a position-independent, selective-recompute reuser (CacheBlend-style)
   applied to *visual* tokens recover accuracy for near-duplicates at a fraction of the compute?

---

## Scope & plan (2 months, single RTX 4090 · 24 GB)

**Phase 0 — De-risk (Week 1)**
Reproduce GUI-KV's ScreenSpot-v2 + AgentNetBench numbers with Qwen2.5-VL-3B. Confirm environment,
baseline, and that everything fits in 24 GB.

**Phase 1 — Guaranteed result (Weeks 2–4): capability-sliced reliability**
Take existing methods (exact prefix caching, GUI-KV compression, temporal reuse) and, instead of
aggregate accuracy, measure **per-capability accuracy + instance-flip rate + hallucination rate**
(using MMLongBench-Doc's evidence-source labels and unanswerable questions). Headline finding:
*"the reported 1% drop hides an X% collapse on OCR / small-change detection."*

**Phase 2 — Upside (Weeks 5–7): similarity-gated near-duplicate reuse**
Build a cheap gate (CLIP/ViT-embedding distance or perceptual hash) + port CacheBlend/EPIC's
selective-recompute to visual tokens for *near-duplicate* images. Test on multi-page docs
(natural near-dups) and **synthetic perturbations** (insert row / flip digit / add modal — gives
ground truth for "small visual change, big semantic change"). Produce the **reuse-safety vs
similarity curve, per task**.

**Phase 3 — Write-up (Week 8)**
Ablations, plots, short report/blog, clean repo.

---

## Models (all fit a single 4090)

| Model | Size | Role | Link |
|---|---|---|---|
| **Qwen2.5-VL-3B-Instruct** | 3B | Primary backbone (docs + GUI) | https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct |
| ShowUI-2B | 2B | GUI-specific comparison | https://huggingface.co/showlab/ShowUI-2B |
| UI-TARS (2B) | 2B | GUI agent comparison | https://github.com/bytedance/UI-TARS |
| Qwen2.5-VL-7B-Instruct | 7B | "does it hold at 7B" stretch | https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct |

Default: **Qwen2.5-VL-3B** — the backbone the GUI-grounding subfield standardized on
(ZonUI-3B, Qwen-GUI-3B both fully fine-tuned it on a single 4090), so results stay comparable.

---

## Datasets

**GUI / agents** (all pre-wired in the GUI-KV eval scripts):
- **ScreenSpot-v2** — GUI element grounding (cleaned). https://github.com/SalesforceAIResearch/GUI-KV
- **ScreenSpot-Pro** — 1,581 expert-annotated high-res professional screenshots.
- **AgentNetBench**, **Multimodal Mind2Web** (https://huggingface.co/datasets/osunlp/Multimodal-Mind2Web),
  **AndroidControl** — multi-step trajectories (semi-temporal).

**Documents** (near-duplicate goldmine):
- **MMLongBench-Doc** — 135 PDFs, avg 47.5 pages, 1,091 Qs. Evidence labeled by source
  (text/table/chart/image/layout → *free capability slices*); 22.5% unanswerable (hallucination probe);
  33% cross-page. https://mayubo2333.github.io/MMLongBench-Doc · https://github.com/mayubo2333/MMLongBench-Doc
- **MP-DocVQA** — multi-page (≤20). **DocVQA** — single-page baseline. **M3DocVQA** — https://m3docrag.github.io/
- **Synthetic near-duplicates** — perturb a base doc/screenshot (insert row, flip digit, add modal)
  for controlled ground truth.

---

## Metrics

**Efficiency:** TTFT, decode FLOPs, peak GPU memory, KV-cache budget (%), throughput, cache hit rate.

**Quality (the differentiator — sliced, not aggregate):**
- Per-capability accuracy (OCR/text vs table vs chart vs spatial grounding)
- **Instance-flip rate** (fraction of individual answers that change vs full compute)
- **Hallucination rate** on unanswerable questions
- Task accuracy (step accuracy for agents, F1/ANLS for DocVQA) — for comparability

---

## Expected outcomes / deliverables

1. **Reliability finding + curves** — which capabilities break first under reuse/compression, and
   by how much the aggregate number lies. (Novel-ish, safe, lands regardless of Phase 2.)
2. **A method (stretch)** — similarity-gated selective-recompute reuse for near-duplicates + a
   safe-threshold predictor.
3. **Artifacts** — forked GUI-KV repo, eval harness with capability slices, accuracy-vs-budget /
   accuracy-vs-similarity plots, short writeup/blog. CV-ready + a real dissertation seed for Luo Mai.

---

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| 7B won't fit with large KV on 24 GB | Use 3B / fewer images / int4 quantization |
| Phase 2 reuser is hard to get working | Phase 1 reliability result stands alone |
| Real near-duplicate doc data is scarce | Synthetic perturbations (better — ground truth) |
| Reproducing baselines eats time | GUI-KV ships eval scripts for 5 benchmarks |

---

## Supervisor alignment

- **Luo Mai** — leads Large-Scale ML Systems Group; **ContextPilot** (MLSys) is literally about
  context/KV reuse. Direct lane.
- **Edoardo Ponti** — efficient LLM inference, KV-cache compression. Teaches ANLP (Sem 1).

---

## Open decisions (to finalize)

1. **Primary surface: GUI/agents vs documents?** (Changes primary dataset + models.)
   - GUI → sequential screenshots, semi-temporal, GUI-KV code ready.
   - Docs → clearer near-duplicate story, MMLongBench-Doc's capability slices + hallucination probe.
2. How far to push Phase 2 (measurement-only vs build a working reuser).

> Recommendation: **start doc-first** (cleaner reliability story + built-in capability slices),
> keep GUI as the comparison surface. But this is your call.
