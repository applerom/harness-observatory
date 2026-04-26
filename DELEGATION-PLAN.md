# Delegation Plan — v0.1 First Working Slice

> **Audience:** lead agent (architect) coordinating subagents who will write the v0.1 code.
> **Status:** v0.1 executed — retained as the historical delegation contract and source for post-v0.1 retrospectives.
> **References:** `SPIRIT.md`, `docs/PRD.md` §24/§26, `docs/why-graph.xml`, `AGENTS.md` §9 Delegation Design.

---

## 1. Roles

| Role | Who | Responsibility |
|---|---|---|
| **Owner** | Roman | intent, acceptance criteria, "is this in spirit", final yes/no on slices |
| **Lead agent** | Active high-capability agent in the current harness: Claude Code/Opus-class, Codex/GPT-5.x-class, or equivalent | architecture, delegation contracts, subagent review, validator runs, integration, communication with owner |
| **Subagents (impl)** | Harness-local bounded agents selected per task — see §3 and §4.1 | bounded code-writing or exploration per delegation contract, return evidence per acceptance criteria |
| **AgentRunner (runtime)** | not in v0.1 | future runtime agents executed BY the app (`claude -p`); separate category from delegation subagents |

Owner does **not** dispatch subagents directly. Lead agent does. Owner reviews lead-agent output and gives go/no-go per slice.

Lead agent normally does **not** write production code. Lead agent writes specs, contracts, reviews diffs, runs validators, integrates. Code-writing belongs to subagents when the active harness can delegate safely. If the active harness cannot delegate a particular task, the lead may implement the smallest safe slice directly and must record the reason in WORKLOG/CONTEXT.

---

## 2. v0.1 Acceptance Criteria (from PRD §26, restated for delegation)

When v0.1 is "done", the owner can:

1. Run `uv run uvicorn observatory.web.app:create_app --factory --reload` on Windows; FastAPI server starts on `localhost:8000`.
2. Open browser to `http://localhost:8000/` and see a dashboard with counts (N harnesses, N topics, N evidence items).
3. Click into a harness dossier — see all insights for that harness, EvidenceItems collapsed under "Show the proof" buttons.
4. Click into a topic dossier — see all harnesses' positions on that topic.
5. Open the comparison matrix — see harness × topic grid, click a cell to expand evidence inline.
6. Run `uv run python -m observatory.importers.canon --source ../harness-architecture` — markdown gets imported into SQLite, dashboard counts update.
7. Run `uv run pytest` — all tests pass.
8. Run `uv run python scripts/validate_anchors.py` — every `<ANCHOR>` in `why-graph.xml` resolves to a real `START_*` marker in source (or reports concrete failures).

**NOT in v0.1 (deferred to later phases):** any AgentJob execution, any cron, Live Studio, "Ask the agent why", full confidence-band automation or per-pass breakdowns (v0.1 may show raw status badges and "not yet verified" placeholders), engagement hooks, doc generation.

---

## 3. Subagent decomposition

Five subagent tasks. Tasks A–C can run **in parallel** once file ownership is clear. Task D depends on A+B+C. Task E depends on A.

### Task A — Data model + migrations (sequential prerequisite for D and E)

**Suggested subagent class:** Sonnet-class worker, or Codex worker on the inherited/strong model
**WHY graph subtree:** `MOD-MODELS` and the FEATUREs that depend on it
**Deliverable:**
- `src/observatory/models/__init__.py` — SQLModel entity definitions for all PRD §7 first-class entities. v0.1 needs at minimum: `Harness`, `Topic`, `Feature`, `EvidenceItem`, `Insight`, `ComparisonCell`, `Source`, `MediaAttachment`. Non-v0.1 entities (`AgentJob`, `PromptTemplate`, `RevisionNote`, `ObservationReview`, `Lens`, `Score`, `EcosystemObject`) — define stub tables (empty for v0.1, ready for later phases). Note: do NOT invent entities not listed in PRD §7 (no `QueueItem`, no `AgentRun-history` — `AgentJob` already covers run history).
- `src/observatory/db.py` — engine + session management.
- `migrations/` (Alembic) — initial migration that creates the schema.
- `alembic.ini` + `migrations/env.py` configured for SQLite at `./observatory.sqlite`.
- One module-contract header per file per `docs/why-contracts-v1.md` rules.
- `START_*` anchors in source matching the planned anchors in `why-graph.xml` MOD-MODELS node.

**Acceptance:**
- `alembic upgrade head` creates the schema cleanly on a fresh SQLite file.
- `pytest tests/models/test_schema.py` passes — round-trip insert/select for each entity.
- Anchor validator finds every `START_*` in source matching the WHY graph plan.

