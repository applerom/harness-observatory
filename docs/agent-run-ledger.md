# Agent Run Ledger

> Rolling, short ledger of subagent dispatches by the Codex execution lead.
> Purpose: turn every dispatch into evidence the lead can use to (a) sharpen
> its own brief writing, (b) re-route work to a better-fitting subagent class
> next time, (c) graduate stable patterns into `docs/codex-subagent-profile.md`
> or `docs/lessons/`.
>
> This is **not** a permanent archive. Rows whose lesson has already graduated
> into the profile or a lesson file are deleted on the next sweep. The ledger
> stays short on purpose.

## How to use this ledger

1. **Append a row when a subagent dispatch finishes** (success, failure, or rework).
   Be terse: one phrase per cell. Long stories belong in `EVOLUTION.md` or in a
   lesson file, not here.
2. **Write a verdict before integrating the result.** One of `useful`,
   `partial`, `wasted`, `rework`. The verdict reflects whether the dispatch
   net-saved the lead's context — not whether the worker tried.
   - `useful` — patch + report integrated as-is or with minor tweaks; lead
     spent less attention than doing it directly.
   - `partial` — usable but the lead did real follow-up work to finish or
     correct.
   - `wasted` — the lead would have been faster doing it directly; the
     dispatch was net context loss.
   - `rework` — re-dispatched the same task with a different brief or worker
     class.
3. **Mark the friction → rule column** when the verdict suggests a pattern.
   Empty is fine if the dispatch was clean.
4. **Periodic sweep** (every ~10 rows or roughly weekly): re-read the ledger,
   group repeating frictions, and graduate them:
   - operational rule for dispatch craft → add a paragraph to
     `docs/codex-subagent-profile.md` and reference it from the row.
   - lesson worth showing students → write or extend a file under
     `docs/lessons/` and reference it from the row.
   - row whose rule has graduated → **delete the row**. It has done its job.

## Active runs

| Date | Agent (label) | Task | Outcome | Verdict | Friction → Rule? |
|---|---|---|---|---|---|
| 2026-04-27 | Peirce — `fast_implementation_worker[gpt-5.3-codex-spark/medium]` | Matrix detail hygiene implementation | Bounded patch landed; `visual:matrix` green; lead added stricter redirect validation, latest-only explanation, several detail-noise fixes during integration | partial | Spark needs explicit edge cases and route-test acceptance up front → see profile "Subagent Prompt Contract" |
| 2026-04-27 | Curie — `reviewer[gpt-5.5/high]` | Matrix detail review | Found real issues, all fixable | useful | High-cost reviewer is wasted on small visual churn → see profile "Default Codex Shape" (reserve strong review for stabilized/risky checkpoints) |
| 2026-04-27 | Harvey — `fast_implementation_worker[gpt-5.3-codex-spark/medium]` | Curation action affordance implementation | Implementation, redirects, undo route, route tests, visual test landed; live log showed broad cold-read of project docs and a compaction before a tiny patch | partial | Lead prompt-budget failure; Spark over-reads when no explicit read budget is set → graduated to `docs/lessons/subagent-dispatch-craft.md` and to profile "Subagent Prompt Contract" tiny-slice clause |
| 2026-04-27 | Herschel — `gpt-5.3-codex-spark/low` | Mechanical validation for Curation slice | Ran focused pytest, visual:curation, ruff, mypy, anchor validator; caught that a stale long-running dev server can make `visual:curation` fail while a fresh server passes | useful | Visual tests need a fresh dev server after route/template edits → graduated to profile "Subagent Prompt Contract" command/test expectations |
| 2026-04-27 | Faraday — `fast_implementation_worker[gpt-5.3-codex-spark/medium]` | Curation status views with explicit read budget | Implemented Needs review / Verified / Historical / All tabs and destination redirects; reported no broad-doc reads | useful | Counter-evidence to Harvey: explicit context packet + allowed-read set produces a clean Spark dispatch → graduated alongside Harvey to `docs/lessons/subagent-dispatch-craft.md` |
| 2026-04-27 | Carver — `gpt-5.3-codex-spark/low` | Mechanical validation after status-view patch | Ran validation; caught an ambiguous Playwright strict locator | useful | Cheap validators are high-signal on Playwright strict locators; covered by validation profile |
| 2026-04-27 | Anscombe — `fast_implementation_worker[gpt-5.3-codex-spark/medium]` | Markdown-ish sibling-surface sweep | Shared safe renderer wired across Curation, Insight Library, Live, Matrix, harness/topic proof partials; focused tests + visual checks green | useful | Spark is a good fit for cross-surface UI consistency when same-data-type scope and write set are explicit; covered by profile |
| 2026-05-01 | Hume — `repo_explorer[gpt-5.4-mini/medium]` | Doc status/subagent-consent wording scout | Read only named docs; identified exact stale phase labels and PRD engagement conflict; no code or broad cold-read | useful | Narrow read-only scouts are high-ROI when the lead provides the suspected contradiction and file set up front |
| 2026-05-01 | Lorentz — `reviewer[gpt-5.5/high]` | Compact AGENTS.md review | Found one missing safety invariant and one duplicated reading-order authority; both patched | useful | Strong reviewer is justified for globally loaded operating rules; keep review scope tiny and read-only |

## Graduated rules — pointers, not content

When a row's lesson has matured, the rule moves to the canonical file and the
row above gets a pointer. Drop the row entirely on the next sweep when the
pointer adds nothing. Current pointers:

- **Brief shape determines dispatch ROI; Spark workers need explicit read
  budget for tiny slices.** → `docs/lessons/subagent-dispatch-craft.md`
  (real-episode comparison of Harvey and Faraday); also reflected in
  `docs/codex-subagent-profile.md` "Subagent Prompt Contract" tiny-slice
  paragraph.
- **Visual tests after route/template edits need a fresh dev server.** →
  `docs/codex-subagent-profile.md` "Subagent Prompt Contract" command/test
  expectations.
- **Strong reviewers are reserved for stabilized or risky checkpoints, not
  every iteration.** → `docs/codex-subagent-profile.md` "Default Codex
  Shape" routing rules.

## Open questions (note, then delete on graduation)

- Effective context-budget delta for Spark dispatches: when the lead packages a
  context packet of size P and reads back a report of size R, what P/R range
  produces consistently `useful` verdicts? After ~10 more rows, decide whether
  this becomes a profile guideline or stays as judgment.
- First sweep prompt for the next execution lead: review the seven existing
  rows above, decide which ones are now redundant given the lessons/profile
  text, and delete them. The ledger should be a runway, not a museum.
