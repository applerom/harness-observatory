# PRD — Harness Observatory

> **Status:** Draft v2 — interview-locked
> **Date:** 2026-04-25
> **Owner:** Roman + lead agent
> **Project type:** local-first single-user research, comparison, and teaching application

---

## 1. Purpose

This project evolves from a Markdown research meta-repo (`harness-architecture/`) into a database-first application for studying, comparing, and teaching AI coding harnesses and related ecosystem objects.

The application must preserve the spirit of the source project:

- insight-first, evidence-backed (per §4.8 — code is always available under "Show the proof", but never the default frame)
- comparative, not vendor-marketing-driven
- useful for instructors and researchers
- focused not only on feature inventory, but on insights, trade-offs, and real engineering problems
- capable of tracking historical change when that history matters for teaching or practical use

In addition, the v2 application adds a new engine: **agent orchestration**. Comparison views are the dashboard; scheduled and interactive agent jobs are what keeps them alive and honest.

The application is not being designed for backward compatibility with the current Markdown canon. The owner explicitly allows a full DB-first transition. Existing Markdown is imported into the DB and then archived; it is not a dual source of truth.

---

## 2. Problem Statement

The current Markdown-only project already solves real educational and research tasks, but its structure is now under strain:

- the number of harnesses keeps growing
- the number of comparison parameters keeps growing
- many important differences are dynamic product features, not stable static topics
- harnesses change quickly, so old material becomes partially outdated faster than humans can manually update it
- single-pass agent research misses things — what one agent pass overlooks, a second pass with fresh attention often catches
- students during live lectures catch the instructor with outdated information, because the refresh cycle is manual and slow
- useful teaching insights can become historically true but currently absent
- it is increasingly hard to compare, filter, visualize, and refresh this material from text files alone

The result is friction in four areas:

1. comparison at scale
2. historical tracking of observations and changes
3. refresh and monitoring workflows
4. lecturer-oriented retrieval of teaching hooks and insights

---

## 3. Vision

Create a local-first application that acts as both:

- a **research workbench and orchestration engine** for the owner and agents
- a **reference and lecturer system** for comparison, analysis, and teaching preparation

The application's primary engine is **agent orchestration**: scheduled and interactive agent jobs discover, verify, abstract, and explain findings. The comparison matrix, dossiers, and insight library are the dashboard over that orchestrated work.

The application should let the team:

- track harnesses, topics, features, plugins, extension systems, agent tools, and related ecosystem objects
- compare them through matrices, dossiers, timelines, and lenses
- store evidence as reusable atomic facts, always available under every Insight
- preserve historically useful observations without pretending they are still current
- dispatch agent jobs manually (button) or on schedule (cron), using any configured AgentRunner
- stream live agent output to a projector during teaching sessions
- generate documentation and comparative artifacts from the database

---

## 4. Product Principles

### 4.1 DB-first

The database is the source of truth.

- structured data lives in the DB
- generated docs, matrices, reports, and exports are derived artifacts
- old Markdown is not canonical after migration

### 4.2 Insight-first, not table-only

The product is not only a feature matrix. It must preserve:

- surprising implementation details
- teaching hooks
- revision notes
- historical context
- evidence quality

### 4.3 Comparative, not monographic

A harness profile is important, but comparison is a first-class use case.

### 4.4 Historical only where useful

The system does not need perfect archival chronology everywhere.

It must support historical statements when they matter for:

- teaching
- version-specific recommendations
- explaining why a previous insight was once true
- distinguishing "removed", "changed", and "absent by design"

### 4.5 Local-first simplicity

The first version is single-user and local.

- no auth
- no roles
- no multi-user workflows
- no heavy security model

The architecture may later support self-hosting, but that is not a v1 requirement.

### 4.6 Mixed evidence model

Open-source and closed products both participate fully in comparison.

- open-source gets a meaningful explicit advantage via inspectability and auditability
- open-source products are primarily tracked via upstream code and git plus official docs
- closed products are tracked only via official documentation and official product surfaces

### 4.7 Popular over optimal

Stack choices are biased toward popular, well-understood tools (Python + FastAPI + SQLite + HTMX, with React and Postgres as later upgrade paths, GitHub Actions for CI). This is not accidental — harness-observatory is itself teaching material. It demonstrates how to build an application per the agent1st protocol. Students must be able to fork it, understand every decision, and improve it. A clever bespoke stack would undermine that goal. "Why did you choose this?" must have a short, satisfying answer.

### 4.8 Three-stage learner journey

The UI and data model do not try to remove code, but do not center it either. Insight is the primary artifact. EvidenceItem is the proof underneath — always present, always in one click, collapsed by default. This structure supports a gradual transition from code-thinking to agent-thinking without forcing it.

Three stages:

- **Stage 1 — Code-comfortable.** Student reads the Insight, then clicks "Show the proof" to check the `file:line` citation. After a dozen cells, notices the Insight already said the same thing, shorter and clearer. Clicks less.
- **Stage 2 — Agent-first, code-second.** Relies on the Insight by default, expands EvidenceItem only for verification or precision.
- **Stage 3 — Agent-first.** Expands code only in rare cases — debugging a specific location, writing a new harness runner.

EvidenceItem is never removed from the system. It is always required under every Insight. It is secondary in the UI (collapsed), not secondary in importance.

The button is named "Show the proof", not "Show the code." This is a deliberate semantic shift: Insight = claim, EvidenceItem = its evidence — not "code = truth, agent = wrapper."

### 4.9 Agent fallibility as pedagogy

The system does not hide that agents are probabilistic and make mistakes. It makes their reasoning, revisions, and disagreements visible.

- All Insights are visible as soon as produced, marked with their confidence status (`proposed`, `corroborated`, `disputed`, `human-verified`, `corrected`)
- Inter-pass disagreements are displayed, not smoothed over
- Every Insight carries an "Ask the agent why" button — dispatches a short `explain` job; the agent comments on its own reasoning
- Live discovery sessions run unfiltered — wrong turns and overconfident wrong answers are part of the content, not embarrassments to hide

The design principle: engineer for **honest** agent output and the human's ability to interpret it — not for the illusion of perfect agent output. Filtering agent mistakes before students see them creates fragile trust that breaks at first contact with a real agent in a real task.

### 4.10 Agent-runner agnosticism

All agent invocations go through an `AgentRunner` interface. The system orchestrates agents, not a specific CLI.

Early implementations include `ClaudeRunner` and `CodexRunner`, both using local CLI subprocesses rather than direct API SDKs. `AgentJob.runner_name` is a first-class config field from day one.

Semantic rule: **target** and **runner** are different concepts. A target is what the job studies (`target_kind="Harness"`, `target_id=OpenCode`). A runner is the agent implementation doing the work (`CodexRunner`, `ClaudeRunner`, later `OpenCodeRunner`). "Refresh OpenCode with CodexRunner" means Codex studies OpenCode; it does not mean OpenCode launches Codex.

