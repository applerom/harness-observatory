# Delegation Plan — v0.1 First Working Slice

> **Audience:** lead agent (architect) coordinating subagents who will write the v0.1 code.
> **Status:** Draft — pending owner review of foundational docs before dispatch.
> **References:** `SPIRIT.md`, `docs/PRD.md` §24/§26, `docs/why-graph.xml`, `AGENTS.md` §9 Delegation Design.

---

## 1. Roles

| Role | Who | Responsibility |
|---|---|---|
| **Owner** | Roman | intent, acceptance criteria, "is this in spirit", final yes/no on slices |
| **Lead agent** | Claude Opus 4.7 (current session or future Opus session, contextful via SPIRIT/PRD/WHY/CONTEXT) | architecture, delegation contracts, subagent review, validator runs, integration, communication with owner |
| **Subagents (impl)** | Sonnet/Haiku per task — see §3 | bounded code-writing per delegation contract, return evidence per acceptance criteria |
| **AgentRunner (runtime)** | not in v0.1 | future runtime agents executed BY the app (`claude -p`); separate category from delegation subagents |

Owner does **not** dispatch subagents directly. Lead agent does. Owner reviews lead-agent output and gives go/no-go per slice.

Lead agent does **not** write production code. Lead agent writes specs, contracts, reviews diffs, runs validators, integrates. Code-writing belongs to subagents.

---

## 2. v0.1 Acceptance Criteria (from PRD §26, restated for delegation)

When v0.1 is "done", the owner can:

1. Run `uv run observatory` (or equivalent CLI entry point) on Windows; FastAPI server starts on `localhost:8000`.
2. Open browser to `http://localhost:8000/` and see a dashboard with counts (N harnesses, N topics, N evidence items).
3. Click into a harness dossier — see all insights for that harness, EvidenceItems collapsed under "Show the proof" buttons.
4. Click into a topic dossier — see all harnesses' positions on that topic.
5. Open the comparison matrix — see harness × topic grid, click a cell to expand evidence inline.
6. Run `uv run observatory import-canon --source ../harness-architecture` — markdown gets imported into SQLite, dashboard counts update.
7. Run `uv run pytest` — all tests pass.
8. Run `uv run python scripts/validate_anchors.py` — every `<ANCHOR>` in `why-graph.xml` resolves to a real `START_*` marker in source (or reports concrete failures).

**NOT in v0.1 (deferred to later phases):** any AgentJob execution, any cron, Live Studio, "Ask the agent why", confidence label rendering (data model has the field; UI just shows the raw status), engagement hooks, doc generation.

---

## 3. Subagent decomposition

Five subagent tasks. Tasks A–C can run **in parallel** (no shared files except for shared seed of types). Tasks D–E are **sequential** (depend on A and C respectively).

### Task A — Data model + migrations (sequential prerequisite for D and E)

**Owner subagent type:** Sonnet
**WHY graph subtree:** `MOD-MODELS` and the FEATUREs that depend on it
**Deliverable:**
- `src/observatory/models/__init__.py` — SQLModel entity definitions for all PRD §7 first-class entities. v0.1 needs at minimum: `Harness`, `Topic`, `Feature`, `EvidenceItem`, `Insight`, `ComparisonCell`, `Source`, `MediaAttachment`. Non-v0.1 entities (`AgentJob`, `PromptTemplate`, `AgentRun`-history, `RevisionNote`, `ObservationReview`, `Lens`, `Score`, `EcosystemObject`, `QueueItem`) — define stub tables (empty for v0.1, ready for later phases).
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

**Owner subagent type:** Sonnet
**WHY graph subtree:** `MOD-WEB-APP`, `MOD-WEB-ROUTES-DASHBOARD`, base layout
**Deliverable:**
- `src/observatory/web/app.py` — FastAPI app factory, mounts routers, serves static.
- `src/observatory/web/templates/_base.html` — HTML5 layout with Tailwind via CDN (v0.1 — no build step), HTMX via CDN.
- `src/observatory/web/templates/_nav.html` — top nav: Dashboard, Harnesses, Topics, Matrix.
- `src/observatory/web/routes/dashboard.py` — `/` route returning dashboard with placeholder counts (real counts wired by Task D).
- `src/observatory/web/routes/__init__.py` — router registration.
- `pyproject.toml` — uv project config with all stack dependencies pinned.
- `README` snippet for `uv run observatory web` to start the server.

**Acceptance:**
- `uv sync && uv run uvicorn observatory.web.app:create_app --factory` starts server on `:8000`.
- Browser to `localhost:8000/` returns 200 with the dashboard placeholder.
- Tailwind utility classes render correctly (one visible Tailwind-styled element).
- HTMX swap works (one `hx-get` demonstration on the dashboard).

