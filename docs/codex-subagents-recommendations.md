# Codex Subagent Strategy for `applerom/harness-observatory`

**Prepared for:** the next lead agent working on `harness-observatory`  
**Prepared on:** 2026-04-26  
**Scope:** recommendations for using Codex as a strict hierarchical development harness: one lead/orchestrator agent plus bounded subagents.  
**Status:** advisory handoff, not a project source of truth. The project source of truth remains `SPIRIT.md`, `AGENTS.md`, `CONTEXT.md`, `WORKLOG.md`, `DELEGATION-PLAN.md`, `docs/PRD.md`, and `docs/why-graph.xml`.

---

## 1. Executive recommendation

Use a **small strict hierarchy**, not a broad swarm.

```text
Roman / owner
  ↓
Codex lead / orchestrator: gpt-5.5 + high
  ↓
  ├─ repo explorers / scouts: gpt-5.4-mini + medium, read-only
  ├─ default implementation workers: gpt-5.5 + medium
  ├─ hard implementation workers: gpt-5.5 + high
  ├─ validators: gpt-5.4-mini + medium or gpt-5.5 + low/medium
  └─ reviewers: gpt-5.5 + high, read-only
```

Do **not** use `gpt-5.5 + xhigh` as a permanent lead or normal subagent. Treat `xhigh` as an explicit escalation mode for rare cases: architecture deadlock, difficult root-cause debugging, final high-risk review, or contradiction resolution.

The best default shape for this repository is:

| Role | Recommended model | Reasoning effort | Mode | Main purpose |
|---|---:|---:|---|---|
| Lead / orchestrator | `gpt-5.5` | `high` | main session | Holds full context, scope, architecture, delegation, integration, final decisions. |
| Default coding worker | `gpt-5.5` | `medium` | subagent | Implements bounded slices with tests. |
| Hard coding worker | `gpt-5.5` | `high` | subagent | Handles importer, migrations, cross-module integration, tricky edge cases. |
| Explorer / scout | `gpt-5.4-mini` | `medium` | read-only subagent | Reads files, maps requirements, extracts entities, finds contradictions. |
| Mechanical validator | `gpt-5.4-mini` or `gpt-5.5` | `medium` or `low` | subagent | Runs tests/validators, summarizes failures, usually does not edit. |
| Reviewer | `gpt-5.5` | `high` | read-only subagent | Finds correctness, scope, test, and semantic-contract risks. |
| Rare escalation | `gpt-5.5` | `xhigh` | lead turn or special review | Only when the extra reasoning cost is justified. |

---

## 2. Why this recommendation

### 2.1 OpenAI Codex guidance

OpenAI's current Codex subagent documentation says Codex can use subagents for parallel exploration/implementation/review while reducing main-thread context pollution. If a model and reasoning effort are not pinned, Codex may choose `gpt-5.4-mini` for fast scans or a higher-effort `gpt-5.5` configuration for harder reasoning. The same page recommends starting most Codex tasks with `gpt-5.5` when available, using `gpt-5.4` as rollout/fallback, and using `gpt-5.4-mini` for lighter subagent work.

Source: OpenAI Codex Subagents concept guide  
https://developers.openai.com/codex/concepts/subagents

OpenAI's Codex subagent configuration docs also state that `agents.max_depth` defaults to `1`, which allows direct child agents but avoids deeper recursive fan-out. This is important here: this is a personal-subscription, local-first project, so predictable token usage and bounded delegation matter more than deep agent trees.

Source: OpenAI Codex Subagents configuration guide  
https://developers.openai.com/codex/subagents

OpenAI's GPT-5.5 guide says reasoning effort supports `low`, `medium`, `high`, and `xhigh`; default is `medium`; many workloads perform well with `low`; `none` should be reserved for cases where latency matters more than intelligence.

Source: OpenAI GPT-5.5 model guide  
https://developers.openai.com/api/docs/guides/latest-model

OpenAI's reasoning guide says `gpt-5.5` defaults to `medium`, and describes `medium` as the best starting point for GPT-5.5's balance of quality, reliability, and performance. The deployment guidance recommends `low` for extraction/routing/classification/simple rewriting, `medium` or `high` for diagnosing, planning, comparing options, and reasoning through code, and reserving `xhigh` for cases where evals show the extra latency is worth it.