This enables:

- comparing the same research task run with different agents ("refresh topic X with ClaudeRunner AND with OpenCodeRunner — compare what each found")
- meta-dogfooding at level 3: the application that studies agents can call any agent, making it a tool for studying how different agents solve the same task
- students writing their own `AgentRunner` for their harness or bot and plugging it in — a concrete teaching exercise

Concrete CLI commands must never be hardcoded below the `AgentRunner` abstraction boundary. Each runner owns its own subprocess command.

### 4.11 Semantic runtime tracing for agents

The observatory treats runtime logs as future agent context, not only as human debug output. A job should leave enough structured trace for a later agent to answer:

- what semantic step was happening;
- which WHY/module anchor the step belongs to;
- what was expected;
- what actually happened;
- whether the issue was target data, runner dependency, parser logic, UI, or orchestration.

This is deliberately different from ordinary "print a line" logging. The trace is an agent-readable learning surface. It should reduce future debugging tokens by making failure shape visible near the failure, instead of forcing the next agent to reconstruct intent from code and raw stdout.

The first v0.2c slice is small: write append-only semantic events for refresh jobs into `live-sessions/semantic-events.jsonl`, mirror critical failures into the per-job raw log, and show a compact per-job trace on the Job Dashboard detail page. Later versions may promote these events into a DB table if the JSONL trace proves useful.

---

## 5. Users and Primary Jobs

### 5.1 Primary user: owner and lead instructor

Jobs:

- compare harnesses quickly
- prepare explanations and teaching examples
- track what changed and what became outdated
- retrieve interesting insights by topic
- decide which harness or version to show or recommend
- dispatch live discovery sessions during lectures
- curate agent-produced Insights (promote, dispute, correct)

### 5.2 Secondary user: agent maintainer and research agent

Jobs:

- ingest observations and produce Insights
- attach evidence
- mark stale items
- create revision notes
- run verification passes on existing Insights
- maintain comparison coverage

### 5.3 Secondary user: lecturer and reference consumer

Jobs:

- look up differences between harnesses
- find concise explanations and evidence-backed talking points
- see which claims are current vs historical
- run a live discovery session during teaching and stream agent output to the projector
- claim a new finding for a student observer during live sessions

---

## 6. Product Modes

The system has two primary modes.

### 6.1 Workbench Mode

For the owner and agents.

Core behaviors:

- dispatch and monitor agent jobs
- ingest and curate observations (promote, demote, dispute)
- review evidence
- track refresh status
- create revision notes
- maintain comparison coverage
- manage cron schedule

### 6.2 Reference and Lecturer Mode

For explanation, comparison, and preparation.

Core behaviors:

- matrix comparison with confidence bands
- harness dossiers
- topic and feature dossiers
- insight retrieval and filtering
- historical explanations
- lens-based scoring
- live agent studio for teaching sessions

Note: This is not a student-only presentation mode. It is primarily for the owner and other instructors and researchers.

---

## 7. Core Information Model

The application uses a multi-entity model. Insight is the **primary deliverable** of every research agent job. EvidenceItem is the required proof under every Insight.

### 7.1 First-class entities

- `Harness`
- `Topic`
- `Feature`
- `EcosystemObject`
- `EvidenceItem`
- `Insight`
- `ObservationReview`
- `RevisionNote`
- `ComparisonCell`
- `Lens`
- `Score`
- `Source`
- `DocumentArtifact`
- `AgentJob`
- `PromptTemplate`
- `MediaAttachment`

### 7.2 Entity intent

#### Harness

A primary agentic tool or coding harness under study.

Examples:

- OpenCode
- Codex CLI
- Gemini CLI
- Claude Code
- Qwen-Code
- Copilot Chat
- Pi
- Cline

More harnesses are added as the canon grows. No count is baked into file names or section titles.

#### Topic

A comparatively stable axis of comparison.

Examples:

- agent loop
- prompt system
- instruction files
- file editing
- multi-agent
- memory
- sandboxing
- hooks and events

#### Feature

A dynamic product capability that may appear, disappear, or migrate across tools.

Examples:

- Telegram integration
- marketplace install flow
- web search
- remote dispatch
- voice mode
- image input
- plan mode

#### EcosystemObject

A related non-harness object linked to the harness ecosystem.

Examples:

- plugin
- marketplace entry
- extension API
- agent tool
- protocol
- provider integration

Harness remains central in v1, but the data model must support future growth toward a wider ecosystem graph.

#### EvidenceItem

Atomic fact unit. The proof layer under every Insight.

Fields include:

- claim summary
- evidence class
- source type
- source location
- exact citation or paraphrased note
- `code_snippet` — auto-pulled from `file:line` at evidence creation, stored in DB to survive upstream changes (historical accuracy)
- `code_snippet_pulled_at` — timestamp of pull
- `verification_passes` — count of agent passes that have checked this item
- `verifier_agents` — JSON array of which agents have verified
- confidence
- related entities
- observed time range
- reviewer

#### Insight

The **primary deliverable** of every research agent job. A pedagogical or analytical finding.

Fields:

- `id`
- `short_title`
- `body` — the concise formulation
- `why_it_matters`
- `teaching_value`
- `lecturer_note`
- `format`: `text` | `mermaid_diagram` | `ascii_art` | `image_attachment` | `code_snippet`
- `audience`: `student-introductory` | `student-advanced` | `lecturer-only` | `developer-deep-dive`
- `engagement_hook` — optional short copy for the "А-АХ!" moment
- `joke_or_telegram_seed` — optional engagement copy for publication
- `status`: `proposed` (1 pass) | `corroborated` (2+ passes agree) | `disputed` (passes disagree) | `human-verified` (owner confirmed) | `historical` | `corrected` (agent self-corrected, old version in revisions)
- `confidence_band` — derived from status + verification_passes count
- `agent_authored_at` — timestamp
- `agent_model` — which model produced this Insight
- `agent_runner` — which AgentRunner produced this Insight
- `first_observed_by` — nullable free-text handle; for student attribution in live discovery sessions (v1 has no user accounts — this is a name or handle, not a FK to a user record)
- `revisions` — edit history (agent or human revisions, old versions preserved)
- linked evidence items
- related harnesses, topics, features

#### ObservationReview

A concrete review event. The core historical unit.

Records:

- when something was reviewed
- by whom (agent or human)
- against which source snapshot, version, commit, or release
- what changed
- what evidence was added or updated
- what cells or insights were affected

#### RevisionNote

A pedagogically useful historical annotation.

Examples:

- "This was true until version X"
- "Removed after commit Y"
- "Good teaching example, but no longer current"
- "Absent today; used in spring 2026 lectures"

#### ComparisonCell

Structured outcome for a given subject/object axis.

