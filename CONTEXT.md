# Harness Observatory — Current Context

> **Last update:** 2026-04-30 — post-v1.1 process cleanup and root artifact cleanup
>
> This file is the compact handoff for the current project state. Historical
> trajectory and process lessons live in `EVOLUTION.md`; shipped truth lives in
> git.

---

## 1. Current Product State

Harness Observatory is a working v1.1+ local-first application for comparing AI
coding harnesses and teaching agent-operation practice.

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

Roman owns intent, taste, and acceptance. Codex is the day-to-day execution lead
and may use bounded subagents when that speeds delivery or protects lead context.
Spirit-lead review remains possible when Roman explicitly asks for a constitutional
pass.

The old heavy continuity model has been replaced with a lean model:

- `WORKLOG.md` is only a short current runway.
- In-session detail lives in the Codex plan/subagent tools.
- Product/architecture changes still go through PRD + WHY graph before or with
  code.
- Reusable process lessons go into `EVOLUTION.md`.
- Fast feedback slices may use Spark workers with strict read budgets and narrow
  write scopes.

## 3. Reading Order For A New Agent

1. `SPIRIT.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/why-graph.xml`
5. `docs/why-graph-principles.md`
6. `docs/why-contracts-v1.md`
7. `CONTEXT.md`
8. `WORKLOG.md`
9. `EVOLUTION.md`
10. `docs/codex-subagent-profile.md` before dispatching Codex subagents

For tiny delegated implementation workers, do not copy this full reading order.
Give the worker a small context packet, exact files, acceptance criteria, and a
read budget.

## 4. Repository Layout

```text
harness-observatory/
├── AGENTS.md                  agent operating rules
├── SPIRIT.md                  project constitution
├── CONTEXT.md                 compact current handoff
├── WORKLOG.md                 lightweight current runway
├── EVOLUTION.md               teaching-facing trajectory and lessons
├── alembic.ini                Alembic entrypoint kept at root by convention
├── data/                      local SQLite data directory; ignored except .gitkeep
├── docs/                      PRD, WHY graph, lessons, runtime notes
├── generated-docs/            generated artifacts; ignored
├── live-sessions/             product runner raw logs and semantic JSONL traces; ignored
├── media/                     local media attachments; ignored
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

1. Finish the 2026-04-30 cleanup: stale docs, root artifacts, runtime paths, and
   lean continuity model.
2. Validate with pytest, ruff, mypy, and the WHY anchor checker.
3. Continue feedback-hardening from real use.
4. Do a focused structure audit before the next larger feature wave; promote any
   real refactor into PRD/WHY first.

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
