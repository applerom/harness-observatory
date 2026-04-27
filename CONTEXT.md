# Harness Observatory — Current Context

> **Last update:** 2026-04-27 — Curation status views and Spark prompt-budget feedback implemented
> **Phase:** v1.1 published to `main`; feedback-hardening active on `development`
> **Next milestone:** continue owner/student feedback hardening on the next surfaced tab

## Update 2026-04-27 — spirit-lead deep review after v1.0-minimal

Owner asked the spirit lead (Claude Opus, original author of SPIRIT/PRD/AGENTS) to deep-review the trajectory now that Codex GPT-5.5 has carried the project from v0.1 to v1.0-minimal in ~30 commits over one day. Three parallel Explore subagents produced converging findings: implementation is substantially faithful to PRD; spirit is well-honored on the most important fronts (Insight>Evidence, L1 auto-merge, file:line citations, target/runner naming, real lessons in `docs/lessons/`); engineering is shipped-but-solid (97/97 tests; ruff/mypy clean; 60/60 anchors).

Two real drifts found and addressed in this pass:

1. **Lead role moved from Opus to Codex GPT-5.5 in practice without SPIRIT update.** Owner confirmed the reality and the intent: Opus stays lead by spirit (constitutional steward, periodic deep review), Codex GPT-5.5 is the primary execution lead (orchestrator-implementer, runs subagents, maintains EVOLUTION). Both useful for students seeing real cross-harness collaboration in EVOLUTION.md. Spirit lead has standing right to refine SPIRIT/PRD/AGENTS based on observed drift. Now formalized in `SPIRIT.md` "Collaboration Model" and `AGENTS.md` Cross-Harness Lead-Agent Model.

2. **`engagement` job is deterministic templating, not agent-authored** — currently labelled as if it were an agent job. Owner direction: don't reimplement, just spec honestly. v1.1 = labelling pass (UI badge + Insight detail note + PRD §14.2 amendment); real agent-authored engagement deferred to v1.2 or later (only if FEEDBACK-HARDENING shows engagement copy is actually noticed/used).

PRD §24 gained an initial v1.1 phase block with four acceptance items (engagement honesty / parser silent-zero-Insights guard / ClaudeRunner empirical validation / Co-Authored-By discipline) chosen to be **feedback-orthogonal** so the parallel implementation track does not collide with the UI/product moves the FEEDBACK-HARDENING wave may demand. Items deliberately deferred to v1.2+: Feature Radar (PRD §11.5), real engagement agent, operational hardening (SQLite OperationalError retry, SSE client-disconnect cleanup, concurrency tests).

Owner-stated philosophy locked in this pass: production-ready was never the v1.0 aim; minimum-working-version-for-feedback was. Engineering hardening enters PRD only when feedback creates demand. Both leads run in parallel (FEEDBACK-HARDENING owner-driven; v1.1 execution-lead-driven), both feed into the next spirit-lead pass.

## Update 2026-04-27 — v1.0-minimal snapshot hygiene before main squash

Roman asked Codex to fix stale documentation and process drift before treating v1.0-minimal as the working `main` snapshot. The review found one human-facing doc bug and one process bug:

- `README.md` still described the repo as "Pre-v0.1 — foundational docs only", even though v1.0-minimal is implemented and validated locally.
- Recent agent-authored commits were authored as `Roman Siewko <applerom@gmail.com>`, which hides whether work came from Roman, the spirit lead, or the execution lead.

What changed in this pass:
- README/CONTEXT/module contracts were brought back to the v1.0-minimal reality.
- PRD §24 v1.1 now names v1.0 snapshot hygiene and commit author identity as explicit acceptance items.
- AGENTS/EVOLUTION now treat agent commit attribution as a continuity rule, not a courtesy.

Outcome: `development` was first committed as `371ce21` (`docs(v1): fix snapshot state and agent attribution`) with explicit Codex author identity. It was then squash-merged into `main` as `8dc0cdc` (`feat(v1): publish v1.0-minimal observatory snapshot`). The local `main` tree now represents the v1.0-minimal working product; push remains a separate operation.

## Update 2026-04-27 — v1.1 runner/parser execution evidence

Codex execution lead started PRD §24 v1.1 implementation after the v1.0-minimal main snapshot.

What changed / was observed:
- Engagement honesty UI now labels deterministic engagement copy as `template-generated` on Insight Library and Live detail surfaces.
- Parser empty-result guard now marks successful runner output with zero parsed artifacts as `done_no_findings` and emits `parser_returned_no_findings`.
- `ClaudeRunner` gained a cheap `preflight()` and Windows-runnable executable resolution.
- Real ClaudeRunner refresh Job #9 ran against target `claude-code`; Claude CLI version was `2.1.119 (Claude Code)`, runner status `done`, raw log `live-sessions/agent-job-00009.log`.
- Job #9 exposed a parser shape gap: Claude wrote plain evidence path bullets, not Markdown links. Parser was hardened to parse those; local Job #9 now has Insight #37 and EvidenceItems #80-#82.

Validation evidence: `uv run pytest` passed 101 tests; `uv run ruff check src/ tests/ scripts/validate_anchors.py` passed; `uv run mypy src/observatory tests` passed; `uv run python scripts/validate_anchors.py` checked 64 anchors / skipped 0; Playwright CLI `visual:insight`, `visual:jobs`, and `visual:live` passed. What's now possible: commit v1.1 with explicit Codex author identity.

