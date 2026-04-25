# Harness Observatory — Current Context

> **Last update:** 2026-04-25
> **Phase:** Pre-v0.1 — foundational docs landed, no code yet
> **Next milestone:** v0.1 First Working Slice (read-only viewer + markdown import)

This file is the **current handoff state**. Read it after `SPIRIT.md` and `AGENTS.md` to understand where work is right now.

---

## 1. What just happened

A new sibling project `harness-observatory/` was created at `D:/ai/harnesses/harness-observatory/`.

Decisions were locked through a structured interview between the project owner (Roman) and the lead agent (Claude Opus 4.7). The interview covered six discriminating questions: scope, project location, tech stack, demonstration model, agent-job entity shape, and v0.1 slice definition.

All decisions are written into `docs/PRD.md` (v2). The pedagogical and collaborative spirit is captured in `SPIRIT.md`. The intent-to-implementation map starts in `docs/why-graph.xml` (stem only — modules will gain anchors as code lands).

**No code has been written yet.** The next phase delegates v0.1 implementation to subagents per `DELEGATION-PLAN.md`.

---

## 2. Reading order for a new agent (cold start)

1. `SPIRIT.md` — project soul, pedagogical bet, what would betray this spirit
2. `AGENTS.md` — agent1st protocol (the 11 numbered principles) plus observatory-specific addendum
3. `docs/PRD.md` — what we're building, locked decisions, phases v0.1 → v1.0
4. `docs/why-graph.xml` — intent → code map (stem; expanded as code lands)
5. `docs/why-graph-principles.md` + `docs/why-contracts-v1.md` — how to extend the graph and write contracts (reference)
6. `CONTEXT.md` (this file) — current handoff state
7. `DELEGATION-PLAN.md` — if you're coordinating subagents or writing code

