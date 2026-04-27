# Runtime Dependencies

> Status: living note for local-first harness-observatory development.
> Purpose: record tool dependencies that affect AgentRunner behavior.

This project studies agent harnesses, so local harness CLIs are not invisible
developer conveniences. They are runtime dependencies of the product.

## Current Local Baseline

Checked on 2026-04-27:

| Dependency | Current local version | Why it matters |
|---|---:|---|
| Python | 3.14.4 | Project runtime and validation target. |
| Codex CLI (`@openai/codex`) | 0.125.0 | `CodexRunner` uses `codex exec`; `gpt-5.5` no-op prompt succeeds on this version. |
| Claude Code CLI (`claude`) | 2.1.119 | `ClaudeRunner` uses `claude -p`; Job #9 completed through this runner against the Claude Code target on 2026-04-27. |
| APScheduler | 3.11.2 | In-process schedule registration for v0.3b. 4.0.0a6 exists but is pre-release, so the project pins latest stable 3.x. |

## Empirical Runner Notes

- **2026-04-27 — ClaudeRunner:** `RefreshJobService(ClaudeRunner)` ran Job #9 against target `claude-code`. Target cwd preflight repaired stale imported path `d:/ai/claude-code-architecture/` to `D:/ai/harnesses/claude-code-architecture`. Claude preflight resolved `C:\Users\Intel\.local\bin\claude.exe` and returned `2.1.119 (Claude Code)`. Runner status was `done`; raw log is `live-sessions/agent-job-00009.log`; parser produced Insight #37 and EvidenceItems #80-#82 after v1.1 plain-path parser hardening.

## Rule

Before broadening refresh jobs to more harnesses:

- check that the target path exists;
- check that the runner executable resolves to a runnable command;
- check the runner CLI version when model support depends on it;
- fail the `AgentJob` with a semantic event and raw-log evidence when preflight
  fails.

Fallback models are acceptable as an emergency continuation tactic, but they
should not become silent permanent state. If the better fix is upgrading a local
runtime dependency, record that decision and add a preflight check.