Examples:

- Harness × Topic
- Harness × Feature
- Harness × Lens criterion

Possible states:

- present
- absent
- partial
- unknown
- historical
- absent by design
- unverified

Extended fields (v2):

- `aggregated_confidence_band` — derived from the Insights in this cell
- `inter_pass_disagreement` — boolean flag; triggers visual indicator in matrix

#### Lens

A scoring or interpretation frame.

Examples:

- research lens
- lecturer lens
- practical selection lens
- ecosystem lens

#### Score

Lens-based calculated or curated score. No universal single winner score exists in the system.

#### AgentJob

Every agent invocation is a Job. Jobs are triggered by cron schedule, by manual button, by live dispatch, or chained from a parent job. A Job is the audit trail for every piece of agent-produced content.

Fields:

- `id`
- `created_at`
- `started_at`
- `finished_at`
- `type` — one of six types: `discover` | `verify` | `abstract` | `engagement` | `refresh` | `explain`
- `target_kind` — the entity type the job targets (e.g., `Harness`, `Topic`, `Insight`)
- `target_id` — FK to the target entity
- `prompt_template_id` — FK to `PromptTemplate`
- `model` — model name/version used
- `runner_name` — which AgentRunner implementation (e.g., `ClaudeRunner`)
- `runner_version` — version of the runner
- `trigger` — `cron` | `manual` | `live` | `chained`
- `parent_job_id` — FK self, nullable; for chained job DAGs
- `status` — `queued` | `running` | `done` | `failed` | `timeout`
- `stdout_log_path` — path to flat raw log file
- `produced_artifact_ids` — JSON array of FKs to produced Insights or EvidenceItems
- `error_message` — nullable
- `cost_estimate` — nullable estimated token or compute cost

**Six job types:**

- `discover` — find new Insights in a harness or topic not currently in the DB
- `verify` — re-run a previous claim against current upstream; updates `verification_passes`, may change status to `corroborated` or `disputed`
- `abstract` — produce a higher-level diagram, ascii art, or mermaid summary from a set of EvidenceItems
- `engagement` — produce `engagement_hook`, `joke_or_telegram_seed`, or audience-specific formulations from existing Insights
- `refresh` — full re-sweep of a harness or topic (may chain discover + verify)
- `explain` — triggered by "Ask the agent why" button; agent explains its own reasoning for a specific Insight

#### PromptTemplate

Versioned prompt templates per AgentJob type.

Fields:

- `id`
- `name`
- `type` — matches AgentJob.type
- `version`
- `body` — the prompt text
- `expected_artifact_kind` — what kind of artifact this template should produce
- `created_at`
- `notes` — why this version exists, what changed from prior version

#### MediaAttachment

For Insights and EvidenceItems.

Fields:

- `id`
- `kind` — `image` | `asciicast` | `video` | `external_url`
- `path_or_url`
- `caption`
- `attached_to_kind` — `Insight` or `EvidenceItem`
- `attached_to_id`

### 7.3 Autonomy model

**L1 auto-merge with confidence labelling.**

All job types publish results directly to the DB as `proposed` Insights and EvidenceItems — no staging queue, no approval gate before publication. Confidence labels surface the raw state transparently. Multi-pass verification handles most concerns automatically: 3 passes agree → status becomes `corroborated`. The owner curates after the fact via promote, demote, and dispute actions in the UI. There is one uniform autonomy mode — simpler than per-type rules, and consistent with §4.9 (agent fallibility as pedagogy).

The Curation Queue (§11.7) is a **curation surface**, not an approval gate. It surfaces Insights that are `proposed` with low pass count, `disputed`, or stale by time since last refresh. It does not block publication.

### 7.4 Live discovery

The live discovery flow is a first-class use case, not an edge case:

1. Lecturer opens Live Agent Studio (§11.8) — projector-optimized surface
2. Dispatcher form: select harness, enter task (e.g., "find something in OpenCode from the last 7 days not in docs")
3. Agent job is dispatched; `stdout` streams via SSE to the projector in real time
4. If a genuinely new finding appears, any student-observer can "claim" it — their name or handle goes into `Insight.first_observed_by`
5. System generates a `telegram_seed` from the `engagement` job type
6. Student publishes first — this has happened in the owner's real teaching practice, and the architecture must make it fast and easy, not rare

**LiveSession entity is NOT in v1.** Live agent output streams via SSE during runs. Final Insights and EvidenceItems are persisted normally. Raw stdout is optionally written to `./live-sessions/<timestamp>-<harness>.log` flat file. No DB table for sessions, no replay UI. Phase 2+ if demand emerges.

---

## 8. Topics vs Features

This distinction is explicit and required.

### Topic

- comparatively stable
- structural
- useful for understanding the class of systems
- not expected to appear or disappear rapidly

### Feature

- dynamic
- product-level
- may spread across competitors
- may become obsolete or disappear
- often tracked through refresh cycles

This distinction is foundational to the product and must appear in both data model and UI.

---

## 9. Sources and Evidence Policy

### 9.1 Open-source products

Primary sources:

- upstream repositories
- commits
- tags
- releases
- file paths and code locations
- official documentation

### 9.2 Closed products

Primary sources:

- official documentation only
- official release notes
- official product pages
- official marketplace surfaces

No unofficial community rumor source should be treated as canonical evidence for closed products.

### 9.3 Documentation quality as a parameter

The system must support comparison of:

- documentation quality
- documentation completeness
- documentation freshness
- lag between product change and docs update

This is itself a meaningful comparison dimension.

### 9.4 Open source advantage

Open source must be explicitly represented as a meaningful evaluation parameter.

Suggested criterion family:

- openness
- inspectability
- auditability
- code-level verifiability

This criterion can also receive extra weight in some lenses.

---

## 10. Historical Model

The product uses review-centric history, not archive-for-archive's-sake history.

### 10.1 Main historical unit

`ObservationReview`

This is the event that says:

- what was reviewed
- at what version, commit, release, or date
- what was observed
- whether something changed

Agent-produced revisions are also tracked in `Insight.revisions` — a per-Insight edit history that preserves old versions when the agent self-corrects or a human edits.

### 10.2 Historical goals

Support statements such as:

- "This insight was valid for versions A-B"
- "This feature existed in spring 2026 but is gone now"
- "This lecture example is historical, not current"
- "This behavior changed after release X"

### 10.3 Version precision

Use a normal engineering level of precision:

- exact release, tag, commit, or date when available
- soft observed ranges when exact versioning is unavailable

The system should not require perfect version ranges for every claim.

---

## 11. Main Product Surfaces

### 11.1 Overview Dashboard

Balanced landing view with entry points into:

- comparison matrix
- harness dossiers
- topic dossiers
- feature radar
- insight feed
- curation queue
- job status summary

### 11.2 Comparison Matrix