## Update 2026-04-27 — feedback-hardening: Matrix must scan, not read like cards

Roman's first usage-feedback item targeted the Comparison Matrix: the old cell design used large card-like boxes containing only `present/unknown` and `unverified`, causing horizontal scrolling while communicating little. This is not only a visual complaint; it means the Matrix failed its core purpose as an overview surface.

Execution-lead decision: keep harnesses as rows and topics as columns for now, but convert the table into a dense symbolic scan surface before trying a stronger transpose. Cells use compact symbols for state, confidence is visual styling with accessible labels/tooltips, topic headers can be vertical, and expanded cell detail moves beside the matrix on desktop. This preserves the original intent (click cell -> Insight + proof) while making the default view useful at classroom/laptop scale.

Validation evidence: `uv run pytest` passed 101 tests; `uv run ruff check src/ tests/ scripts/validate_anchors.py` passed; `uv run mypy src/observatory tests` passed; `uv run python scripts/validate_anchors.py` checked 65 anchors / skipped 0; `npm run visual:matrix` passed. Additional Playwright screenshots were captured at `test-results/matrix-dense-feedback.png` and `test-results/matrix-dense-feedback-clicked.png`.

## Update 2026-04-27 — feedback-hardening process correction + Matrix detail slice

Roman corrected the execution process after the Matrix-density pass: feedback fixes should still follow PRD/task/WHY/delegation rather than direct lead implementation. Codex accepts this correction. The lead owns intent, scope, review, durable state, and integration; bounded implementation goes to subagents when the harness permits it.

Operational update: a new `fast_implementation_worker` profile based on `gpt-5.3-codex-spark` was added for small, reversible feedback-hardening slices. Official OpenAI sources checked on 2026-04-27 list Spark as a Codex research preview with non-final credit rates, so the project treats it as a fast implementation lane with lead verification, not as a replacement for reviewer/hard-worker roles.

Completed feedback item: Matrix detail hygiene. Roman reported that the side detail panel repeated scaffolding (`Expanded cell`, State/Confidence, repeated topic titles, repeated `Confidence: unverified`), rendered Markdown-ish payload as plain text, collapsed the selected cell after `Ask the agent why`, and showed duplicated explanations. PRD §11.2 and WHY graph now carry this intent. Spark worker Peirce implemented the bounded patch; reviewer Curie found no blockers and raised four issues, all addressed before commit: strict matrix reopen URL validation, duplicate status suppression, durable delegation evidence, and visual test coverage for Ask-why preservation.

Validation evidence: `uv run pytest` passed 105 tests; `uv run ruff check src/ tests/ scripts/validate_anchors.py` passed; `uv run mypy src/observatory tests` passed; `uv run python scripts/validate_anchors.py` checked 66 anchors / skipped 0; `npm run visual:matrix` passed and now covers detail hygiene plus Ask-why preservation.

## Update 2026-04-27 — feedback-hardening: Curation actions must feel reversible

Roman's next feedback item targeted the Curation Queue. The original buttons (`Mark verified`, `Mark disputed`, `Mark historical`) were technically small label mutations, but visually felt like opaque destructive actions: a user could not tell what pressing them changed, whether agent output/evidence would disappear, or whether a wrong click could be undone.

Execution-lead decision: treat this as a trust and teaching problem, not only button copy. PRD §11.7 and the WHY graph now state that Curation actions are label-only, preserve agent output, and must show an immediate Undo path. Spark worker Harvey implemented the bounded route/template/test patch; the lead tightened undo semantics so Undo is offered after the original action but not again after restoration.

Process correction captured: Roman explicitly deprioritized heavy strong-agent review during early visual-feedback churn. The project now keeps a lightweight `docs/agent-run-ledger.md` to tune which subagent profiles are useful. Spark is preferred for small implementation and validation/server tasks; strong reviewers are reserved for stabilized/risky checkpoints.

Validation evidence: Spark validator Herschel ran focused curation route tests (`2 passed, 31 deselected`), `npm run visual:curation` on a fresh server (`1 passed`), `uv run ruff check .`, `uv run mypy src tests`, and `uv run python scripts/validate_anchors.py` (66 anchors OK). A first visual run against a stale long-running server failed before the fresh-server rerun, reinforcing that visual QA after template/route edits should restart or isolate the server.

## Update 2026-04-27 — feedback-hardening: verified items need a visible home

Roman tested the improved Curation buttons and found the next trust problem: after pressing `Verify`, the Insight no longer appears in the default Curation Queue. That is correct under the old filter, but wrong for user confidence because the item feels lost. The product answer is explicit status navigation, not more explanation.

What changed:
- `/curation` now has visible views/tabs: `Needs review`, `Verified`, `Historical`, and `All`, with counts.
- `Verify` redirects into `view=verified`, so the changed Insight stays visible.
- `Archive historical` redirects into `view=historical`.
- `Flag dispute` stays in `view=review`.
- Undo redirects to the view where the restored status is visible.

