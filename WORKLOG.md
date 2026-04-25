# WORKLOG — Harness Observatory

> Durable state of *current work in flight*. Read after `AGENTS.md` (specifically the
> "Interrupt-and-Resume Pattern" section). This is the single source of truth for
> "what is the lead agent doing right now; what comes next; what is blocked."
>
> **Update after every meaningful step.** Commit WORKLOG with the same change that
> triggered the update — never let it drift uncommitted across a session boundary.
>
> Distinct from `CONTEXT.md`: CONTEXT is the decision log (what was decided and why),
> WORKLOG is task state (what is happening and what comes next).

**Last update:** 2026-04-25 — interrupt-and-resume runbook landed; sequencing question closed
**Active session lead:** Claude Opus 4.7 (interactive)
**Current phase:** Pre-v0.1 — foundational docs aligned, awaiting owner go-ahead for v0.1 dispatch

---

## 1. Current state (1-3 sentences)

Foundational docs landed and aligned through three commits (`94423c3` bootstrap, `bd6ee8e` alignment pass 1 after gpt-5.5 review, `0d90bd1` alignment pass 2 after fresh-eyes review + PRD §27 long-haul concern named). Manual interrupt-and-resume runbook now in place (this file + `AGENTS.md` "Interrupt-and-Resume Pattern" section) — replaces the deferred automated orchestrator. **Awaiting owner go-ahead** to dispatch v0.1 first wave (Tasks A + B + C in parallel) per `DELEGATION-PLAN.md §3`.

## 2. Active items

| ID | Brief | Runner | Status | Started | Last update |
|---|---|---|---|---|---|
| _(none — paused awaiting owner go-ahead for v0.1 first wave)_ | | | | | |

## 3. Next ordered queue

When owner gives go-ahead, the v0.1 first wave dispatches. Decomposition lives in `DELEGATION-PLAN.md §3`; condensed here:

| ID | Brief | Runner | Status | Blocked by |
|---|---|---|---|---|
| A | Data model + Alembic migrations (`DELEGATION-PLAN` Task A) | Sonnet | pending | owner go-ahead |
| B | FastAPI app skeleton + Jinja+HTMX layout (Task B) | Sonnet | pending | owner go-ahead |
| C | Markdown importer (Task C) | Sonnet | pending | owner go-ahead |
| D | Read-only dossier + matrix routes (Task D) | Sonnet | pending | A, B, C all green |
| E | AgentRunner Protocol + stub `ClaudeRunner` + anchor validator (Task E) | Haiku | pending | A green |

A, B, C dispatch in parallel. D dispatches when A+B+C return green. E dispatches when A returns green. See `DELEGATION-PLAN.md §5` for the sequencing diagram.

## 4. Blocked / waiting

- **All v0.1 work** — blocked on owner go-ahead per `AGENTS.md` Core §1 (owner reviews lead-agent output and gives go/no-go before each major dispatch).
- **Future orchestrator (PRD §27)** — deferred to far horizon per owner direction 2026-04-25. Manual interrupt-and-resume runbook is the v0 substitute. Reopen only if/when manual handoff proves too painful in practice.

## 5. Recent history (append-only, dated)

- **2026-04-25** — Added manual interrupt-and-resume runbook: `AGENTS.md` "Interrupt-and-Resume Pattern" section + this `WORKLOG.md` durable state file. Owner direction: orchestrator deferred to far horizon; manual runbook is the v0 substitute. CONTEXT.md §6 sequencing question closed (neither (A) nor (B) — runbook instead).
- **2026-04-25** — Committed `0d90bd1`: alignment pass 2 (startup commands unified to `uv run uvicorn observatory.web.app:create_app --factory --reload` and `uv run python -m observatory.importers.canon`; ClaudeRunner stub-class wording reconciled in `DELEGATION-PLAN` Task E vs PRD §26.3; PRD §27 "Long-Haul Orchestration on Personal Subscriptions" added with 8 design constraints but no scaffolding).
- **2026-04-25** — Committed `bd6ee8e`: alignment pass 1 (8 drifts caught by gpt-5.5 review — PRD §1 framing, importer path/CLI form, validator filename, 18 stale PRD_REFs in WHY graph, AgentRun-history/QueueItem removed from DELEGATION Task A, validator skip-PLANNED policy, Documentation conventions formalized in AGENTS.md, README/SPIRIT/CONTEXT reading-order deferral to AGENTS.md).
- **2026-04-25** — Committed `94423c3`: bootstrap of foundational docs (SPIRIT, AGENTS, PRD v2, WHY graph, README, DELEGATION-PLAN, CONTEXT, CLAUDE.md, .gitignore, media+live-sessions placeholders, three verbatim agent1st reference docs — 14 files, ~3250 lines docs, 0 lines code).
- **2026-04-25** — Interview between Roman (owner) and Claude Opus 4.7 (lead) covering 6 discriminating questions: scope (orchestration-first hybrid), location (`harness-observatory/` sibling), stack (Python + uv + FastAPI + SQLite + HTMX), demo model (live agent runs with student attribution), autonomy (L1 auto-merge with confidence labels), agent abstraction (`AgentRunner` Protocol + `ClaudeRunner` v1), v0.1 slice (read-only viewer + markdown importer).

---

## How to update this file

After meaningful steps:
1. Move items between sections 2 (active) ↔ 3 (queue) ↔ 4 (blocked) as state changes.
2. Append a dated bullet to section 5.
3. Update the "Last update" header at the top.
4. Update "Active session lead" if a different agent class takes over (e.g., resume in Codex/Sonnet after Opus rate-limited).
5. Commit WORKLOG with the same change that triggered the update.

When section 5 grows past ~50 entries, archive earlier entries to `WORKLOG-history.md`.

If a previous session ended mid-action and the active item state is unclear, do **not** guess — surface to the owner per `AGENTS.md` Core §3 (Right to Disagree). The 5-minute test (a fresh agent should know what to do next within 5 minutes of reading SPIRIT → AGENTS → CONTEXT → WORKLOG) is the acceptance criterion for this file.
