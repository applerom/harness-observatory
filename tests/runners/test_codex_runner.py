import asyncio
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from observatory.runners.base import AgentContext, AgentEvent, AgentRunner
from observatory.runners import codex
from observatory.runners.codex import CodexRunner, build_codex_exec_args, parse_codex_version
from observatory.web.routes.harness import CODEX_REFRESH_MODEL, CODEX_REFRESH_TIMEOUT_SECONDS, make_refresh_runner


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
    assert runner.version == "0.2c-cli"


def test_codex_exec_args_put_global_approval_before_exec() -> None:
    args = build_codex_exec_args(
        executable="codex",
        cwd="D:/ai/harnesses/harness-observatory",
        prompt="Inspect one harness.",
        model="gpt-5.4",
    )

    exec_index = args.index("exec")
    approval_index = args.index("--ask-for-approval")

    assert approval_index < exec_index
    assert args[approval_index + 1] == "never"
    assert args[exec_index + 1 : exec_index + 3] == ["--sandbox", "read-only"]
    assert "--model" in args[exec_index:]
    assert args[-1] == "Inspect one harness."


def test_codex_refresh_factory_uses_gpt_5_5_timeout() -> None:
    runner = make_refresh_runner("codex")

    assert isinstance(runner, CodexRunner)
    assert runner.model == CODEX_REFRESH_MODEL
    assert runner.timeout_seconds == CODEX_REFRESH_TIMEOUT_SECONDS


def test_codex_run_reports_missing_cli_without_crashing() -> None:
    runner = CodexRunner(executable_name="definitely-missing-observatory-codex")

    result = asyncio.run(runner.run(_context()))

    assert result.status == "failed"
    assert "not found" in (result.error_message or "")