Process lesson from the same feedback: Roman inspected Spark logs and caught a lead-orchestration problem. A fast Spark worker had read the broad cold-start docs and compacted before a tiny patch. The Codex subagent profile and fast-worker profile now require context-budgeted Spark prompts: a tiny context packet, exact allowed files, and no broad SPIRIT/PRD/WHY/WORKLOG/CONTEXT/EVOLUTION read unless the delegated task explicitly needs it.

Validation evidence: Faraday (`gpt-5.3-codex-spark/medium`) implemented the bounded Curation patch while obeying the read budget. Carver (`gpt-5.3-codex-spark/low`) ran validation without edits and caught an ambiguous Playwright locator. After the lead narrowed the locator, `uv run pytest tests/web/test_readonly_routes.py -k "curation"` passed (`3 passed, 31 deselected`) and `npm run visual:curation` passed.

---

This file is the **current handoff state**. Read it after `SPIRIT.md` and `AGENTS.md` to understand where work is right now.

---

## 1. What just happened

A new sibling project `harness-observatory/` was created at `D:/ai/harnesses/harness-observatory/`.

Decisions were locked through a structured interview between the project owner (Roman) and the lead agent (Claude Opus 4.7). The interview covered six discriminating questions: scope, project location, tech stack, demonstration model, agent-job entity shape, and v0.1 slice definition.

All decisions are written into `docs/PRD.md` (v2). The pedagogical and collaborative spirit is captured in `SPIRIT.md`. The intent-to-implementation map starts in `docs/why-graph.xml` (stem only — modules will gain anchors as code lands).

Historical note: at project bootstrap, no code had been written yet and v0.1 was delegated per `DELEGATION-PLAN.md`. As of 2026-04-26, v1.0-minimal exists locally: importer/viewer, refresh jobs, parser persistence, scheduler, curation, Live Studio SSE, abstract artifacts, verification/confidence UI, engagement seeds, first-observer claims, Insight Library, explain jobs, lens scoring, generated docs export, legacy archive manifest, and onboarding checklist.

---

## 2. Reading order for a new agent (cold start)

1. `SPIRIT.md` — project soul, pedagogical bet, what would betray this spirit
2. `AGENTS.md` — agent1st protocol (the 11 numbered principles) plus observatory-specific addendum (incl. "Interrupt-and-Resume Pattern")
3. `docs/PRD.md` — what we're building, locked decisions, phases v0.1 → v1.0
4. `docs/why-graph.xml` — intent → code map (stem; expanded as code lands)
5. `docs/why-graph-principles.md` + `docs/why-contracts-v1.md` — how to extend the graph and write contracts (reference)
6. `CONTEXT.md` (this file) — running decision log
7. `WORKLOG.md` — durable state of current work (active items, next queue, blocked, recent history)
8. `EVOLUTION.md` — development trajectory log and reusable process lessons
9. `DELEGATION-PLAN.md` — if you're coordinating subagents or writing code

After reading 1–8, output once: `Observatory Agent1st ON`

---

## 3. Project layout right now

```
harness-observatory/
├── .git/                       (initialized 2026-04-25)
├── .gitignore                  Python+SQLite+local-state ignores
├── README.md                   public-facing entry (98 lines)
├── SPIRIT.md                   project soul — Russian, English headers (162 lines)
├── AGENTS.md                   agent1st core + observatory addendum (237 lines)
├── CLAUDE.md                   3-line import file (@AGENTS @SPIRIT @CONTEXT)
├── CONTEXT.md                  this file (running decision log)
├── WORKLOG.md                  durable state of current work in flight (interrupt-resume substrate)
├── EVOLUTION.md                development trajectory log (lessons, drift, process changes)
├── DELEGATION-PLAN.md          orchestration plan for subagents
├── package.json                Playwright CLI visual QA tooling
├── playwright.config.mjs       visual QA config
├── docs/
│   ├── PRD.md                  product spec v2 — interview-locked (1271 lines)
│   ├── lessons/                short student-facing lessons extracted from real development episodes
│   ├── why-graph.xml           intent→code map (expanded as code lands)
│   ├── why-graph-principles.md  agent1st reference (verbatim from upstream)
│   ├── why-contracts-v1.md      agent1st reference (verbatim from upstream)
│   └── WHY-APPROACH.md         agent1st reference (verbatim from upstream)
├── media/.gitkeep              for lecturer-attached images/asciicasts (per-machine, .gitignored)
└── live-sessions/.gitkeep      for raw stdout logs from live agent runs (per-machine, .gitignored)
```

Historical note: this was true at bootstrap. `src/` now exists after v0.1 implementation.

---

## 4. Locked decisions (one-line each, full detail in PRD.md)

