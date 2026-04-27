# Codex Subagent Operating Profile

> Status: project operating profile for Codex-led sessions.
> Scope: how a Codex lead agent should use Codex subagents in this repository.
> Authority: subordinate to `AGENTS.md`, `WORKLOG.md`, `CONTEXT.md`, `DELEGATION-PLAN.md`, `docs/PRD.md`, and `docs/why-graph.xml`.

This profile converts the advisory memo in `docs/codex-subagents-recommendations.md` into the smaller policy this project will actually use. The memo is useful and broadly aligned with the project, but it is guidance, not a command surface.

## Assessment

The recommendations are adequate for `harness-observatory`:

- They preserve the strict lead/subagent hierarchy already defined in `AGENTS.md`.
- They keep `max_depth = 1`, which matches the project's bias against recursive delegation and quota surprises.
- They keep small active fan-out, with `agents.max_threads = 5` treated as headroom rather than a default swarm size.
- They prefer small fan-out over swarm behavior, which fits a personal-subscription, local-first teaching project.
- They separate read-only exploration, implementation, validation, and review.
- They correctly reserve `xhigh` for rare escalation, not normal work.

Project-specific adjustments:

- Do not run a broad scout swarm by default. Start with one or two scouts when they can answer a concrete uncertainty.
- Do not pin a smaller model just because it is cheaper. Use lighter models only when the result is easy for the lead to verify.
- Do not delegate the immediate critical path if the lead's next action depends on that result.
- Close completed subagents promptly after their evidence is summarized into WORKLOG, EVOLUTION, or a commit message.
- Treat custom `.codex/agents/*.toml` files as a convenience for future Codex sessions; if a Codex surface only exposes built-in `explorer` and `worker` roles, map the profile onto those roles in the prompt.

## Default Codex Shape

| Purpose | Preferred Codex role | Model posture | Reasoning posture | Write access |
|---|---|---|---|---|
| Lead/orchestrator | main session | strongest available GPT-5.x, normally inherited | high for architecture/integration | yes |
| Repository scout | `repo_explorer` or built-in `explorer` | smaller/faster acceptable | medium | no |
| Default implementation | `implementation_worker` or built-in `worker` | strong default/inherited | medium | yes, bounded |
| Fast feedback implementation | `fast_implementation_worker` or built-in `worker` with `gpt-5.3-codex-spark` | GPT-5.3-Codex-Spark research preview | low/medium | yes, tiny bounded |
| Hard implementation | `hard_worker` or built-in `worker` | strongest available | high | yes, bounded |
| Validation | `validator` or built-in `worker` | smaller/faster acceptable | low/medium | command-running only |
| Review | `reviewer` or built-in `explorer` | strongest available | high | no |

`fast_implementation_worker` is for feedback-hardening speed, not architectural judgment. Use it for small, reversible UI/template/route/test changes where the lead has already written acceptance criteria and can inspect the result with tests and Playwright. Default to `medium` reasoning for UI/route behavior; `low` is acceptable for mechanical copy/tests. Do not use Spark for schema design, security boundaries, cross-cutting refactors, or final review.

Official-source note checked on 2026-04-27: OpenAI Help lists `GPT-5.3-Codex-Spark` as a Codex research preview with non-final credit rates, and OpenAI model docs list GPT-5.3-Codex as the capable agentic coding model with `low`/`medium`/`high`/`xhigh` reasoning. Project policy therefore treats Spark as a fast implementation lane requiring lead verification, while reviewer/final-risk checks stay on `reviewer`/stronger models.

Spark context-budget note (2026-04-27): the lead must not rely on Spark to infer a minimal read set from the project's required-reading ritual. For tiny feedback-hardening slices, the lead prompt should say:

- do not cold-start-read `SPIRIT.md`, full `docs/PRD.md`, full WHY graph, `CONTEXT.md`, `WORKLOG.md`, or `EVOLUTION.md` unless explicitly told;
- use the provided context packet as the product truth for this slice;
- read only the exact implementation/test files named in the prompt, plus at most 2 targeted `rg` checks if needed;
- stop and report if those files contradict the packet instead of broad-scanning the repository;
- keep validation command-running separate from implementation when possible.

Reason: OpenAI docs describe Codex usage as token-sensitive to task size and extended sessions that require more context, while GPT-5.3-Codex-Spark is a research-preview fast lane with non-final credit rates. The project therefore treats Spark context as something the lead budgets deliberately, not a free resource.

