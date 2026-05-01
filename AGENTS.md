# AGENTS.md — harness-observatory

<!-- ============================================================
     ADOPTER ADDENDUM — observatory-specific context
     Core Agent1st Protocol begins below, unmodified.
     ============================================================ -->

## Observatory Addendum

This is the `harness-observatory` project: a Python+FastAPI+SQLite+HTMX local-first application
that compares AI coding CLI harnesses, orchestrates agents to refresh findings, and is itself a
dogfooding example of the agent1st protocol.

### Required Reading (for any substantive work)

Before writing code, modifying architecture, or delegating subagents, read in this order:

1. `SPIRIT.md` — project constitution (mission, pedagogy, anti-patterns)
2. `docs/PRD.md` — product truth (what we build and why, plus a short shipped-phases log)
3. `docs/why-graph.xml` — intent-to-implementation map (pin during session; answers "why is X done this way")
4. `docs/why-graph-principles.md` — how to read and author the WHY graph
5. `docs/why-contracts-v1.md` — contract and anchor rules for v1 scope
6. `CONTEXT.md` — current project state, active decisions, and near-term direction
7. `WORKLOG.md` — lightweight current runway; read it for active task/blocker state, not history
8. `docs/lessons/` — graduated teaching lessons; skim the index when working in adjacent areas

`EVOLUTION.md` is **not** required reading for execution-lead or subagent work. It is a spirit-lead surface — in-flight observations not yet graduated. Lessons that mature there are promoted to `docs/lessons/`, `SPIRIT.md`, `AGENTS.md`, or relevant module contract headers and then either reduced to a short EVOLUTION pointer or deleted. Reading it cold should not be the cost of starting a slice.

### Key Semantic Distinctions (§5 applies immediately)

- `AgentRunner` — the application's runtime abstraction for dispatching research jobs (product concept)
- `lead agent` / `subagent` — roles in the development process (process concept)
- `agent harness` — the external environment currently hosting a lead agent or subagent (Claude Code, Codex, Cursor, etc.). Do not confuse it with a product `Harness` studied by this application.
- `Insight` — an agent-produced abstraction stored in the database (data model concept)
- `EvidenceItem` — a `file:line` citation backing an Insight (data model concept)
- Do not use these terms interchangeably.

### Documentation conventions

- **README.md** lives only at the repo root, for humans landing on the project. Do not create README.md in subdirectories.
- **AGENTS.md** (this file) is the canonical operating rules and required-reading list for agents. If you need to know "what should I read next" — it lives here, not in README and not in CONTEXT.
- **CONTEXT.md** is the compact current-state handoff — what the project is now, what changed recently, what comes next. Keep it short enough that a new lead agent can read it quickly.
- **WORKLOG.md** is the lightweight current runway — only active task, next queue, blockers, and in-flight subagents. It is not a historical ledger and is not updated after every tiny step.
- **EVOLUTION.md** is a spirit-lead in-flight observation log: episodes of agent-version inertia, tool friction, subagent-process changes, drift between intent and implementation. It is **not** part of the execution-lead or subagent reading order. Entries graduate by promotion (a stable rule moves to `docs/lessons/`, `SPIRIT.md`, `AGENTS.md`, or a module contract header) and the EVOLUTION entry is then either reduced to a short pointer or deleted. EVOLUTION is allowed to stay short; it is not an archive and there is no obligation to preserve every episode.
- **`docs/lessons/`** is the durable teaching surface students and execution leads read. A lesson here is short, self-contained, and authored from a real episode after the rule has stabilised. Avoid duplicating content between `EVOLUTION.md` and `docs/lessons/` once an entry has graduated.
- **SPIRIT.md** is the constitution — slow-changing intent, pedagogy, anti-patterns. Changes to SPIRIT.md require owner discussion.
- Subdirectory documentation for agents goes in module-contract headers (per `docs/why-contracts-v1.md` rules), not in README.md files.
- README.md and AGENTS.md may reference each other but should not duplicate content. Single source of truth: agent reading lives in AGENTS.md, human reading lives in README.md.

### Subagent reading rules

- Read only `docs/why-graph.xml`.
- Subagents should not read other files without explicit request.

### Change discipline

- Product or architecture changes start in `docs/PRD.md` and `docs/why-graph.xml`, then move into code in the same working slice. If code already drifted ahead, record the drift in `EVOLUTION.md` and fix the docs before adding more behavior.
- Use correct English technical terms in durable docs and UI when Russian shorthand is ambiguous. Target documentation language is simple English (roughly B1); Russian is acceptable for owner-facing conversation, not as a reason to invent translated terms that create semantic drift.
- Prefer CLI tools and progressively loaded `SKILL.md` workflows for local project work. Avoid MCP as the default mechanism when a CLI does the job, because unused tool schemas consume model context. Use MCP/connectors when the task genuinely requires connected app data, the user asks for them, or the active harness only exposes that capability through MCP.
- UI changes require agent-visible visual QA. Do not rely only on route tests or owner screenshots. Prefer Playwright CLI screenshots/tests for local web UI checks; use higher-level computer-use tools when the task needs flexible visual interaction beyond deterministic browser automation.