- **Scope:** orchestration-first hybrid — agent jobs are the engine, comparison views are the dashboard. (PRD §3, §14)
- **Location:** `D:/ai/harnesses/harness-observatory/` as a new sibling. `harness-architecture/` stays as constitution + migration input. (CONTEXT this file)
- **Tech stack:** Python 3.14 + uv + FastAPI + SQLModel + SQLite + Alembic + Jinja2 + HTMX + APScheduler + lxml + asyncio.subprocess + ruff + pytest. NOT: Anthropic SDK, React (in v1), Postgres (in v1), Docker (in v1). (PRD §20)
- **Pedagogy:** three-stage learner journey; Insight on top, EvidenceItem ("Show the proof") collapsed below; agent fallibility as pedagogy; engagement > perfection. (PRD §4.7–4.9, SPIRIT)
- **Agent abstraction:** `AgentRunner` interface — first-class. v0.2a has `CodexRunner` and `ClaudeRunner`; runner-specific CLI commands live only inside runner modules. UI and logs distinguish `target` (what is studied) from `runner` (agent doing the work). (PRD §4.10)
- **Autonomy:** L1 auto-merge with confidence labelling. All produced Insights publish as `proposed`. No staging review queue. Multi-pass verification handles raw output. (PRD §7, §12)
- **Live discovery:** first-class use case. Lecturer dispatches agent live; SSE stream to projector; student attribution on fresh findings. (PRD §11.8, SPIRIT)
- **v0.1 slice:** read-only viewer + markdown importer only. No agents yet. Validates schema on real data before agents depend on it. (PRD §26)
- **Phases:** v0.1 read-only → v0.2 single-harness vertical → v0.3 all harnesses + cron → v0.4 Live Studio + abstract → v0.5 multi-pass + confidence UI → v0.6 engagement → v0.7 ask-why → v1.0 lens scoring + doc gen. (PRD §24)

---

## 5. What's next

v1.0-minimal is working locally and ready to be fixed as the current `main` snapshot. The immediate ordered work is:

1. Squash-merge the v1.0-minimal `development` history into `main` with an honest summary of the product state.
2. Implement PRD §24 v1.1 feedback-orthogonal items from WORKLOG:
   - `V11-ENGAGEMENT-HONESTY`
   - `V11-PARSER-EMPTY-GUARD`
   - `V11-CLAUDE-RUNNER-EMPIRICAL`
   - `V11-COAUTHOR-DISCIPLINE`
3. Keep FEEDBACK-HARDENING running in parallel: Roman/lecturers/students use the app and turn real findings into PRD/WHY/WORKLOG deltas.

Decision note: the product has advanced beyond the original v0.1/v0.2 narrative. The current discipline stays the same: frame feedback as PRD/WHY deltas first, delegate bounded implementation when appropriate, then prove with tests, visual checks, and durable logs.

---

## 6. Open questions / known gaps

- **Migration data scope.** ~~Mapping not pre-specified.~~ **Resolved 2026-04-25 alignment pass:** see PRD §26.1.1 and §26.1.2 for the explicit field-by-field translation, including the MiniMax CLI ecosystem-object exception.
- **Initial seed PromptTemplates** for all 6 AgentJob types (`discover`/`verify`/`abstract`/`engagement`/`refresh`/`explain`). v0.2a seeds only the rough OpenCode `refresh` prompt in `RefreshJobService`; the other five templates are still pending.
- **`first_observed_by` identity model.** PRD v2 defaults this to a free-text handle (no auth, no user table). Open to revisit if engagement features in v0.6 need more.
- **Anchor validator policy on PLANNED state.** **Resolved 2026-04-25 alignment pass:** validator skips anchors inside `MODULE_*` nodes with `STATE="PLANNED"`. The graph plans more than the code implements at any moment; `STATE` is the watershed. Validator only fails when an anchor is referenced from a node with `STATE="STARTED"` or `STATE="DONE"` and the anchor is missing from source (or a `STATE="PLANNED"` node has been left STARTED-without-cleanup). Documented in the validator script's docstring when it lands as part of v0.1 Task E.
- **Broken absolute paths in `harness-architecture/`** (7 known references to old `D:/ai/harness-architecture/` location, listed by an exploration subagent earlier). Not blocking — fix as a separate cleanup pass when convenient.
- **~~Sequencing of orchestration vs v0.1 dispatch.~~ Resolved 2026-04-25:** owner directed neither (A) nor (B). The automated orchestrator is **deferred to the far horizon** — building it before any code lands risks designing for imagined needs and adds scope before the project has earned the right to it. The v0 substitute is a manual interrupt-and-resume runbook that costs zero code:
  - `AGENTS.md` "Interrupt-and-Resume Pattern" section — describes the hierarchy (owner = orchestrator; lead agent = architect; subagents = bounded executors), WORKLOG discipline, resume protocol across rate-window stops.
  - `WORKLOG.md` (root) — durable state file for current work in flight (active items, next ordered queue, blocked, recent history). Hand-editable Markdown.
  - On rate-window stop or session loss: owner reads WORKLOG, starts a new session (same or different agent class), the new session does the resume protocol, picks up from the active item.
  - PRD §27 design constraints remain valid as guardrails for if/when an automated orchestrator is later built.

## Update 2026-04-25 — interrupt-and-resume runbook + sequencing question closed

After alignment pass 2 (commit `0d90bd1`) named the long-haul orchestration concern in PRD §27 and surfaced the sequencing question in §6 above, the owner gave clear direction: **do not build the orchestrator now — defer to the far horizon.** Reasoning: the orchestration ask was a *constraint to keep in mind*, not a green light to build. Premature orchestration = imagined-needs design + scope creep before the project has earned the right.

The v0 substitute, landing in this update:

