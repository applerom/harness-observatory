# EVOLUTION.md — development trajectory log

> This is the teaching-facing development trajectory log.
>
> `CONTEXT.md` records project decisions and handoff state.
> `WORKLOG.md` records current work in flight.
> `EVOLUTION.md` records lessons learned while building: agent mistakes,
> process friction, tool/version drift, and rule changes that future agents and
> students should understand.

## 2026-04-26 — Live Streaming Must Be End-To-End

Observation:
- The v0.4a Live Agent Studio slice initially had an SSE endpoint and fake-runner
  tests, but concrete `CodexRunner.stream()` / `ClaudeRunner.stream()` still
  delegated to `run()`, which buffered stdout/stderr with `communicate()`.
- A reviewer subagent caught the cross-boundary mismatch: the route was shaped
  like live streaming, but real CLI output would not appear until process exit.
- The same review caught three smaller semantic risks: live cancellation could
  leave `AgentJob.status="running"`, refresh jobs did not persist the exact
  rendered prompt, and a quick `Mark corrected` button implied a real correction
  workflow that did not exist.

Impact:
- Agent-visible UI tests are necessary but not sufficient for runtime truth.
- Product words like "live", "corrected", and "exact prompt" are contracts
  across routes, services, runners, data, and tests.
- Reviewer agents are valuable when the main implementation has passed local
  tests but may still be semantically false.

Action:
- Concrete runner `stream()` methods now launch subprocesses directly and pump
  stdout/stderr incrementally.
- Live stream cancellation marks the job failed and runner stream cleanup kills
  the subprocess.
- Refresh jobs persist `AgentJob.prompt_text` using the same rendered prompt
  passed to `AgentContext`.
- The unsupported `corrected` quick action was removed until a real correction
  flow can capture replacement text and preserve old content.

Teaching extraction:
- This episode is now a reusable lesson:
  `docs/lessons/live-streaming-is-a-contract.md`.

## 2026-04-26 — Worker-Green Is Not Integration-Green

Observation:
- The v0.4b/v0.5/v0.6 product train was split across bounded workers:
  abstract artifacts, verification/confidence, and engagement/Insight Library.
- Each worker returned green local evidence, but a reviewer subagent still found
  five cross-slice semantic problems: live claims were too broad, orphan
  EvidenceItems could receive verification without affecting the Insight,
  verification job artifact IDs mixed entity types, abstract output used a
  drifting `format` vocabulary, and deterministic engagement jobs lacked
  execution timestamps.

Impact:
- Parallel workers are good at their slice. They are not automatically good at
  the product meaning formed between slices.
- Lead integration review must check nouns and contracts, not just tests.
- Reviewer subagents are especially useful after a parallel product train
  because they see the whole dirty workspace without owning any patch.

Action:
- Live first-observer claims now require a live job and an Insight ID present in
  that job's `produced_artifact_ids`.
- Verification links orphan EvidenceItems to the target Insight before deriving
  confidence.
- Verify jobs now store only Insight/Evidence IDs in `produced_artifact_ids`;
  `ObservationReview` remains the typed audit trail for verification pass
  details.
- Abstract artifacts use canonical `format="mermaid_diagram"`.
- Engagement jobs set `created_at`, `started_at`, and `finished_at` together.

Rule added:
- After parallel implementation slices, run a dedicated semantic reviewer before
  commit. Ask it to look for cross-slice vocabulary drift, overly broad routes,
  ambiguous audit fields, and UI claims that are stronger than the underlying
  data contract.

Teaching extraction:
- This episode is now a reusable lesson:
  `docs/lessons/worker-green-is-not-integration-green.md`.

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

Teaching extraction:
- This episode is now a reusable lesson:
  `docs/lessons/runtime-freshness.md`.

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

Teaching extraction:
- This episode is now a reusable lesson:
  `docs/lessons/subagent-orchestration.md`.

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

## 2026-04-26 — Development As Curriculum

Observation:
- Roman explicitly confirmed that real project development episodes should be
  captured as teaching material, not merely as private process notes.
- The project already had Level 2 dogfooding ("we build with agents"), but the
  curriculum extraction rule needed to be explicit.

Impact:
- Future agents should treat process friction, decision changes, and v0.x
  compromises as source material for students.
- Lessons should be short, evidence-backed, and linked to concrete project
  episodes.

Action:
- `SPIRIT.md` now includes "Development as Curriculum".
- `docs/lessons/` now holds extracted short lessons from real development
  episodes.

Rule added:
- Record raw process observations in this file.
- Extract reusable student-facing lessons into `docs/lessons/` when an episode
  teaches a transferable operator habit.

## 2026-04-26 — v0.2a Before Full v0.2

Observation:
- PRD v0.2 says one full end-to-end refresh cycle should eventually create
  visible Insights.
