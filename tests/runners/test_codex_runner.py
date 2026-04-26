import asyncio

from observatory.runners.base import AgentContext, AgentEvent, AgentRunner
from observatory.runners.codex import CodexRunner


def _context() -> AgentContext:
    return AgentContext(
        job_id=1,
        job_type="refresh",
        prompt="Inspect one harness.",
        metadata={"cwd": "."},
    )


def test_codex_runner_satisfies_protocol_shape() -> None:
    runner: AgentRunner = CodexRunner()

    assert runner.name == "codex"
    assert runner.version == "0.2b-cli"


def test_codex_run_reports_missing_cli_without_crashing() -> None:
    runner = CodexRunner(executable_name="definitely-missing-observatory-codex")

    result = asyncio.run(runner.run(_context()))

    assert result.status == "failed"
    assert "not found" in (result.error_message or "")


def test_codex_stream_reports_status_events() -> None:
    runner = CodexRunner(executable_name="definitely-missing-observatory-codex")
    events: list[AgentEvent] = []

    async def consume_stream() -> list[AgentEvent]:
        async for event in runner.stream(_context()):
            events.append(event)
        return events

    asyncio.run(consume_stream())

    assert [event.message for event in events] == ["started", "failed"]
