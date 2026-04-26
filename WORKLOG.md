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

**Last update:** 2026-04-26 — v0.1 Task D integrated
**Active session lead:** Codex GPT-5.5-class (interactive)
**Current phase:** v0.1 implementation — first-wave docs alignment and subagent dispatch in progress

---

## 1. Current state (1-3 sentences)

Foundational docs landed and aligned through six commits through `0cbf888` (cross-harness lead delegation), then pushed to the public GitHub repo with `main` as a squash snapshot and `development` as the working branch with full history. Manual interrupt-and-resume runbook is in place, Roman has granted standing project authorization for harness-local subagents, and on 2026-04-26 explicitly gave this Codex session the v0.1 implementation start signal plus permission to use Codex subagents as the lead agent sees fit.

## 2. Active items

| ID | Brief | Runner | Status | Started | Last update |
|---|---|---|---|---|---|
| A | Data model + Alembic migrations (`DELEGATION-PLAN` Task A). Codex subagent Noether `019dc91c-4ca3-7a30-b449-1c5df03f23d1`; owns `src/observatory/models/**`, `src/observatory/db.py`, `migrations/**`, `alembic.ini`, `tests/models/**`. | Codex implementation_worker | completed | 2026-04-26 | integrated with pytest/ruff/mypy/Alembic green |
| B | FastAPI app skeleton + Jinja/HTMX layout (`DELEGATION-PLAN` Task B). Codex subagent Epicurus `019dc91c-4d2c-7a83-9a9b-ad2af323e1e7`; owns `pyproject.toml`, `src/observatory/web/**`, `tests/web/**`, needed package init files. | Codex implementation_worker | completed | 2026-04-26 | integrated with pytest/ruff/mypy green |
| C-SCOUT | Read-only importer source-shape scout for `../harness-architecture`. Codex subagent Einstein `019dc91c-4d9b-7533-b6a9-70d187e93ef5`; no writes. | Codex repo_explorer | completed | 2026-04-26 | found 13 topic folders, 8 harness rows, 1 agent-tool row; `teaching.md` missing for 2 topics; importer should treat teaching as optional |
| C | Markdown importer (`DELEGATION-PLAN` Task C). Codex subagent Nash `019dc924-ce93-7ca2-b5e3-280b5977b587`; owns `src/observatory/importers/**`, `tests/importers/**`. | Codex hard_worker | completed | 2026-04-26 | integrated; real-source import produced 8 harnesses, 13 topics, 1 agent-tool, 72 evidence items, 34 insights, 76 comparison cells |
| E | AgentRunner Protocol + stub `ClaudeRunner` + anchor validator (`DELEGATION-PLAN` Task E). Codex subagent Hooke `019dc925-2b72-7390-8393-9bf278efd12c`; owns `src/observatory/runners/**`, `scripts/validate_anchors.py`, `tests/runners/**`, `tests/scripts/**`. | Codex implementation_worker | completed | 2026-04-26 | integrated with runner tests, mypy, ruff, anchor validator, and forbidden-literal check green |
| D | Read-only dossier + matrix routes (`DELEGATION-PLAN` Task D). Codex subagent Pascal `019dc92c-e752-7011-b201-2e5a86625949`; owns web route/template/test integration. | Codex implementation_worker | completed | 2026-04-26 | integrated; real DB smoke and full validation green |

## 3. Next ordered queue

When Roman gives the implementation start signal, the v0.1 first wave dispatches. Decomposition lives in `DELEGATION-PLAN.md §3`; condensed here:

| ID | Brief | Runner | Status | Blocked by |
|---|---|---|---|---|
| FINAL-V0.1 | Start local dev server and hand owner the URL for hands-on testing | Codex lead | pending | D committed |

A, B, C dispatch in parallel. D dispatches when A+B+C return green. E dispatches when A returns green. See `DELEGATION-PLAN.md §5` for the sequencing diagram.

## 4. Blocked / waiting

- **Future orchestrator (PRD §27)** — deferred to far horizon per owner direction 2026-04-25. Manual interrupt-and-resume runbook is the v0 substitute. Reopen only if/when manual handoff proves too painful in practice.

## 5. Recent history (append-only, dated)