**Estimate:** 1-2 days of subagent work. Single-track, since other tasks depend on it.

---

### Task B — FastAPI app skeleton + Jinja+HTMX layout (parallel with A)

**Suggested subagent class:** Sonnet-class worker, or Codex worker on a lower/medium reasoning setting if the harness supports it
**WHY graph subtree:** `MOD-WEB-APP`, `MOD-WEB-ROUTES-DASHBOARD`, base layout
**Deliverable:**
- `src/observatory/web/app.py` — FastAPI app factory, mounts routers, serves static.
- `src/observatory/web/templates/_base.html` — HTML5 layout with Tailwind via CDN (v0.1 — no build step), HTMX via CDN.
- `src/observatory/web/templates/_nav.html` — top nav: Dashboard, Harnesses, Topics, Matrix.
- `src/observatory/web/routes/dashboard.py` — `/` route returning dashboard with placeholder counts (real counts wired by Task D).
- `src/observatory/web/routes/__init__.py` — router registration.
- `pyproject.toml` — uv project config with all stack dependencies pinned. No `[project.scripts]` entry in v0.1 (Typer CLI wrapper deferred to v0.2 per PRD §26.1).
- `README` snippet documenting the canonical dev startup: `uv run uvicorn observatory.web.app:create_app --factory --reload`.

**Acceptance:**
- `uv sync && uv run uvicorn observatory.web.app:create_app --factory --reload` starts server on `:8000`.
- Browser to `localhost:8000/` returns 200 with the dashboard placeholder.
- Tailwind utility classes render correctly (one visible Tailwind-styled element).
- HTMX swap works (one `hx-get` demonstration on the dashboard).

**Estimate:** 1 day. Parallel with A — they share no files until Task D wires routes to models.

---

### Task C — Markdown importer (parallel with A and B)

**Suggested subagent class:** Sonnet-class worker, or Codex worker/explorer pair if importer uncertainty needs a read-only scout first
**WHY graph subtree:** `MOD-IMPORTER` and `FEAT-MARKDOWN-IMPORT`
**Deliverable:**
- `src/observatory/importers/canon.py` — entry point that reads `D:/ai/harnesses/harness-architecture/registry/harnesses.md` (table → `Harness` rows), `topics/*/topic.md` and `topics/*/evidence.md` (→ `Topic` and `EvidenceItem` rows), `comparisons/harness-map.md` (→ `ComparisonCell` rows). Handles both ASCII tables and pipe-tables.
- `src/observatory/importers/markdown_table.py` — table parser utility.
- A `__main__` block in `src/observatory/importers/canon.py` exposing the entry as `uv run python -m observatory.importers.canon --source <path>`. No `scripts/import_canon.py`, no Typer wrapper in v0.1 (per PRD §26.1).
- Tests in `tests/importers/` — sample fixture markdown files exercise each parser path; the real `harness-architecture/` is read in an end-to-end test.

**Acceptance:**
- Running the importer against the real `D:/ai/harnesses/harness-architecture/` populates SQLite with ≥8 Harnesses and ≥11 Topics. (Empty DB → populated → re-run is idempotent.)
- Importer handles markdown-table edge cases: footnotes, code spans inside cells, non-ASCII characters.
- For markdown that doesn't parse cleanly (e.g., row with merged cells), the importer logs a warning and continues — does NOT silently drop data, does NOT crash.
- `pytest tests/importers/` green.

**Estimate:** 2-3 days. Most error-prone task — markdown parsing edge cases. Subagent should propose its DTO mapping in a short design note before coding.

---

### Task D — Read-only dossier + matrix routes (depends on A, B, C)