Sources:  
https://developers.openai.com/api/docs/guides/reasoning  
https://developers.openai.com/api/docs/guides/deployment-checklist

The Codex prompting guide recommends `medium` reasoning as a good all-around interactive coding setting and `high`/`xhigh` for the hardest tasks.

Source: OpenAI Codex prompting guide  
https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide

### 2.2 Repository-specific reasons

`harness-observatory` is currently **pre-v0.1**: foundational docs exist; code has not started. The repository is a local-first FastAPI/SQLite/HTMX application for comparing AI coding CLI harnesses and teaching developers to work with agents by making agent behavior visible.

Repo README:  
https://github.com/applerom/harness-observatory  
https://raw.githubusercontent.com/applerom/harness-observatory/main/README.md

The project already defines a lead/subagent process model. `AGENTS.md` says the lead agent holds full project context, makes architecture/scope decisions, dispatches subagents, reviews/integrates output, and owns commits; subagents receive bounded tasks and return evidence. It also explicitly says lead context is the scarce resource.

Project AGENTS.md:  
https://raw.githubusercontent.com/applerom/harness-observatory/main/AGENTS.md

`WORKLOG.md` and `CONTEXT.md` say implementation has not started yet, the project is awaiting the implementation start signal, and v0.1 work is decomposed into Tasks A-E.

Project state files:  
https://raw.githubusercontent.com/applerom/harness-observatory/main/CONTEXT.md  
https://raw.githubusercontent.com/applerom/harness-observatory/main/WORKLOG.md

`DELEGATION-PLAN.md` defines v0.1 acceptance criteria and task decomposition. v0.1 is a read-only viewer plus markdown importer. It explicitly defers runtime agent execution, cron, Live Studio, Ask-the-agent-why, confidence UI, and related future features.

Project delegation plan:  
https://raw.githubusercontent.com/applerom/harness-observatory/main/DELEGATION-PLAN.md

Therefore, the model strategy should optimize for:

1. preserving lead context;
2. preventing scope drift;
3. keeping local/personal-subscription token usage predictable;
4. separating read-only exploration from write-heavy implementation;
5. making subagent output reviewable and resumable through `WORKLOG.md`.

---

## 3. Final model policy

### 3.1 Lead / orchestrator

Use:

```text
model: gpt-5.5
reasoning effort: high
```

Why:

- The lead has to hold more than code. It must also hold product scope, WHY graph contracts, naming semantics, task ownership, acceptance criteria, and durable handoff discipline.
- `medium` is a good default for implementation, but lead orchestration here is closer to architecture + process control + review.
- `xhigh` is too expensive to keep on constantly under Codex Plus / personal balanced limits.

Lead responsibilities:

- Read the required project files in order.
- Maintain the actual work state in `WORKLOG.md`.
- Decide what to delegate.
- Write subagent briefs.
- Review returned output.
- Integrate changes.
- Run or dispatch validation.
- Commit only after evidence is adequate.
- Surface contradictions or blockers instead of hiding them.

The lead should not normally write production code directly if safe delegation is available. If direct implementation is unavoidable, the lead should record the reason in `WORKLOG.md` / `CONTEXT.md`.

### 3.2 Default implementation worker

Use:

```text
model: gpt-5.5
reasoning effort: medium
```

Why:

- `medium` is the best all-around coding balance.
- Most v0.1 tasks are bounded and have explicit acceptance criteria.
- It is cheaper and faster than `high`, while still strong enough for normal implementation.

Use for:

- FastAPI skeleton;
- SQLModel models after the schema is clarified;
- simple Jinja/HTMX views;
- simple tests;
- command wiring;
- documentation updates tied to implemented behavior.

Do not use for:

- final architecture review;
- tricky importer design;
- unresolved data-model contradictions;
- scope decisions.

### 3.3 Hard implementation worker

Use:

```text
model: gpt-5.5
reasoning effort: high
```

Why:

- Some slices have hidden edge cases and cross-module consequences.
- This project has semantic contracts: `AgentRunner` vs development subagent vs studied harness must not be confused.
- The markdown importer is likely the most error-prone part of v0.1.