- **`AGENTS.md` "Interrupt-and-Resume Pattern" section** added to the Observatory Addendum. Describes:
  - the substrate (WORKLOG.md = task state; CONTEXT.md = decision log; git = historical truth; TaskCreate/TaskList = session-local only, do not rely on)
  - the hierarchy (owner = orchestrator; lead agent = architect; subagents = bounded executors)
  - lead agent's WORKLOG discipline (read at session start; update after each meaningful step; ensure 5-minute resume test passes before any known stop; commit with the change)
  - resume protocol (cold-start agent reads SPIRIT → AGENTS → CONTEXT → WORKLOG → DELEGATION; check for orphaned subagent output before re-dispatch; surface to owner if state is unclear)
  - manual resume across rate-window stops (owner waits for window or escalates to different agent class; new session does resume protocol; no automated retry)
- **`WORKLOG.md`** created at root. Five sections: current state / active items / next ordered queue / blocked / recent history. Hand-editable Markdown. Initial content reflects current pre-v0.1 state (paused awaiting owner go-ahead for v0.1 first wave).
- **`AGENTS.md` Required Reading list** updated: WORKLOG.md inserted as item 7 (between CONTEXT.md and DELEGATION-PLAN.md).
- **`AGENTS.md` Documentation conventions** updated: WORKLOG.md described and distinguished from CONTEXT.md.

What's now possible: lead agent can be interrupted (rate window, compaction, session end) at any point and a fresh session — same or different agent class — can pick up from WORKLOG with the resume protocol. No code lost, no work duplicated, no orchestrator dependency.

What's now blocking: still nothing in this commit's scope. The original v0.1 first-wave dispatch is still gated on owner go-ahead — that gate did not move.

## Update 2026-04-25 — alignment pass 2 + long-haul orchestration concern named

A third reviewer agent (fresh-eyes pass after the GPT-5.5 alignment commit) caught three more drifts; the owner also surfaced a substantial new concern (long-haul project on Pro/Plus subscription rate windows). One alignment commit handles both:

**Drift fixes (small):**
- **Startup command unified across PRD §26.6, DELEGATION-PLAN §2 + Task B + Task C** to: web → `uv run uvicorn observatory.web.app:create_app --factory --reload`; importer → `uv run python -m observatory.importers.canon --source <path>`. The earlier "`uv run observatory import-canon`" form (recorded in alignment pass 1 above) implied a Typer/Click CLI wrapper and a `[project.scripts]` entry that didn't exist in the v0.1 stack — an unintentional scope-add. Reverted to the cheap unification (one `uv run <tool>` pattern, no new CLI module). A Typer CLI is a candidate v0.2 ergonomics improvement, named in PRD §26.1 and §26.6.
- **README stale phrase** — "`docs/PRD.md` (once it exists)" trimmed; PRD does exist.
- **ClaudeRunner stub wording reconciled** — DELEGATION-PLAN Task E said "NO concrete implementations in v0.1" while PRD §26.3 said "stub class raising `NotImplementedError`". Resolution: the stub class **is** in v0.1, with every method body raising `NotImplementedError("ClaudeRunner is a v0.1 stub; …v0.2 per PRD §24")`. The wiring is real (DI sites resolve a real type, "Refresh" button can render disabled with a tooltip), the call is not (no `claude -p` subprocess literal anywhere in v0.1 — Task E acceptance now greps for it).

**New concern named — PRD §27 "Long-Haul Orchestration on Personal Subscriptions":**
- Owner surfaced the constraint: project runs on personal Claude Pro + Codex Plus, multi-week timeline, needs to keep moving across rate-window resets without burning quota on retries or losing partial progress. Pattern is also a Level-3 dogfood — students will face the same constraint.
- §27 commits to *handling* the problem and locks 8 design constraints (no LLM in cron loop; timing-based detection first; multi-runner aware; plan as durable artifact; lead-agent owns plan, orchestrator owns dispatch; partial-completion is first-class state; configurable back-off; dogfood by default). It deliberately does *not* scaffold the directory, plan format, or scripts — that requires a separate checkpoint (see §6 below).

**Earlier alignment pass 1 (preserved for history):**

A second reviewer agent caught real drift between foundational docs. Fixed in one alignment commit before any code subagent dispatch:

A second reviewer agent caught real drift between foundational docs. Fixed in one alignment commit before any code subagent dispatch:

- PRD §1 framing line: replaced "code-first and evidence-first" leftover with "insight-first, evidence-backed" (consistent with §4.8).
- PRD §26.1: importer command unified across PRD/WHY-graph/DELEGATION-PLAN to `uv run python -m observatory.importers.canon --source <path>` (Python module entry — see alignment pass 2 below for why the earlier `uv run observatory import-canon` form was reverted), with module path `src/observatory/importers/canon.py` (avoids reserved word `import` as module name).
- PRD §26.1 expanded with explicit field-by-field source→entity mapping and the MiniMax CLI ecosystem-object exception.
- PRD §26.4: validator filename unified to `scripts/validate_anchors.py` (PEP 8 underscore).
- WHY graph: 18 stale `PRD_REF` entries rewritten against PRD v2's actual section numbering. MOD-IMPORTER FILE attribute and 4 anchor COORDs updated to new path.
- DELEGATION-PLAN.md Task A: removed `AgentRun-history` and `QueueItem` from stub-table list (neither exists in PRD §7).
- DELEGATION-PLAN.md Task E: validator policy ("skip PLANNED MODULE nodes") added to acceptance criteria.
- Documentation conventions formalized in AGENTS.md addendum: README only at root for humans; agent reading order canonical in AGENTS.md; do not duplicate.
- SPIRIT.md "Hello Agent" and README "For agents" both deferred to AGENTS.md as single source of truth for reading order.

