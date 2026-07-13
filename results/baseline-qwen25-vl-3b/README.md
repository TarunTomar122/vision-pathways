# Qwen2.5-VL-3B Unpruned Baseline

Run date: 2026-07-13
Hardware: NVIDIA GeForce RTX 4090, 24,564 MiB
Model revision: `66285546d2b821cf421d4f5eb2576359d3770cd3`
Manifest SHA-256: `3dcae96bfb9f63d34362f0abde7dafcf883b3f42a5578c353512b7593c079fcd`

## Configuration

- BF16, SDPA, greedy decoding, maximum 24 generated tokens.
- Three warm-up examples excluded from recorded measurements.
- Qwen dynamic resolution pinned to 256-1,280 visual tokens.
- 32 vision-encoder blocks, 668,684,288 vision parameters.
- 3,754,622,976 total model parameters.

## Dataset

- 1,480 image-question examples and 1,136 unique images.
- 280 controlled MME examples.
- 1,200 external examples: 300 each from OCRBench, TallyQA, VSR, and POPE.
- 742 development and 738 test examples, assigned by image hash.

## Main Results

| Group | Examples | Accuracy | Median vision latency | Median total latency |
|---|---:|---:|---:|---:|
| Overall | 1,480 | 81.62% | 69.48 ms | 197.80 ms |
| Controlled MME | 280 | 88.57% | 70.92 ms | 201.57 ms |
| External suite | 1,200 | 80.00% | 69.15 ms | 189.55 ms |
| OCRBench | 300 | 81.00% | 63.16 ms | 202.76 ms |
| TallyQA | 300 | 72.00% | 60.89 ms | 153.31 ms |
| VSR | 300 | 79.33% | 82.10 ms | 217.01 ms |
| POPE | 300 | 87.67% | 72.61 ms | 186.27 ms |

Overall p95 vision latency was 97.96 ms and p95 total latency was 255.48 ms. Median visual
context was 322 tokens and p95 was 484. The sum of recorded per-example durations was about
294.8 seconds, or approximately 5.02 examples/second at batch size one.

Peak allocated memory was 7,726 MiB and peak reserved memory was 8,318 MiB. An uncapped preflight
allowed one high-resolution OCR image to retain 22.7 GiB and take about 11 seconds; the published
run uses the fixed visual-token ceiling and excludes those invalid preflight measurements.

## Diagnostic Results

- MME: existence 96.67%, color 93.33%, position 88.33%, count 86.67%, OCR 72.50%.
- TallyQA: simple 76.67%, complex 67.33%.
- POPE: random 89.00%, popular 88.00%, adversarial 86.00%.
- OCRBench: handwriting 58.00%, digit strings 66.00%, artistic text 90.00%, and non-semantic
  text 94.00%. Dataset-specific regular/irregular subsets are in `summary.json`.

These are baseline observations, not evidence about encoder blocks. The next experiment must run
the same fixed examples under one-block interventions and compare paired answer changes.

## Verification

- All 1,480 manifest IDs have exactly one prediction.
- No generated prediction is empty.
- Correctness was recomputed from raw outputs and matched every stored score.
- Twenty repeated greedy predictions were identical.
- Resume mode preserved the prediction file byte-for-byte.
- Raw predictions remain on the experiment machine and are excluded from Git.

See `summary.json` for complete capability/source/subtype aggregates and `run_metadata.json` for
the environment and exact configuration.
