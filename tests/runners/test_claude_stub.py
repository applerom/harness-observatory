import asyncio

from observatory.runners.base import AgentContext, AgentEvent, AgentResult, AgentRunner
from observatory.runners.claude import ClaudeRunner


def _context() -> AgentContext:
    return AgentContext(job_id=1, job_type="refresh", prompt="Inspect one harness.")


def test_claude_runner_satisfies_protocol_shape() -> None:
    runner: AgentRunner = ClaudeRunner()

    assert runner.name == "claude"
    assert runner.version == "0.2a-cli"


def test_runner_dto_defaults_are_small_and_explicit() -> None:
    event = AgentEvent(kind="stdout", message="hello")
    result = AgentResult(status="done", output="ok", events=(event,), artifact_ids=(7,))

    assert result.events == (event,)
    assert result.artifact_ids == (7,)
    assert result.error_message is None


def test_claude_run_reports_missing_cli_without_crashing() -> None:
    runner = ClaudeRunner(executable_name="definitely-missing-observatory-claude")

    result = asyncio.run(runner.run(_context()))

    assert result.status == "failed"
    assert "not found" in (result.error_message or "")


def test_claude_stream_reports_status_events() -> None:
    runner = ClaudeRunner(executable_name="definitely-missing-observatory-claude")
    events: list[AgentEvent] = []

    async def consume_stream() -> list[AgentEvent]:
        async for event in runner.stream(_context()):
            events.append(event)
        return events

    asyncio.run(consume_stream())

    assert [event.message for event in events] == ["started", "failed"]
