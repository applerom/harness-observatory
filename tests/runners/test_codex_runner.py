import asyncio
from pathlib import Path

import pytest

from observatory.runners.base import AgentContext, AgentEvent, AgentRunner
from observatory.runners import codex
from observatory.runners.codex import CodexRunner, build_codex_exec_args


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


def test_codex_stream_reports_status_events() -> None:
    runner = CodexRunner(executable_name="definitely-missing-observatory-codex")
    events: list[AgentEvent] = []

    async def consume_stream() -> list[AgentEvent]:
        async for event in runner.stream(_context()):
            events.append(event)
        return events

    asyncio.run(consume_stream())

    assert [event.message for event in events] == ["started", "failed"]