Primary working surface in reference mode.

Capabilities:

- compare harnesses by topic
- compare harnesses by feature
- filter by current/historical state
- show evidence markers
- show insight markers
- show historical notes inline
- show absent-by-design vs not-investigated
- **show aggregated confidence band per cell** — derived from the Insights in that cell
- click a cell to expand per-pass breakdown showing how many passes agree, how many disagree, and which agents ran
- wide matrix tables show horizontal scroll affordances both above and below the table
- after a cell click updates the expanded detail region, the page scrolls to that region so the user sees the result immediately

### 11.3 Harness Dossier

Profile of one harness:

- identity and classification
- source model
- versions and releases observed
- topic coverage
- feature coverage
- strengths and weaknesses by lens
- insights (each showing: Insight on top, EvidenceItem collapsed below with "Show the proof" button; confidence band always visible; "Ask the agent why" button on every Insight)
- revision history
- manual trigger button for refresh job

### 11.4 Topic Dossier

One stable topic across all harnesses:

- topic definition
- why it matters
- comparative summary
- evidence-backed per-harness states (same Insight/EvidenceItem layout as Harness Dossier)
- teaching-relevant insights
- historical notes where needed

### 11.5 Feature Dossier and Radar

Dynamic feature view:

- feature definition
- first seen
- spread across harnesses
- current state by harness (same Insight/EvidenceItem layout)
- historical transitions
- related insights

### 11.6 Insight Library

Searchable repository of:

- teaching hooks
- surprising findings
- historical but useful examples
- lecturer notes
- filterable by audience, format, status, harness, topic, feature
- confidence band visible per Insight

### 11.7 Curation Queue

Workbench surface for the owner. **Not an approval gate** — Insights are already published when they appear here. This surface surfaces items that warrant attention:

- Insights with `status = proposed` and fewer than 2 verification passes
- Insights with `status = disputed`
- ComparisonCells where inter-pass disagreement flag is set
- Harnesses or topics whose last refresh job ran more than N days ago (staleness threshold, configurable)

Actions available: promote to `corroborated`, mark `human-verified`, mark `disputed`, correct, or demote. All actions are logged in `Insight.revisions`.

### 11.8 Live Agent Studio

Projector-optimized surface for teaching sessions.

Features:

- full-screen SSE stream of agent stdout from the running job
- dispatcher form: select harness or topic, enter task, select AgentRunner, submit
- student-attribution flow: when a new Insight appears, any observer can enter their name/handle → stored in `Insight.first_observed_by`
- generated `telegram_seed` displayed immediately for the attributed student
- minimal chrome — this screen is for projectors, not dashboards

### 11.9 Job Dashboard

Operational surface for job management:

- list of all AgentJobs: running, queued, recent completions, failures
- cron schedule view with next-run times
- manual trigger forms for all six job types
- chained-job DAG view for parent/child job chains
- link to raw stdout log for any job
- compact semantic trace for any job that has structured runtime events
- cost estimate display where available

---

## 12. Editing and Maintenance Model

V1 is not a full CMS.

### 12.1 Editing in v1

Priority editing surfaces:

- observations and revision notes
- insight cards (promote, demote, dispute, correct — all logged in revisions)
- comparison statuses
- curation queue actions
- source metadata

The editing model follows L1 autonomy (§7.3): agents publish directly, humans curate after.

### 12.2 Lower-priority editing

More structural editing may remain controlled or partial in v1:

- deep schema mutation
- bulk topology changes
- complex lesson authoring

The first success criterion is visibility and comparison, not editing elegance.

---

## 13. Document Generation

Because the system is DB-first, it must generate artifacts from structured data.

Potential generated artifacts:

- comparison reports
- harness summaries
- topic summaries
- feature radar exports
- lecturer briefing notes
- revision digests
- Markdown docs for archival or publication
- engagement seeds and telegram-ready post drafts (from `Insight.joke_or_telegram_seed`)

Generated docs are outputs, not the source of truth.

---

## 14. Automation Strategy

**Orchestration-first.** Cron-based agent jobs are in v1. Manual triggers are UI wrappers over the same `AgentJob` infrastructure — there is no separate "manual mode" vs "automated mode." The infrastructure is identical; only the trigger type differs.

### 14.1 In v1

- APScheduler runs in-process with FastAPI
- cron schedule is configurable per harness or topic
- v0.1 scaffolds AgentRunner as empty interface; v0.2 ships the first working end-to-end job cycle
- v0.3 enables scheduled refresh for all harnesses
- manual trigger buttons in the Harness Dossier and Job Dashboard dispatch the same AgentJob infrastructure

### 14.2 Job types and their role in the automation strategy

All six job types (discover, verify, abstract, engagement, refresh, explain) are part of the automation engine. Cron typically runs `refresh` (which chains discover + verify). Manual buttons can trigger any type. Live Studio dispatches `discover` interactively.

### 14.3 Autonomy posture

The system biases toward assistive automation with transparent output, not silent autonomous truth mutation. All agent-produced content is immediately visible and clearly labeled with its confidence status. The owner is never surprised by invisible changes — but is also not a bottleneck that blocks publication.

---

## 15. Lenses and Scoring

The system supports lens-based scoring only.

There is no universal single ranking.

### 15.1 Initial lenses

Suggested starting lenses:

- `Research`
- `Lecturer`
- `Practical Selection`
- `Ecosystem`

### 15.2 Example criteria families

- inspectability and openness
- evidence quality
- documentation quality
- feature breadth
- stability and maturity
- refreshability
- pedagogical richness
- comparative usefulness

Some lenses may weight inspectability and open source more heavily.

---

## 16. Scope Boundaries

### 16.1 In scope for v1 PRD

- local-first app
- DB-first data model
- harness/topic/feature comparison
- evidence storage
- insight storage (Insight as primary agent deliverable)
- review-centric history and Insight revisions
- revision notes
- matrix + dossier + overview surfaces with confidence bands
- generated docs as outputs
- AgentJob infrastructure with AgentRunner abstraction
- scheduled cron jobs (APScheduler in-process)
- SSE streaming for live agent output
- Live Agent Studio
- Job Dashboard
- Curation Queue (no approval gate — curation surface only)

### 16.2 Out of scope for initial build

- multi-user collaboration
- authentication and permissions
- production-grade security model
- LiveSession DB table and replay UI (Phase 2+)
- full lesson package management as a primary subsystem
- public SaaS deployment
- Docker
- Celery/Redis
- Anthropic SDK or any direct API SDK

---

## 17. Lesson Layer Positioning

Full lesson-package management is not a v1 core requirement.

However, the v1 data model must preserve enough educational structure for later expansion:

- `Insight.engagement_hook` — short copy for the "А-АХ!" moment
- `Insight.joke_or_telegram_seed` — engagement copy for publication
- `Insight.audience` — target audience classification
- `Insight.lecturer_note`
- `Insight.why_it_matters`
- historical teaching notes via RevisionNote

