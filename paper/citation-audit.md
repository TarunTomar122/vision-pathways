# Citation Audit

This audit records the primary source and the reason each reference appears in the paper. Metadata was checked
against the linked publisher, repository, or arXiv record on 2026-07-18. This is an agent-assisted metadata and
relevance audit. It does not replace the author's obligation to read the cited work and verify the paper's
characterization before submission.

## Models And Motivation

| Key | Primary source | Use in this paper | Status |
| --- | --- | --- | --- |
| `bai2025qwen25vl` | [Qwen2.5-VL](https://arxiv.org/abs/2502.13923) | Qwen architecture and model context | Checked |
| `huggingface2025smolvlm2` | [SmolVLM2 model card](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct) | Exact model and pinned revision | Checked |
| `kaplan2020scaling` | [Scaling Laws](https://arxiv.org/abs/2001.08361) | Scaling motivation | Checked |
| `hoffmann2022training` | [Chinchilla](https://arxiv.org/abs/2203.15556) | Compute-scaling motivation | Checked |

## Compression And Routing

| Key | Primary source | Use in this paper | Status |
| --- | --- | --- | --- |
| `men2024shortgpt` | [ShortGPT](https://arxiv.org/abs/2403.03853) | Training-free residual-layer pruning baseline | Checked |
| `ma2025shortlvlm` | [Short-LVLM](https://arxiv.org/abs/2507.23362) | Closest generic VLM layer-pruning comparison | Checked against arXiv and DOI |
| `ashkboos2024slicegpt` | [SliceGPT](https://arxiv.org/abs/2401.15024) | Structured width-pruning comparison | Checked |
| `rao2021dynamicvit` | [DynamicViT](https://arxiv.org/abs/2106.02034) | Learned visual-token sparsification | Checked |
| `bolya2023tome` | [Token Merging](https://arxiv.org/abs/2210.09461) | Training-free visual-token merging | Checked |
| `zhang2025vscan` | [VScan](https://arxiv.org/abs/2505.22654) | Visual-token reduction comparison | Corrected to current title, authors, and TMLR 2026 venue |
| `zhang2025sparsevlm` | [SparseVLM](https://arxiv.org/abs/2410.04417) | Visual-token sparsification comparison | Checked |
| `tong2025flowcut` | [FlowCut](https://proceedings.neurips.cc/paper_files/paper/2025/hash/88441fee0c0dacceb95e4ad77ece5d0a-Abstract-Conference.html) | Information-flow-based VLM efficiency | Checked against NeurIPS proceedings |
| `sarkar2026flashvlm` | [FlashVLM](https://openreview.net/forum?id=7U9pt9yUQF) | Input-dependent VLM layer skipping | Checked against OpenReview |
| `khaki2026domainaware` | [Domain-aware pruning](https://arxiv.org/abs/2603.20275) | Domain-dependent decoder-layer selection | Checked |
| `deb2002nsga2` | [NSGA-II DOI](https://doi.org/10.1109/4235.996017) | Multi-objective selection method | Checked |

## Benchmarks

| Key | Primary source | Use in this paper | Status |
| --- | --- | --- | --- |
| `fu2023mme` | [MME](https://arxiv.org/abs/2306.13394) | Controlled second source across capability cells | Checked |
| `liu2023ocrbench` | [OCRBench](https://arxiv.org/abs/2305.07895) | OCR development and selection data | Corrected to current title and author list |
| `acharya2019tallyqa` | [TallyQA](https://arxiv.org/abs/1810.12440) | Counting data | Checked |
| `liu2023vsr` | [VSR](https://arxiv.org/abs/2205.00363) | Spatial-reasoning data | Checked |
| `li2023pope` | [POPE](https://arxiv.org/abs/2305.10355) | Object-presence data | Checked |
| `goyal2017vqav2` | [VQAv2](https://arxiv.org/abs/1612.00837) | Attribute data | Checked |
| `mishra2012iiit5k` | [IIIT5K DOI](https://doi.org/10.5244/C.26.127) | Sealed post-freeze OCR transfer audit | Checked |

## Corrections Made

- Updated OCRBench's title and full author list from its current primary record.
- Updated VScan to its current title, eight-author list, 2026 year, and TMLR venue.
- Replaced FlowCut's generic reference URL with the official NeurIPS proceedings page.

All 22 bibliography entries are cited by `paper/main.tex`; the clean-package preflight rejects missing or unused
entries.