After reading 1–7, output once: `Observatory Agent1st ON`

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
├── CONTEXT.md                  this file
├── DELEGATION-PLAN.md          orchestration plan for subagents
├── docs/
│   ├── PRD.md                  product spec v2 — interview-locked (1271 lines)
│   ├── why-graph.xml           intent→code map (286 lines, schema 0.8, 7 UC + 18 FEAT + 8 MOD + 58 edges + 24 anchor stubs)
│   ├── why-graph-principles.md  agent1st reference (verbatim from upstream)
│   ├── why-contracts-v1.md      agent1st reference (verbatim from upstream)
│   └── WHY-APPROACH.md         agent1st reference (verbatim from upstream)
├── media/.gitkeep              for lecturer-attached images/asciicasts (per-machine, .gitignored)
└── live-sessions/.gitkeep      for raw stdout logs from live agent runs (per-machine, .gitignored)
```

**No `src/` yet.** That lands in v0.1 implementation.

---

## 4. Locked decisions (one-line each, full detail in PRD.md)

- **Scope:** orchestration-first hybrid — agent jobs are the engine, comparison views are the dashboard. (PRD §3, §14)
- **Location:** `D:/ai/harnesses/harness-observatory/` as a new sibling. `harness-architecture/` stays as constitution + migration input. (CONTEXT this file)
- **Tech stack:** Python 3.12 + uv + FastAPI + SQLModel + SQLite + Alembic + Jinja2 + HTMX + APScheduler + lxml + asyncio.subprocess + ruff + pytest. NOT: Anthropic SDK, React (in v1), Postgres (in v1), Docker (in v1). (PRD §20)
- **Pedagogy:** three-stage learner journey; Insight on top, EvidenceItem ("Show the proof") collapsed below; agent fallibility as pedagogy; engagement > perfection. (PRD §4.7–4.9, SPIRIT)
- **Agent abstraction:** `AgentRunner` interface — first-class. v1 has only `ClaudeRunner` (calls `claude -p`), but never hardcode below the abstraction. (PRD §4.10)
- **Autonomy:** L1 auto-merge with confidence labelling. All produced Insights publish as `proposed`. No staging review queue. Multi-pass verification handles raw output. (PRD §7, §12)
- **Live discovery:** first-class use case. Lecturer dispatches agent live; SSE stream to projector; student attribution on fresh findings. (PRD §11.8, SPIRIT)
- **v0.1 slice:** read-only viewer + markdown importer only. No agents yet. Validates schema on real data before agents depend on it. (PRD §26)
- **Phases:** v0.1 read-only → v0.2 single-harness vertical → v0.3 all harnesses + cron → v0.4 Live Studio + abstract → v0.5 multi-pass + confidence UI → v0.6 engagement → v0.7 ask-why → v1.0 lens scoring + doc gen. (PRD §24)

---

## 5. What's next

The lead agent has finished foundational docs and **paused for owner review** before any code-writing subagent is dispatched.

After owner review and any adjustments, the next steps are:

1. **Owner review of foundational docs** (SPIRIT, PRD v2, WHY graph, AGENTS, README). Major-direction adjustments happen here, before code.
2. **Lead agent dispatches v0.1 subagent tasks** per `DELEGATION-PLAN.md`. The plan decomposes v0.1 into ~5 parallel-friendly units, each with a deliverable, acceptance criteria, and a slice of the WHY graph it owns.
3. **Subagents return implementation + tests + WHY graph anchors filled in** (planned anchors in `why-graph.xml` get matched by real `START_*` markers in code).
4. **Lead agent reviews + integrates + runs validators** (anchor validator, type checks, tests). Reports back to owner.
5. **Owner runs the v0.1 app locally**, gives feedback, decides whether to proceed to v0.2 or iterate on v0.1.

---

## 6. Open questions / known gaps

- **Migration data scope.** ~~Mapping not pre-specified.~~ **Resolved 2026-04-25 alignment pass:** see PRD §26.1.1 and §26.1.2 for the explicit field-by-field translation, including the MiniMax CLI ecosystem-object exception.
- **Initial seed PromptTemplates** for the 6 AgentJob types (`discover`/`verify`/`abstract`/`engagement`/`refresh`/`explain`). Not in v0.1 (no jobs yet). Will be drafted in v0.2 when first job lands. Templates are versioned entities — first version is OK to be rough.
- **`first_observed_by` identity model.** PRD v2 defaults this to a free-text handle (no auth, no user table). Open to revisit if engagement features in v0.6 need more.
- **Anchor validator policy on PLANNED state.** **Resolved 2026-04-25 alignment pass:** validator skips anchors inside `MODULE_*` nodes with `STATE="PLANNED"`. The graph plans more than the code implements at any moment; `STATE` is the watershed. Validator only fails when an anchor is referenced from a node with `STATE="STARTED"` or `STATE="DONE"` and the anchor is missing from source (or a `STATE="PLANNED"` node has been left STARTED-without-cleanup). Documented in the validator script's docstring when it lands as part of v0.1 Task E.
- **Broken absolute paths in `harness-architecture/`** (7 known references to old `D:/ai/harness-architecture/` location, listed by an exploration subagent earlier). Not blocking — fix as a separate cleanup pass when convenient.
- **Sequencing of orchestration vs v0.1 dispatch (open, NEEDS OWNER DECISION).** PRD §27 names the long-haul orchestration concern and locks design constraints, but deliberately does not scaffold. Two reasonable paths, owner picks:
  - **(A) Build orchestrator first.** Add a Task F (design + scaffold `orchestration/`, build `orchestrate.py` + plan format + scheduled-task setup), then dispatch v0.1 (Tasks A–E) *under* the new orchestrator from the start. Trade-off: delays v0.1 dispatch by ~1-2 days of subagent work; pays back as soon as A–E start running, since wake-up across rate windows is automated. Also: dogfoods immediately. Risk: orchestrator design is informed by *imagined* needs rather than real dispatch experience.
  - **(B) Dispatch v0.1 manually first; build orchestrator alongside as Task F using v0.1 hand-dispatch as empirical input.** Trade-off: matches AGENTS.md §7 (Explore → Execute) — v0.1's 5 hand-dispatches *are* the explore. Plan format and rate-limit detection are designed against actual observed signals (real partial completions, real window hits) instead of guesses. Risk: lead agent has to hand-shepherd v0.1, including the rate-window awkwardness this whole exercise is trying to solve.
  - Lead agent's recommendation: **(B)**, per advisor reasoning — but the orchestrator is genuinely useful from the start, and (A) is defensible if owner wants to dogfood the long-haul pattern from day one. Either path requires its own design checkpoint *before* code lands; this open question is just about which work item lands next.

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
