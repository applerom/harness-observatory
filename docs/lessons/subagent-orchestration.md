# Lesson: Subagent Orchestration Is A Lifecycle

## Real Episode

During v0.1, Codex hit a thread-limit error while completed subagents were still open. The first tempting answer was "raise the limit." The better answer was more specific: increase the project-local cap modestly, but close completed subagents promptly after their evidence is summarized.

## Lesson

Subagents are not just parallel workers. They are a lifecycle:

1. Give a bounded task with ownership and acceptance criteria.
2. Let the subagent produce evidence.
3. Integrate or reject the result.
4. Summarize the outcome into durable state.
5. Close the completed thread.

Raising concurrency without lifecycle discipline creates more review load and more stale state. For this project, 2-4 active subagents is the normal range, with a fifth Codex thread kept as headroom.

## Student Exercise

After a multi-agent session, reconstruct:

- which subagent owned which files;
- what evidence each returned;
- what the lead agent changed during integration;
- which friction became a new rule.

If that reconstruction is impossible from durable files, the orchestration failed even if the code happened to work.
