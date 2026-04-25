# harness-observatory

A local-first application that puts AI agents to work comparing AI coding CLI tools — and teaches
developers how to work with agents by letting them watch (and question) the process live. Built
by agents, about agents, for developers who are skeptical of agents but ready to look at the
evidence themselves.

**Status: Pre-v0.1 — foundational docs only, code not yet started.**

---

## What this is

- **A live comparison surface** — database-backed matrix of AI coding CLI harnesses (OpenCode,
  Codex CLI, Gemini CLI, Claude Code, Qwen-Code, Copilot Chat, Cline, and more), refreshed by
  agents on a schedule, not curated by hand
- **An honest agent classroom** — agents make mistakes here, and those mistakes are visible and
  labeled, not hidden; confidence states (`proposed`, `corroborated`, `disputed`, `human-verified`)
  replace editorial curation
- **A live discovery tool** — during lectures or pairing sessions, send an agent into a real
  upstream repo and watch it find something nobody documented yet; stake your name on the finding
- **A dogfooding example** — the application itself is built by agents under human oversight,
  following the [agent1st protocol](https://github.com/applerom/agent1st); the repo is a
  starter template for research tools built this way

## What this is NOT

- **Not a code-reading tutorial.** If you want to read harness source with `file:line` citations,
  see the sibling project [`../harness-architecture/`](../harness-architecture/) — that is the
  markdown meta-repo this application will eventually supersede as the canonical research surface.
- **Not a SaaS.** Local-first, single-user, SQLite-backed. You run it on your laptop. No accounts,
  no cloud sync, no subscription.
- **Not a "look how great AI is" demo.** The pedagogical premise is the opposite: show agents
  failing, disagreeing, correcting themselves — and teach developers to work productively in that
  environment rather than flinching from it.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.12 | Readable, mainstream, forkable |
| Package manager | `uv` | Fast, modern, replaces pip/virtualenv |
| Web framework | FastAPI | Async, typed, popular |
| Database | SQLite (via SQLModel) | Zero-config, single-file, local-first |
| Frontend | HTMX + Tailwind | Server-driven HTML, no SPA complexity |
| Agent dispatch | `claude -p` subprocess (v1) | Works with Claude Pro; runner-agnostic interface |
| Task queue | APScheduler (v1) | Lightweight cron for refresh jobs |

All decisions are explained in `docs/why-graph.xml` with intent-to-implementation traceability.
If you see something and wonder "why not X instead?" — the WHY graph probably has the answer.

---

## For agents starting work

Read in this order before touching anything:

1. `SPIRIT.md` — project constitution (mission, pedagogy, anti-patterns). In Russian (owner's
   native language), English headers. Read it first; it governs everything else.
2. `AGENTS.md` — agent1st protocol (operating rules for all agents on this project)
3. `docs/PRD.md` — product truth: what we build, version scope, acceptance criteria
4. `docs/why-graph.xml` — intent-to-implementation map; pin this during your session
5. `CONTEXT.md` — current handoff state: where we are, what was just done, what is blocked

After reading all five, output: `Observatory Agent1st ON`

If `CONTEXT.md` or `docs/PRD.md` do not exist yet when you read this, that is your first
blocker — escalate before assuming.

---

## For humans contributing

Contribution guide is TBD — will be written after v0.1 ships with working code. Until then:

- The project is in the foundational-docs phase; the right entry point is `docs/PRD.md` (once
  it exists) and `SPIRIT.md` (now)
- All architectural decisions go through the WHY graph before code is written
- If you want to understand the agent1st protocol that governs how this is built:
  [https://github.com/applerom/agent1st](https://github.com/applerom/agent1st)

---

## Related projects

- [`../harness-architecture/`](../harness-architecture/) — the markdown meta-repo: cross-harness
  analysis, `file:line` citations, teaching lessons. Currently the canonical research artifact;
  will become legacy/migration-input as harness-observatory matures.
- [agent1st protocol](https://github.com/applerom/agent1st) — the operating protocol used to
  build this project and embedded in `AGENTS.md`

---

## License

TBD — will be set before v0.1 public release.
