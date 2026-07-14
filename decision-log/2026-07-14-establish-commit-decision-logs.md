# Decision: Require a detailed Markdown decision log in every agent-created commit

- Date: 2026-07-14
- Intended commit subject: `Require decision logs for agent commits`
- Status: Accepted

## Context

The repository has accumulated model runs, benchmark revisions, scoring corrections, and experimental interpretations across multiple commits. Git provides exact diffs, but a diff does not explain why a threshold was selected, which evidence was considered exploratory, what failed during execution, or which scientific claims remain unsupported.

The user requested a changeset-like Markdown record for every future commit with substantially more detail than a normal commit message.

## Decision

Every commit created by an agent must include one new Markdown entry in `decision-log/`. The entry is written before committing and travels in the same commit as the implementation it explains.

Each entry must document context, decision, exact changes, alternatives, verification, limitations, and the enabled next step. An intended commit subject identifies the commit without requiring its not-yet-known hash.

## Changes

- Added `AGENTS.md` with an explicit repository-level rule forbidding undocumented agent commits.
- Added `decision-log/README.md` with naming and content requirements.
- Added a retrospective entry for commit `d5298c5`, including dataset counts, manifest hash, failures encountered, interpretation boundaries, and the next experiment.
- Added this entry so the policy-establishment commit follows its own policy.

## Alternatives Considered

- Expand commit messages only. Rejected because long commit messages are harder to browse, link, and evolve as project documentation.
- Maintain one append-only changelog. Rejected because merge conflicts and unclear commit-to-entry mapping become more likely.
- Name entries with commit hashes. Rejected as the primary convention because the hash does not exist until after the file has been committed, creating an unnecessary follow-up commit or amend cycle.
- Document only experimental commits. Rejected because infrastructure and scoring changes can materially alter scientific results.

## Verification

- Confirmed the worktree was clean before creating the policy files.
- Confirmed the latest relevant commit was `d5298c5`.
- Checked all added Markdown files for readable structure and explicit scientific limitations.
- `git diff --check` passed before this commit was created.

## Limitations And Risks

- This policy governs commits created after it is introduced. Earlier history is not yet fully backfilled.
- A detailed entry can still contain an incorrect interpretation; raw artifacts and executable verification remain authoritative.
- The policy depends on contributors and agents following `AGENTS.md`; no automated CI check is added in this commit.

## Next Step

For every subsequent commit, create its decision-log entry before staging. Add a CI check later if undocumented commits become a recurring problem.
