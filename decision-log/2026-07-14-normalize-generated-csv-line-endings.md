# Decision: Normalize generated CSV artifacts to LF line endings

- Date: 2026-07-14
- Intended commit subject: `Normalize generated CSV line endings`
- Status: Accepted

## Context

Commit `fa91be9` added two generated CSV artifacts. Python's `csv.DictWriter` defaults to the `excel` dialect, whose line terminator is CRLF. Git's staged whitespace check therefore reported every CSV row as trailing whitespace.

The pre-staging `git diff --check` did not inspect untracked result files. The later staged check found the problem, but the shell command used newline-separated commands rather than an `&&` guard, so the commit and push continued despite the nonzero check result.

The data values and experimental conclusions were unaffected. This is a repository-formatting and verification-control defect.

## Decision

Set `lineterminator="\n"` explicitly in every CSV writer involved in this experiment and normalize the two committed CSV artifacts to LF. Do not amend the already published commit; preserve history with a separate documented correction.

## Changes

- `scripts/analyze_task_routes.py`
  - Generates `route_metrics.csv` with LF endings.
- `scripts/run_layer_ablation.py`
  - Generates `heatmap.csv` with LF endings.
- `results/task-route-analysis-qwen25-vl-3b/route_metrics.csv`
  - Normalized existing CRLF endings to LF without changing data.
- `results/color-capability-qwen25-vl-3b/heatmap.csv`
  - Normalized existing CRLF endings to LF without changing data.

## Alternatives Considered

- Ignore the warnings because CSV commonly uses CRLF. Rejected because repository checks treat carriage returns as trailing whitespace and future generated diffs would repeat the problem.
- Amend and force-push `fa91be9`. Rejected because the commit was already pushed and repository rules prohibit amending without explicit user direction.
- Configure Git to suppress the warning. Rejected because explicit LF generation is simpler and consistent with the rest of the repository.

## Verification

- Python compilation passed for both modified scripts.
- Each normalized CSV matched the version in `fa91be9` after removing carriage returns from that committed version, proving that field values and row ordering are unchanged.
- `git diff --check` passed after normalization.
- `git diff --cached --check` passed before this corrective commit.
- The commit command was guarded by `&&` so it could not run if the staged check failed.

## Limitations And Risks

- This correction does not change any model predictions, metrics, statistical intervals, or conclusions.
- Other CSV writers outside the touched experiment were not audited unless they appeared in the current result-generation path.

## Next Step

Use guarded commit command chains for future agent commits and continue research from the interaction-aware four-block route-search result.