Use for:

- markdown importer;
- idempotent import logic;
- parser DTO mapping;
- migrations if model shape is uncertain;
- cross-module integration;
- difficult test failures.

### 3.4 Explorer / scout

Use:

```text
model: gpt-5.4-mini
reasoning effort: medium
sandbox: read-only
```

Why:

- Official OpenAI guidance explicitly points to `gpt-5.4-mini` for faster/lower-cost lighter subagent work.
- Read-heavy repository scans are ideal for a mini model: search, extraction, classification, contradiction finding, source mapping.
- `medium` is the safer balance than `low` when the task involves comparing docs and preserving nuance.

Use for:

- reading `PRD.md` and extracting entity lists;
- reading `DELEGATION-PLAN.md` and mapping task boundaries;
- locating all mentions of `AgentRunner`, `Harness`, `EvidenceItem`, `Insight`;
- checking whether acceptance criteria are reflected in tests;
- scanning for naming collisions and scope drift;
- producing compact reports for the lead.

Use `low` only when the request is pure search/extraction and does not require judgment.

### 3.5 Validator

Use one of:

```text
model: gpt-5.4-mini
reasoning effort: medium
```

or:

```text
model: gpt-5.5
reasoning effort: low/medium
```

Why:

- Running commands and summarizing failures is usually not deep reasoning.
- If the validator must interpret a complex failure and propose a fix, switch to `gpt-5.5 + medium`.
- If it only reports command output, `gpt-5.4-mini + medium` is enough.

Use for:

- `uv run pytest`;
- `uv run python scripts/validate_anchors.py`;
- lint/type checks if added;
- startup smoke test reporting;
- summarizing failure owners.

Default validator rule:

> Do not edit files unless the lead explicitly asks for a fix.

### 3.6 Reviewer

Use:

```text
model: gpt-5.5
reasoning effort: high
sandbox: read-only
```

Why:

- Review is not mechanical. It requires detecting hidden risks, scope drift, false completion, missing tests, and semantic contract violations.
- Review should be separated from implementation to avoid confirmation bias.

Reviewer should check:

- correctness;
- tests;
- acceptance criteria;
- scope drift;
- WHY graph anchor discipline;
- broken project terminology;
- hidden coupling;
- Windows startup commands;
- accidental v0.2/v1 implementation in v0.1.

### 3.7 `xhigh`

Use:

```text
model: gpt-5.5
reasoning effort: xhigh
```

Only for rare escalation.

Appropriate cases:

- repeated failure under `high`;
- architectural contradiction between PRD / WHY graph / delegation plan;
- final high-risk review before a major milestone;
- root-cause debugging where several plausible explanations conflict;
- scope decision with long-term consequences.

Not appropriate:

- routine coding;
- read-only search;
- test running;
- normal validation;
- every lead turn.

---

## 4. Recommended `.codex/config.toml`

This is a starting point, not a mandatory final config.

```toml
model = "gpt-5.5"
model_reasoning_effort = "high"
sandbox_mode = "workspace-write"
approval_policy = "on-request"

[agents]
max_threads = 5
max_depth = 1
```

Rationale:

- `gpt-5.5 + high` keeps the lead strong enough for architecture/process control.
- `max_threads = 5` is a deliberate personal-subscription/local-machine cap with one slot of operational headroom. OpenAI's default may allow more, but this project benefits from lower fan-out and easier review.
- `max_depth = 1` matches OpenAI's default child-agent pattern and prevents recursive delegation from exploding token usage.

---

## 5. Suggested custom Codex agents

### 5.1 `.codex/agents/repo-explorer.toml`

```toml
name = "repo_explorer"
description = "Read-only project explorer for mapping docs, contracts, files, and implementation boundaries."
model = "gpt-5.4-mini"
model_reasoning_effort = "medium"
sandbox_mode = "read-only"

developer_instructions = """
Stay read-only.
Map the real project state from files.
Return concise findings with file paths and exact references.
Do not propose implementation unless the parent asks.
Surface blockers or contradictions explicitly.
Do not hide repeated friction or missing context.
"""
```

### 5.2 `.codex/agents/implementation-worker.toml`