- **2026-04-26** — Roman gave the v0.1 implementation start signal in Codex and explicitly authorized Codex subagent use for this session as a lead-agent orchestration mechanism. Lead first action: clean up small doc drift, then dispatch the first bounded v0.1 work wave.
- **2026-04-26** — Committed `2f0da69`: small v0.1 start alignment docs update. Fixed PRD §27 stale sequencing wording, DELEGATION Task dependency/count wording, README WHY graph overstatement, and recorded Codex session-level subagent authorization.
- **2026-04-26** — Dispatched Codex first wave: Task A to Noether (`019dc91c-4ca3-7a30-b449-1c5df03f23d1`), Task B to Epicurus (`019dc91c-4d2c-7a83-9a9b-ad2af323e1e7`), importer read-only scout to Einstein (`019dc91c-4d9b-7533-b6a9-70d187e93ef5`). Next lead action: wait for the scout or one implementation slice, then dispatch Task C/E as dependencies clear.
- **2026-04-26** — Importer scout Einstein completed. Key evidence: `../harness-architecture/topics` has 13 folders; 11 include `teaching.md`, while `hooks-and-events` and `runtime-context` do not; `registry/harnesses.md` has 8 harness rows plus separate MiniMax CLI agent-tool row; `comparisons/` has 13 root essays plus 10 investigations. Importer strategy: minimal useful ingest, optional teaching files, raw markdown preservation, `import-ambiguous.log` for unclear rows.
- **2026-04-26** — Integrated first code wave from Noether/Epicurus. Added SQLModel schema, SQLite/Alembic setup, FastAPI app factory, dashboard route/templates/static, and tests. Lead fixed one mypy test assertion and marked `MOD-MODELS`, `MOD-WEB-APP`, `MOD-WEB-ROUTES-DASHBOARD`, and `FEAT-DASHBOARD` as STARTED in WHY graph. Validation used `UV_PROJECT_ENVIRONMENT=%TEMP%\harness-observatory-v01-venv`: `uv run pytest` 4 passed, `uv run ruff check src/ tests/` passed, `uv run mypy src/observatory tests` passed, `uv run alembic upgrade head` passed.
- **2026-04-26** — Committed `73cb252`: first v0.1 code slice from Task A/B. Then dispatched Task C importer to Nash (`019dc924-ce93-7ca2-b5e3-280b5977b587`) and Task E runner/validator to Hooke (`019dc925-2b72-7390-8393-9bf278efd12c`). Next lead action: integrate whichever returns first; after C is green, dispatch Task D read-only dossiers/matrix.
- **2026-04-26** — Integrated Task E from Hooke. Added `AgentRunner` Protocol DTOs, v0.1 `ClaudeRunner` stub, `scripts/validate_anchors.py`, runner tests, and validator tests. Marked `MOD-RUNNER-BASE` STARTED in WHY graph. Validation: runner mypy passed, `pytest tests/runners tests/scripts` passed, `python scripts/validate_anchors.py` passed, runner/validator ruff passed, forbidden subprocess literal absent from `src/` and `scripts/`.
- **2026-04-26** — Integrated Task C from Nash. Added minimal canon importer, markdown pipe-table parser, importer tests, and marked `FEAT-MARKDOWN-IMPORT` / `MOD-IMPORTER` STARTED in WHY graph. Real-source import against `D:/ai/harnesses/harness-architecture` produced 8 harnesses, 13 topics, 1 ecosystem object, 72 evidence items, 34 insights, and 76 comparison cells; no ambiguity log was needed. Known v0.1 compromise: `harness-map.md` only covers 6 harness columns, so comparison coverage is useful but not full 8-harness matrix until later importer/view refinements.
- **2026-04-26** — Committed `94819a6`: Task C importer. Closed completed Nash/Hooke subagent threads and dispatched Task D read-only routes to Pascal (`019dc92c-e752-7011-b201-2e5a86625949`). Next lead action: integrate D, run full v0.1 validation, then start the local dev server for owner testing.
- **2026-04-26** — Integrated Task D from Pascal. Added read-only harness/topic/matrix routes, evidence-rich shared rendering, real dashboard counts, and route tests. Marked comparison matrix, harness dossier, topic dossier, evidence-rich view, and their route modules STARTED in WHY graph. Validation with imported real DB: `uv run pytest` 21 passed, `uv run ruff check src/ tests/ scripts/validate_anchors.py` passed, `uv run mypy src/observatory tests` passed, `uv run python scripts/validate_anchors.py` checked 24 anchors and skipped 0, forbidden subprocess literal absent, real route smoke returned 200 for `/`, `/harnesses`, `/harnesses/opencode`, `/topics`, `/topics/instruction-files`, `/matrix`, and `/matrix/cells/opencode/instruction-files`.
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