- Doing that in one move would mix three unknowns: real CLI subprocess behavior,
  prompt/output shape, and parser rules for turning freeform output into
  `Insight`/`EvidenceItem` rows.

Decision:
- Ship a smaller v0.2a first: OpenCode refresh button, durable `AgentJob`
  lifecycle, `ClaudeRunner` execution boundary, raw log file, and Job Dashboard.
- Defer parsing raw output into Insights until real logs exist.

Why:
- This preserves the minimum "something real" loop while avoiding a fake parser
  designed around imagined output.
- It also creates teaching material: students can see how an agent-first project
  narrows a milestone without losing the larger intent.

## 2026-04-26 — Target/Runner Semantic Hygiene

Observation:
- Roman asked why an OpenCode dossier launches `ClaudeRunner`.
- The implementation was technically correct (`OpenCode` was the target and
  `ClaudeRunner` was the runtime agent), but the wording made the two roles easy
  to confuse.

Decision:
- UI and docs must explicitly label `Target` and `Runner`.
- `CodexRunner` is added as a second runtime runner so the project can dogfood
  Codex as both development harness and product-level AgentRunner.

Rule added:
- Never write "OpenCode launches ClaudeRunner" style copy. Write "Refresh target
  OpenCode with runner Codex/Claude" or equivalent.

## 2026-04-26 — Visual QA And Current Tooling Checks

Observation:
- Roman found matrix UX issues by eye: wide tables need a top scrollbar, and
  clicking a matrix cell changes a lower detail region that may be off-screen.
- Codex could have missed this if it only ran backend and route tests.
- Roman also flagged that expert knowledge about agent UI tooling ages quickly.

Evidence:
- Official OpenAI computer-use docs checked on 2026-04-26 describe GPT-5.5 with
  the GA `computer` tool for flexible UI operation, while still recommending
  browser automation frameworks such as Playwright or Selenium as the fastest
  path for local browser automation.
- For this project, deterministic local UI QA should use Playwright CLI first.
  MCP/browser connectors remain optional and task-specific, not the default.

Rule added:
- UI changes need agent-visible visual QA, preferably Playwright CLI screenshots
  or tests.
- When model/tool capabilities affect workflow choice, check current primary
  docs before encoding the rule.
  Sources:
  - https://developers.openai.com/api/docs/guides/tools-computer-use
  - https://developers.openai.com/codex/cli

## 2026-04-26 — Lead Agent Over-Execution

Observation:
- Roman noted that the lead agent directly implemented the matrix scrollbar and
  visual QA work.
- The result worked, but part of that work was bounded enough for a subagent
  after the PRD/WHY decision had been made.
- This consumed lead-agent context on implementation details instead of keeping
  the lead focused on orchestration, contracts, and integration.

Nuance:
- Some direct work was reasonable because this was the first Playwright CLI setup
  in the project and the lead needed to establish the pattern.
- After the pattern exists, similar UI polish and test additions should be
  delegated by default.

Rule added:
- Lead agent owns intent, PRD/WHY changes, scope cuts, delegation contracts,
  integration review, and final evidence.
- Bounded implementation tasks should be delegated whenever the active harness
  exposes suitable subagents.
- If the lead implements directly, record why the work was not delegated.

Teaching extraction:
- This episode is now a reusable lesson:
  `docs/lessons/orchestrator-over-execution.md`.

## 2026-04-26 — Runtime Runner CLI Truth Beats Remembered CLI Shape

Observation:
- The first real `CodexRunner` refresh did not produce a useful research log.
- Three operational facts appeared only when the app called the real local CLI:
  stale imported OpenCode paths, Windows `codex` shim launch failure, and Codex
  CLI argument ordering (`--ask-for-approval` is global, not an `exec` option).
- A manual probe also showed local Codex CLI v0.104 rejects the configured
  default `gpt-5.5` model and asks for a newer Codex version, while `gpt-5.4`
  works.

Impact:
- Runner implementations must be tested against the actual local CLI, not only
  against remembered command syntax.
- A failed runtime job can still be useful if it is durable: `AgentJob` status,
  raw log, and error message become evidence for the next fix.

Action:
- `CodexRunner` now resolves Windows-runnable commands, puts global approval
  options before `exec`, and catches launch errors.
- `RefreshJobService` marks unexpected runner exceptions as failed instead of
  leaving jobs stuck in `running`.
- The web route temporarily used `gpt-5.4` for Codex runtime refresh until the
  local Codex CLI could run the desired default model.
- Roman flagged that Codex CLI is itself a project runtime dependency. Codex
  checked npm, found local `@openai/codex` at `0.104.0` and stable latest at
  `0.125.0`, upgraded the local CLI, and verified `codex exec --model gpt-5.5`
  with a no-op prompt.

Rule added:
- Before calling a CLI runner from the app, probe the concrete command form with
  `--help` or a tiny no-op prompt and record any version/model compatibility
  mismatch.