This allows future generation of:

- webinar scripts
- lesson packages
- student companion documents

without making lesson authoring block the first implementation.

---

## 18. Functional Requirements

### 18.1 Data management

The system must allow the user and agents to:

- create and edit harnesses, topics, features
- create and edit evidence items with auto-pulled code snippets
- create and edit insights with full field set (§7.2)
- create observation reviews
- create revision notes
- update comparison cells
- attach sources and version context
- attach media (images, asciicasts) to Insights and EvidenceItems

### 18.2 Comparison

The system must allow:

- matrix comparison by topic and by feature
- filtering by current, historical, and unknown state
- viewing cell explanations with confidence bands
- viewing per-pass verification breakdown per cell
- tracing cells back to evidence and reviews

### 18.3 Historical context

The system must allow:

- viewing what changed
- viewing why an old claim existed
- distinguishing current truth from historical teaching value
- associating observations with versions, commits, and releases where possible
- viewing Insight revision history (agent and human edits)

### 18.4 Insight retrieval

The system must allow:

- searching insights by keyword
- filtering by harness, topic, feature, audience, format, status
- identifying lecturer-worthy material quickly
- finding historical-but-useful teaching examples
- reading confidence band and verification pass count per Insight

### 18.5 Source tracking

The system must allow:

- storing official source links and metadata
- marking evidence type and confidence
- tracking documentation quality and freshness

### 18.6 Artifact generation

The system should support:

- generating Markdown or report artifacts from DB state
- generating topic or harness summaries
- generating lecturer-oriented briefs
- generating engagement seeds from `Insight.joke_or_telegram_seed`

### 18.7 Agent job management

The system must allow:

- dispatching any of the six AgentJob types from the UI
- viewing job status (running, queued, done, failed, timeout)
- viewing cron schedule and next-run times
- streaming live agent stdout via SSE during job runs
- viewing raw stdout log for any completed job
- triggering the "Ask the agent why" explain job from any Insight
- claiming a new finding during a live session (entering name/handle → `first_observed_by`)
- curating Insights in the Curation Queue (promote, dispute, correct, demote)

---

## 19. Non-Functional Requirements

### 19.1 Simplicity

The first version should prefer a simpler local architecture over premature platform complexity. The stack is chosen for student understandability, not benchmarked performance.

### 19.2 Inspectability

Even though the app is DB-first, data should remain inspectable and exportable. SQLite is a single file. The WHY graph (`docs/why-graph.xml`) explains every significant decision.

### 19.3 Evolvability

The schema should be capable of future growth toward:

- additional AgentRunner implementations
- Postgres migration (ORM stays portable via SQLModel)
- broader ecosystem objects
- lesson generation layer
- self-hosted deployment

### 19.4 Explicit uncertainty

The system must model uncertainty directly.

Examples:

- unknown
- not checked
- historical
- absent by design
- official-doc-only
- partially verified
- proposed (1 pass, unverified)
- disputed (passes disagree)

### 19.5 Forkability

The codebase must be legible to a student engineer who wants to fork and extend it. No black boxes. Every architectural decision that is non-obvious has a WHY graph node.

---

## 20. Technical Stack

These choices are locked. They are chosen with bias toward popular, well-understood tools (§4.7).

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.14 | Latest stable CPython line at v0.1 implementation time; agents must verify this against upstream before changing it. |
| Package manager | `uv` | not pip, not poetry |
| Web framework | FastAPI | async, OpenAPI built-in |
| Templates | Jinja2 + HTMX | server-render, no SPA in v1 |
| Client state | Alpine.js | lightweight, optional for small client interactions |
| CSS | Tailwind CSS | utility-first, minimal custom CSS |
| ORM | SQLModel | Pydantic + SQLAlchemy combined |
| DB | SQLite | single file, portable; Postgres upgrade path via ORM |
| Migrations | Alembic | standard SQLAlchemy migration tool |
| Scheduler | APScheduler | in-process with FastAPI; no separate worker process |
| Agent runner | `asyncio.subprocess` calling local runner CLIs | NOT direct LLM SDKs in v1; `ClaudeRunner` owns Claude CLI, `CodexRunner` owns Codex CLI |
| Visual QA | Playwright CLI (`@playwright/test`) | agent-visible screenshots/DOM checks; avoid MCP for routine local UI checks |
| XML (WHY graph) | lxml | parsing and validation |
| Tests | pytest | |
| Lint and format | ruff | not flake8, not black, not isort |

**Explicitly NOT in stack:**

- ❌ Anthropic SDK / OpenAI SDK / any direct LLM API SDK for v1 runner dispatch — no API key management
- ❌ MCP as the default local QA mechanism — prefer CLI tools and progressively loaded skills unless a connector is explicitly needed
- ❌ React / Vue / Svelte in v1 — HTMX server-render is sufficient
- ❌ Postgres in v1 — SQLite for single-user local-first
- ❌ Docker in v1 — local-first, no containerization required
- ❌ Celery / Redis — APScheduler + SQLite job storage is sufficient
- ❌ Any scheduler requiring a separate worker process in v1

---

## 21. Migration Strategy

The current Markdown canon in `harness-architecture/` is the migration input, not a long-term dual source of truth.

### Migration posture

1. Define schema (done via §7)
2. Import existing canonical Markdown from `harness-architecture/topics/*/`, `comparisons/harness-map.md`, `registry/harnesses.md` into DB
3. Mark ambiguous imported items for curation review
4. Generate new derived docs from DB
5. Archive the imported Markdown data under `harness-architecture/legacy-data/`

### What stays in `harness-architecture/`

**Do NOT delete `harness-architecture/` after migration.** The repo stays as:

- `SPIRIT.md`, `AGENTS.md` — operational protocols and project constitution; agents read these, they are not data
- `GUIDE.md` — methodology for research and teaching
- `operations/*.md` — agent workflows and delegation rules

These are knowledge about **how the team works**, not **what the team has found**. They stay as text, readable by agents in future sessions.

Only `topics/`, `comparisons/`, and `lessons/` data migrates into the DB and then gets archived under `harness-architecture/legacy-data/`.

---

## 22. Success Criteria

The first meaningful version is successful if the owner can:

1. Compare multiple harnesses across topics and features in one place
2. See current vs historical truth without confusion
3. Retrieve strong teaching insights quickly
4. Trace important claims back to structured evidence
5. Track revisions without maintaining everything manually in Markdown
6. Generate useful comparative and reference artifacts from the database
7. Dispatch a live discovery session against any harness in under 30 seconds and stream agent output to a projector
8. Add a new harness in under 1 hour from clone to first refresh job (target under 15 minutes after onboarding is polished)
9. Show students agent errors and let them ask "why did the agent say this?" — and receive a useful explanation, not silence

