# EVOLUTION.md — development trajectory log

> This is the teaching-facing development trajectory log.
>
> `CONTEXT.md` records project decisions and handoff state.
> `WORKLOG.md` records current work in flight.
> `EVOLUTION.md` records lessons learned while building: agent mistakes,
> process friction, tool/version drift, and rule changes that future agents and
> students should understand.

## 2026-04-26 — Runtime Freshness And Agent Version Inertia

Observation:
- v0.1 was initially scaffolded with Python 3.12.
- That was not an owner requirement. It was likely agent/model inertia: 3.12 is a
  well-represented, familiar training-era choice, but not the newest stable
  CPython line on 2026-04-26.
- Official Python.org downloads showed Python 3.14.4 as the latest stable source,
  Windows, and macOS release on 2026-04-26. Python 3.15 existed only as alpha, so
  it was explicitly not the stable target.

Impact:
- Teaching projects should not silently encode the model's stale default as a
  product decision.
- Runtime and dependency choices are time-sensitive. Agents must verify them
  against current upstream sources before pinning.
- Lockfiles can preserve old choices even after `pyproject.toml` is updated.

Action:
- Project target moved to Python `>=3.14,<3.15`.
- `uv.lock` was regenerated with Python 3.14.4.
- Validation passed on Python 3.14.4: pytest, ruff, mypy, and anchor validator.

Rule added:
- Before choosing or changing a runtime, framework, or dependency version, the
  lead agent must check a current primary source or package index, record the
  evidence in `EVOLUTION.md` or the commit message, and update both config and
  lockfiles.
- If the latest stable upstream version is not locally available, record that as
  environment friction instead of quietly falling back.

## 2026-04-26 — Codex Subagent Thread Lifecycle

Observation:
- During v0.1, Codex hit a thread-limit error while completed subagent threads
  were still open.
- The issue was not simply "too few threads"; completed agents were not closed
  promptly after their evidence was extracted.
- The project-local Codex cap had been `max_threads = 4`. That allowed useful
  parallelism but left little room for a follow-up worker when completed threads
  were still occupying slots.

Impact:
- Lead-agent orchestration needs lifecycle discipline, not just more parallelism.
- A broad swarm would increase review load and token burn; a small queue with
  prompt closure is better for this project.

Action:
- Codex `agents.max_threads` increased from 4 to 5 to allow one extra integration
  or validation worker.
- The operating rule is now: close completed subagents immediately after their
  report has been summarized into durable state or a commit message.

Rule added:
- Prefer 2-4 active subagents for normal work.
- Use the fifth slot as operational headroom, not as a reason to fan out by
  default.
- If thread pressure appears again, first close completed agents, then split or
  queue work; only raise the cap after observing repeated real need.

## 2026-04-26 — v0.1 Subagent Quality Notes

Observation:
- The read-only scout produced high-value importer evidence with no code churn.
- Implementation workers stayed mostly inside ownership boundaries and returned
  useful validation evidence.
- The lead still had to catch integration-level details: stale UI copy after Task
  D, a mypy strictness issue in tests, and lockfile/runtime mismatch.

Lesson:
- Subagents are excellent for bounded production slices and source-shape
  exploration.
- The lead must remain accountable for cross-slice truth: docs, lockfiles, WHY
  graph state, final validation, and product semantics.

Rule added:
- Keep using bounded subagents, but reserve final integration and semantic
  consistency checks for the lead or a dedicated reviewer subagent.
