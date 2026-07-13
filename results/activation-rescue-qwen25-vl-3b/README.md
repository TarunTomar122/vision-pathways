# Activation Rescue Trace

## Experiment

The four-block pathway skips blocks `3, 5, 9, 28`. For every image, we first capture the normal
model's visual state after each of those blocks. We then run the pruned pathway and optionally
replace its state with the corresponding full-model state. This is a prefix-restoration trace:
restoring after block 5 restores the normal computation through block 5, not block 5 in isolation.

## Results

| Condition | Overall accuracy | Accuracy recovered from fully pruned |
|---|---:|---:|
| Fully pruned | 77.91% | 0.00 pp |
| Restore after block 3 | 78.65% | 0.74 pp |
| Restore after block 5 | 80.34% | 2.43 pp |
| Restore after block 9 | 81.49% | 3.58 pp |
| Restore after block 28 | 81.62% | 3.72 pp |
| Full baseline | 81.62% | 3.72 pp |

The final restore point exactly reproduces the baseline outputs, validating the patching mechanism.

## Capability Interpretation

| Condition | Counting | Object | OCR | Spatial |
|---|---:|---:|---:|---:|
| Fully pruned | 70.83% | 88.06% | 72.06% | 77.22% |
| Restore after 3 | 74.44% | 85.83% | 74.71% | 76.94% |
| Restore after 5 | 74.17% | 88.33% | 77.65% | 78.89% |
| Restore after 9 | 76.67% | 88.61% | 78.82% | 80.00% |
| Full baseline | 74.44% | 89.17% | 80.00% | 80.83% |

The main recovery happens by blocks 5 and 9. OCR improves from 72.06% to 77.65% after restoring
the state after block 5, then to 78.82% after block 9. Restoring after block 28 recovers the final
1.18 points. This indicates that the removed blocks participate in a cumulative visual refinement
rather than each storing one isolated capability.

The object curve is not perfectly monotonic, and small attribute changes are not interpretable
because that bucket contains only 60 examples. Recovery is evidence about where the representation
becomes sufficient, not proof that a block stores a named semantic concept.

Raw per-condition predictions remain on the GPU machine. `summary.json` contains the compact
results, and `scripts/run_activation_rescue.py` reproduces the trace.