```toml
name = "implementation_worker"
description = "Implementation-focused worker for bounded v0.1 code tasks."
model = "gpt-5.5"
model_reasoning_effort = "medium"
sandbox_mode = "workspace-write"

developer_instructions = """
Implement only the delegated task.
Respect file ownership boundaries.
Make the smallest complete change that satisfies the acceptance criteria.
Add or update tests for changed behavior.
Do not commit.
Return: files changed, validation commands run, results, blockers, and judgment calls.
If the requested result format would hide a blocker or repeated friction, report the blocker explicitly.
"""
```

### 5.3 `.codex/agents/hard-worker.toml`

```toml
name = "hard_worker"
description = "Higher-reasoning worker for error-prone implementation tasks such as importers, migrations, and cross-cutting integration."
model = "gpt-5.5"
model_reasoning_effort = "high"
sandbox_mode = "workspace-write"

developer_instructions = """
Use for tasks with ambiguous mapping, edge cases, or cross-module consequences.
Before editing, state the intended mapping briefly.
Implement within the delegated boundary.
Prefer explicit tests for edge cases.
Do not commit.
Return evidence, validation output, unresolved risks, and any contradiction discovered in project docs.
"""
```

### 5.4 `.codex/agents/reviewer.toml`

```toml
name = "reviewer"
description = "Read-only reviewer focused on correctness, tests, scope control, and Agent1st semantic hygiene."
model = "gpt-5.5"
model_reasoning_effort = "high"
sandbox_mode = "read-only"

developer_instructions = """
Review like a project owner.
Prioritize correctness, missing tests, scope drift, semantic collisions, and broken project contracts.
For each finding, include severity, file/path, concrete evidence, and suggested minimal fix.
Avoid style-only comments unless they hide a real maintainability risk.
Do not edit files.
"""
```

### 5.5 `.codex/agents/validator.toml`

```toml
name = "validator"
description = "Runs and summarizes validation commands without making code changes unless explicitly asked."
model = "gpt-5.4-mini"
model_reasoning_effort = "medium"
sandbox_mode = "workspace-write"

developer_instructions = """
Run requested validation commands.
Summarize failures compactly.
Do not modify files unless the parent explicitly asks for a fix.
Return command, exit code, key failure lines, and likely owner.
"""
```

---

## 6. Mapping to `DELEGATION-PLAN.md` v0.1 tasks

| v0.1 task | Recommended agent | Why |
|---|---|---|
| Task A — Data model + Alembic migrations | `implementation_worker`: `gpt-5.5 + medium`; reviewer: `gpt-5.5 + high` | Central schema work, but bounded if PRD mapping is clear. Needs review because all later work depends on it. |
| Task B — FastAPI app skeleton + Jinja/HTMX layout | `implementation_worker`: `gpt-5.5 + medium` | Normal coding slice with clear startup acceptance criteria. |
| Task C — Markdown importer | scout first: `gpt-5.4-mini + medium`; implementation: `hard_worker`: `gpt-5.5 + high` | Highest edge-case density: table parsing, idempotency, mapping source markdown to DB entities. |
| Task D — Read-only dossier + matrix routes | `implementation_worker`: `gpt-5.5 + medium`; escalate to `high` if integration gets messy | Depends on A/B/C and touches UI + DB. |
| Task E — AgentRunner Protocol + stub `ClaudeRunner` + anchor validator | `implementation_worker`: `gpt-5.5 + medium`; validator-specific parts may use `gpt-5.4-mini + medium` | Mostly bounded, but terminology is risky: runtime `AgentRunner` must not be confused with development subagents. |
| Final v0.1 review | `reviewer`: `gpt-5.5 + high`; optionally lead turn with `xhigh` only if contradictions remain | Review is semantic and architectural, not just syntax. |

Important adjustment:

`DELEGATION-PLAN.md` says Tasks A-C can run in parallel. This handoff recommends a **read-only scout wave first** before write-heavy parallelism. After the lead has clear file ownership and schema boundaries, A/B can run in parallel. Task C can run in parallel too if the DTO contract is clear; otherwise stage it after Task A's model shape is stable.

---

## 7. Recommended first Codex session flow

### Step 1 — Lead cold start

Use this first prompt in Codex:

```text
You are the Codex lead agent for harness-observatory.

Read, in order:
1. SPIRIT.md
2. AGENTS.md
3. CONTEXT.md
4. WORKLOG.md
5. DELEGATION-PLAN.md
6. docs/PRD.md sections relevant to v0.1
7. docs/why-graph.xml

Then produce:
- current project state in 10 bullets max
- v0.1 implementation sequence
- proposed subagent dispatch plan
- any contradictions/blockers
Do not write production code yet.
```

### Step 2 — Read-only scout wave

```text
Spawn three read-only repo_explorer subagents and wait for all results:

1. Schema scout:
   Read PRD sections relevant to v0.1 data model and DELEGATION-PLAN Task A.
   Return the exact entity list, field mapping, relationships, and open schema questions.

2. Web skeleton scout:
   Read DELEGATION-PLAN Task B and current repo layout.
   Return the proposed FastAPI/Jinja/HTMX file plan, startup command, and dependencies.

3. Importer scout:
   Read DELEGATION-PLAN Task C and inspect any available sibling harness-architecture source path if present locally.
   Return importer input shapes, table edge cases, source-to-DB mapping, and parsing risks.

All scouts must remain read-only.
Consolidate their findings into one implementation plan.
Do not edit code yet.
```

### Step 3 — First implementation wave

After the lead consolidates scouts:

```text
Spawn implementation_worker for Task A and implementation_worker for Task B.
Keep file ownership disjoint.
Do not commit from subagents.
Each subagent must return:
- files changed
- tests added/updated
- validation commands run
- command results
- blockers
- judgment calls
```

### Step 4 — Importer implementation

Use `hard_worker` unless the scout report proves the importer is trivial.

```text
Spawn hard_worker for Task C: markdown importer.
Use the approved model/DTO mapping from Task A.
Implement only the importer slice.
Add tests for normal markdown tables, pipe tables, missing fields, non-ASCII text, and idempotent re-import if in scope.
Return files changed, tests, validation output, unresolved risks.
Do not commit.
```

### Step 5 — Review and validation

```text
Spawn reviewer read-only after A/B/C return.
Review for:
- v0.1 acceptance criteria
- scope drift into v0.2+
- terminology collisions: AgentRunner vs subagent vs studied Harness
- missing tests
- broken startup/import commands
- WHY graph anchor consistency
Do not edit files.
```

Then run validator:

```text
Spawn validator.
Run:
- uv run pytest
- uv run python scripts/validate_anchors.py
- any startup smoke test requested by DELEGATION-PLAN
Do not edit files.
Return command, exit code, key failures, likely owner.
```

---

## 8. Rules for subagent briefs

Every subagent brief should contain:

1. **Role** — explorer, implementation worker, hard worker, reviewer, validator.
2. **Allowed files / forbidden files** — prevent accidental overlap.
3. **Task boundary** — one subagent = one bounded task.
4. **Acceptance criteria** — copied from `DELEGATION-PLAN.md` / PRD.
5. **Evidence required** — tests, commands, file paths, limitations.
6. **Blocker escape hatch** — subagent must report blockers even if the requested output format is narrow.
7. **No commit rule** — only lead commits unless Roman explicitly changes that.

Recommended return format:

```text
## Result
<done / partially done / blocked>

## Files changed
- path: what changed

## Validation
- command: exit code + relevant output

## Evidence
- tests added
- acceptance criteria covered

## Blockers / contradictions
- explicit, if any

## Judgment calls
- decisions made inside the delegated boundary

## Recommended next step
- one sentence
```

Do not design subagent prompts that force subagents to hide environment friction, repeated failures, missing context, or contradictions.

---

## 9. Where to use `low` or `none`

### Good use of `low`

Use `low` for:

- pure grep/search;
- listing files;
- extracting headings;
- classifying test failures;
- summarizing command output;
- rewriting short reports;
- converting subagent output into a compact table.

### Avoid `low`

Avoid `low` for:

- schema design;
- migrations;
- importer implementation;
- review;
- architecture decisions;
- WHY graph contract work;
- ambiguous failures.

### Avoid `none` for this project

`none` is generally not a good fit here. The project is small, but the work is semantically dense. Even simple changes can violate naming contracts or scope boundaries. Use `none` only for latency-critical non-coding tasks, and only when correctness risk is low.

