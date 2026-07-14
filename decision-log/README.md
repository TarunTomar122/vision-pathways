# Decision Log

This directory is the permanent, human-readable history of why the project changed. Git records what changed; these files record the reasoning, evidence, constraints, and remaining uncertainty behind each agent-created commit.

## One Entry Per Commit

Every agent-created commit must add one Markdown file named:

```text
YYYY-MM-DD-short-description.md
```

The filename describes the decision, not merely the edited file. If multiple commits are created on one day, use distinct descriptions.

## Required Structure

```markdown
# Decision: Short title

- Date: YYYY-MM-DD
- Intended commit subject: `Imperative commit subject`
- Status: Accepted

## Context

What problem existed, what was known, and why a change was necessary.

## Decision

The chosen behavior or project direction in precise terms.

## Changes

Every material file, interface, dataset, experiment, or behavior changed.

## Alternatives Considered

Other reasonable choices and why they were rejected or deferred.

## Verification

Commands, tests, dataset hashes, measurements, and observed outputs.

## Limitations And Risks

What remains uncertain and what must not be inferred from this change.

## Next Step

The concrete action this decision enables.
```

## Interpretation

A decision log is not evidence that an experiment succeeded. Experimental claims still require saved predictions, reproducible configurations, held-out evaluation, and appropriate uncertainty estimates.