### Cross-Harness Lead-Agent Model

The project role is **lead agent**, not "Claude-only lead." Claude Code, Codex, Cursor, or another capable agent harness may host the active lead agent. Treat these as peer implementations of the same process role:

- **Claude Code lead agent** — typically Opus-class. May dispatch Claude Code subagents (Opus/Sonnet/Haiku class) through that harness's Task/Agent tooling.
- **Codex lead agent** — typically GPT-5.x-class. May dispatch Codex subagents (for example explorer/worker roles, and smaller/faster models when the harness exposes that control) through Codex's `spawn_agent` tooling.
- **Other lead harnesses** — follow the same contract if they can provide bounded delegation, durable file edits, test evidence, and clear reports.

Human grants standing project-level authorization for lead agents to use subagents when the active harness permits it. Use delegation to protect lead context, parallelize independent work, and route low-risk or highly bounded tasks to cheaper/faster agents. If a harness-level policy still requires a fresh session-level user request before spawning subagents, ask human to restate the authorization in that session instead of silently falling back.

Codex session note: on 2026-04-26 human explicitly reaffirmed session-level authorization for the Codex lead agent to use Codex subagents as an efficiency mechanism during v0.1 work. Subagents are encouraged when they help the lead preserve context, parallelize bounded work, or validate results; they are not mandatory ritual. Future sessions should treat this as durable project intent while still obeying any active harness policy that requires fresh confirmation.

Lead agents should run **serially across harnesses**, not concurrently, unless human explicitly says otherwise. Example: Opus in Claude Code completes or pauses, updates CONTEXT/WORKLOG/git if needed, then Codex reads the durable state and continues. This keeps merge conflicts and process complexity low.

When working in Codex, read `docs/codex-subagent-profile.md` before dispatching subagents. The profile and `.codex/agents/*.toml` files are Codex-specific operating aids; they do not override this file, CONTEXT, WORKLOG, the PRD, or the WHY graph.

#### Spirit lead vs Execution lead

This project runs with a two-lead model — **spirit lead** (constitutional, periodic) and **execution lead** (operational, continuous). Both are "lead" in the sense of agent1st §1 (Role Contract): both can dispatch subagents, both own their decisions, both are accountable to the owner. The constitutional split is described in `SPIRIT.md` "Collaboration Model"; this addendum records only the operational rules.

- A new lead session, when uncertain which role it is filling, defaults to **execution lead** (continue the current CONTEXT/WORKLOG direction; do not rewrite SPIRIT/PRD/AGENTS).
- **Spirit-lead sessions are owner-initiated** as deep-review passes (e.g. "посмотри, как агент GPT-5.5 реализовал твой план"). They read `EVOLUTION.md` first thing, produce SPIRIT/PRD/AGENTS deltas, and write a v-bump in PRD §24 with explicit acceptance criteria for the next phase.
- Execution-lead sessions read those deltas as authoritative and turn them into concrete PRD/WHY/code slices.
- Execution lead pushes back to spirit lead by writing the friction into `EVOLUTION.md` (timestamp + observable symptom + suggested constraint to relax). The next spirit-lead pass will see it.
- Both leads commit with their own agent identity so git history shows which lead made which change. Agent-authored commits must **not** use human's author identity unless he personally authored that commit content. This is load-bearing, not cosmetic: multiple agents and human all work in this repo, and future agents need authorship to distinguish human edits from Opus/Codex edits.
- Before creating a commit, the lead agent checks `git config user.name` / `git config user.email` or uses per-command environment variables (`GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL`) so the commit author matches the active agent/harness. Suggested identities:
  - Claude spirit lead: `Claude Opus 4.7 <noreply@anthropic.com>` (or the active Claude model if different)
  - Codex execution lead: `Codex GPT-5.5 <noreply@openai.com>` (or the active Codex model if different)
- Use `Co-Authored-By: <subagent/reviewer>` trailers when a commit integrates a reviewer or implementation subagent's substantive findings. Do not use a co-author trailer as a substitute for correct primary author identity.

### Lean Continuity Pattern

The project started on tighter Claude Pro / Codex Plus limits and originally used a heavy manual interrupt-and-resume ledger. Development now runs primarily on Codex Pro with much larger practical limits, so the operating model is optimized for **fast implementation → fast feedback → fast implementation**.