What's now possible: subagent dispatch for v0.1 Task A/B/C without ambiguity about importer path, validator name, schema entity list, or which doc is the canonical reading-order source.

What's now blocking: nothing in this commit's scope. Owner go-ahead is the next gate.

---

## 7. Things the next agent should NOT do

- Do not write code before reading the full reading-order list above.
- Do not bypass the `AgentRunner` abstraction by directly invoking `claude -p` from anywhere except inside `ClaudeRunner` (when it lands in v0.2).
- Do not create a "review queue" / "staging" / "approval workflow" — autonomy is L1 auto-merge with confidence labelling per PRD §12.
- Do not re-architect to "Insight-as-wrapper-around-code". Insight is the primary artifact (PRD §4.8) — EvidenceItem is the proof beneath, always collapsed by default.
- Do not silently delete or filter agent outputs that look "low quality" or "wrong". Agent fallibility is teaching material per §4.9. Use `disputed` / `corrected` status, not deletion.
- Do not add scope to v0.1 beyond `docs/PRD.md §26`. Read-only viewer + import. Nothing else.

---

## 8. Where to record progress

Future updates to this file should append a dated section at the bottom:

```markdown
## Update 2026-MM-DD — <short subject>

What changed: ...
What's now possible: ...
What's now blocking: ...
```

Old sections stay; this file is a running log, not a snapshot. When it grows past ~500 lines, archive earlier sections to `CONTEXT-history.md`.

## Update 2026-04-26 — cross-harness lead-agent delegation aligned

Roman clarified the intended collaboration model: Claude Code/Opus and Codex/GPT-5.x are peer **lead-agent harnesses** for this project, working serially rather than concurrently. Either lead agent may disagree with the other on project-quality grounds, but durable project state (WORKLOG, CONTEXT, git) is the handoff boundary. Roman's role stays intent/feedback/domain taste; lead agents are expected to act proactively for project benefit.

What changed:
- `AGENTS.md` now distinguishes `agent harness` from product `Harness`, records standing project-level authorization for lead agents to use harness-local subagents, and describes Claude Code and Codex as peer lead-agent environments.
- `DELEGATION-PLAN.md` is no longer Claude Code-specific: it maps v0.1 tasks to "suggested subagent class" and adds harness adapters for Claude Code, Codex, and future harnesses.
- `WORKLOG.md` now records Codex as the current active session lead for this alignment pass and updates the v0.1 queue from fixed Sonnet/Haiku labels to harness-local worker classes.

What's now possible: Codex can run as a full lead-agent/orchestrator for this repo when the active session permits subagent spawning; Claude Code can do the same through its own Task/Agent tooling. Future agents should preserve the same delegation contract: bounded task, clear ownership, evidence report, lead-owned review/integration/commit.

What's now blocking: no code has started yet. v0.1 implementation still waits for Roman's explicit implementation start signal after this process alignment is reviewed.

## Update 2026-04-26 — Codex subagent operating profile added

Roman provided `docs/codex-subagents-recommendations.md`, an advisory memo on how Codex should use subagents for this project. Codex checked it against current official OpenAI docs and converted it into a smaller project operating profile.

What changed:
- Added `docs/codex-subagent-profile.md` as the Codex-specific operating profile: small hierarchy, at most 1-2 scouts before write-heavy work, bounded worker ownership, no subagent commits, lead-owned integration.
- Added project-local `.codex/config.toml` with `agents.max_threads = 4` and `agents.max_depth = 1`, plus default lead model posture. Superseded 2026-04-26 by the Python 3.14 / EVOLUTION update: current Codex cap is `agents.max_threads = 5` with the fifth slot reserved as operational headroom.
- Added custom Codex agent profiles under `.codex/agents/`: `repo_explorer`, `implementation_worker`, `hard_worker`, `reviewer`, and `validator`.
- Linked the profile from `AGENTS.md` and `DELEGATION-PLAN.md`.

What's now possible: a future Codex lead can start v0.1 with a known subagent scheme instead of redesigning delegation each session.

What's now blocking: still no production code. Next implementation start should begin from `WORKLOG.md` and `DELEGATION-PLAN.md`, using the Codex profile only as an operating aid.

## Update 2026-04-26 — v0.1 implementation start authorized in Codex

Roman gave the Codex lead agent the explicit v0.1 implementation start signal and reaffirmed session-level authorization to use Codex subagents as an orchestration mechanism. The intended posture is not "spawn subagents ritualistically"; it is lead-agent judgment: delegate when it preserves lead context, parallelizes bounded work, or improves validation.

What changed:
- `WORKLOG.md` moved from awaiting implementation start to v0.1 implementation in progress.
- Small documentation drift noted during the Codex project read-through is being cleaned before the first code wave: PRD §27 no longer refers to an open sequencing question, DELEGATION task dependencies/count thresholds are aligned, README no longer overstates WHY graph completeness, and AGENTS records the Codex session-level subagent authorization.

What's now possible: v0.1 Tasks A/B/C can begin under the existing delegation plan after the drift cleanup lands.

