# FILE: src/observatory/runners/claude.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Claude CLI backed AgentRunner implementation for v0.2 refresh jobs.
# PRD_REF: docs/PRD.md §24, §26.3
# WHY_REF: docs/why-graph.xml MOD-RUNNER-BASE
# SCOPE: subprocess execution boundary; stdout/stderr capture; failure envelope
# INVARIANTS:
# - Concrete Claude CLI invocation lives only in this module.
# - Missing CLI, non-zero exit, and timeout return AgentResult(status="failed") instead of crashing callers.
# :END_MODULE_CONTRACT

import asyncio
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from contextlib import suppress
from pathlib import Path

from observatory.runners.base import AgentContext, AgentEvent, AgentPreflightResult, AgentResult


WINDOWS_RUNNABLE_EXTENSIONS = (".exe", ".cmd", ".bat", ".com")


@dataclass(slots=True)
class ClaudeRunner:
    """Run Claude CLI prompts for observatory AgentJobs."""

    executable_name: str = "claude"
    timeout_seconds: float = 120.0

    name: str = "claude"
    version: str = "0.2c-cli"

    # START_CLAUDE_PREFLIGHT:
    async def preflight(self) -> AgentPreflightResult:
        """Resolve Claude CLI and read its version without running a model call."""
        executable = resolve_runnable_command(self.executable_name)
        try:
            process = await asyncio.create_subprocess_exec(
                executable,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=min(self.timeout_seconds, 15.0),
            )
        except FileNotFoundError as exc:
            return AgentPreflightResult(
                ok=False,
                error_message=f"Claude CLI executable not found: {exc.filename}",
                metadata={"executable": executable},
            )
        except asyncio.TimeoutError:
            await _clean_up_timed_out_process(process)
            return AgentPreflightResult(
                ok=False,
                error_message="Claude CLI version preflight timed out",
                metadata={"executable": executable},
            )
        except OSError as exc:
            return AgentPreflightResult(
                ok=False,
                error_message=f"Claude CLI failed to launch: {exc}",
                metadata={"executable": executable},
            )

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        output = (stdout + stderr).strip()
        if process.returncode != 0:
            return AgentPreflightResult(
                ok=False,
                output=output,
                error_message=output or f"Claude CLI --version exited with code {process.returncode}",
                metadata={"executable": executable},
            )
        return AgentPreflightResult(
            ok=True,
            output=output,
            metadata={"executable": executable, "version_output": output},
        )

    # :END_CLAUDE_PREFLIGHT

    # START_CLAUDE_RUN:
    async def run(self, context: AgentContext) -> AgentResult:
        """Execute one prompt through the configured Claude CLI."""
        cwd = context.metadata.get("cwd") or None
        executable = resolve_runnable_command(self.executable_name)
        try:
            process = await asyncio.create_subprocess_exec(
                executable,
                "-p",
                context.prompt,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )
        except FileNotFoundError as exc:
            return AgentResult(
                status="failed",
                output="",
                error_message=f"Claude CLI executable not found: {exc.filename}",
            )
        except TimeoutError:
            process.kill()
            await process.communicate()
            return AgentResult(
                status="failed",
                output="",
                error_message=f"Claude CLI timed out after {self.timeout_seconds:g} seconds",
            )
        except OSError as exc:
            return AgentResult(
                status="failed",
                output="",
                error_message=f"Claude CLI failed to launch: {exc}",
            )

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        events = (
            AgentEvent(kind="stdout", message=stdout),
            AgentEvent(kind="stderr", message=stderr),
        )
        if process.returncode == 0:
            return AgentResult(status="done", output=stdout, events=events)
        return AgentResult(
            status="failed",
            output=stdout,
            events=events,
            error_message=stderr.strip() or f"Claude CLI exited with code {process.returncode}",
        )

    def stream(self, context: AgentContext) -> AsyncIterator[AgentEvent]:
        """Yield subprocess output incrementally for Live Agent Studio callers."""
        return self._stream(context)

    async def _stream(self, context: AgentContext) -> AsyncIterator[AgentEvent]:
        yield AgentEvent(kind="status", message="started")
        cwd = context.metadata.get("cwd") or None
        executable = resolve_runnable_command(self.executable_name)
        try:
            process = await asyncio.create_subprocess_exec(
                executable,
                "-p",
                context.prompt,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            yield AgentEvent(
                kind="error",
                message=f"Claude CLI executable not found: {exc.filename}",
            )
            yield AgentEvent(kind="status", message="failed")
            return
        except OSError as exc:
            yield AgentEvent(kind="error", message=f"Claude CLI failed to launch: {exc}")
            yield AgentEvent(kind="status", message="failed")
            return

        async for event in _stream_process_output(
            process=process,
            timeout_seconds=self.timeout_seconds,
            timeout_message=f"Claude CLI timed out after {self.timeout_seconds:g} seconds",
        ):
            yield event

    # :END_CLAUDE_RUN


def resolve_runnable_command(executable_name: str) -> str:
    """Resolve a Windows-runnable Claude CLI command without choosing npm shims."""
    if not _is_windows():
        return executable_name

    executable_path = Path(executable_name)
    if executable_path.suffix:
        return executable_name

    if executable_path.parent != Path("."):
        for suffix in WINDOWS_RUNNABLE_EXTENSIONS:
            candidate = executable_path.with_suffix(suffix)
            if candidate.is_file():
                return str(candidate)
        return executable_name

    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not directory:
            continue
        base = Path(directory) / executable_name
        for suffix in WINDOWS_RUNNABLE_EXTENSIONS:
            candidate = base.with_suffix(suffix)
            if candidate.is_file():
                return str(candidate)
    return executable_name


def _is_windows() -> bool:
    return os.name == "nt"


async def _stream_process_output(
    *,
    process: asyncio.subprocess.Process,
    timeout_seconds: float,
    timeout_message: str,
) -> AsyncIterator[AgentEvent]:
    """Stream stdout/stderr chunks until the process reaches a terminal state."""
    queue: asyncio.Queue[AgentEvent] = asyncio.Queue()
    pump_tasks = [
        asyncio.create_task(_pump_stream("stdout", process.stdout, queue)),
        asyncio.create_task(_pump_stream("stderr", process.stderr, queue)),
    ]
    wait_task = asyncio.create_task(process.wait())
    deadline = asyncio.get_running_loop().time() + timeout_seconds

    try:
        while True:
            if wait_task.done() and all(task.done() for task in pump_tasks) and queue.empty():
                break

            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                await _clean_up_timed_out_process(process)
                yield AgentEvent(kind="error", message=timeout_message)
                yield AgentEvent(kind="status", message="failed")
                return

            get_task = asyncio.create_task(queue.get())
            done, _pending = await asyncio.wait(
                [get_task, wait_task, *pump_tasks],
                timeout=remaining,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if get_task in done:
                yield get_task.result()
            else:
                get_task.cancel()
                with suppress(asyncio.CancelledError):
                    await get_task
    finally:
        for task in pump_tasks:
            if not task.done():
                task.cancel()
        for task in pump_tasks:
            with suppress(asyncio.CancelledError):
                await task
        if not wait_task.done():
            wait_task.cancel()
            with suppress(asyncio.CancelledError):
                await wait_task
        if process.returncode is None:
            await _clean_up_timed_out_process(process)

    yield AgentEvent(kind="status", message="done" if process.returncode == 0 else "failed")


async def _pump_stream(
    kind: str,
    stream: asyncio.StreamReader | None,
    queue: asyncio.Queue[AgentEvent],
) -> None:
    if stream is None:
        return
    while chunk := await stream.read(4096):
        queue.put_nowait(AgentEvent(kind=kind, message=chunk.decode("utf-8", errors="replace")))


async def _clean_up_timed_out_process(process: asyncio.subprocess.Process) -> None:
    if process.returncode is None:
        try:
            process.kill()
        except ProcessLookupError:
            pass
    with suppress(ProcessLookupError):
        await process.communicate()
