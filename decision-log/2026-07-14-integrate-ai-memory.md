# Decision: Integrate ai-memory routing for cross-session continuity

- Date: 2026-07-14
- Intended commit subject: `Integrate ai-memory project routing`
- Status: Accepted

## Problem And Decision

The project now spans long-running GPU jobs, multiple experiment phases, remote-host state, and
methodological decisions that are expensive to reconstruct in a new agent session. Repository
documentation remains the canonical research record, but a local cross-session retrieval and
handoff layer can reduce context loss between Codex sessions and other supported agents.

The decision is to install ai-memory as a machine-local, loopback-only Docker service and commit
only its project-facing routing instructions, managed Agent Skills, and explicit project marker.
Provider configuration, lifecycle logs, SQLite state, and wiki storage remain outside Git.

## Files And Behavior Changed

- `AGENTS.md`
  - Adds the ai-memory-managed routing block without changing the existing decision-log rule.
  - Instructs agents to use current-project scope by default and rely on lifecycle capture for
    routine events.
- `.agents/skills/ai-memory-retrieval/SKILL.md`
  - Adds managed read-only retrieval and briefing guidance.
- `.agents/skills/ai-memory-handoff/SKILL.md`
  - Adds managed session handoff guidance.
- `.agents/skills/ai-memory-durable-pages/SKILL.md`
  - Adds managed explicit durable-page and project-rule guidance.
- `.agents/skills/ai-memory-learning-maintenance/SKILL.md`
  - Adds managed consolidation, lint, and retention guidance.
- `.agents/skills/ai-memory-routing-install/SKILL.md`
  - Adds managed installation and refresh guidance.
- `.ai-memory.toml`
  - Pins all sessions under this repository to workspace `default` and project `vlm-bench`.
  - Avoids incorrect subdirectory projects because this checkout stores Git metadata in
    `.git-data`, which normal Git root discovery does not detect without custom environment flags.
- `decision-log/2026-07-14-integrate-ai-memory.md`
  - Documents this commit.

Machine-local changes not committed here:

- Docker image `akitaonrails/ai-memory:latest`, resolved to ai-memory 1.13.0.
- Container `ai-memory`, bound to `127.0.0.1:49374`, restart policy `unless-stopped`.
- Persistent Docker volume `ai-memory-data`.
- Wrapper at `~/.local/bin/ai-memory`.
- Codex MCP entry in `~/.codex/config.toml`.
- Codex lifecycle config in `~/.codex/hooks.json`.
- Hook scripts under `~/.local/share/ai-memory/hooks/codex/`.

## Alternatives Considered

- Expose the service on the VPS network. Rejected because local Codex is the only current client;
  loopback binding avoids unnecessary authentication and network exposure.
- Manage an API-key or OAuth provider in repository files. Rejected because provider credentials
  and billing configuration are machine-local concerns. A provider was configured concurrently by
  another machine-level process during verification and was preserved rather than overwritten.
- Run ai-memory from source. Rejected in favor of the project's recommended Linux Docker path,
  which provides a published binary, persistent volume, and restart policy.
- Rely only on `repo-root` hook discovery. Rejected because this checkout uses `.git-data` rather
  than `.git`; an explicit marker is more reliable from nested working directories.
- Run full historical bootstrap without an LLM. Rejected because bootstrap summarization requires
  a configured provider. The canonical current-status document is seeded directly instead.
- Commit machine-local memory data. Rejected because sessions can contain prompts, paths, tool
  arguments, and other local context that does not belong in the public source repository.

## Verification Evidence

- Docker 29.6.1 was available and the host port 49374 was unused.
- `ai-memory --version` reported 1.13.0.
- `ai-memory status --json` reached the local server and reported the expected page/index counts.
- `curl http://127.0.0.1:49374/mcp` returned HTTP 405 for GET, confirming the MCP endpoint is
  reachable and correctly requires POST.
- Codex MCP installation preserved existing project configuration and wrote a timestamped backup.
- Codex hook installation staged 14 scripts and configured six lifecycle events with
  `repo-root` strategy.
- Managed instruction and skill installation preserved the existing decision-log instructions.
- Bootstrap dry-run collected README, six documentation files, and AGENTS.md without making an LLM
  call or writing generated pages.
- Directly seeded `docs/current_status.md` as `project/current-status.md`; FTS5 search for `pruning`
  returned that page.
- Marker resolution from the `scripts/` subdirectory returned workspace `default` and project
  `vlm-bench`.
- Container inspection reported healthy status, `unless-stopped` restart policy, loopback-only port
  binding, and persistent volume `ai-memory-data`.
- Verify Git whitespace and repository status before commit.

## Limitations, Risks, And Unsupported Claims

- Provider ownership, cost, and model quality were not audited by this repository change. A full
  historical bootstrap was intentionally not run.
- Codex does not expose a reliable true session-end hook. Run `ai-memory finalize-session` when a
  final summary and handoff are required.
- A newly installed Codex hook set requires trust review on the next Codex start.
- Memory state is local to this VPS and is not automatically shared with the remote GPU host.
- Lifecycle capture may include sensitive prompt or tool context. The service is loopback-only, but
  backups and future network exposure require deliberate security review.
- The committed skills are maintained by the external ai-memory project and should be refreshed
  together with the managed AGENTS.md block after upgrades.
- This integration does not replace repository documentation, decision logs, experiment artifacts,
  or Git history as the authoritative research record.

## Next Action Enabled

Restart Codex, review and trust the installed hooks, and use normal project sessions. Query the
seeded status through MCP or `ai-memory search`; run `ai-memory finalize-session` when explicitly
closing a Codex work session. Audit the machine-local provider configuration before enabling a full
historical bootstrap or relying on paid consolidation.
