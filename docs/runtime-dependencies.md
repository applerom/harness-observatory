# Runtime Dependencies

> Status: living note for local-first harness-observatory development.
> Purpose: record tool dependencies that affect AgentRunner behavior.

This project studies agent harnesses, so local harness CLIs are not invisible
developer conveniences. They are runtime dependencies of the product.

## Current Local Baseline

Checked on 2026-04-26:

| Dependency | Current local version | Why it matters |
|---|---:|---|
| Python | 3.14.4 | Project runtime and validation target. |
| Codex CLI (`@openai/codex`) | 0.125.0 | `CodexRunner` uses `codex exec`; `gpt-5.5` no-op prompt succeeds on this version. |
| APScheduler | 3.11.2 | In-process schedule registration for v0.3b. 4.0.0a6 exists but is pre-release, so the project pins latest stable 3.x. |

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
