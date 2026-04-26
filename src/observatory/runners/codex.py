# FILE: src/observatory/runners/codex.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Codex CLI backed AgentRunner implementation for v0.2 refresh jobs.
# PRD_REF: docs/PRD.md §4.10, §20, §1162
# WHY_REF: docs/why-graph.xml#MOD-RUNNER-CODEX
# SCOPE: Codex CLI subprocess boundary; read-only execution; stdout/stderr capture; cheap version preflight
# INVARIANTS:
# - Concrete Codex CLI invocation lives only in this module.
# - Runtime research jobs use read-only sandbox and never ask for approval.
# - Missing CLI, non-zero exit, timeout, and incompatible local versions fail without crashing callers.
# :END_MODULE_CONTRACT

import asyncio
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

from observatory.runners.base import AgentContext, AgentEvent, AgentPreflightResult, AgentResult


WINDOWS_RUNNABLE_EXTENSIONS = (".exe", ".cmd", ".bat", ".com")
GPT_5_5_MIN_CODEX_VERSION = (0, 125, 0)


@dataclass(slots=True)
class CodexRunner:
    """Run Codex CLI prompts for observatory AgentJobs."""

    executable_name: str = "codex"
    timeout_seconds: float = 240.0
    model: str | None = None

    name: str = "codex"
    version: str = "0.2c-cli"

    # START_CODEX_PREFLIGHT:
    async def preflight(self) -> AgentPreflightResult:
        """Resolve Codex CLI and read its version without running a model call."""
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
                error_message=f"Codex CLI executable not found: {exc.filename}",
                metadata={"executable": executable},
            )
        except asyncio.TimeoutError:
            await _clean_up_timed_out_process(process)
            return AgentPreflightResult(
                ok=False,
                error_message="Codex CLI version preflight timed out",
                metadata={"executable": executable},
            )
        except OSError as exc:
            return AgentPreflightResult(
                ok=False,
                error_message=f"Codex CLI failed to launch: {exc}",
                metadata={"executable": executable},
            )

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        output = (stdout + stderr).strip()
        if process.returncode != 0:
            return AgentPreflightResult(
                ok=False,
                output=output,
                error_message=output or f"Codex CLI --version exited with code {process.returncode}",
                metadata={"executable": executable},
            )

        version = parse_codex_version(output)
        metadata = {"executable": executable, "version_output": output}
        if version is not None:
            metadata["version"] = ".".join(str(part) for part in version)
        if self.model == "gpt-5.5" and version is not None and version < GPT_5_5_MIN_CODEX_VERSION:
            return AgentPreflightResult(
                ok=False,
                output=output,
                error_message=(
                    "Codex CLI model preflight failed: model gpt-5.5 requires "
                    "Codex CLI >= 0.125.0; installed version is "
                    f"{metadata['version']}"
                ),
                metadata=metadata,
            )
        return AgentPreflightResult(ok=True, output=output, metadata=metadata)

    # :END_CODEX_PREFLIGHT

    # START_CODEX_RUN:
    async def run(self, context: AgentContext) -> AgentResult:
        """Execute one prompt through Codex CLI non-interactive mode."""
        cwd = context.metadata.get("cwd") or "."
        executable = resolve_runnable_command(self.executable_name)
        args = build_codex_exec_args(
            executable=executable,
            cwd=cwd,
            prompt=context.prompt,
            model=self.model,
        )

        try:
            process = await asyncio.create_subprocess_exec(
                *args,
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
                error_message=f"Codex CLI executable not found: {exc.filename}",
            )
        except asyncio.TimeoutError:
            await _clean_up_timed_out_process(process)
            return AgentResult(
                status="failed",
                output="",
                error_message=f"Codex CLI timed out after {self.timeout_seconds:g} seconds",
            )
        except OSError as exc:
            return AgentResult(
                status="failed",
                output="",
                error_message=f"Codex CLI failed to launch: {exc}",
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
            error_message=stderr.strip() or f"Codex CLI exited with code {process.returncode}",
        )

    def stream(self, context: AgentContext) -> AsyncIterator[AgentEvent]:
        """Yield a small event stream for callers that want progress shape now."""
        return self._stream(context)

    async def _stream(self, context: AgentContext) -> AsyncIterator[AgentEvent]:
        yield AgentEvent(kind="status", message="started")
        result = await self.run(context)
        for event in result.events:
            if event.message:
                yield event
        yield AgentEvent(kind="status", message=result.status)

    # :END_CODEX_RUN


def resolve_runnable_command(executable_name: str) -> str:
    """Resolve a Windows-runnable Codex CLI command without choosing npm shims."""
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


def build_codex_exec_args(
    *,
    executable: str,
    cwd: str,
    prompt: str,
    model: str | None = None,
) -> list[str]:
    """Build Codex exec argv with global-only options before the subcommand."""
    args = [
        executable,
        "--ask-for-approval",
        "never",
        "exec",
        "--sandbox",
        "read-only",
        "--cd",
        cwd,
        "--color",
        "never",
    ]
    if model:
        args.extend(["--model", model])
    args.append(prompt)
    return args


def parse_codex_version(output: str) -> tuple[int, int, int] | None:
    """Parse the first semantic version from Codex CLI version output."""
    for token in output.replace(",", " ").split():
        cleaned = token.strip().lstrip("v")
        parts = cleaned.split(".")
        if len(parts) < 2:
            continue
        numeric_parts: list[int] = []
        for part in parts[:3]:
            digits = []
            for char in part:
                if char.isdigit():
                    digits.append(char)
                else:
                    break
            if not digits:
                break
            numeric_parts.append(int("".join(digits)))
        if len(numeric_parts) >= 2:
            while len(numeric_parts) < 3:
                numeric_parts.append(0)
            return numeric_parts[0], numeric_parts[1], numeric_parts[2]
    return None


async def _clean_up_timed_out_process(process: asyncio.subprocess.Process) -> None:
    """Best-effort cleanup after communicate() times out."""
    if process.returncode is None:
        try:
            process.kill()
        except ProcessLookupError:
            pass
    try:
        await process.communicate()
    except ProcessLookupError:
        pass


def _is_windows() -> bool:
    return os.name == "nt"
