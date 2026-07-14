# Decision: Separate pruning selection from evaluation and strengthen attribute coverage

- Date: 2026-07-14
- Commit: `d5298c5`
- Commit subject: `Add held-out pruning protocol and attribute slice`
- Status: Accepted

## Context

The original 1,480-example benchmark was useful for exploration, but the same full manifest had influenced block selection, combined-ablation analysis, and interpretation. Consequently, its existing combined-path results cannot be presented as untouched held-out evidence in a paper.

The original benchmark also contained only 60 attribute examples, all from MME color questions. Its development partition contained only 32 of those examples. A one-example change therefore moved development attribute accuracy by 3.125 percentage points, making small attribute comparisons unstable.

The project needed a protocol that clearly separated model-selection data from final evaluation data and a larger attribute bucket that remained deterministic and auditable.

## Decision

Create a V2 benchmark without changing or deleting V1. V2 must:

1. Preserve image-grouped development/test assignment.
2. Add 300 high-agreement VQAv2 color questions to strengthen attribute coverage.
3. Use development predictions to choose pruning configurations.
4. Keep test predictions out of candidate selection.
5. Label all previous full-manifest combined-ablation results as exploratory rather than held-out results.

The VQAv2 slice is restricted to questions beginning with `What color is` or `What color are`, answers supported by at least 9 of 10 annotators, and a balanced allocation across 11 common colors. Official VQAv2 question and annotation archives are pinned by SHA-256. Only selected COCO images are downloaded.

## Changes

- `src/vlm_bench/dataset_builder.py`
  - Added optional VQAv2 color ingestion.
  - Added balanced color quotas and annotator-agreement filtering.
  - Added official archive download and SHA-256 provenance.
  - Added explicit PIL image cleanup to bound memory usage.
  - Preserved V1 behavior when the new attribute count is zero.
- `scripts/prepare_dataset.py`
  - Added `--attribute-per-capability`.
- `scripts/select_development_candidates.py`
  - Added paired one-block analysis restricted to rows marked `development`.
  - Added explicit thresholds and a machine-readable selection report.
- `docs/protocol_v2.md`
  - Documented the dataset build and selection/evaluation boundary.
- `results/development-selection-qwen25-vl-3b/`
  - Saved the compact V1 development-only screening artifact.

## Resulting Dataset

The validated V2 manifest on the GPU host contains:

| Property | Value |
|---|---:|
| Total examples | 1,780 |
| Unique images | 1,431 |
| Development examples | 904 |
| Test examples | 876 |
| Attribute examples | 360 |
| Counting examples | 360 |
| Object examples | 360 |
| OCR examples | 340 |
| Spatial examples | 360 |
| Manifest SHA-256 | `ec3712d74a43caf8dd3d1818788ee0a92bc82e7aa597d640b00f089c6ed357c8` |

The added VQAv2 answer distribution is balanced: 28 examples each for black, blue, and brown; 27 each for gray, green, orange, pink, purple, red, white, and yellow.

## Development Screening Result

Applying the declared rule to the old V1 development predictions selected block 28. Under that intervention, development overall accuracy dropped by one net-correct example, approximately 0.135 percentage points. The largest capability-level net loss was three examples.

This result checks that the selector works. It is not the V2 pruning result because no V2 model inference had been run when this commit was created.

## Alternatives Considered

- Continue using the original full-manifest results as final evidence. Rejected because candidate choices had already been informed by those examples.
- Add all VQAv2 attribute-like questions. Rejected because broad free-form attributes introduce ambiguous categories and scoring semantics.
- Use the Hugging Face streaming image adapter. Rejected after it left long-running image-stream processes on the GPU host and failed to checkpoint reliably with the installed `datasets` runtime.
- Use the main COCO image hostname. Rejected on this host because TLS hostname validation failed. The established S3 COCO endpoint was used instead.
- Treat block 28 as the final V2 candidate. Rejected because V2 development inference has not yet been run.

## Verification

- Local Python compilation succeeded for all changed scripts.
- `git diff --check` reported no whitespace errors.
- V2 preparation completed from the official archives.
- A second checkpoint-reuse build reproduced the same manifest hash.
- `scripts/validate_dataset.py` passed with 1,780 examples and the counts shown above.
- The remote VQAv2 build process completed; no dataset-builder process remained afterward.
- The commit was pushed to `origin/main` as `d5298c5`.

## Limitations And Risks

- V2 contains 360 rather than exactly 300 examples in every capability because the 60 MME color questions are retained alongside 300 VQAv2 color questions.
- The VQAv2 slice measures color recognition, not every kind of visual attribute.
- Exact short-text scoring is not the full official VQAv2 soft-consensus metric. The 9-of-10 filter reduces ambiguity but does not make the scorer official.
- Existing V1 test outcomes are already known and cannot become statistically untouched by relabeling them.
- No V2 baseline or V2 block sweep was run in this commit.
- A block selected by an identity intervention is only a candidate for physical removal; deployable speedup still requires physical pruning and repeated latency measurement.

## Next Step

Run the unmodified model and all 32 one-block interventions on V2 development only. Freeze candidate configurations from that result, then evaluate those fixed configurations on V2 test.