def test_codex_runner_prefers_windows_runnable_extension(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extensionless_shim = tmp_path / "codex"
    command_shim = tmp_path / "codex.cmd"
    extensionless_shim.write_text("not directly runnable by CreateProcess", encoding="utf-8")
    command_shim.write_text("@echo off\n", encoding="utf-8")
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setattr(codex, "_is_windows", lambda: True)

    assert codex.resolve_runnable_command("codex") == str(command_shim)


def test_parse_codex_version_reads_semantic_version() -> None:
    assert parse_codex_version("codex-cli 0.124.0") == (0, 124, 0)
    assert parse_codex_version("codex v0.125.1") == (0, 125, 1)


def test_codex_preflight_rejects_gpt_5_5_on_old_cli_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class VersionProcess:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"codex-cli 0.124.0\n", b""

    async def fake_create_subprocess_exec(*args: str, **_kwargs: object) -> VersionProcess:
        assert args[-1] == "--version"
        return VersionProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    runner = CodexRunner(model="gpt-5.5")

    result = asyncio.run(runner.preflight())

    assert not result.ok
    assert "requires Codex CLI >= 0.125.0" in (result.error_message or "")
    assert result.metadata["version"] == "0.124.0"


def test_codex_preflight_accepts_gpt_5_5_on_new_cli_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class VersionProcess:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"codex-cli 0.125.0\n", b""

    async def fake_create_subprocess_exec(*_args: str, **_kwargs: object) -> VersionProcess:
        return VersionProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    runner = CodexRunner(model="gpt-5.5")

    result = asyncio.run(runner.preflight())

    assert result.ok
    assert result.metadata["version"] == "0.125.0"


def test_codex_run_reports_permission_launch_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def raise_permission_error(*_args: str, **_kwargs: object) -> object:
        raise PermissionError(5, "Access is denied")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", raise_permission_error)
    runner = CodexRunner()

    result = asyncio.run(runner.run(_context()))

    assert result.status == "failed"
    assert "failed to launch" in (result.error_message or "")
    assert "Access is denied" in (result.error_message or "")


def test_codex_run_reports_timeout_and_kills_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class TimeoutProcess:
        returncode: int | None = None

        def __init__(self) -> None:
            self.communicate_calls = 0
            self.killed = False

        async def communicate(self) -> tuple[bytes, bytes]:
            self.communicate_calls += 1
            if self.communicate_calls == 1:
                await asyncio.sleep(60)
            return b"", b""

        def kill(self) -> None:
            self.killed = True
            self.returncode = -9

    process = TimeoutProcess()

    async def fake_create_subprocess_exec(*_args: str, **_kwargs: object) -> TimeoutProcess:
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    runner = CodexRunner(timeout_seconds=0.001)

    result = asyncio.run(runner.run(_context()))

    assert result.status == "failed"
    assert result.error_message == "Codex CLI timed out after 0.001 seconds"
    assert process.killed is True
    assert process.communicate_calls == 2


def test_codex_run_timeout_cleanup_tolerates_already_exited_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class AlreadyExitedProcess:
        returncode: int | None = 0

        def __init__(self) -> None:
            self.communicate_calls = 0
            self.kill_calls = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            self.communicate_calls += 1
            return b"", b""

        def kill(self) -> None:
            self.kill_calls += 1

    process = AlreadyExitedProcess()

    async def fake_create_subprocess_exec(*_args: str, **_kwargs: object) -> AlreadyExitedProcess:
        return process

    async def fake_wait_for(awaitable: Any, timeout: float) -> object:
        assert timeout == 2.0
        awaitable.close()
        raise asyncio.TimeoutError

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(asyncio, "wait_for", fake_wait_for)
    runner = CodexRunner(timeout_seconds=2.0)

    result = asyncio.run(runner.run(_context()))

    assert result.status == "failed"
    assert result.error_message == "Codex CLI timed out after 2 seconds"
    assert process.kill_calls == 0
    assert process.communicate_calls == 1


def test_codex_stream_reports_status_events() -> None:
    runner = CodexRunner(executable_name="definitely-missing-observatory-codex")
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


def test_codex_stream_yields_stdout_before_process_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    process = _FakeProcess(stdout_chunks=[(0.001, b"first\n")], exit_delay=0.05, returncode=0)

    async def fake_create_subprocess_exec(*_args: str, **_kwargs: object) -> _FakeProcess:
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    runner = CodexRunner()

    events = asyncio.run(_collect_stream(runner.stream(_context())))

    assert [(event.kind, event.message) for event in events] == [
        ("status", "started"),
        ("stdout", "first\n"),
        ("status", "done"),
    ]


def test_codex_stream_reports_nonzero_exit_as_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    process = _FakeProcess(
        stdout_chunks=[(0.001, b"partial\n")],
        stderr_chunks=[(0.001, b"bad\n")],
        exit_delay=0.01,
        returncode=7,
    )

    async def fake_create_subprocess_exec(*_args: str, **_kwargs: object) -> _FakeProcess:
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    runner = CodexRunner()

    events = asyncio.run(_collect_stream(runner.stream(_context())))

    assert ("stdout", "partial\n") in [(event.kind, event.message) for event in events]
    assert events[-1] == AgentEvent(kind="status", message="failed")


def test_codex_stream_reports_timeout_as_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    process = _FakeProcess(stdout_chunks=[(0.001, b"before timeout\n")], exit_delay=60, returncode=0)

    async def fake_create_subprocess_exec(*_args: str, **_kwargs: object) -> _FakeProcess:
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    runner = CodexRunner(timeout_seconds=0.01)

    events = asyncio.run(_collect_stream(runner.stream(_context())))

    assert ("stdout", "before timeout\n") in [(event.kind, event.message) for event in events]
    assert events[-1] == AgentEvent(kind="status", message="failed")
    assert process.killed is True


def test_codex_stream_reports_permission_launch_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def raise_permission_error(*_args: str, **_kwargs: object) -> object:
        raise PermissionError(5, "Access is denied")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", raise_permission_error)
    runner = CodexRunner()

    events = asyncio.run(_collect_stream(runner.stream(_context())))

    assert events[-1] == AgentEvent(kind="status", message="failed")
    assert "Access is denied" in events[-2].message


def test_codex_stream_cancellation_kills_process(monkeypatch: pytest.MonkeyPatch) -> None:
    process = _FakeProcess(stdout_chunks=[(0.001, b"partial\n")], exit_delay=60, returncode=0)

    async def fake_create_subprocess_exec(*_args: str, **_kwargs: object) -> _FakeProcess:
        return process

    async def consume_then_cancel() -> list[AgentEvent]:
        events: list[AgentEvent] = []
        stream = CodexRunner().stream(_context())
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