---

## 10. GPT-5.4 vs GPT-5.5 policy

Use `gpt-5.5` when correctness, code quality, integration, or review matters.

Use `gpt-5.4` only when:

- GPT-5.5 is not available;
- a workflow is already pinned and stable on 5.4;
- you intentionally choose a cheaper fallback for non-critical work.

Use `gpt-5.4-mini` when:

- work is read-heavy;
- output can be checked by the lead;
- the task is bounded;
- mistakes are cheap;
- parallelism is more valuable than maximum intelligence.

Do not let a mini model own architecture or final correctness.

---

## 11. Project-specific hazards to guard against

1. **Confusing process subagents with product AgentRunner.**  
   `lead agent` / `subagent` are development-process roles. `AgentRunner` is the application's runtime abstraction.

2. **Hardcoding `claude -p` below the abstraction.**  
   v1 may use ClaudeRunner, but the code should preserve runner-agnostic boundaries.

3. **Scope creep past the active phase.**  
   Keep PRD/WHY updated before implementation and make deferred slices explicit instead of smuggling them into a nearby feature.

4. **WORKLOG drift.**  
   `WORKLOG.md` must be updated after meaningful steps and committed with the relevant change.

5. **Over-delegation.**  
   Subagents protect lead context, but they still consume tokens and can produce review load. Prefer 2-4 high-quality subagents over a broad swarm.

6. **Write-heavy parallelism before boundaries are clear.**  
   Run read-only scouts before parallel implementation if file ownership or schema boundaries are uncertain.

7. **Silent failure / fake completion.**  
   If proof is missing, say so. Completion without validation is not completion.

---

## 12. Final operational policy

Default operating posture:

```text
Lead: gpt-5.5 + high
Implementation: gpt-5.5 + medium
Hard implementation: gpt-5.5 + high
Exploration: gpt-5.4-mini + medium
Validation: gpt-5.4-mini + medium, or gpt-5.5 + low/medium
Review: gpt-5.5 + high
Escalation: gpt-5.5 + xhigh only when justified
```

Most important rule:

> Keep the lead agent's context clean. Delegate bounded work, but make the lead own architecture, integration, evidence, and final truth.

Second most important rule:

> Use subagents for contained evidence, not for responsibility laundering. The lead remains accountable for the result.

---

## 13. Source links

OpenAI / Codex:

- Codex subagents concept guide: https://developers.openai.com/codex/concepts/subagents
- Codex subagents configuration guide: https://developers.openai.com/codex/subagents
- Codex config reference: https://developers.openai.com/codex/config-reference
- Codex sample config: https://developers.openai.com/codex/config-sample
- Codex changelog: https://developers.openai.com/codex/changelog
- Codex prompting guide: https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide
- GPT-5.5 latest model guide: https://developers.openai.com/api/docs/guides/latest-model
- Reasoning models guide: https://developers.openai.com/api/docs/guides/reasoning
- API deployment checklist: https://developers.openai.com/api/docs/guides/deployment-checklist
- GPT-5.5 model page: https://developers.openai.com/api/docs/models/gpt-5.5
- GPT-5.4 model page: https://developers.openai.com/api/docs/models/gpt-5.4
- GPT-5.4 mini model page: https://developers.openai.com/api/docs/models/gpt-5.4-mini

Project:

- Repository: https://github.com/applerom/harness-observatory
- README: https://raw.githubusercontent.com/applerom/harness-observatory/main/README.md
- AGENTS.md: https://raw.githubusercontent.com/applerom/harness-observatory/main/AGENTS.md
- CONTEXT.md: https://raw.githubusercontent.com/applerom/harness-observatory/main/CONTEXT.md
- WORKLOG.md: https://raw.githubusercontent.com/applerom/harness-observatory/main/WORKLOG.md
- DELEGATION-PLAN.md: https://raw.githubusercontent.com/applerom/harness-observatory/main/DELEGATION-PLAN.md
- PRD.md: https://raw.githubusercontent.com/applerom/harness-observatory/main/docs/PRD.md
- why-graph.xml: https://raw.githubusercontent.com/applerom/harness-observatory/main/docs/why-graph.xml