- Runtime runner CLIs are dependencies, not invisible personal tools. Record
  their minimum useful versions and add preflight checks before broadening runs.

## 2026-04-26 — Parser Failure Is A Runtime Boundary Too

Observation:
- v0.2b deliberately parsed the first real raw refresh log instead of inventing
  a format in advance.
- Reviewer feedback showed a second boundary after runner success: parser errors
  can still turn a successful refresh into a web 500 or duplicate partial rows
  on retry if persistence is not atomic.

Action:
- `RefreshJobService` now treats parser failure as a job failure with a durable
  parser error appended to the raw log, rather than leaking an exception to the
  web route.
- Parser persistence is reviewed as part of the same AgentJob lifecycle, not as
  a harmless post-processing detail.

Rule added:
- A job is not only the external CLI call. Every transformation from raw output
  to database artifacts is part of the runtime boundary and needs failure tests.

## 2026-04-26 — Agent-Visible Runtime Tracing

Observation:
- Playwright CLI gave the lead agent eyes for frontend work: it could verify
  scroll affordances and clicked-cell behavior without waiting for Roman's
  manual report.
- The equivalent backend/runtime need is not more freeform logs, but semantic
  traces that say which step and WHY anchor expected what, and what actually
  happened.

Decision:
- Add a v0.2c semantic-event JSONL trace for refresh jobs before expanding to
  more harnesses.
- Keep it small and append-only first; promote to a DB table/UI only after the
  trace proves useful.

Teaching extraction:
- The lesson is not "agents magically see." They see when the harness gives
  them durable, inspectable instruments: screenshots for UI and structured
  semantic events for runtime behavior.

## 2026-04-26 — Parallel Agents Need Isolation, Not Just Warnings

Observation:
- Roman noticed the lead warns subagents that they are not alone in the
  repository.
- That warning is correct, but it is a weak control compared with giving each
  concurrent implementation worker an isolated workspace.
- OpenAI's harness-engineering article describes making the app bootable per
  git worktree so Codex can run one isolated app instance per change.

Decision:
- Keep the current default fan-out modest: 2-3 active subagents for normal work,
  with the configured fifth Codex thread treated as operational headroom.
- Before increasing parallel write-heavy fan-out, add a worktree strategy:
  disjoint worktrees, separate app ports/logs/semantic event files, and an
  integration step owned by the lead.

Rule added:
- "You are not alone in the repo" is a prompt-level guard. Worktrees are the
  stronger architectural guard and should be considered before scaling parallel
  implementation beyond small disjoint slices.

Source:
- https://openai.com/index/harness-engineering/

## 2026-04-26 — Better Agent Visibility Should Increase Autonomy

Observation:
- Roman noticed that after adding Playwright visual QA and semantic runtime
  traces, the lead agent still kept stopping after relatively small slices.
- Some of that was process churn: we were adding the instruments themselves,
  so short checkpoints were useful.
- Once those instruments exist, they should let the lead agent take larger
  product slices, not become a reason to ask for more human confirmation.

Decision:
- Move v0.3 work in larger autonomous chunks: frame the PRD/WHY slice, delegate
  bounded implementation, run tests plus live smoke, inspect semantic traces,
  and report back with evidence.
- Keep Roman informed with short progress notes, but do not stop after every
  small internal step when the next step is clear and reversible.

Rule added:
- Agent visibility tools are autonomy multipliers. If an agent has screenshots,
  semantic traces, tests, and durable logs, it should use them to complete a
  larger verified loop before handing control back.

## 2026-04-26 — Stale Dev Servers Are A Visual QA Finding

Observation:
- The new Playwright harness-dossier check initially failed because the running
  local Uvicorn process was still serving the old OpenCode-only UI.
- Unit tests were already green against the new code, but the browser still saw
  stale runtime state.

Action:
- Restarted the dev server, reran the Playwright CLI check, and kept the visual
  test as a durable regression guard.

Rule added:
- A failing visual smoke after a UI patch is not noise. First ask whether the
  live app is stale, then verify with a fresh server before judging the code.
  The browser view tests the actual development harness, not just templates.

## 2026-04-26 — Schedulers Need Guarded Startup

Observation:
- v0.3b adds in-process APScheduler, which is powerful but risky in an
  agent-run project: a dev server restart could accidentally trigger expensive
  model-backed refresh jobs.
- The product wants scheduled work, but the development harness must stay
  predictable and cheap by default.

Decision:
- Scheduler startup is opt-in through `OBSERVATORY_SCHEDULER_ENABLED`.
- Registration computes and records the next run, but does not call the job
  function immediately.
- Scheduled dispatch uses the same `RefreshJobService` path as manual refresh
  and labels `AgentJob.trigger` as `cron`.

Rule added:
- Cron features should first prove visibility and registration before automatic
  execution. The default local/test posture is "show schedules, do not spend
  model calls."
