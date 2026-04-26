# Worker-Green Is Not Integration-Green

## The Episode

During the v0.4b/v0.5/v0.6 product train, Codex delegated three bounded slices:
abstract teaching artifacts, verification/confidence, and engagement/Insight
Library. The workers returned useful code and green local tests.

A reviewer subagent still found cross-slice problems before commit:

- live first-observer claims accepted old harness Insights, not only live-job
  artifacts
- orphan EvidenceItems could be verified without updating the target Insight
- verify jobs mixed Insight, EvidenceItem, and ObservationReview IDs in one
  untyped `produced_artifact_ids` list
- abstract artifacts used `format="mermaid"` while the PRD model vocabulary said
  `mermaid_diagram`
- deterministic engagement jobs were already `done` but had no execution
  timestamps

## The Lesson

A worker can be correct inside its assigned slice and still produce an
integration problem. This is normal. Parallel work increases throughput, but it
also creates semantic joints between slices.

The lead agent should not only ask "did the tests pass?" It should ask:

- Do route permissions match the product claim?
- Do data fields still mean one thing?
- Are audit fields typed enough for future readers?
- Does UI copy promise more than the data contract proves?
- Did all slices keep the same vocabulary?

## The Practice

After a parallel implementation train, run a read-only reviewer before commit.
Give it the dirty workspace and ask specifically for cross-slice semantic
issues. Then fix the smallest real problems and add regression tests.

This keeps subagents useful without pretending that worker-local success equals
product success.
