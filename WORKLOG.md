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

**Last update:** 2026-04-26 — Codex subagent operating profile added
**Active session lead:** Codex GPT-5.5-class (interactive)
**Current phase:** Pre-v0.1 — foundational docs aligned; Codex subagent profile recorded; awaiting implementation start signal

---

## 1. Current state (1-3 sentences)

Foundational docs landed and aligned through six commits through `0cbf888` (cross-harness lead delegation), then pushed to the public GitHub repo with `main` as a squash snapshot and `development` as the working branch with full history. Manual interrupt-and-resume runbook is in place, Roman has granted standing project authorization for harness-local subagents, and Codex now has a project-local subagent operating profile in `docs/codex-subagent-profile.md` plus `.codex/agents/`. Implementation has not started yet.

## 2. Active items

| ID | Brief | Runner | Status | Started | Last update |
|---|---|---|---|---|---|
| _(none — ready for v0.1 implementation start)_ | | | | | |

## 3. Next ordered queue

When Roman gives the implementation start signal, the v0.1 first wave dispatches. Decomposition lives in `DELEGATION-PLAN.md §3`; condensed here:

| ID | Brief | Runner | Status | Blocked by |
|---|---|---|---|---|
| A | Data model + Alembic migrations (`DELEGATION-PLAN` Task A) | harness-local worker | pending | implementation start signal |
| B | FastAPI app skeleton + Jinja+HTMX layout (Task B) | harness-local worker | pending | implementation start signal |
| C | Markdown importer (Task C) | harness-local worker | pending | implementation start signal |
| D | Read-only dossier + matrix routes (Task D) | harness-local worker | pending | A, B, C all green |
| E | AgentRunner Protocol + stub `ClaudeRunner` + anchor validator (Task E) | harness-local small worker | pending | A green |

A, B, C dispatch in parallel. D dispatches when A+B+C return green. E dispatches when A returns green. See `DELEGATION-PLAN.md §5` for the sequencing diagram.

## 4. Blocked / waiting

- **All v0.1 implementation work** — waiting for Roman's implementation start signal.
- **Future orchestrator (PRD §27)** — deferred to far horizon per owner direction 2026-04-25. Manual interrupt-and-resume runbook is the v0 substitute. Reopen only if/when manual handoff proves too painful in practice.

## 5. Recent history (append-only, dated)

- **2026-04-26** — Codex subagent operating profile added: reviewed `docs/codex-subagents-recommendations.md` against official OpenAI docs; added `docs/codex-subagent-profile.md`, `.codex/config.toml`, and custom Codex agent profiles for `repo_explorer`, `implementation_worker`, `hard_worker`, `reviewer`, and `validator`; linked the profile from `AGENTS.md` and `DELEGATION-PLAN.md`. The scheme is an operating aid, not a source of truth above AGENTS/PRD/WHY/WORKLOG.
- **2026-04-26** — Published repository to GitHub: `main` is a single squash public snapshot (`31d627c`), `development` preserves full pre-v0.1 history through `0cbf888`, and local work continues on `development`.
- **2026-04-26** — Committed `0cbf888`: Codex GPT-5.5-class alignment pass. Verified Opus alignment pass 3 resolved the previously reported contradictions; recorded Roman's standing authorization for lead agents to use harness-local subagents; generalized `AGENTS.md` and `DELEGATION-PLAN.md` from Claude Code-specific orchestration to a cross-harness lead-agent model covering Claude Code and Codex; clarified that lead-agent sessions are serial across harnesses by default.
- **2026-04-26** — Committed `e5065c2`: alignment pass 3 caught by reviewer agent against post-runbook state. Five fixes: (1) DELEGATION Task E `NotImplementedError` message no longer contains the literal `claude -p` (was contradicting the v0.1 grep acceptance check); (2) PRD §23.8 risk mitigation now says AgentRunner Protocol exists from v0.1, concrete subprocess body from v0.2 (was saying "interface from v0.2", contradicting §26.3 acceptance); (3) WHY graph `FEAT-ENGAGEMENT-HOOKS` INTENT clarified — engagement Insights publish to DB immediately per L1 auto-merge, "human review" applies only to external publication (was reading as a DB approval gate, contradicting PRD §7.3/§11.7 + SPIRIT anti-pattern); (4) WORKLOG §1 + §5 history reflect the four prior commits explicitly; (5) SPIRIT.md "Observatory Spirit ON" hello dropped — single ritual sentinel "Observatory Agent1st ON" lives only in AGENTS.md (last reading-order file).
- **2026-04-25** — Committed `f93c387`: manual interrupt-and-resume runbook landed (`AGENTS.md` "Interrupt-and-Resume Pattern" section + `WORKLOG.md` durable state file + CONTEXT.md update closing the sequencing question). Owner direction: automated orchestrator deferred to far horizon; manual runbook is the v0 substitute. CONTEXT.md §6 sequencing question closed (neither (A) nor (B) — runbook instead).
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
