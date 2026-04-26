# FILE: src/observatory/runners/codex.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Codex CLI backed AgentRunner implementation for v0.2 refresh jobs.
# PRD_REF: docs/PRD.md §4.10, §20, §1162
# WHY_REF: docs/why-graph.xml#MOD-RUNNER-CODEX
# SCOPE: Codex CLI subprocess boundary; read-only execution; stdout/stderr capture
# INVARIANTS:
# - Concrete Codex CLI invocation lives only in this module.
# - Runtime research jobs use read-only sandbox and never ask for approval.
# - Missing CLI, non-zero exit, and timeout return AgentResult(status="failed") instead of crashing callers.
# :END_MODULE_CONTRACT

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass

from observatory.runners.base import AgentContext, AgentEvent, AgentResult


@dataclass(slots=True)
class CodexRunner:
    """Run Codex CLI prompts for observatory AgentJobs."""

    executable_name: str = "codex"
    timeout_seconds: float = 240.0
    model: str | None = None

    name: str = "codex"
    version: str = "0.2b-cli"

    # START_CODEX_RUN:
    async def run(self, context: AgentContext) -> AgentResult:
        """Execute one prompt through Codex CLI non-interactive mode."""
        cwd = context.metadata.get("cwd") or "."
        args = [
            self.executable_name,
            "exec",
            "--sandbox",
            "read-only",
            "--ask-for-approval",
            "never",
            "--cd",
            cwd,
            "--color",
            "never",
        ]
        if self.model:
            args.extend(["--model", self.model])
        args.append(context.prompt)

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
        except TimeoutError:
            process.kill()
            await process.communicate()
            return AgentResult(
                status="failed",
                output="",
                error_message=f"Codex CLI timed out after {self.timeout_seconds:g} seconds",
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