---

## 23. Risks

### 23.1 Turning into a dead spreadsheet

Risk: The system becomes only a matrix and loses the insight-first educational value.

Mitigation: Make `Insight`, `RevisionNote`, and `EvidenceItem` first-class entities. Insight is the primary agent deliverable; the matrix is its summary view.

### 23.2 Overscoping the first implementation

Risk: Trying to build comparison engine, lesson CMS, automation platform, and publication system at once.

Mitigation: Phase the product per §24. v0.1 is read-only viewer; each phase adds one capability slice.

### 23.3 Overfitting to current Markdown structure

Risk: The new system inherits accidental complexity from the repo layout.

Mitigation: Model real entities first, not current folders.

### 23.4 Weak evidence mixing

Risk: Code-backed facts and docs-backed claims blur together.

Mitigation: Track evidence class, source type, and confidence explicitly. `EvidenceItem.code_snippet` is stored at pull time for open-source items; docs-only claims are clearly marked.

### 23.5 Historical confusion

Risk: Users mistake historical teaching examples for current product truth.

Mitigation: Strong labeling for current, historical, and deprecated states. `Insight.status` and `RevisionNote` both carry this.

### 23.6 Agent noise overwhelming curation

Risk: L1 auto-merge floods the DB with `proposed` Insights faster than the owner can curate, degrading trust in the Insight Library.

Mitigation: Multi-pass verification auto-promotes to `corroborated` without human touch. Confidence band in the matrix makes noise visible without requiring immediate action. Curation Queue surfaces only what actually needs attention.

### 23.7 Live demo failure on stage

Risk: A scheduled job or SSE stream fails during a projector session, creating a bad teaching moment.

Mitigation: Job Dashboard shows status before session starts. Manual dispatch always available as fallback. Failure is itself teaching material — "watch how we diagnose a failed agent job" is a valid live lesson.

### 23.8 AgentRunner abstraction eroding

Risk: Developers hardcode runner-specific CLI commands below the `AgentRunner` interface, defeating §4.10 and Level 3 dogfooding.

Mitigation: `AgentRunner` is a defined Protocol from v0.1. Concrete subprocess bodies landed in v0.2a and live only inside runner modules (`ClaudeRunner`, `CodexRunner`, later peers). Code review, the anchor validator script, and grep checks for runner CLI literals enforce that runner-specific invocation does not leak into web, job-service, importer, or script layers.

---

## 24. Implementation Phases

Current phase status (2026-04-26):

- v0.1 is complete locally: importer, schema, read-only dashboard/dossiers/matrix.
- v0.2a is complete locally: OpenCode refresh job spine, selectable Codex/Claude runners, raw logs, Job Dashboard, and Playwright CLI visual QA.
- v0.2b is complete locally: one real OpenCode Codex refresh raw log has been parsed into proposed `Insight` / `EvidenceItem` rows visible in the OpenCode dossier.
- Full v0.2 is functionally complete for the one-harness vertical; remaining v0.2 work, if any, is hardening and UX polish before moving toward v0.3.

### v0.1 — Read-only viewer slice

~3-5 days of subagent work.

- Markdown importer ingests `harness-architecture/registry/harnesses.md`, all `topics/*/`, `comparisons/harness-map.md` into SQLite
- All 8 harnesses + ~11 topics + their evidence cells visible in DB after import
- Web UI surfaces: home dashboard (counts, links), harness list, harness dossier, topic list, topic dossier, comparison matrix (harness × topic, read-only)
- Confidence band fields exist in schema but display as "not yet verified" for all imported data
- **No agent jobs in v0.1.** `AgentRunner` abstraction scaffolded as empty interface; not invoked.
- WHY graph file exists (`docs/why-graph.xml`), starts with USECASE and FEATURE skeletons
- Anchor validator script exists, checks WHY graph anchors resolve (trivial in v0.1 since little code)
- Validates schema against real data before agents depend on it

### v0.2 — One harness vertical with one AgentJob type

- Pick OpenCode (most-covered in canon)
- Add `refresh` AgentJob type
- Implement `AgentRunner` interface and `ClaudeRunner` (calls `claude -p` subprocess)
- Implement `CodexRunner` using `codex exec` so Codex can be used as a runtime runner, not only as the development harness hosting the lead agent
- Manual trigger button on Harness Dossier dispatches a `refresh` job
- Watch one full end-to-end cycle work: trigger → subprocess → parse output → Insights stored → visible in dossier
- Job Dashboard (basic: list of jobs, status, stdout log link)

Implementation sequencing note (2026-04-26): v0.2 was split into smaller feedback slices. v0.2a shipped the durable job spine first: OpenCode refresh button → `AgentJob` lifecycle → selected `AgentRunner` execution → raw log visible in Job Dashboard. v0.2b then parsed the first real raw runner log into proposed `Insight` / `EvidenceItem` rows, intentionally using observed output rather than an invented format.

### v0.3 — All harnesses and cron

- Generalize `refresh` to all 8+ harnesses
- APScheduler in-process; cron schedule configurable per harness
- Job Dashboard shows cron next-run times
- Curation Queue surfaces `proposed` Insights

### v0.4 — Live Agent Studio and abstract job type

- SSE streaming UI for live agent stdout
- Live Agent Studio surface (§11.8) — projector-optimized
- `abstract` job type for diagram and ascii art generation from EvidenceItems
- First live discovery demo possible: lecturer dispatches, students watch, finding claimed

### v0.5 — Multi-pass verification and confidence labels in UI

- `verify` job type
- Confidence band displayed in comparison matrix and all dossiers
- Per-pass UI breakdown on cell click
- `disputed` status visible with inter-pass disagreement indicator

### v0.6 — Engagement layer

- `engagement` job type: generates `engagement_hook`, `joke_or_telegram_seed`
- `first_observed_by` student attribution flow in Live Agent Studio
- Telegram seed displayed on attribution
- Insight Library filterable by `audience` and `format`

### v0.7 — "Ask the agent why" and explain job type

- "Ask the agent why" button on every Insight
- `explain` job type dispatched; output streamed and stored
- Per-Insight explanation available on demand

### v1.0 — Lens scoring, generated docs export, legacy Markdown archived

- Lens-based scoring UI
- Generated Markdown export from DB (comparison reports, harness summaries, lecturer briefs)
- `harness-architecture/legacy-data/` archive complete
- Full feature parity with PRD intent
- Onboarding polished: new harness from clone to first refresh in under 15 minutes

---

## 25. Final Product Statement

Harness Observatory should become:

> a local, database-first comparative research and lecturer-reference system for AI coding harnesses and related ecosystem objects, powered by orchestrated agent jobs, preserving evidence and pedagogically useful history, making agent fallibility visible as a teaching asset, and generating its own documents and comparison artifacts from structured data — while itself serving as a living example of how to build a production application per the agent1st protocol.