What's now blocking: no project-level blocker. The first implementation risk is importer reality against `../harness-architecture`; keep v0.1 minimal and iterate from real feedback rather than trying to design the final data model upfront.

## Update 2026-04-26 — Python 3.14 and evolution log

Roman noticed that v0.1 had been scaffolded on Python 3.12, likely from agent/model familiarity rather than current stable runtime evidence. Codex checked official Python.org sources on 2026-04-26: Python 3.14.4 is the latest stable release, while 3.15 is still alpha.

What changed:
- Project runtime target moved from Python 3.12 to Python 3.14 (`>=3.14,<3.15`).
- `uv.lock` was regenerated against Python 3.14.4 after installing a local project runtime under `D:/ai/harnesses/.runtimes/python-3.14.4`.
- Added `EVOLUTION.md` as a teaching-facing trajectory log for agent-version inertia, dependency freshness, subagent process friction, and other lessons from building.
- Codex subagent thread cap moved from 4 to 5, with an explicit lifecycle rule: close completed agents promptly; treat the fifth slot as headroom, not a swarm default.

What's now possible: future agents and students can see not just the final stack choice, but the path by which the project corrected stale agent defaults.

What's now blocking: local developer machines need Python 3.14 available. On this Windows machine, current `uv python install 3.14.4` did not have a managed download yet, so Codex used the official Python.org Windows installer into a local runtime directory. This is environment friction, not a product blocker.

## Update 2026-04-26 — v0.3a manual refresh generalized beyond OpenCode

Roman asked Codex to take larger autonomous product slices now that Playwright visual QA and semantic runtime traces exist. Codex framed v0.3a as "manual refresh generalization before cron" and delegated the bounded implementation after a read-only scout confirmed the main blocker: imported non-OpenCode `local_upstream_path` values were stale, while sibling architecture directories exist under `D:/ai/harnesses`.

What changed:
- Manual refresh is target-generic in service and UI; non-OpenCode dossiers now show `Run with Codex` / `Run with Claude`.
- The refresh prompt template is `harness-refresh-v0.3a`.
- Target cwd preflight can repair stale imported paths to obvious sibling architecture directories, and semantic events record configured vs resolved cwd.
- Parser output no longer hardcodes OpenCode titles, trims any `*-architecture` repo prefix, and attaches parsed artifacts to the actual `AgentJob.target_id` harness without defaulting to OpenCode.
- Added Playwright CLI visual coverage for non-OpenCode dossier refresh controls.

Evidence:
- `uv run pytest` passed with 51 tests.
- `ruff`, `mypy`, and anchor validator passed.
- `npm run visual:harness` and `npm run visual:matrix` passed after a stale dev server restart.
- Live smoke job #5 for Codex CLI used the real SQLite DB with a fake runner, resolved `d:/ai/codex-architecture/` to `D:/ai/harnesses/codex-architecture`, rendered `/jobs/5`, and parsed proposed artifacts #36/#79.

What's now possible: v0.3 can proceed toward APScheduler/cron knowing the manual refresh path is no longer a one-target special case.

What's now blocking: no product blocker. A future real model-backed Codex CLI refresh can be run when useful, but v0.3a's code path is already covered without spending a long `gpt-5.5` runtime call.

## Update 2026-04-26 — v0.3b guarded scheduler slice

Roman asked Codex to increase autonomous work chunk size again. Codex took the next PRD v0.3 product step as a larger loop: first scheduler slice from PRD/WHY through implementation, validation, visual smoke, live smoke, and commit.

What changed:
- Added `RefreshSchedule` as the DB-backed per-harness cadence table.
- Added APScheduler `3.11.2`, deliberately choosing latest stable 3.x over `4.0.0a6` alpha.
- Added `observatory.scheduler.service` for opt-in registration, next-run calculation, and testable scheduler boundaries.
- FastAPI lifespan can start/shutdown a `BackgroundScheduler`, guarded by `OBSERVATORY_SCHEDULER_ENABLED`; default local/test startup does not dispatch background jobs.
- Job Dashboard now shows refresh schedule metadata before recent jobs.
- Scheduled dispatch reuses `RefreshJobService` and labels jobs with `trigger="cron"`.
- Durable dispatch labels now omit long Codex agent ids unless a live technical operation needs the id.

Evidence:
- `uv run pytest` passed with 57 tests.
- `ruff`, `mypy`, and anchor validator passed.
- `uv run alembic upgrade head` applied the schedule migration to the real local SQLite DB.
- `npm run visual:jobs`, `npm run visual:harness`, and `npm run visual:matrix` passed.
- Live `/jobs` showed schedule metadata, and a registration smoke produced `registered=1`, `calls=0`.

What's now possible: v0.3 can proceed to the first Curation Queue for proposed Insights, or to enabling a narrow real cron run once Roman wants to spend a model-backed scheduled refresh.

## Update 2026-04-26 — v0.3c/v0.4a Curation Queue and Live Agent Studio

Roman pushed for a larger milestone-sized pass instead of minor substeps. Codex combined the remaining v0.3 Curation Queue with the first v0.4a Live Agent Studio SSE vertical, while deferring abstract teaching artifacts to v0.4b.

