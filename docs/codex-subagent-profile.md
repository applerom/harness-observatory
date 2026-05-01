# Codex Subagent Operating Profile

> Status: current Codex-led operating profile for v1.1+ feedback-hardening.
> Scope: how a Codex execution lead uses Codex subagents in this repository.
> Authority: subordinate to `AGENTS.md`, `CONTEXT.md`, `WORKLOG.md`,
> `docs/PRD.md`, and `docs/why-graph.xml`.

This project no longer uses the bootstrap v0.1 task plan. The current operating
shape is fast feedback: the lead agent frames the slice, writes or updates
PRD/WHY when intent changes, delegates bounded work when useful, integrates, and
validates with evidence.

## Default Codex Shape

| Purpose | Preferred Codex role | Model posture | Reasoning posture | Write access |
|---|---|---|---|---|
| Lead/orchestrator | main session | strongest available GPT-5.x, normally inherited | high for architecture/integration | yes |
| Repository scout | `repo_explorer` or built-in `explorer` | smaller/faster acceptable | medium | no |
| Fast feedback implementation | `fast_implementation_worker` or built-in `worker` with Spark-class model | fast Codex implementation lane | low/medium | yes, tiny bounded |
| Default implementation | `implementation_worker` or built-in `worker` | strong default/inherited | medium | yes, bounded |
| Hard implementation | `hard_worker` or built-in `worker` | strongest available | high | yes, bounded |
| Validation | `validator` or built-in `worker` | smaller/faster acceptable | low/medium | command-running only |
| Review | `reviewer` or built-in `explorer` | strongest available | high | no |

`fast_implementation_worker` is for speed on small, reversible UI/template/route
and focused test patches. It is not for schema design, security boundaries,
cross-cutting refactors, or final review. Strong reviewers are reserved for
risky behavior, stable checkpoints, schema/runtime boundaries, or repeated
failures.

## Dispatch Decision — When To Delegate, When Not To

Subagents are not free. Each dispatch costs the lead's brief-writing time, plus
review time on the report, plus integration time. The dispatch is worth doing
only when it net-saves the lead's attention or compresses wall-clock through
parallelism.

**Delegate when:**

- The work is bounded enough to brief in roughly fifteen lines or less.
- The lead can specify acceptance criteria without doing the work first.
- The result protects lead context for harder downstream decisions.
- Two or more independent sub-tasks can run in parallel with disjoint write
  sets.
- The task is mechanical enough that a smaller/faster worker is a strict
  improvement (validation, Playwright runs, ruff/mypy sweeps, focused tests).

**Do not delegate when:**

- The next step is the lead's own thinking (architecture, scope, taste).
- Writing a clean brief would take longer than doing the work.
- The result needs immediate iteration where round-trips through delegation
  are slower than a local edit.
- The task touches `SPIRIT.md`, `docs/PRD.md` principles, or `AGENTS.md`
  doctrine — those are spirit-lead surfaces, not delegable.
- A previous identical dispatch shape failed and the brief has not changed.

When in doubt, do the small thing locally; reserve dispatches for slices where
the lead-context save is unambiguous.

## Lead Responsibilities

- Own architecture, PRD/WHY movement, integration, and final evidence.
- Use subagents when they protect lead context or materially speed a bounded
  slice.
- Do not delegate the immediate blocking next step if the lead can do it faster
  and safer locally.
- Keep write scopes disjoint for parallel implementation.
- Close completed subagents promptly after extracting the useful evidence.
- Use `WORKLOG.md` only for active runway, blockers, or in-flight subagent state
  that must survive a crash.

## Subagent Prompt Contract

Every Codex subagent prompt should include:

- one-paragraph project/slice context;
- exact task boundary and deliverable;
- exact file or module ownership;
- files it must not edit;
- relevant PRD/WHY references or a small context packet;
- context budget and allowed read set;
- acceptance criteria;
- command/test expectations;
- blocker escape hatch;
- no-commit rule;
- short report format.

For tiny feedback-hardening slices, the lead should explicitly say:

- do not cold-start-read `SPIRIT.md`, full `docs/PRD.md`, full WHY graph,
  `CONTEXT.md`, `WORKLOG.md`, or `EVOLUTION.md` unless told;
- use the provided context packet as product truth for this slice;
- read only the named implementation/test files, plus at most a few targeted
  `rg` checks if needed;
- stop and report if those files contradict the packet instead of broad-scanning
  the repo.

## Dispatch Labels

Use this compact label in durable notes when a subagent's identity matters:

```text
<profile>[<model>/<reasoning>] (<nickname>)
```

Examples:

```text
implementation_worker[gpt-5.5/medium] (Leibniz)
fast_implementation_worker[gpt-5.3-codex-spark/medium] (Peirce)
```

Omit long agent ids from ordinary notes unless a live technical operation needs
the exact id.

## Recommended Report Format

```text
## Result
done / partial / blocked

## Files changed
- path: summary

## Validation
- command: exit code + relevant output

## Evidence
- acceptance criteria covered

## Blockers / contradictions
- explicit if any

## Judgment calls
- decisions made inside the delegated boundary

## Recommended next step
- one sentence
```

## Verdict And Ledger Discipline

After every dispatch finishes (success, failure, or rework), the lead writes a
one-line verdict before integrating the result and appends a row to
`docs/agent-run-ledger.md`. This is not optional ceremony — it is the only
mechanism that lets the dispatch craft self-improve.

**Verdict vocabulary** (use one):

- `useful` — patch and report integrate as-is or with minor tweaks; the lead
  spent less attention than doing the work directly.
- `partial` — usable, but the lead did real follow-up to finish or correct.
- `wasted` — the lead would have been faster doing it directly; the dispatch
  was net context loss.
- `rework` — the same task was re-dispatched with a different brief or worker
  class.

**The real metric: lead-context delta.** A dispatch is successful when the
lead reads a shorter report than the patch the lead would have produced
locally. If the report is longer than the patch, or if the report demanded
extra clarifying reads from the lead, the dispatch was a context loss and the
verdict reflects that — even when the patch itself is correct.

**Periodic sweep.** Every roughly ten dispatches, or weekly while feedback work
is hot, the lead re-reads the ledger and looks for repeated friction:

- Same brief shape produced two `partial` or `wasted` verdicts → graduate the
  fix (sharpen this profile, add an explicit clause to the Subagent Prompt
  Contract, or update the dispatch decision rules above).
- The pattern is teachable to students → write or extend a file under
  `docs/lessons/` and pointer the ledger row at it.
- The row's lesson has graduated → **delete the row**. The ledger is a runway,
  not an archive. Long ledgers signal a missed sweep, not careful record
  keeping.

The ledger graduation loop mirrors the EVOLUTION → lessons graduation loop:
in-flight observations crystallise into a canonical rule, then the in-flight
copy is removed.

## Practical Fan-Out

Normal work should keep fan-out small: one scout plus one implementation worker,
or two implementation workers with clearly disjoint write sets. During fast UI
feedback, Spark-class workers can be useful, but the lead should still inspect
the patch and run focused validation before claiming done.

Parallel write-heavy work needs stronger isolation before scaling further:
separate git worktrees, app ports, logs, and an explicit lead-owned integration
step.
