# EVOLUTION.md — development trajectory log

> This is the teaching-facing development trajectory log.
>
> `CONTEXT.md` records project decisions and handoff state.
> `WORKLOG.md` records current work in flight.
> `EVOLUTION.md` records lessons learned while building: agent mistakes,
> process friction, tool/version drift, and rule changes that future agents and
> students should understand.

## 2026-04-27 — Commit Attribution Is Operational Context

Observation:
- Roman pointed out that the previous execution flow forgot, after a few commits,
  that agents must commit under their own identities.
- Recent development commits were authored as `Roman Siewko <applerom@gmail.com>`
  even when WORKLOG and commit messages show agent-led implementation.
- In a two-lead project (spirit lead + execution lead) with occasional human
  edits, this is not a cosmetic problem. Authorship is one of the cheapest
  durable signals future agents have for deciding whether a change came from
  Roman, Claude/Opus, Codex, or a subagent-reviewed integration.

Impact:
- Human and agent edits blur together in `git log`.
- Future agents lose a fast way to reason about role, responsibility, and
  likely intent behind a change.
- The two-lead model becomes harder to teach because the repository history
  hides the collaboration it is supposed to demonstrate.

Action:
- `AGENTS.md` now states that agent-authored commits must not use Roman's human
  author identity unless Roman actually authored the commit content.
- `PRD.md` §24 v1.1 now includes commit author identity discipline alongside
  `Co-Authored-By` reviewer/subagent trailers.
- This current pass uses an explicit Codex author/committer identity as the new
  baseline.

Rule added:
- Before committing, an agent checks or overrides Git author/committer identity.
  Co-author trailers credit subagents/reviewers; they do not repair an incorrect
  primary author.

## 2026-04-27 — Matrix Feedback: Overview Surfaces Must Scan First

Observation:
- Roman's first usage-feedback screenshot showed the Comparison Matrix using
  large card-like cells for values that were mostly `present`, `unknown`, and
  `unverified`.
- The old layout technically exposed the state, but it made the user scroll
  horizontally and vertically to learn almost nothing. The surface looked like a
  table but behaved like a set of repeated cards.

Impact:
- Students and lecturers cannot see the field at once, so the Matrix fails as a
  pattern-recognition surface.
- `unverified` repeated in every cell reads like noise rather than useful trust
  calibration.
- Expanded cell detail below the table makes each click feel like losing the
  overview.

Action:
- The Matrix is now treated as a dense scan surface: symbolic cells for state,
  visual confidence styling, compact legend, vertical topic labels, and a
  desktop side detail panel.
- The original proof path is preserved: clicking a cell still opens the Insight
  and EvidenceItem detail.

Rule added:
- Overview surfaces should optimize for shape recognition first and move prose
  into detail panels. If every repeated cell says the same words, the UI should
  probably encode that state visually instead.

## 2026-04-27 — Feedback Speed Still Needs the Agent1st Loop

Observation:
- Roman corrected Codex after the first Matrix-density pass: even feedback UI
  fixes must pass through PRD/task/WHY/delegation, because the lead agent's
  context and judgment are the scarce resource.
- The direct implementation was useful, but it skipped the project's own
  pedagogy: make intent durable, delegate bounded work, then integrate with
  evidence.
- Roman also pointed out a new tactical resource: GPT-5.3-Codex-Spark workers
  appear to have separate practical limits and are very fast, which matters
  during iterative feedback where the first UI attempt may need quick revision.

Impact:
- Direct lead coding can make the product move faster for one turn while making
  the process less teachable and less repeatable for the next turn.
- Without a formal Spark lane, future agents may either ignore a useful fast
  worker class or overuse it for tasks that need stronger reasoning/review.

Action:
- Added `fast_implementation_worker` based on `gpt-5.3-codex-spark` for small,
  reversible feedback-hardening edits.
- Raised Codex thread headroom from 5 to 7, while keeping the policy that thread
  count is headroom, not a default swarm.
- Dispatched the Matrix detail hygiene fix to Spark worker Peirce with a narrow
  write scope while the lead owned PRD/WHY/WORKLOG/EVOLUTION/profile updates.

Rule added:
- Spark workers are for speed on bounded implementation, not for final truth.
  They need explicit acceptance criteria, disjoint write scope, and lead/reviewer
  verification before commit.

## 2026-04-27 — Early Feedback Does Not Want Gold-Plated Review

Observation:
- Roman pointed out that applying strong-agent code review to every early visual
  feedback slice is locally "best practice" but globally wrong for this moment.
- The product has only just reached v1.0-minimal and feedback has started on the
  first of many tabs. Many UI decisions will be thrown away or revised quickly.
- Waiting for expensive review on each small visual iteration makes the owner
  wait longer and burns tokens where the right answer may be "try it, look, and
  revise."

Impact:
- The lead can accidentally optimize for correctness ceremony instead of
  feedback-cycle speed.
- Strong reviewers remain valuable, but only when a slice stabilizes or carries
  real risk.

Action:
- Added `docs/agent-run-ledger.md` to track which agent profiles work well for
  which feedback tasks.
