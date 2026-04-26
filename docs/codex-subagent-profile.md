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
| Hard implementation | `hard_worker` or built-in `worker` | strongest available | high | yes, bounded |
| Validation | `validator` or built-in `worker` | smaller/faster acceptable | low/medium | command-running only |
| Review | `reviewer` or built-in `explorer` | strongest available | high | no |

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
8. Keep at most 2-4 subagents actively working in normal flow; the fifth thread is operational headroom for a validator or follow-up worker.

## Subagent Contract

Every Codex subagent prompt must include:

- role and task boundary;
- exact file or module ownership;
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
<profile>[<model>/<reasoning>] (<nickname>, <agent-id>)
```

Example:

```text
implementation_worker[gpt-5.5/medium] (Leibniz, 019d...)
```

Later entries may refer to the nickname or agent id if the dispatch label was
already recorded. The stable part is profile/model/reasoning; the nickname is
lookup metadata for the current Codex session.

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
- Parallel write-heavy work requires disjoint write sets.
- If a subagent returns noisy output, the lead extracts only the durable evidence into WORKLOG/CONTEXT or the commit message.
- If direct lead implementation is safer than delegation, do it and record why.

## Official OpenAI Docs Checked

These project choices were checked against official OpenAI docs on 2026-04-26:

- Codex subagents can run specialized agents in parallel, but Codex should only use them when explicitly requested; parallel read-heavy tasks are a safer starting point than parallel write-heavy edits: https://developers.openai.com/codex/concepts/subagents
- Codex custom agent files can define `model`, `model_reasoning_effort`, and `sandbox_mode`; omitted fields inherit from the parent session: https://developers.openai.com/codex/subagents
- GPT-5.5 is a strong fit for complex coding and long-running agent workflows; `medium` is the default balanced reasoning effort, and `high`/`xhigh` should be justified by task complexity: https://developers.openai.com/api/docs/guides/latest-model
- Reasoning effort trades speed/cost for deeper reasoning; `xhigh` should be reserved for cases where the extra latency/cost has clear value: https://developers.openai.com/api/docs/guides/reasoning