**Estimate:** 1 day. Parallel with A — they share no files until Task D wires routes to models.

---

### Task C — Markdown importer (parallel with A and B)

**Owner subagent type:** Sonnet
**WHY graph subtree:** `MOD-IMPORTER` and `FEAT-MARKDOWN-IMPORT`
**Deliverable:**
- `src/observatory/importers/canon.py` — entry point that reads `D:/ai/harnesses/harness-architecture/registry/harnesses.md` (table → `Harness` rows), `topics/*/topic.md` and `topics/*/evidence.md` (→ `Topic` and `EvidenceItem` rows), `comparisons/harness-map.md` (→ `ComparisonCell` rows). Handles both ASCII tables and pipe-tables.
- `src/observatory/importers/markdown_table.py` — table parser utility.
- `scripts/import_canon.py` or `observatory import-canon --source <path>` CLI command.
- Tests in `tests/importers/` — sample fixture markdown files exercise each parser path; the real `harness-architecture/` is read in an end-to-end test.

**Acceptance:**
- Running the importer against the real `D:/ai/harnesses/harness-architecture/` populates SQLite with ≥8 Harnesses and ≥10 Topics. (Empty DB → populated → re-run is idempotent.)
- Importer handles markdown-table edge cases: footnotes, code spans inside cells, non-ASCII characters.
- For markdown that doesn't parse cleanly (e.g., row with merged cells), the importer logs a warning and continues — does NOT silently drop data, does NOT crash.
- `pytest tests/importers/` green.

**Estimate:** 2-3 days. Most error-prone task — markdown parsing edge cases. Subagent should propose its DTO mapping in a short design note before coding.

---

### Task D — Read-only dossier + matrix routes (depends on A, B, C)

**Owner subagent type:** Sonnet
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

**Owner subagent type:** Haiku (small task)
**WHY graph subtree:** `MOD-RUNNER-BASE`, `FEAT-AGENT-RUNNER` (interface only)
**Deliverable:**
- `src/observatory/runners/base.py` — `AgentRunner` Protocol class with method signatures only. Type stubs for `AgentEvent`, `AgentContext`. NO concrete implementations in v0.1. Module contract header explicitly states: "no `claude -p` invocation may exist below this abstraction boundary."
- `scripts/validate_anchors.py` — parses `docs/why-graph.xml` (lxml), enumerates `<ANCHOR COORD="path#NAME"/>`, opens each path, checks `# START_NAME:` (or `// START_NAME:`, etc., language-agnostic) is present. Reports missing/extra. Exit code 0 if all resolve; non-zero with a clear list otherwise.
- Tests for both the Protocol shape and the validator.

**Acceptance:**
- `mypy src/observatory/runners/base.py` clean (no concrete code, just protocol).
- `python scripts/validate_anchors.py` returns exit 0 after Tasks A, B, C, D have placed all `START_*` markers.
- Validator regression test: introduces a fake "missing anchor" in a fixture WHY graph, asserts exit code is non-zero.

**Estimate:** 0.5–1 day. Mostly mechanical.

---

## 4. Coordination protocol

### How subagents are dispatched

Lead agent creates a TaskCreate item per subagent, then dispatches via Agent tool with a self-contained prompt that:

- States the project context in 1 paragraph
- Points the subagent at SPIRIT.md, PRD.md (specific sections), why-graph.xml (specific subtree), and AGENTS.md
- States the deliverable list verbatim from §3 above
- States the acceptance criteria verbatim
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
5. Stages and commits with conventional message (`feat(v0.1): <slice>`) and `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` (matching the runtime model used)
6. Updates CONTEXT.md with progress note
7. Updates `why-graph.xml` if any anchor names were renamed during implementation (graph and code must agree)

### When owner is consulted

Owner is consulted (not just informed):

- Before any subagent is dispatched the FIRST time (this is the current pause point)
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

---

## 9. Anti-patterns to avoid in delegation

These are violations to catch in subagent output and refuse to merge:

1. **Silent friction** — subagent worked around a blocker without flagging. Per `AGENTS.md` §6 (CDD), surface and propose a fix; don't paper over.
2. **Scope creep** — subagent added features beyond the deliverable. Even nice features. Reject and ask them to remove; v0.1 is read-only ONLY.
3. **Hardcoded `claude -p`** anywhere except inside `ClaudeRunner` (which is NOT in v0.1 — so any occurrence in v0.1 is a bug).
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
- **Where do code commits attribute?** Suggested: `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` for code-writing subagents, `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>` for lead-agent integration commits. Confirm or adjust.
