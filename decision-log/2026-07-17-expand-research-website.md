# Expand Research Website

## Intended Commit Subject

`Expand research website`

## Problem Or Decision

The monochrome website had the correct visual tone but read as a short results summary. It did not provide enough context for a new reader to understand the research question, model choice, dataset composition, intervention, experimental process, baselines, full result hierarchy, or claim limitations.

## Files And Behavior Changed

- Expanded `docs/index.html` into a complete research explainer with an abstract, contents list, research questions, architecture flow, model table, capability dataset table, split definitions, identity-skip definition, matched baselines, evolutionary-search settings, seven-step experimental process, full results table, transfer analysis, efficiency accounting, lessons, limitations, future work, and reproducibility links.
- Added the Qwen budget and route-stability figures so the website now presents all seven publication figures.
- Extended `docs/styles.css` with paper-native components for factual summaries, tables, definitions, process steps, notes, and mobile overflow handling while preserving the monochrome light design.
- Retained the required evidence boundaries and avoided en dash and em dash punctuation in the README and website.

## Alternatives Considered

- Link readers directly to the manuscript and keep the website short. This was rejected because the site should explain the project without requiring repository navigation.
- Add collapsible cards for every section. This was rejected because hidden content and card-heavy layouts conflict with the requested paper-like presentation.
- Copy the full manuscript verbatim. This was rejected because the website should remain a readable research explainer rather than duplicate a PDF article.

## Verification Evidence

- `make PYTHON=/tmp/vlm-paper-venv/bin/python submission`
- `git --git-dir=.git-data --work-tree=. diff --check`
- A Unicode punctuation scan of `README.md` and `docs/` returned no en dash or em dash matches.
- Rendered and visually inspected the expanded page in Chromium at 1440 x 2400 and 390 x 2400.
- Confirmed that every website figure references a generated asset under `docs/assets/`.

## Known Limitations And Unsupported Claims

- The page summarizes the frozen study but does not replace the full manuscript or protocols.
- Tables scroll horizontally on narrow screens rather than collapsing columns and losing context.
- The site does not claim a universal capability router, edge-device performance, physical checkpoint compression, or causal localization of capabilities to named blocks.
- This documentation change does not alter experimental results.

## Next Action Enabled

Publish the expanded site through GitHub Pages and use it as the public entry point for the paper, code, protocols, and frozen evidence.
