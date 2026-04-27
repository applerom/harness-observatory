# Lesson: Orchestrator Agents Also Over-Execute

## Real Episode

Codex lead agent fixed the comparison matrix scrollbar, scroll-to-detail behavior, and first Playwright visual test directly.

The outcome was good: the UI improved and the new visual QA check passed. But Roman noticed a process problem: this was a bounded implementation task that could have been delegated after the lead agent made the PRD and WHY graph decisions.

## Lesson

Strong agents can do the work, so they often do. That is not always the best use of the strongest agent.

In an agent-first project, the lead agent should preserve attention for:

- intent and product judgment;
- PRD and WHY graph updates;
- delegation design;
- integration review;
- semantic consistency;
- final evidence.

Bounded implementation tasks should usually go to subagents.

## Nuance

Direct lead implementation can still be correct when the lead is establishing a new project pattern. In this episode, the first Playwright CLI setup was partly pattern-setting, so lead involvement was defensible.

The reusable rule is: after the pattern exists, delegate similar work.

## Student Exercise

After a successful agent-built change, ask:

- Did the strongest agent need to implement this?
- Could a smaller subagent have owned the patch?
- Did the lead agent spend context on work it should have reviewed instead?
- If direct implementation was chosen, was the reason recorded?
