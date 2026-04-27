# Lesson: Live Streaming Is A Contract

> Source episode: v0.3c/v0.4a Harness Observatory development, 2026-04-26.
> Audience: students learning agent-first software development.

The first Live Agent Studio implementation had an SSE endpoint and a fake runner
test. It looked like streaming from the web layer. A reviewer agent caught the
important missing part: the concrete `CodexRunner.stream()` and
`ClaudeRunner.stream()` methods still waited for `run()`, and `run()` used
`communicate()`. That means real CLI stdout would arrive only after process
exit.

The product word "live" is not a UI decoration. It is a runtime contract:

- the web route must stream events;
- the service must preserve raw logs and semantic events;
- the runner must read stdout/stderr incrementally;
- cancellation must not leave a subprocess or `AgentJob` stuck forever;
- tests should use delayed chunks so buffered implementations fail.

This episode is also a good delegation lesson. The lead agent owned the PRD/WHY
decision and semantic cleanup. A worker handled the bounded runner patch. A
reviewer then found the cross-boundary truth: route tests alone did not prove
real live behavior.

For students: when a system says "streaming", ask which layer actually streams.
If only the UI streams fake events after buffered work, the system is not live.