`xhigh` is an escalation mode only: repeated failure, architecture contradiction, difficult root-cause debugging, or final high-risk review.

## v0.1 Dispatch Shape

The default v0.1 sequence is:

1. Lead does the first reconciliation: `git status`, `WORKLOG.md`, `DELEGATION-PLAN.md`, and the current sibling `../harness-architecture` availability.
2. Dispatch at most two read-only scouts if uncertainty is real:
   - schema/import scout: PRD entity mapping plus `harness-architecture` source shape;
   - route/UI scout only if the web skeleton boundaries are unclear.
3. Dispatch Task A and Task B in parallel if file ownership is clear:
   - Task A owns models, DB, and migrations;
   - Task B owns FastAPI skeleton, base templates, pyproject, and placeholder route.
4. Dispatch Task C with a hard worker after the importer input shapes and model boundaries are clear.
5. Dispatch Task E after Task A creates enough project structure for runner stubs and validator tests.
6. Dispatch Task D after A/B/C are integrated and validated.
7. Use reviewer/validator subagents after meaningful integration points, not after every tiny edit.
8. Keep at most 2-4 subagents actively working in normal flow; during feedback-hardening, the lead may briefly run up to 4 Spark workers plus one validator/reviewer when write scopes are disjoint and the lead can review every result. `agents.max_threads = 7` is headroom, not a default swarm.

## Subagent Contract

Every Codex subagent prompt must include:

- role and task boundary;
- exact file or module ownership;
- context budget and allowed read set;
- files it must not edit;
- acceptance criteria copied from `DELEGATION-PLAN.md` or PRD;
- command/test expectations;
- blocker escape hatch;
- no-commit rule;
- short report format.

### Dispatch Labels

Codex may assign human-readable nicknames automatically. Treat those nicknames
as aliases, not the stable identity of the delegation.

For WORKLOG and durable process notes, use this compact dispatch label on first
dispatch and first completion:

```text
<profile>[<model>/<reasoning>] (<nickname>)
```

Example:

```text
implementation_worker[gpt-5.5/medium] (Leibniz)
fast_implementation_worker[gpt-5.3-codex-spark/medium] (Peirce)
```

Later entries may refer to the nickname if the dispatch label was already
recorded. Omit the long agent id from ordinary notes because it consumes
attention without helping Roman or students. Include it only when a live
technical operation needs that exact id, such as `wait_agent`, `send_input`,
`resume_agent`, or `close_agent`.

Recommended report format:

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

## Lead Rules

- The lead owns architecture, integration, evidence, and final truth.
- Subagents never commit.
- Subagents do not edit outside their ownership boundary.
- Parallel write-heavy work requires disjoint write sets; Spark workers are no exception.
- If a subagent returns noisy output, the lead extracts only the durable evidence into WORKLOG/CONTEXT or the commit message.
- If direct lead implementation is safer than delegation, do it and record why.

## Official OpenAI Docs Checked

These project choices were checked against official OpenAI docs on 2026-04-26 and refreshed for Spark on 2026-04-27:

- Codex subagents can run specialized agents in parallel, but Codex should only use them when explicitly requested; parallel read-heavy tasks are a safer starting point than parallel write-heavy edits: https://developers.openai.com/codex/concepts/subagents
- Codex custom agent files can define `model`, `model_reasoning_effort`, and `sandbox_mode`; omitted fields inherit from the parent session: https://developers.openai.com/codex/subagents
- GPT-5.5 is a strong fit for complex coding and long-running agent workflows; `medium` is the default balanced reasoning effort, and `high`/`xhigh` should be justified by task complexity: https://developers.openai.com/api/docs/guides/latest-model
- Reasoning effort trades speed/cost for deeper reasoning; `xhigh` should be reserved for cases where the extra latency/cost has clear value: https://developers.openai.com/api/docs/guides/reasoning
- GPT-5.3-Codex supports `low`, `medium`, `high`, and `xhigh` reasoning effort and is the stronger review/agentic-coding reference point for the 5.3 Codex family: https://developers.openai.com/api/docs/models/gpt-5.3-codex
- GPT-5.3-Codex-Spark may be available in Codex as a research preview and its credit rates are not final; treat it as a fast lane with lead verification rather than a replacement for reviewer/hard-worker roles: https://help.openai.com/en/articles/20001106-codex-rate-card
