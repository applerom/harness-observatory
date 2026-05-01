# Agent Run Ledger

> Lightweight feedback-era ledger for subagent usefulness. This is not a blame log.
> Purpose: help the Codex lead tune which agents to use for fast UI iterations,
> validation, review, and harder implementation.

## Current policy snapshot

- Feedback-hardening favors speed and reversibility over expensive review gates.
- `fast_implementation_worker[gpt-5.3-codex-spark/low|medium]` is preferred for small UI/template/route/test patches.
- Spark workers may also run validation/server/screenshot tasks when commands are explicit.
- Strong reviewer agents are reserved for stabilized slices, risky behavior, security, schema, or persistent process changes.
- The lead still owns PRD/WHY intent, integration, and final evidence; WORKLOG is only a lightweight runway when needed.

## Runs

| Date | Agent | Task | Result | Lead assessment | Next tuning |
|---|---|---|---|---|---|
| 2026-04-27 | Peirce — `fast_implementation_worker[gpt-5.3-codex-spark/medium]` | Matrix detail hygiene implementation | Useful bounded patch; focused tests and `visual:matrix` green | Fast and directionally good, but needed lead fixes for stricter redirect validation, latest-only explanation, and several detail-noise cases | Keep using Spark for UI slices; give very explicit edge cases and ask for route tests |
| 2026-04-27 | Curie — `reviewer[gpt-5.5/high]` | Matrix detail review | Found real issues, all fixable | High-quality but too expensive for every feedback iteration at this phase | Reserve strong review for stabilized/risky checkpoints, not each visual churn |
| 2026-04-27 | Harvey — `fast_implementation_worker[gpt-5.3-codex-spark/medium]` | Curation action affordance implementation | Implemented copy, clearer labels, redirect confirmation, undo route, route tests, and visual test quickly | Good fit for bounded UI+route slice, but live log showed over-reading broad project docs and compaction before a tiny patch. This was a lead prompt-budget failure, not just a worker issue | Keep using Spark for small reversible feedback patches; include "after undo" behavior and a strict allowed-read budget in acceptance criteria |
| 2026-04-27 | Herschel — `gpt-5.3-codex-spark/low` | Mechanical validation for Curation slice | Ran focused pytest, visual curation, ruff, mypy, and anchor validator without edits | Useful validation lane. Caught that stale long-running dev server can make `visual:curation` fail while a fresh server passes | Delegate routine validation to Spark; explicitly require fresh server for visual tests after route/template edits |
| 2026-04-27 | Faraday — `fast_implementation_worker[gpt-5.3-codex-spark/medium]` | Curation status views implementation with read budget | Implemented Needs review / Verified / Historical / All tabs and destination redirects; reported no broad-doc reads | Strong positive signal for context-budgeted Spark prompts. Needed only lead tightening of visual coverage | Keep using explicit context packet + allowed read set for Spark implementation |
| 2026-04-27 | Carver — `gpt-5.3-codex-spark/low` | Mechanical validation after status-view patch | Ran validation without edits and caught an ambiguous Playwright strict locator | Useful cheap validator; its failure was high-signal and quick to fix | Keep delegating mechanical validation, especially Playwright strict-locator checks |
| 2026-04-27 | Anscombe — `fast_implementation_worker[gpt-5.3-codex-spark/medium]` | Markdown-ish sibling-surface sweep | Added shared safe renderer and wired Curation, Insight Library, Live, Matrix, harness/topic proof partials; focused tests and visual checks green | Good fit for bounded cross-surface UI consistency when the lead defines exact same-data-type scope. Needed only lead review and extra self-click validation | Use Spark for small cross-surface sweeps if write set is explicit and renderer/test acceptance is concrete |
