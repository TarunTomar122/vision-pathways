# Generate the final static research report

## Intended commit subject

`Generate final research report`

## Problem and decision

The project has many completed phases, including meaningful negative results,
but its evidence is distributed across compact JSON summaries, Markdown notes,
and plots. The requested final webpage must include the whole experimental
record without manually copying partial values while the robust search is still
running. Generate a static report only after frozen-route analysis completes.

## Changed files and behavior

- `scripts/generate_research_report.py` reads committed compact summaries and
  final robust analysis, then writes a self-contained report to
  `results/robust-route-search-qwen25-vl-3b/site/index.html`.
- The page covers the research question, model baseline, single-block screen,
  non-additivity, feature repair, interaction-aware search, sealed external
  evaluation, robust matched-K controls, literature constraints, and explicit
  evidence boundaries.
- `scripts/supervise_robust_route_search.py` now waits for the generated report
  rather than stopping immediately after analysis, and launches this generator
  only after analysis exists.
- `README.md` documents manual report generation.

## Alternatives considered

- Hand-author a report now. Rejected because final robust metrics do not exist
  yet and would invite stale or partial claims.
- Omit failures for a shorter presentation. Rejected because the negative
  evidence determines the credible research conclusion.
- Create a separate dashboard application. Rejected because a standalone static
  artifact is reproducible, versionable, and sufficient for this research log.

## Verification evidence

- `python3 -m py_compile scripts/generate_research_report.py
  scripts/supervise_robust_route_search.py`
- A render smoke test injects a minimal frozen robust-analysis structure while
  reading every existing compact result artifact, and verifies that the report
  contains the source-balanced and K8 capability sections.
- The generator requires the frozen robust analysis artifact, so it cannot
  render a final page from an unfinished route search.
- The supervisor continues to prevent duplicate workers and only invokes the
  report after controls and analysis are complete.

## Limitations and unsupported claims

- The generated report does not create new evidence. It renders the source
  summaries and preserves their exploratory, method-selection, and external
  evidence boundaries.
- The report is static and is not a deployed public website.
- Raw predictions and benchmark images remain intentionally outside Git.

## Next action enabled

Allow the active supervisor to generate a complete local report once the route
search and controls are done, then inspect, commit, and push the final compact
artifacts and report.
