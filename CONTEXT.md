# Harness Observatory — Current Context

> **Last update:** 2026-05-01 — post-v1.2 feedback-hardening wording + Codex subagent mandate clarified
>
> This file is the compact handoff for the current project state. Shipped truth
> lives in git; durable teaching lessons live in `docs/lessons/`; in-flight
> spirit-lead observations live in `EVOLUTION.md` (not part of the standard
> reading order).

---

## 1. Current Product State

Harness Observatory is a working post-v1.2 local-first application for comparing
AI coding harnesses and teaching agent-operation practice.

Implemented surfaces and services include:

- Markdown import from the legacy research corpus into SQLite.
- Dashboard, harness/topic dossiers, comparison matrix, curation queue, Insight
  Library, Job Dashboard, Live Agent Studio, lens scoring, and generated exports.
- AgentJob infrastructure with `CodexRunner` and `ClaudeRunner`, raw logs,
  semantic runtime traces, parser persistence, guarded scheduler registration,
  deterministic abstract/verification/engagement/explain services, and visible
  confidence/status labels.
- Feedback-hardening improvements for dense matrix scanning, curation action
  reversibility, status views, and shared Markdown-ish payload rendering.

The project is not being optimized for a polished enterprise release. It is a
dogfooding/teaching product: fast implementation, fast feedback, visible mistakes,
and durable lessons.

## 2. Active Operating Model

Human owns intent, taste, and acceptance. Codex is the day-to-day execution lead
and should use bounded subagents when that speeds delivery, protects lead
context, or teaches the project how to route real work better.
Spirit-lead review remains possible when human explicitly asks for a constitutional
pass.

The old heavy continuity model has been replaced with a lean model:

- `WORKLOG.md` is only a short current runway.
- In-session detail lives in the Codex plan/subagent tools.
- Product/architecture changes still go through PRD + WHY graph before or with
  code.
- Reusable lessons graduate from `EVOLUTION.md` into `docs/lessons/` (or
  `SPIRIT.md` / `AGENTS.md` / module contract headers if the rule belongs
  there). `EVOLUTION.md` is allowed to stay short and is a spirit-lead surface,
  not required reading.
- Fast feedback slices may use Spark workers with strict read budgets and narrow
  write scopes.

## 3. Reading Order

Canonical reading order lives in `AGENTS.md` so every lead agent and subagent
sees one boot authority. This file only adds current-state handoff details after
that boot sequence.

For tiny delegated implementation workers, do not copy the full lead-agent
reading order. Give the worker a small context packet, exact files, acceptance
criteria, and a read budget. Use `docs/codex-subagent-profile.md` for the current
Codex delegation contract.

## 4. Repository Layout

```text
harness-observatory/
├── AGENTS.md                  agent operating rules
├── SPIRIT.md                  project constitution
├── CONTEXT.md                 compact current handoff
├── WORKLOG.md                 lightweight current runway
├── EVOLUTION.md               in-flight spirit-lead observations (not required reading)
├── alembic.ini                Alembic entrypoint kept at root by convention
├── data/                      local SQLite data directory; ignored except .gitkeep
├── docs/                      PRD, WHY graph, lessons, runtime notes
├── generated-docs/            generated artifacts; ignored
├── live-sessions/             product runner raw logs and semantic JSONL traces; ignored
├── migrations/                Alembic migrations
├── scripts/                   validators and local scripts
├── src/observatory/           application code
└── tests/                     unit, route, service, and Playwright visual tests
```

Local dev-server stdout/stderr logs belong in `.logs/` and are gitignored. The
default SQLite database is `data/observatory.sqlite`; an old ignored
`observatory.sqlite` may exist in the repo root until no local process holds it.

## 5. Locked Decisions

- Insight is primary; EvidenceItem is proof underneath. UI copy says "Show the
  proof", not "Show the code".
- Agent fallibility is visible and labelled. Do not hide bad or uncertain output;
  model it with status/confidence/revisions.
- Target and runner are separate concepts. A target is what the job studies; a
  runner is the agent implementation doing the work.
- AgentRunner concrete CLI invocations live only inside runner modules.
- Scheduler startup is guarded; local/test startup must not accidentally spend
  model calls.
- Use Playwright visual checks for UI changes that affect layout or interaction.
- Keep `alembic.ini` at repo root unless there is a stronger reason than tidiness;
  the standard `uv run alembic upgrade head` command is valuable for students and
  agents.

## 6. Current Next Steps

1. Continue feedback-hardening from real lecturer/student use; each item should
   produce visible evidence (Playwright screenshot or test) and a short
   commit-message rationale.
2. Run the focused structure audit (`STRUCTURE-AUDIT` in `WORKLOG.md`) before
   the next larger feature wave. Audit reports pain, then PRD/WHY captures any
   intent change, then code follows. Do not refactor without that loop.
3. After a feedback or audit slice ships, briefly check whether any new rule it
   produced should graduate from `EVOLUTION.md` into `docs/lessons/`,
   `SPIRIT.md`, `AGENTS.md`, or a module contract header — and prune the
   EVOLUTION entry once the rule lives canonically elsewhere.
4. Validate every slice with pytest, ruff, mypy, and the WHY anchor checker.

## 7. Known Gaps

- `Feature Radar` remains a product gap from the larger PRD, intentionally
  deferred until feedback says it matters.
- Engagement copy is currently template-generated, not agent-authored.
- Operational hardening such as SQLite retry behavior, SSE disconnect cleanup,
  and larger-scale performance should be driven by observed pain.
- Long-haul autonomous orchestration remains far-future; current Codex Pro
  development does not justify heavy orchestration machinery.

## 8. Things The Next Agent Should Not Do

- Do not recreate old bootstrap planning files.
- Do not turn WORKLOG back into a large historical ledger.
- Do not move `alembic.ini` merely for a cleaner root if that makes common Alembic
  commands less obvious.
- Do not put dev logs or local SQLite files in the repo root as the default.
- Do not implement product features without updating PRD/WHY when scope or intent
  changes.
