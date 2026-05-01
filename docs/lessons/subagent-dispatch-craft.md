# Lesson: Dispatch ROI Is The Lead's Brief, Not The Worker's Speed

## Real Episode

On 2026-04-27 the Codex execution lead dispatched two `fast_implementation_worker[gpt-5.3-codex-spark/medium]` subagents within the same feedback-hardening session.

**Harvey** got a small Curation-action-affordance task. The brief named the goal but did not bound the read set. The live log showed Harvey cold-reading broad project documents and triggering an internal compaction before producing a tiny patch. The patch and tests landed, but the worker burned context the lead had no reason to spend, and the lead reviewed a longer report than the patch itself.

**Faraday** got the very next slice — Curation status views — with an explicit context packet, an allowed-read set, and the line "do not cold-read SPIRIT, PRD, CONTEXT, WORKLOG, or EVOLUTION." Faraday returned a clean focused patch. Same model. Same hardware. Different brief. Faraday saved the lead's context; Harvey did not.

## Lesson

A subagent's effective speed is bounded by what the lead packaged in the brief, not by the worker's nominal capability. Spark/fast workers will eagerly explore until told what is in scope. The lead pays for that exploration in:

- wall-clock time before the patch lands;
- the worker's own context window (compaction is a tax on quality);
- the lead's review burden when a small task comes back over-touched.

The metric for a dispatch is not "did the patch land?" but "did the lead read a report shorter than the patch it would have written locally?" When the answer is no, the dispatch was a context loss, regardless of whether the code is correct.

Three rules emerge from Harvey/Faraday and are now codified in `docs/codex-subagent-profile.md` "Subagent Prompt Contract" and "Dispatch Decision":

1. **For tiny slices, hand the worker a context packet, not a reading list.** Name the files it must read, the files it must not edit, and what it must treat as authoritative for this slice. Forbid cold-reading the heavy docs unless explicitly required.
2. **Verdict every dispatch on the lead-context delta.** Append a row to `docs/agent-run-ledger.md` with `useful`, `partial`, `wasted`, or `rework`. A `wasted` verdict is not a worker failure; most often it is a brief failure.
3. **Do not delegate the next time the same brief shape produced the same friction.** Either change the brief or change the worker class. Repeating the experiment is not a dispatch — it is a habit.

## Why This Matters Beyond One Project

Most operators learn subagent craft by anecdote: "this worker is good," "that one is flaky." Anecdotes do not survive a model upgrade, a profile change, or a new harness. A short, structured ledger plus periodic graduation into a profile turns scattered episodes into a craft that improves on purpose. The same loop transfers directly to any team running multi-agent workflows on Codex, Claude Code, or any future harness — the surface changes, but the discipline (brief → dispatch → verdict → graduate) does not.

## Student Exercise

Open `docs/agent-run-ledger.md`. For each row whose verdict is `partial` or `wasted`:

- name one specific change to the brief that would likely have moved the verdict toward `useful`;
- find which line in `docs/codex-subagent-profile.md` "Subagent Prompt Contract" already encodes that change, or, if none does, draft the missing line.

If an existing rule already covers the friction, the row is graduated and ready to be deleted on the next sweep. If no rule covers it, that is the next graduation candidate.