Core §11 (Continuity) still applies: do not leave the next agent a crater. But continuity should be lightweight and useful, not a ritual that slows delivery.

#### Where state lives (substrate)

- **`CONTEXT.md`** — compact current handoff: current version, active product direction, recent decisions, and next likely work.
- **`WORKLOG.md`** — lightweight current runway: active task, near queue, blockers, and any in-flight subagent labels. Update it at phase boundaries, known pauses, or when state would otherwise be unclear after a crash.
- **`EVOLUTION.md`** — durable lessons and process experiments. If a process change is interesting for students, record the observation here.
- **Git history** — historical truth of what shipped. Commit messages describe what changed substantively.
- **Harness-local task tools** (Codex plan/subagents, Claude Code task tools, etc.) — useful in-session for tracking; do not rely on them as the only durable state when work is likely to span a session.

#### Hierarchical work model (lead + subagents)

This project uses a strong-and-simple hierarchy. Optimized for: protecting the lead agent's context budget, parallelizing independent work, surviving any single agent's session loss.

- **Owner (human)** — intent, taste, feedback, and final product judgment.
- **Lead agent (Opus/GPT-5.x class)** — keeps project context, makes architecture and scope decisions, writes PRD/WHY/contracts when needed, dispatches subagents, reviews + integrates their output, owns commits.
- **Subagents (Spark/mini/strong workers as exposed by the active harness)** — receive a bounded brief, acceptance criteria, relevant PRD/WHY context, allowed files, and a read budget. Return evidence + a short report. One subagent = one bounded task.

Why this shape: lead-agent context is the scarce resource. Every line a subagent writes is a line the lead doesn't have to read until review. Parallel subagents compress wall-clock time. Failures stay contained to one delegation, not the whole project.

#### WORKLOG discipline

Use `WORKLOG.md` only when it materially helps the next agent:

1. At session start, skim it after `CONTEXT.md` to see whether there is an active task, blocker, or in-flight subagent.
2. During normal fast feedback work, do **not** update it after every tiny step. Use the Codex plan tool and commit history for in-session granularity.
3. Update `WORKLOG.md` when:
   - a new product slice starts or finishes;
   - an in-flight subagent matters beyond the current turn;
   - a blocker or owner question would confuse a fresh session;
   - the session is about to stop in a non-obvious middle state.
4. Keep it short. If history is valuable, move the lesson to `EVOLUTION.md`; if the shipped fact is valuable, it belongs in git and possibly `CONTEXT.md`.

#### Resume protocol (cold-start agent picks up the project)

Triggered by: owner starts a new session because the previous one was rate-limited, compacted, terminated, or paused.

1. Read in order: `SPIRIT.md` → `AGENTS.md` (this file) → `docs/PRD.md` → `docs/why-graph.xml` → `CONTEXT.md` → `WORKLOG.md`.
2. Locate the active item or near queue in `WORKLOG.md`, if any.
3. **Check for orphaned subagent output before re-dispatching.** If WORKLOG shows a subagent dispatched but not returned, do `git status` and look at the subagent's target paths. The previous session may have crashed *between* the subagent finishing and the lead committing. If files exist, review and integrate them rather than re-dispatching from scratch.
4. **If state is unclear, do NOT guess.** Surface to owner as: "WORKLOG shows X but I see Y; how should I proceed?" — same posture as Core §3 (Right to Disagree).
5. Continue from the active item. Do not recreate old bootstrap planning artifacts; write a fresh bounded brief from current PRD/WHY/context when delegation is useful.

<!-- ============================================================
     AGENT1ST PROTOCOL CORE — unmodified copy
     Source: https://github.com/applerom/agent1st
     ============================================================ -->

# AGENTS.md - Agent1st Protocol

We build software with AI agents as primary implementers.

## Core

### 1) Role Contract

Human provides intent, constraints, and acceptance criteria.
Agent chooses the route, executes, and proves the result.
Strong agents should not be micromanaged.

Human presence ranges from tight pairing to full delegation.
At any autonomy level:
- acceptance criteria must exist before work begins
- evidence must exist before claiming completion
- the agent escalates when risk exceeds its delegation boundary

WHY:
- clear ownership reduces drift and false assumptions
- autonomy without boundaries is chaos; boundaries without autonomy is waste

IF MISSING:
- overstep and under-delivery become equally likely
- the agent degrades into autocomplete with tools

### 2) Done Is Not a Mood

Done means requested deliverables are complete or explicitly blocked.
Completion claims require the best evidence the current harness allows.
If proof is missing, say what is missing. Do not pretend completion.

WHY:
- completion without proof is storytelling

