# WORKLOG — Current Runway

> Lightweight state for the current execution lead.
>
> This file is intentionally short. It is not a changelog, not a historical task
> archive, and not a ritual to update after every command. Git records shipped
> changes; `EVOLUTION.md` records lessons; `CONTEXT.md` records current project
> direction. WORKLOG exists only to help a fresh agent resume if the active work
> stops in the middle.

**Last update:** 2026-05-01 — server smoke check + post-v1.2 wording cleanup
**Active session lead:** Codex GPT-5.5-class execution lead
**Current phase:** post-v1.2 feedback-hardening on `development`

---

## 1. Current State

Harness Observatory is a working post-v1.2 local product. The old bootstrap task
plan has been retired; current work is driven by human's feedback, PRD slices,
WHY graph updates, bounded Codex subagents, and fast validation.

The main product loop is now: fast implementation -> fast feedback -> fast
implementation, while preserving agent-visible evidence through tests,
Playwright screenshots when UI changes, semantic traces for runner jobs, and
short process lessons in `EVOLUTION.md`.

## 2. Active Work

| ID | Brief | Status | Notes |
|---|---|---|---|
| SPIRIT-DOCPRUNE-2026-05-01 | Spirit-lead doc-pruning pass: PRD §24 collapsed to short shipped-phases log + canonical-rule pointers; PRD §26 reduced to evergreen importer mapping; EVOLUTION removed from required reading and reframed as spirit-lead surface with explicit graduation rule; CONTEXT/AGENTS reading orders updated; README gained Quickstart. | completed | Anchor validator OK (66 anchors), ruff clean, pytest 111 passed. PRD_REF anchors in code updated to point at canonical sections (§14.2 / §24.1 / §26.X / README). |

## 3. Next Queue

| ID | Brief | Trigger |
|---|---|---|
| FEEDBACK-HARDENING | Continue improving the app from human/student/lecturer feedback. | Owner or lecturer feedback |
| STRUCTURE-AUDIT | Review code/package structure for student readability and agent development speed; promote real refactor work into PRD/WHY before implementation. | Lead-agent audit before next larger feature wave |
| EXEC-CLEANUP-MINORS | Two small bounded items left by the 2026-05-01 spirit-lead pass: (a) add a thin unit test for `engagement/service.py` (the only deterministic service without one); (b) opportunistic pass over older `EVOLUTION.md` entries to graduate stable rules into `docs/lessons/` and prune the EVOLUTION entry — see EVOLUTION preamble for the graduation rule. | Execution lead, opportunistic |
| DISPATCH-LEDGER-DISCIPLINE | Pick up the rolling subagent-dispatch ledger discipline scaffolded on 2026-05-01: (a) append a row to `docs/agent-run-ledger.md` after every Codex subagent dispatch with the verdict (`useful` / `partial` / `wasted` / `rework`) per `docs/codex-subagent-profile.md` "Verdict And Ledger Discipline"; (b) on the first occasion that has ~10 fresh rows or feels like a natural lull, run the periodic sweep — graduate stable patterns into the profile or `docs/lessons/`, and delete the seven 2026-04-27 seed rows whose lessons have already graduated to `docs/lessons/subagent-dispatch-craft.md` and the profile updates; (c) if a friction recurs that the existing profile does not cover, propose the new rule before adding a third instance — repeating the experiment is not a dispatch. | Execution lead, recurring |

## 4. Blocked / Waiting

- No product blocker.
- Old root `observatory.sqlite` may be held by a Windows file handle. It is ignored and no longer the default runtime target after the 2026-04-30 cleanup.
- Far-future autonomous long-haul orchestrator remains deferred; Codex Pro limits make the heavy manual resume machinery unnecessary for current development.

## 5. Update Rule

Update this file only when the current runway changes:

- new active product/process slice;
- blocker or owner question;
- in-flight subagent whose output must be found after a crash;
- known pause in the middle of unfinished work.

Do not paste long histories here. Put reusable process observations in
`EVOLUTION.md`; put shipped state in git and compact current truth in
`CONTEXT.md`.
