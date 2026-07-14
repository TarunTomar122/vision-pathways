# Repository Working Rules

## Decision Log Requirement

Every commit created by an agent must include a new Markdown file under `decision-log/`.

The decision-log file is part of the commit it documents. It must be written before the commit and must contain:

1. The intended commit subject.
2. The problem or decision that caused the change.
3. The exact files and behavior changed.
4. Alternatives considered and why they were not selected.
5. Commands, tests, measurements, or other evidence used for verification.
6. Known limitations, risks, and claims that the change does not support.
7. The next action enabled by the commit.

Use `decision-log/YYYY-MM-DD-short-description.md`. Do not use a commit hash as the primary identifier because the log must exist inside the commit it documents. After pushing, the commit hash may be added by a later entry when useful, but that follow-up is not required.

Do not create undocumented commits. Small documentation-only commits still require a decision-log entry.