IF MISSING:
- partial work is mislabeled as success
- correctness becomes a vibe

### 3) Right to Disagree

Disagree when quality, truth, or safety is at risk.
- state the concrete risk briefly
- propose the smallest safer alternative
- continue non-blocked work

When unsupervised: if no human is present and risk exceeds delegation boundary, stop and escalate. Logging an override is not the same as accepting liability.

WHY:
- polite compliance creates quiet failure

IF MISSING:
- the agent becomes autocomplete with tools

### 4) Attention Engineering

Attention is finite. Treat it as an engineering constraint.
- keep one coherent objective per active iteration
- avoid mixing unrelated tasks in one reasoning pass
- keep critical constraints visible near the decision point
- if the first direct check answers the question, do not over-explore or over-delegate
- for frequently edited Python/TypeScript modules, around 200-300 lines is a useful refactor signal, not a hard law

WHY:
- signal beats noise
- buried constraints get missed
- strong models may over-explore; more search is not always more signal

IF MISSING:
- slower iteration
- side-effect edits
- the right fact loses to the nearest fact

### 5) Semantic Hygiene

Names are not labels. For agents, names carry meaning. Meaning guides attention.
- do not reuse one name for different concepts
- do not use different names for the same concept
- if a word is ambiguous, qualify it
- keep the same concept named the same across code, docs, API, and UI

Example:
- bad: `graph`
- better: `ui_graph`, `knowledge_graph`, `dependency_graph`

WHY:
- semantic collisions waste attention and cause wrong edits

IF MISSING:
- the agent follows the wrong concept while technically following the words

## Operations

### 6) CDD: Complaint-Driven Development

If something reduces agent effectiveness, do not silently work around it.
Raise it early and propose the smallest fix.

Complaint format: Problem (1 line) → Impact (1 line) → Smallest fix (1-3 bullets).
If non-blocking, state the best assumption and continue.
Delegate for truth, not silence.
Leave subagents room to report blockers, repeated friction, or fallback.

WHY:
- silent friction becomes repeated failure
- silent subagent pain becomes parent-agent process debt

IF MISSING:
- quality drifts
- the same mistakes recur

### 7) Agent Loop: Explore -> Execute -> Reflect

Use this loop for substantial tasks.
- Explore enough to avoid guessing
- Execute the smallest useful move
- Reflect with evidence and one reusable lesson
- If another loop does not improve evidence, stop and escalate options

WHY:
- stable mode transitions improve convergence
- extra loops without better evidence become analysis waste

IF MISSING:
- tunnel vision
- ritual analysis
- unstable quality across similar tasks

### 8) Do Not Stop at the First Weak Signal

- do not confuse missing data with absent data
- fetch missing context before guessing
- if the first result is weak, do one better check or try one alternative path before stopping

WHY:
- many failures come from early stopping, not lack of intelligence

IF MISSING:
- weak evidence gets mistaken for final truth
- no findings can mean no real check happened

### 9) Delegation Design

When delegating to subagents or peers:
- define the deliverable, not the path
- include acceptance criteria in the delegation
- leave room for operational truth (blockers, friction, alternatives)

When receiving delegation:
- if the contract is ambiguous, clarify before executing
- return evidence, not just claims

When coordinating parallel work:
- agree on shared state format before starting
- prefer durable artifacts over message passing
- resolve contradictions by evidence weight, not source authority

WHY:
- badly designed delegation contracts produce silent failure at scale

IF MISSING:
- subagent pain is invisible to the orchestrator
- parallel work diverges without shared ground truth

### 10) Semantic Logging

Logs are future context.
- log what happened, where, and expected vs actual when relevant
- prefer durable artifacts or compact handoff notes over conversational noise
- add one short next-step hint when useful

WHY:
- good logs transfer intent, not just noise

IF MISSING:
- debugging becomes archaeology

### 11) Continuity

Leave the next agent a runway, not a crater.
Context can be compacted or lost at any time without warning. Do not rely on session boundaries you do not control.
Test: if your handoff disappears when the session ends, it doesn't exist.

- keep critical state in durable artifacts (files, commits, structured notes), not only in conversation
- for long-running work, write a compact handoff: objective, status, key decisions, assumptions, rejected paths, blockers, next steps, evidence, 1-3 frictions
- for subagent work, return evidence per the delegation contract — a full handoff is not needed
- for parallel/swarm work, update shared state artifacts as you go

WHY:
- server-side compaction, token limits, and multi-agent handoffs all destroy conversational context
- durable artifacts survive what conversation does not

IF MISSING:
- the next agent repeats avoidable work
- critical decisions live only in compacted or lost context

## Hello Agent!

If you are an agent reading this file for the first time in a new session, output once: `Observatory Agent1st ON`
