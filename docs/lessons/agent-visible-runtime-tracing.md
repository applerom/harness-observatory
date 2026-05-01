# Lesson: Give Agents Runtime Instruments

> Source episode: v0.2a-v0.2c Harness Observatory development, 2026-04-26.
> Audience: students learning agent-first software development.

An agent can work much better when the harness gives it feedback it can inspect.

In this project, Playwright CLI changed the frontend loop. Before that, the
agent could write UI code and run backend tests, but human still had to report
that a wide matrix was hard to use. After Playwright visual checks existed, the
agent could verify that the top scrollbar was present and that clicking a matrix
cell revealed the detail region. That is not magic vision; it is tooling that
turns UI behavior into evidence the agent can read.

Runtime work needs the same idea. Raw stdout is useful, but it is often too
unstructured. A semantic event says:

- what step was running;
- which WHY/module anchor the step belongs to;
- what was expected;
- what actually happened;
- which component owns the problem.

That makes debugging cheaper in tokens and time. The next agent does not have
to reverse-engineer the whole story from code, logs, and memory. It can start
from a trace written in the system's own concepts.

The important habit is not "log everything." The habit is to make important
runtime boundaries visible in the language of the project.