---

## 26. v0.1 — First Working Slice: Acceptance Criteria

This section defines concrete acceptance criteria for the v0.1 milestone. v0.1 is the first shippable slice. It proves the schema against real data before any agent job infrastructure is built.

### 26.1 Importer

- Markdown importer runs as a Python module entry: `uv run python -m observatory.importers.canon --source <path-to-harness-architecture>`
- Implementation lives in `src/observatory/importers/canon.py` (note plural `importers`; `import` alone is a Python reserved word and cannot be a module name). The module exposes a `__main__` block parsing `--source`; no `[project.scripts]` entry, no Typer/Click wrapper in v0.1
- A unified `observatory` Typer CLI (`uv run observatory dev | import-canon | migrate | …`) is a candidate scope-add for v0.2; deferred from v0.1 to keep the slice tight and avoid an extra dependency before any subagent code lands
- Re-runnable: importing twice from the same source is idempotent (no duplicate rows; existing rows updated by stable identifier)
- Ambiguous items (could not be cleanly parsed) are logged to `import-ambiguous.log`; script does not silently discard them
- All imported Insights default to `status = proposed`, `confidence_band = unverified`

#### 26.1.1 Source → Entity field mapping

| Source file in `harness-architecture/` | Target entity | Key fields |
|---|---|---|
| `registry/harnesses.md` (table rows) | `Harness` | `name`, `slug`, `upstream_url`, `local_upstream_path`, `language`, `status_note`, `last_review_date` |
| `registry/harnesses.md` (rows marked "agent tool") | `EcosystemObject` (kind=`agent-tool`) | same as Harness — see §26.1.2 |
| `topics/<slug>/topic.md` (front matter + prose) | `Topic` | `name`, `slug`, `definition` (first paragraph), `why_it_matters`, `body_markdown` (raw remaining prose) |
| `topics/<slug>/evidence.md` (per-harness sections) | `EvidenceItem` (one row per harness × topic where citation present) | `harness_id`, `topic_id`, `file_path`, `line_number`, `code_snippet` (pulled from upstream at import time), `claim_summary`, `evidence_class` |
| `topics/<slug>/teaching.md` (hooks + telegram seeds) | `Insight` (audience=`lecturer-only` for hooks; `student-introductory` for general framings) | `title`, `concise_formulation`, `why_it_matters`, `audience`, `engagement_hook`, `joke_or_telegram_seed`, `format=text`, `status=proposed` |
| `comparisons/harness-map.md` (table cells) | `ComparisonCell` | `harness_id`, `topic_id`, `state` (present/absent/partial/unknown — parsed from cell text), `cell_summary` (cell text verbatim) |
| `comparisons/<topic>.md` (deep narrative comparison files) | `Insight` (audience=`developer-deep-dive`) | `title`, `concise_formulation` (first paragraph), `why_it_matters`, `body_markdown`, `audience`, `format=text` |
| `comparisons/investigations/*.md` (case studies) | `Insight` (audience=`developer-deep-dive`, `format=text`) | one Insight per investigation file; `title` from H1, `body_markdown` is the file body |

After import, expected counts (acceptance criterion):
- `SELECT COUNT(*) FROM harness` ≥ 8 (registry-listed harnesses, see §26.1.2 for non-harness rows)
- `SELECT COUNT(*) FROM topic` ≥ 11 (current topic directory count in `harness-architecture/topics/`)
- `SELECT COUNT(*) FROM ecosystem_object WHERE kind='agent-tool'` ≥ 1 (MiniMax CLI at minimum)
- `SELECT COUNT(*) FROM insight` ≥ 30 (rough lower bound across topic teaching files + investigations)
- `SELECT COUNT(*) FROM comparison_cell` ≥ 80 (8 harnesses × 10 well-covered topics)

#### 26.1.2 EcosystemObject exception (MiniMax CLI)