**Suggested subagent class:** Sonnet-class worker, or Codex worker on the inherited/strong model
**WHY graph subtree:** `MOD-WEB-ROUTES-HARNESS`, `MOD-WEB-ROUTES-TOPIC`, `MOD-WEB-ROUTES-MATRIX`, the FEATUREs for read-only views
**Deliverable:**
- `src/observatory/web/routes/harness.py` — `/harnesses` list view, `/harnesses/<slug>` dossier view.
- `src/observatory/web/routes/topic.py` — `/topics` list view, `/topics/<slug>` dossier view.
- `src/observatory/web/routes/matrix.py` — `/matrix` view rendering the harness × topic grid; cell click expands evidence via HTMX.
- Templates in `src/observatory/web/templates/` for each view.
- The cell-expand template uses the **"Show the proof"** button label exactly. EvidenceItem is collapsed by default.
- Real counts wired into Dashboard (replaces Task B's placeholders).

**Acceptance:**
- After running the importer, all routes render real data.
- Cell click reveals EvidenceItem inline (no page navigation).
- "Show the proof" button label present and lower than Insight in DOM order.
- A simple Playwright or HTMX-aware test confirms the expand interaction.

**Estimate:** 2-3 days. Owner-visible polish lands here.

---

### Task E — AgentRunner interface stub + anchor validator (depends on A)

**Suggested subagent class:** Haiku-class worker, or Codex worker on a smaller/faster model if the harness supports it
**WHY graph subtree:** `MOD-RUNNER-BASE`, `FEAT-AGENT-RUNNER` (interface only)
**Deliverable:**
- `src/observatory/runners/base.py` — `AgentRunner` Protocol class with method signatures only. Type stubs for `AgentEvent`, `AgentContext`.
- `src/observatory/runners/claude.py` — stub `ClaudeRunner` class implementing the `AgentRunner` Protocol with **every method body** raising `NotImplementedError("ClaudeRunner is a v0.1 stub; concrete subprocess invocation lands in v0.2 per PRD §24")` (per PRD §26.3 — the wiring is real, the call is not). The class exists so dependency-injection sites and the Job Dashboard's "Refresh" button can resolve a real type, while attempting to actually run anything fails loudly. **The literal string `claude -p` must not appear anywhere in `src/` or `scripts/` in v0.1** — neither in `claude.py` (including its docstring/error-message text), nor elsewhere. The acceptance grep below is the authoritative check; this rule must hold against it. The module-contract header for `claude.py` states this prohibition explicitly (without quoting the literal).
- `scripts/validate_anchors.py` — parses `docs/why-graph.xml` (lxml), enumerates `<ANCHOR COORD="path#NAME"/>` BUT only for anchors inside `MODULE_*` nodes whose `STATE` is `STARTED` or `DONE` (skipping `PLANNED` nodes — the graph plans more than the code implements at any moment; STATE is the watershed). For each non-skipped anchor, opens the file, checks `# START_NAME:` (or `// START_NAME:`, etc., language-agnostic) is present. Reports missing/extra. Exit code 0 if all resolve; non-zero with a clear list otherwise. The skip-PLANNED policy must be stated in the script's docstring.
- Tests for both the Protocol shape and the validator.

**Acceptance:**
- `mypy src/observatory/runners/base.py src/observatory/runners/claude.py` clean (Protocol + stub class implementing it; both type-check).
- `pytest tests/runners/test_claude_stub.py` passes — instantiates `ClaudeRunner`, asserts each public method raises `NotImplementedError` whose message mentions "v0.1 stub" and references PRD §24 (the test asserts substring presence, NOT the literal `claude -p`).
- `grep -RIn "claude -p" src/ scripts/` returns no matches in v0.1 (subprocess body is what v0.2 fills in; v0.1 must not contain the literal string anywhere — including docstrings, error messages, and module-contract headers).
- `python scripts/validate_anchors.py` returns exit 0 in v0.1 (all MODULE nodes are still `STATE="PLANNED"`, so all anchors are correctly skipped). When a Task A/B/C/D subagent flips a MODULE node to `STATE="STARTED"`, the validator must then enforce the anchors in that node — the same Task subagent is responsible for placing the `START_*` markers in source.
- Validator regression test: introduces a fake "missing anchor" in a fixture WHY graph (with `STATE="STARTED"`), asserts exit code is non-zero.
- Second regression test: a `STATE="PLANNED"` node with anchors pointing at non-existent files asserts exit code 0 (skip policy honored).

**Estimate:** 0.5–1 day. Mostly mechanical.

---

## 4. Coordination protocol

### 4.1 Harness adapters for delegation

This plan is harness-independent. A lead agent maps each task to the delegation primitive available in its current environment:

- **Claude Code:** create one TaskCreate item per subagent, then dispatch through Claude Code's Agent/Task tool. Use Opus/Sonnet/Haiku according to task risk and owner subscription availability.
- **Codex:** use `spawn_agent` for parallel bounded work when the user/session has authorized subagents (Roman gave standing project authorization in `AGENTS.md`). Follow `docs/codex-subagent-profile.md` and the `.codex/agents/*.toml` profiles when available. Prefer `worker` for implementation, `explorer` for read-only codebase questions, and the default/current model for difficult integration. Use smaller/faster models only for low-risk, bounded tasks when the harness allows explicit model choice and the lead has a concrete reason.
- **Other harnesses:** use their equivalent bounded-agent mechanism only if it can preserve the same contract: self-contained brief, disjoint write ownership, evidence report, no commits by subagents, and lead-owned integration.

Lead agents should not run multiple lead-agent sessions in parallel by default. Roman serializes lead sessions across Claude Code and Codex; durable state in WORKLOG/CONTEXT/git is the handoff boundary. Codex-led sessions should start with the smaller scout-then-worker shape in `docs/codex-subagent-profile.md` unless the lead can explain why direct implementation is safer. Completed Codex subagents should be closed promptly after their evidence is summarized into durable state, so the configured thread cap remains available for real work.

### How subagents are dispatched

Lead agent creates the harness-local tracking item for each subagent, then dispatches with a self-contained prompt that:

- States the project context in 1 paragraph
- Points the subagent at SPIRIT.md, PRD.md (specific sections), why-graph.xml (specific subtree), and AGENTS.md
- States the deliverable list verbatim from §3 above
- States the acceptance criteria verbatim
- Defines ownership: exact files/modules the subagent may write; subagents must not revert or overwrite work by other agents
- Tells the subagent to return a brief (≤200 word) report including: files written, test results, anchor validator output, and any blockers/judgment calls

### How subagents report back

Per `AGENTS.md` §11 (Continuity), subagents must:

- Commit nothing themselves (lead agent owns commits)
- Return all changes as files written to disk + a short report
- Surface any blockers explicitly — silent friction is Class 1 anti-pattern (see §10 below)
- For subagent-internal handoffs (rare in v0.1): write a `tasks/<task-id>-handoff.md` artifact with state

### How lead agent reviews

After each subagent completes, lead agent:

1. Reads the report
2. Reads a sample of files the subagent claims to have written (trust but verify)
3. Runs the anchor validator + pytest + mypy
4. If anything fails, dispatches a focused fix-up subagent (don't fix in lead context — lead context is for orchestration, not code)
5. Stages and commits with conventional message (`feat(v0.1): <slice>`) and agent attribution matching the actual lead/subagent harness used. For Codex-led commits, use a Codex-authored commit message/trailer rather than Claude attribution.
6. Updates CONTEXT.md with progress note
7. Updates `why-graph.xml` if any anchor names were renamed during implementation (graph and code must agree)

### When owner is consulted

Owner is consulted (not just informed):

- Before any subagent is dispatched the FIRST time (this is the current pause point)
- If a harness-level policy requires fresh session authorization for subagents despite the standing project authorization in `AGENTS.md`
- When a subagent reports a deliverable that requires a scope decision (e.g., "PRD says X but the data shape suggests Y — choose")
- When a slice is complete and ready for hands-on owner testing
- When a deferred decision (see CONTEXT.md §6) needs resolution

---

## 5. Sequencing

```
                      ┌── Task A (models) ──┐
START → Owner review →┤                     ├── Task D (read-only routes) ──┐
                      ├── Task B (web skel) ─┤                              ├── Integration & v0.1 release
                      └── Task C (importer) ─┘                              │
                                                                            │
                              Task E (runner stub + validator) ─────────────┘
                              (depends only on A)
```

A, B, C dispatch in parallel after owner review. D dispatches when A, B, C all return green. E dispatches when A returns green.

Estimated total wall time for v0.1 with parallel dispatch: **5-8 days** of subagent work, plus lead-agent integration overhead.

---

## 6. The WHY graph as delegation contract

Each subagent's brief includes a **subtree of the WHY graph** they own. This is the contract:

- The subagent must place `START_*` anchors in source matching the planned anchors in their subtree.
- The subagent may **propose new anchors** if their implementation needs them — they update `why-graph.xml` themselves and explain the addition in their report.
- The subagent must **not delete or rename** anchors planned in their subtree without flagging it. Lead agent reconciles renames during integration.
- After integration, lead agent runs `validate_anchors.py` — graph and code must agree before commit.

This is the agent1st pattern (`docs/why-graph-principles.md` §6): graph + contracts + code move together in one commit, not separately.

---

## 7. Acceptance: lead agent's commit checklist

Before staging any v0.1 commit:

- [ ] Subagent's deliverables exist on disk
- [ ] `uv run pytest` green for all touched tests
- [ ] `uv run ruff check` clean
- [ ] `uv run mypy src/observatory` clean (or annotated exceptions justified)
- [ ] `python scripts/validate_anchors.py` exit 0
- [ ] `why-graph.xml` updated if anchors were renamed/added
- [ ] CONTEXT.md updated with a dated progress note
- [ ] Commit message states what slice + co-authored tag for the runtime model

---

## 8. After v0.1: what feeds into v0.2 planning

When v0.1 ships, lead agent writes a v0.2 delegation plan addendum (this file gets appended; doesn't need to be a new file). v0.2 introduces the AgentRunner concrete + first AgentJob type — that's where the orchestration engine actually starts running.

Owner's feedback after using v0.1 hands-on is the input to v0.2 planning. Probable adjustments: schema fields that turned out wrong on real import, UI affordances that didn't feel right, performance hot spots in matrix rendering. These are normal iteration material — see SPIRIT.md "What Differentiates This Project" §3 (Live, not archival) and the iterative-simplicity principle.

### v0.2a addendum — OpenCode refresh execution spine

Decision: split PRD v0.2 into smaller feedback slices. The first slice ships the durable job spine before parsing freeform agent output into Insights.

Deliverable:

- OpenCode dossier has an active Refresh button.
- POST refresh creates an `AgentJob(type="refresh", target_kind="Harness")`.
- The job runs through selected `AgentRunner` (`CodexRunner` by default, `ClaudeRunner` optional). Concrete CLI subprocess code lives only in the corresponding runner module under `src/observatory/runners/`.
- Raw runner output is written to `live-sessions/agent-job-*.log`.
- `/jobs` lists jobs; `/jobs/{id}` shows status/error/log link; `/jobs/{id}/log` serves the raw log.

Non-goals for v0.2a:

- no parser from raw log to `Insight`;
- no cron;
- no all-harness refresh;
- no SSE/live studio;
- no six-job-type forms.

Why: the full v0.2 chain mixes subprocess behavior, prompt shape, parsing, and UI. Preserving raw logs first makes the next parser slice evidence-driven and keeps agent fallibility visible.

Acceptance:

- `uv run pytest` green;
- `uv run ruff check src/ tests/ scripts/validate_anchors.py` green;
- `uv run mypy src/observatory tests` green;
- `uv run python scripts/validate_anchors.py` green;
- grep confirms the concrete CLI invocation text does not leak outside the runner boundary.
- Playwright CLI visual QA confirms matrix top-scroll and cell-detail reveal behavior.

---

## 9. Anti-patterns to avoid in delegation

These are violations to catch in subagent output and refuse to merge:

1. **Silent friction** — subagent worked around a blocker without flagging. Per `AGENTS.md` §6 (CDD), surface and propose a fix; don't paper over.
2. **Scope creep** — subagent added features beyond the deliverable. Even nice features. Reject and ask them to remove; v0.1 is read-only ONLY.
3. **Any literal `claude -p` string** — anywhere in `src/` or `scripts/` in v0.1. The stub `ClaudeRunner` (per Task E) raises `NotImplementedError`; the actual subprocess call lands in v0.2. Any occurrence in v0.1 is a bug. From v0.2 onward, `claude -p` may exist *only* inside `ClaudeRunner`.
4. **Code-first UI** — if any cell view shows code FIRST and Insight under it, that's wrong. Insight on top, code under "Show the proof". Reject and fix.
5. **Review queue / staging** — if a subagent invents a "pending approval" mechanism, that violates L1 autonomy (PRD §12). Reject.
6. **Deleting agent output that looks bad** — fallibility is teaching material (PRD §4.9, SPIRIT). Use status fields, not deletion.
7. **Dropping data silently in importer** — if the importer can't parse a row, it must log + continue, not drop. `harness-architecture/` is the source of truth being migrated; data loss is not acceptable.
8. **Writing tests after code** — every subagent task acceptance includes tests. If tests are missing, reject the deliverable.

---

## 10. Open meta-questions for owner

(These are NOT v0.1 acceptance blockers — flagged so owner can pick them up if/when relevant.)

- **Lead agent identity continuity.** Is it OK to spawn a fresh Opus session for v0.2 (loading SPIRIT/PRD/WHY/CONTEXT) instead of continuing this session? Per AGENTS.md §11, durable artifacts > session continuity, so yes — but owner may have preferences.
- **Subagent model choice per task.** Currently Sonnet for most, Haiku for E. Owner may want to try Haiku for B (web skeleton — more boilerplate, less judgment) to compare quality.
- **Where do code commits attribute?** Attribute to the actual agent/harness that authored or integrated the change. Claude Code-led work may use Claude Opus/Sonnet trailers. Codex-led work should identify Codex/GPT-5.x in the commit body/trailer. Do not attribute routine agent-authored commits to Roman unless Roman explicitly co-authored the content.
