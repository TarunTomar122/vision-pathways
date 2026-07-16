# Isolate K4 Prior Artifacts

## Intended Commit Subject

`Isolate SmolVLM2 K4 route priors`

## Problem And Decision

The K4 and stopped K6 protocols use the same one-block predictions but require different
budget-specific candidate-route registries. Rebuilding priors in the shared ablation directory
would overwrite the K6 `routes.json` file. Write K4 sensitivity and route priors to a dedicated
directory instead.

## Files And Behavior Changed

- The K4 protocol references `results/smolvlm2-2b-k4-priors` for both sensitivity and routes.
- The supervisor reads and writes K4 priors in that directory while continuing to read the completed
  one-block ablation predictions from `results/smolvlm2-2b-single-block`.

## Alternatives Considered

- Reusing the shared K6 prior directory was rejected because it mutates a recorded K6 input after
  partial route inference.
- Repeating the 27 one-block sweep was rejected because the predictions are budget-independent and
  already complete.

## Verification Evidence

- `build_single_block_priors.py` writes its budget-specific `routes.json` to the requested output
  directory and reads all intervention predictions from the separate ablation directory.
- No K4 route inference had started before the isolated path was introduced.

## Limitations And Non-Claims

- K4 and K6 priors share the same one-block measurements; they are not independent data samples.
- This preserves files but does not convert partial K6 diagnostics into completed evidence.

## Next Action Enabled

Generate K4-only priors from the completed sweep, then launch the frozen K4 route search.