The current `harness-architecture/registry/harnesses.md` registry has rows classified as "agent tool" rather than as a full harness (the project's distinction: harnesses run `while(true)` over a model + tools + prompt; agent tools are component pieces or composable services). MiniMax CLI is the v0.1 known instance.

Importer rule: rows whose registry classification reads "agent tool" (or any non-"harness" classifier) MUST go into the `EcosystemObject` table with `kind` set accordingly, NOT into the `Harness` table. This preserves the ontological distinction even when both row types share most fields. Per PRD §7.2 (`EcosystemObject`), the data model supports this from v0.1 even though most v0.1 surfaces only render Harnesses.

If the importer encounters a registry row whose classifier is unclear, it logs the row to `import-ambiguous.log` and does NOT default-create either entity (avoid silent misclassification — the owner reviews the log and resolves manually before re-running).

### 26.2 Web UI surfaces

All surfaces are read-only in v0.1. No edit forms required except as stubs.

- **Home dashboard:** harness count, topic count, Insight count, link to matrix, link to harness list, link to topic list
- **Harness list:** table of all harnesses with name, source model, status
- **Harness dossier:** identity fields, list of Topics covered, list of Insights (title + status badge), placeholder for "Refresh" button (disabled in v0.1 — no AgentRunner)
- **Topic list:** table of all topics with name, harness coverage count
- **Topic dossier:** topic definition, per-harness ComparisonCell states, list of Insights for this topic
- **Comparison matrix:** harness × topic grid, each cell shows state (present/absent/partial/unknown), confidence band placeholder ("not yet verified" for all v0.1 data)

### 26.3 No agent jobs in v0.1

- `AgentRunner` interface exists in code as an abstract base class with no implementation
- `ClaudeRunner` class exists as a stub (raises `NotImplementedError`)
- `AgentJob` table exists in schema and is migratable, but no jobs are created or dispatched
- "Refresh" button on Harness Dossier exists in HTML but is disabled with tooltip "Agent jobs available from v0.2"

### 26.4 WHY graph and anchor validator

- `docs/why-graph.xml` exists with at minimum: one `USECASE` node per major surface (Comparison Matrix, Harness Dossier, Topic Dossier, Live Agent Studio, Job Dashboard), one `FEATURE` node per entity type
- `scripts/validate_anchors.py` exists and passes with exit code 0 (trivial in v0.1 since all MODULE nodes are still `STATE="PLANNED"` and the validator skips them per the policy in the WHY graph header comment)

### 26.5 Tests

- `pytest` passes with no failures
- At minimum: one test per importer function, one smoke test per web route
- Test coverage is not required to be comprehensive in v0.1, but the test suite must run clean

### 26.6 Dev startup

Canonical commands for v0.1 (no CLI wrapper invented; one `uv run <tool>` pattern):

- `uv run uvicorn observatory.web.app:create_app --factory --reload` starts the server with no errors
- `uv run python -m observatory.importers.canon --source ../harness-architecture` runs the importer with no crashes on the real source data
- `uv run alembic upgrade head` applies all migrations to a fresh SQLite file with no errors
- `uv run pytest` runs all tests
- `uv run python scripts/validate_anchors.py` runs the anchor validator
- `uv run ruff check src/ tests/` lints

A future Typer CLI (`uv run observatory <subcmd>`) would unify these behind one surface and is a probable v0.2 ergonomics improvement; punted from v0.1 because it adds a dependency and a CLI module before any of the things it wraps exist.

---

## 27. Long-Haul Orchestration on Personal Subscriptions

> **Status:** named concern + locked design constraints. Design and scaffolding deferred to a far-future checkpoint per CONTEXT.md "Update 2026-04-25 — interrupt-and-resume runbook + sequencing question closed". This section commits the project to *handling* the problem; it does not yet specify directory layout, file formats, or scripts.

### 27.1 The concern

This project is built and operated on the owner's personal subscriptions: Claude Pro (5-hour rolling usage window) and ChatGPT Plus / Codex Plus (similar 5-hour windows). It is open-source, free, financed personally, and intended to run for many weeks of subagent work — far beyond what one continuous interactive session can cover before hitting a window limit.

A multi-week project under this constraint cannot rely on the lead agent personally clicking "dispatch" on every subagent task. The system needs to keep moving while the owner sleeps, while the rate window resets, and across days when no human is at the keyboard. But it also must not silently burn quota on retries that will fail, and must not lose track of what was *partially* completed when a window closed mid-task.

This is itself a teaching artifact (Level 3 dogfood, §3): "how to run a real multi-week agent project on personal subscriptions" is a lesson students will want, because almost all of them will be in the same constraint.

### 27.2 Design constraints (locked)

Any orchestration mechanism added to this project must satisfy these constraints. Architectures that violate them are out of bounds and should be rejected at proposal time.

**(a) No LLM call in the cron / wake loop.** The wake-up that checks "is there pending work, has the rate window cleared, can I dispatch?" must be pure scripting (filesystem reads, timestamp arithmetic, subprocess exit codes). LLM calls are reserved for the actual subagent work being dispatched. Reason: the wake loop runs frequently (every ~30 minutes for many days) and must not itself consume the quota it is trying to manage.

**(b) Timing-based rate-limit detection first; output-pattern detection only after empirical validation.** When a runner subprocess (e.g., `claude -p`) exits non-zero within an unexpectedly short wall-clock duration, treat it as a probable rate-window hit, mark the work item with state `blocked-rate-limit` plus a runner-specific `unblock_after` timestamp, and back off. Output-string parsing ("rate limit exceeded" etc.) is brittle until the actual limit-hit output has been observed for each runner — designing detection logic on guesses risks both false positives (work stalls on real errors) and false negatives (quota burned on retry loops). The empirical signal is captured the first time a real limit is hit, then layered into the detector as Class A evidence.

**(c) Multi-runner aware.** The mechanism must support per-runner block state from day one (Claude Pro window is independent of Codex Plus window). The runner identity is the key: when ClaudeRunner is blocked, CodexRunner work can still proceed if the plan has any items routed to it.

**(d) Plan as durable artifact, hand-editable.** The work plan (queue of items with state, dependencies, runner assignment, brief) lives as a versioned artifact (likely YAML at first), not an in-memory queue. Owner and lead agent edit it directly between cron firings. Reasons: (1) survives any single process crash; (2) git history shows plan evolution; (3) decouples from the Observatory app's own database (the orchestrator can dispatch work for v0.1 *before* the Observatory app is built); (4) hand-editable means the human can intervene without writing code.

**(e) Lead agent owns plan adjustments; orchestrator owns dispatch and state recording.** Architectural division (matches the (iii) hybrid pattern): an interactive lead agent (Opus session with full context) writes and revises the plan; the cron-driven orchestrator (no LLM) reads the plan, picks the next dispatchable item, runs the subagent, records the result. New items, scope changes, plan revisions happen between cron cycles in a human-in-the-loop session — never inside the cron loop.

**(f) Partial completion is a first-class state.** When a subagent returns work that is incomplete (rate-limited mid-task, returned with explicit blockers, etc.), the item state is `partial` with a `note` field — not silently downgraded to `failed` and not optimistically marked `completed`. Lead agent sees `partial` items on next session and decides: re-dispatch (possibly with a smaller batch), split into smaller items, or escalate to owner. This loop is what eventually informs better batch sizing (a goal §4.7).

**(g) Configurable back-off, not hardcoded "5 hours".** The rate-window duration is a per-runner config value (default 5h for Claude Pro and Codex Plus, but overridable per runner profile). When provider terms change, only config changes — not code.

**(h) Dogfood by default.** The orchestration mechanism, once built, is itself documented as a teaching artifact: a README in the orchestration directory explains the design, the constraints above, and how a student running on their own Pro subscription would use the same pattern for their own multi-week agent project. The first lessons that emerge from operating the orchestrator (real partial completions, real window hits, real plan revisions) become teaching material under `harness-architecture/lessons/`.

### 27.3 Out of scope for §27

This section commits to constraints, not implementation. The following are deliberately *not* decided here and require their own checkpoint:

- Directory layout (`orchestration/` at repo root vs inside `src/observatory/orchestrator/` module vs separate `harness-orchestrator/` repo)
- Exact plan format (YAML schema, top-level fields, item shape)
- Whether to build the orchestrator *before* v0.1 dispatch (delaying dispatch ~1-2 days but running v0.1 under the orchestrator) or *alongside* v0.1 (using v0.1's 5 hand-dispatches as empirical input for orchestrator design — Task F in DELEGATION-PLAN)
- Exactly which runners ship in the first automated orchestrator version. Product-level `ClaudeRunner` and `CodexRunner` already exist in v0.2a, but the future long-haul orchestrator may choose a narrower initial runner set based on empirical rate-window behavior.
- Windows scheduled-task setup script (PowerShell `Register-ScheduledTask` per global CLAUDE.md preference) vs cron on Linux/Mac

### 27.4 What this section *does* commit

Future work on orchestration must:
- live within the constraints of §27.2 above (any deviation requires explicit owner sign-off in the same kind of alignment commit that landed §27 itself)
- treat the constraints as load-bearing decisions worth defending against future "let's just hardcode it" refactors — same posture as §4.10 (AgentRunner agnosticism) and §4.7 (popular over optimal)
- update this section if a constraint is *replaced* by empirical evidence (e.g., when actual `claude -p` rate-limit output is captured, constraint (b) gets a Class A entry; output-pattern detection becomes a usable layer on top of timing)

The mechanism's actual design lives in a future PRD section (likely §28 or a separate `docs/orchestrator.md`) and is dispatched as its own work item only after manual interrupt-and-resume proves insufficient in practice.