What changed:
- Added `/curation` as a post-publication curation workbench for proposed/disputed/unverified Insights.
- Curation actions mark `human-verified`, `disputed`, or `historical` and write `RevisionNote` audit entries. `corrected` is deliberately not a quick action until there is a real correction workflow.
- Added `AgentJob.prompt_text` with Alembic migration `20260426_0003`; refresh and live jobs now preserve the exact prompt text used at runtime.
- Added `/live`, `/live/{job_id}`, and `/live/{job_id}/stream` for Live Agent Studio.
- Live execution creates `AgentJob(type="discover", trigger="live")`, streams `AgentRunner.stream()` events via SSE, writes raw log chunks, and emits semantic runtime events.
- `CodexRunner.stream()` and `ClaudeRunner.stream()` now read subprocess stdout/stderr incrementally instead of buffering through `run()`.
- Live cancellation marks the job failed and runner stream cleanup kills the child subprocess.

Evidence:
- `uv run pytest` passed with 70 tests.
- `ruff`, `mypy`, and anchor validator passed; anchor validator checked 45 anchors.
- `uv run alembic upgrade head` applied `20260426_0003` to the real SQLite DB.
- `npm run visual:curation` and `npm run visual:live` passed on the refreshed local server.
- Live smoke job #6 used the real SQLite DB with a fake live runner, ended `done`, wrote raw log chunks, and produced `live_job_running`, `live_target_cwd_preflight_succeeded`, and `live_runner_stream_result` semantic events.

What's now possible: v0.4b can add the first `abstract` job type for EvidenceItem-to-teaching-artifact generation.

What's now blocking: no product blocker. A real model-backed live session can be run when Roman wants to spend a live Codex/Claude invocation.

## Update 2026-04-26 — v0.4b/v0.5a/v0.6a product train

Roman asked Codex to take a larger product chunk and continue through v0.5 into v0.6 if v0.5 landed cleanly. Codex framed acceptance in PRD and WHY first, then delegated abstract, verification, and engagement slices to separate workers and used a reviewer agent for integration semantics.

What changed:
- Added `observatory.abstracts.service.AbstractJobService`: deterministic `AgentJob(type="abstract")`, `Insight(format="mermaid_diagram")` teaching artifact, `RevisionNote`, raw log, and semantic events.
- Added `observatory.verification.service.VerificationJobService`: deterministic support/dispute passes, `ObservationReview` history, EvidenceItem verifier metadata, and derived Insight/ComparisonCell confidence labels.
- Added engagement jobs, first-observer claim helpers, `/insights` Insight Library, navigation entry, and deterministic engagement-copy generation.
- Live Studio first-observer claims are scoped to Insights listed in the live job's `produced_artifact_ids`; unrelated/stale Insights cannot be claimed as "first observed" for a live session.
- Job Detail, matrix, harness dossier, topic dossier, live view, and Insight Library now expose the new artifact/confidence/engagement state.

Evidence:
- `uv run pytest` passed with 85 tests.
- `ruff`, `mypy`, and anchor validator passed; anchor validator checked 52 anchors.
- Playwright CLI passed for matrix, harness, jobs, live, insight library, and curation.

What's now possible: v0.7 can add the "Ask the agent why" / `explain` job type using the now-established job, prompt, semantic trace, and Insight Library surfaces.

What's now blocking: no product blocker. The next design question is how much explanation text belongs on the existing Insight row versus a separate explain artifact/revision trail.

## Update 2026-04-26 — v0.7-v1.0 minimal product train

Roman asked Codex to add everything currently in PRD through v1.0, explicitly aiming for a working, feedback-ready product rather than an ideal final version. Codex added concrete acceptance criteria for v0.7a and v1.0-minimal, delegated explain/lens/export slices, then integrated and reviewed the combined product surface.

What changed:
- Added deterministic `explain` jobs. The shared Insight card now has "Ask the agent why"; the job stores exact prompt text, raw log, semantic event, and a `RevisionNote`. Explanations render on Insight Library, harness dossier, topic dossier, and matrix detail.
- Added lens scoring: default lenses (`Research`, `Lecturer`, `Practical Selection`, `Ecosystem`), deterministic score refresh, `/lenses`, and a DB uniqueness constraint for `(lens_id, harness_id, topic_id)`.
- Added generated Markdown exports: comparison report, harness summaries, lecturer brief, onboarding checklist, and a legacy archive manifest under `generated-docs/`.
- Added `/exports` to trigger and inspect generated files. The legacy archive manifest records coverage metadata and does not mutate the sibling legacy repo by default.
- Added Playwright visual coverage for Lenses and Exports, plus nav links for both.

Evidence:
- `uv run pytest` passed with 97 tests.
- `ruff`, `mypy`, and anchor validator passed; anchor validator checked 60 anchors.
- `uv run alembic upgrade head` applied migration `20260426_0004`.
- Playwright CLI passed for matrix, harness, insight, lens, export, jobs, curation, and live.
- Live smoke passed for `/lenses/refresh`, `/exports/generate`, `/insights/1/explain`, `/harnesses/opencode`, `/matrix/cells/opencode/instruction-files`, and `/jobs`.

What's now possible: Roman and students can start using the app end-to-end and generate real feedback on rough but connected product flows.

What's now blocking: no known product blocker. The next work should come from actual usage feedback rather than adding more speculative surface.