- Policy shift: Spark workers can run simple implementation, validation, server
  restart, and screenshot tasks; the lead reviews product fit and uses strong
  reviewers sparingly.

Rule added:
- In the feedback-hardening phase, optimize for fast reversible evidence. Use
  heavyweight review only for risky/stable checkpoints.

## 2026-04-27 — Curation Buttons Need Reversibility Before Trust

Observation:
- Roman's next screenshot showed the Curation Queue buttons: "Mark verified",
  "Mark disputed", and "Mark historical".
- The user cannot tell what pressing them changes, whether the original agent
  output is deleted, or whether a mistaken click can be undone.

Impact:
- Even a technically safe curation surface feels unsafe if the action model is
  opaque.
- This is an agent-product lesson: humans need reversible control when managing
  uncertain agent output.

Action:
- PRD/WHY now say Curation actions must explain that they change labels only,
  preserve agent output, and provide a visible undo after action.

## 2026-04-27 — Fast Agents Need Small Context Contracts

Observation:
- Roman inspected the live Spark-worker log and saw the worker immediately read
  broad cold-start documentation (`SPIRIT.md`, full PRD, WHY graph, WORKLOG,
  CONTEXT, EVOLUTION) before a small UI/route patch.
- The worker then hit context compaction and repeated local file reads.
- This was not "Spark is bad"; it was a lead-agent prompt design problem. The
  worker followed a project ritual that was useful for a lead session but
  wasteful for a tiny delegated slice.

Impact:
- The speed advantage of a fast agent can disappear if the lead hands it a broad
  context surface.
- Subagent quality is partly orchestration quality: model capability, prompt
  contract, read budget, and acceptance criteria interact.

Action:
- Spark feedback prompts must now include a tiny context packet, exact allowed
  files, and an explicit read budget.
- For tiny implementation slices, Spark should not cold-start-read SPIRIT/PRD/WHY
  unless the delegated task is itself documentation/architecture work.

Rule added:
- Fast subagents get context-budgeted prompts. The lead preserves project
  context; the worker reads only what the worker needs.

## 2026-04-27 — Verified Should Not Feel Lost

Observation:
- After pressing `Verify` in the Curation Queue, the Insight is filtered out of
  the default queue because it is no longer `proposed`, `disputed`, or
  `unverified`.
- Technically the Insight still exists elsewhere, but the user cannot tell where
  it went or how to inspect verified/historical curation results.

Impact:
- A non-destructive action still feels destructive if the destination state has
  no visible place in the UI.
- Undo helps only immediately; durable trust also needs browsable status views.

Action:
- PRD/WHY now require Curation status views/tabs for Needs review, Verified,
  Historical, and All.

## 2026-04-27 — Same Data Type, Same Visual Risk

Observation:
- Roman found raw Markdown-ish payload in Curation's Verified and Historical
  tabs after Matrix detail had already been fixed for the same symptom.
- The underlying issue was not specific to Matrix or Curation; it was `Insight.body`
  and related agent-produced text being rendered differently across surfaces.

Impact:
- Fixing only the screen where feedback arrived leaves the same visual defect in
  sibling surfaces.
- A full app-wide visual review after every small bug is too expensive, but a
  same-data-type sweep is cheap and usually high-signal.

Action:
- For visual defects tied to a shared field or component (`Insight.body`,
  `EvidenceItem.exact_citation`, confidence badges, action buttons), the lead
  should search where the same data type renders and validate 2-4 adjacent
  surfaces before declaring the feedback slice complete.

Rule added:
- Feedback fix = local fix + sibling-surface check for the same data type.

## 2026-04-27 — ClaudeRunner Empiricism Found A Parser Shape Gap

Observation:
- v1.1 required a real refresh through `ClaudeRunner` because the dual-runner
  architecture was otherwise partly theatrical.
- Job #9 ran through the product `RefreshJobService` with `ClaudeRunner`
  against target `claude-code`.
- The run succeeded: Claude CLI preflight resolved
  `C:\Users\Intel\.local\bin\claude.exe`, version `2.1.119 (Claude Code)`,
  and the runner returned `done`.
- The useful surprise was downstream: Claude emitted evidence paths as plain
  bullets (`path:line — note`) rather than Markdown links. The existing parser
  only understood Markdown links, so the first parse created an Insight without
  EvidenceItems.

Impact:
- Real runner diversity is not only about subprocess syntax. Different agents
  shape evidence differently.
- An Insight without EvidenceItems violates the project pedagogy even when the
  raw log itself contains proof.

Action:
- `ClaudeRunner` now has a cheap `preflight()` like `CodexRunner`, including
  Windows-runnable command resolution and launch-error handling.
- The refresh parser now accepts plain evidence path bullets and line ranges,
  in addition to Markdown links.
- Local Job #9 was repaired by attaching EvidenceItems #80-#82 to Insight #37
  from the preserved raw log; no agent output was deleted.

Rule added:
- Empirical runner validation must inspect the parsed artifacts, not only the
  runner terminal status. `done` is not enough if the proof layer is missing.

