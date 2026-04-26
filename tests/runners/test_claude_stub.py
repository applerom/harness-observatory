import asyncio

import pytest

from observatory.runners.base import AgentContext, AgentEvent, AgentResult, AgentRunner
from observatory.runners.claude import ClaudeRunner


def _context() -> AgentContext:
    return AgentContext(job_id=1, job_type="refresh", prompt="Inspect one harness.")


def test_claude_runner_satisfies_protocol_shape() -> None:
    runner: AgentRunner = ClaudeRunner()

    assert runner.name == "claude"
    assert runner.version == "0.1-stub"


def test_runner_dto_defaults_are_small_and_explicit() -> None:
    event = AgentEvent(kind="stdout", message="hello")
    result = AgentResult(status="done", output="ok", events=(event,), artifact_ids=(7,))

    assert result.events == (event,)
    assert result.artifact_ids == (7,)
    assert result.error_message is None


def test_claude_run_raises_v01_stub_error() -> None:
    runner = ClaudeRunner()

    with pytest.raises(NotImplementedError) as exc_info:
        asyncio.run(runner.run(_context()))

    message = str(exc_info.value)
    assert "v0.1 stub" in message
    assert "PRD §24" in message


def test_claude_stream_raises_v01_stub_error() -> None:
    runner = ClaudeRunner()

    async def consume_stream() -> None:
        async for _event in runner.stream(_context()):
            pass

    with pytest.raises(NotImplementedError) as exc_info:
        asyncio.run(consume_stream())

    message = str(exc_info.value)
    assert "v0.1 stub" in message
    assert "PRD §24" in message
