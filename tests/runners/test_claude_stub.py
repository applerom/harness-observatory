import asyncio
from collections.abc import Sequence
from typing import Any

from observatory.runners.base import AgentContext, AgentEvent, AgentResult, AgentRunner
from observatory.runners.claude import ClaudeRunner


def _context() -> AgentContext:
    return AgentContext(job_id=1, job_type="refresh", prompt="Inspect one harness.")


def test_claude_runner_satisfies_protocol_shape() -> None:
    runner: AgentRunner = ClaudeRunner()

    assert runner.name == "claude"
    assert runner.version == "0.2c-cli"


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


def test_claude_preflight_reports_missing_cli_without_crashing() -> None:
    runner = ClaudeRunner(executable_name="definitely-missing-observatory-claude")

    result = asyncio.run(runner.preflight())

    assert result.ok is False
    assert "not found" in (result.error_message or "")
    assert result.metadata["executable"] == "definitely-missing-observatory-claude"


def test_claude_stream_reports_status_events() -> None:
    runner = ClaudeRunner(executable_name="definitely-missing-observatory-claude")
    events: list[AgentEvent] = []

    async def consume_stream() -> list[AgentEvent]:
        async for event in runner.stream(_context()):
            events.append(event)
        return events

    asyncio.run(consume_stream())

    assert [event.kind for event in events] == ["status", "error", "status"]
    assert events[0].message == "started"
    assert "not found" in events[1].message
    assert events[2].message == "failed"


def test_claude_stream_yields_stdout_before_process_exit(monkeypatch: Any) -> None:
    process = _FakeProcess(stdout_chunks=[(0.001, b"first\n")], exit_delay=0.05, returncode=0)

    async def fake_create_subprocess_exec(*_args: str, **_kwargs: object) -> _FakeProcess:
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    runner = ClaudeRunner()

    events = asyncio.run(_collect_stream(runner.stream(_context())))

    assert [(event.kind, event.message) for event in events] == [
        ("status", "started"),
        ("stdout", "first\n"),
        ("status", "done"),
    ]


def test_claude_stream_reports_nonzero_exit_as_failed(monkeypatch: Any) -> None:
    process = _FakeProcess(
        stdout_chunks=[(0.001, b"partial\n")],
        stderr_chunks=[(0.001, b"bad\n")],
        exit_delay=0.01,
        returncode=7,
    )

    async def fake_create_subprocess_exec(*_args: str, **_kwargs: object) -> _FakeProcess:
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    runner = ClaudeRunner()

    events = asyncio.run(_collect_stream(runner.stream(_context())))

    assert ("stdout", "partial\n") in [(event.kind, event.message) for event in events]
    assert events[-1] == AgentEvent(kind="status", message="failed")


def test_claude_stream_reports_timeout_as_failed(monkeypatch: Any) -> None:
    process = _FakeProcess(stdout_chunks=[(0.001, b"before timeout\n")], exit_delay=60, returncode=0)

    async def fake_create_subprocess_exec(*_args: str, **_kwargs: object) -> _FakeProcess:
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    runner = ClaudeRunner(timeout_seconds=0.01)

    events = asyncio.run(_collect_stream(runner.stream(_context())))

    assert ("stdout", "before timeout\n") in [(event.kind, event.message) for event in events]
    assert events[-1] == AgentEvent(kind="status", message="failed")
    assert process.killed is True


def test_claude_stream_cancellation_kills_process(monkeypatch: Any) -> None:
    process = _FakeProcess(stdout_chunks=[(0.001, b"partial\n")], exit_delay=60, returncode=0)

    async def fake_create_subprocess_exec(*_args: str, **_kwargs: object) -> _FakeProcess:
        return process

    async def consume_then_cancel() -> list[AgentEvent]:
        events: list[AgentEvent] = []
        stream = ClaudeRunner().stream(_context())
        async for event in stream:
            events.append(event)
            if event.kind == "stdout":
                await stream.aclose()  # type: ignore[attr-defined]
                break
        return events

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    events = asyncio.run(consume_then_cancel())

    assert ("stdout", "partial\n") in [(event.kind, event.message) for event in events]
    assert process.killed is True


async def _collect_stream(stream: Any) -> list[AgentEvent]:
    events: list[AgentEvent] = []
    async for event in stream:
        events.append(event)
    return events


class _FakeStream:
    def __init__(self, chunks: Sequence[tuple[float, bytes]]) -> None:
        self._chunks = list(chunks)

    async def read(self, _size: int) -> bytes:
        if not self._chunks:
            return b""
        delay, chunk = self._chunks.pop(0)
        await asyncio.sleep(delay)
        return chunk


class _FakeProcess:
    def __init__(
        self,
        *,
        stdout_chunks: Sequence[tuple[float, bytes]] = (),
        stderr_chunks: Sequence[tuple[float, bytes]] = (),
        exit_delay: float,
        returncode: int,
    ) -> None:
        self.stdout = _FakeStream(stdout_chunks)
        self.stderr = _FakeStream(stderr_chunks)
        self._exit_delay = exit_delay
        self._final_returncode = returncode
        self.returncode: int | None = None
        self.killed = False

    async def wait(self) -> int:
        await asyncio.sleep(self._exit_delay)
        if self.returncode is None:
            self.returncode = self._final_returncode
        return self.returncode

    async def communicate(self) -> tuple[bytes, bytes]:
        self.returncode = self.returncode if self.returncode is not None else -9
        return b"", b""

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9