## 2026-04-27 — Spirit Lead Returns: Two-Lead Model Made Explicit

Observation:
- One day after v1.0-minimal shipped, the owner asked the original spirit lead
  (Claude Opus, who wrote SPIRIT/PRD/AGENTS at bootstrap) to deep-review the
  trajectory: how faithfully had the execution lead (Codex GPT-5.5, who ran the
  v0.1 → v1.0 implementation) honored the original intent.
- Spirit lead dispatched 3 parallel Explore subagents (PRD-vs-implementation gap,
  SPIRIT fidelity, engineering quality) and synthesized the answer instead of
  re-deriving the codebase from scratch — which would have burned context for
  no marginal value.
- The single most important finding was not technical: the SPIRIT.md
  "Collaboration Model" still said "Lead agent (Claude Opus 4.7)" while in
  reality Codex GPT-5.5 had been the lead for the entire v0.1 → v1.0
  implementation. The doc and the practice had silently diverged.

Impact:
- A teaching project that hides its own collaboration model from itself cannot
  teach that model to students.
- Future spirit-lead sessions need a reading order that surfaces this
  discrepancy fast — `EVOLUTION.md` first, not `SPIRIT.md` first, when the
  question is "what did the project actually do."
- Two-lead collaboration is not a defect to fix; it is itself a Level 2
  dogfooding artifact (per SPIRIT). Students see in this very file how two
  agents from different families (Claude / OpenAI) coordinate around a single
  intent, with one keeping vision and one keeping operational context.

Action:
- `SPIRIT.md` "Collaboration Model" rewritten to make the two-lead split
  explicit: **spirit lead** (constitutional, periodic deep-review, owns
  SPIRIT/PRD/AGENTS) vs **execution lead** (operational, continuous, owns
  WORKLOG/EVOLUTION/code dispatch). Same agent in principle; different agents
  in this era; both honor agent1st §3 (Right to Disagree) with a clear
  disagreement protocol.
- `AGENTS.md` Cross-Harness Lead-Agent Model gained an operational subsection:
  default-to-execution-lead when uncertain, spirit-lead sessions are
  owner-initiated and produce PRD v-bumps with acceptance criteria, both leads
  use their own `Co-Authored-By` tag.
- `PRD.md` §24 gained a v1.1 phase block with four explicit acceptance items
  (engagement honesty labelling pass; parser silent-zero-Insights guard;
  ClaudeRunner empirical validation; Co-Authored-By discipline). Out-of-scope
  list explicit so the parallel implementation track will not collide with the
  feedback-driven UI redesign that v1.2 may demand.
- `PRD.md` §14.2 entry for the `engagement` job amended to state v1.1 =
  deterministic templating, not agent-authored. Honest naming over hidden
  compromise.

Rule added:
- When the spirit lead returns for a deep-review pass, the first artifact to
  read is `EVOLUTION.md`, not `SPIRIT.md`. The spirit lead wrote `SPIRIT.md`;
  it does not need to re-read its own constitution to find drift.
  `EVOLUTION.md` is where the execution lead's complaints, surprises, and
  actual operating decisions live — that is the diff against original intent.
- Spirit-lead deep-review passes end with: (a) PRD v-bump with acceptance
  criteria written in the same style as `§26` v0.1 (the execution lead has
  said this format is the most useful to delegate from); (b) WORKLOG queue
  items with concrete IDs prefixed by the version; (c) at most one or two
  SPIRIT/AGENTS deltas per pass (large rewrites destroy continuity).

Teaching extraction (deferred):
- A short student-facing lesson on "the two-lead model" can be extracted later,
  once v1.1 has run through the cycle and confirmed the disagreement protocol
  in practice. Premature extraction would teach a pattern that has not yet been
  stress-tested.

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

## 2026-04-26 — Shared UI Is Not Shared Context

Observation:
- The v0.7 explain slice correctly added "Ask the agent why" to the shared
  Insight card partial.
- A reviewer agent then caught the semantic gap: the shared card rendered on
  harness, topic, matrix, and Insight Library surfaces, but only the Insight
  Library supplied `RevisionNote` explanations back into the template.
- The same gap affected evidence: some cards showed contextual EvidenceItems
  from a harness/topic section even when those EvidenceItems were not directly
  linked to the Insight. The explain job could therefore say "no linked proof"
  while the user had just seen proof below the button.

Impact:
- Reusing a template does not automatically reuse the route data contract.
- Agentic UI actions need to carry the evidence context the user actually saw,
  not only the primary entity id.

Action:
- RevisionNote lookup was factored into a shared helper and passed from Insight
  Library, harness dossier, topic dossier, and matrix cell routes.
- The Ask-why form now submits contextual EvidenceItem ids from the rendered
  proof section.
- `ExplainJobService` validates contextual EvidenceItems against the target
  Insight's linked Insight/topic/harness before using them in prompt, log, and
  explanation text.

Rule added:
- When a shared partial contains a write action, review every route that renders
  it. The route's data context is part of the feature contract.

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
