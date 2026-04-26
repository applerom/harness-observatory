# FILE: src/observatory/runners/base.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: AgentRunner protocol and small DTOs for future runtime agent dispatch.
# PRD_REF: docs/PRD.md §24, §26.3
# WHY_REF: docs/why-graph.xml MOD-RUNNER-BASE
# SCOPE: runner protocol; event context; result envelope; optional preflight envelope
# INVARIANTS:
# - v0.1 defines types only; no AgentJob is created, started, or dispatched here.
# - Runner implementations must report progress through AgentEvent and final state through AgentResult.
# START_MODULE_MAP:
# - AgentEvent: append-only event emitted by future runner implementations.
# - AgentContext: immutable job input envelope passed to a runner.
# - AgentResult: final runner outcome envelope.
# - AgentPreflightResult: cheap runner readiness outcome envelope.
# - AgentRunner: structural Protocol for concrete runners.
# :END_MODULE_MAP
# :END_MODULE_CONTRACT

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AgentEvent:
    """Single append-only event produced during a future AgentJob run."""

    kind: str
    message: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AgentContext:
    """Input envelope for future runtime agent execution."""

    job_id: int
    job_type: str
    prompt: str
    target_kind: str | None = None
    target_id: int | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)


# START_RUNNER_JOB_RESULT:
@dataclass(frozen=True, slots=True)
class AgentResult:
    """Final outcome from a future AgentRunner invocation."""

    status: str
    output: str
    events: tuple[AgentEvent, ...] = ()
    artifact_ids: tuple[int, ...] = ()
    error_message: str | None = None


# :END_RUNNER_JOB_RESULT


# START_RUNNER_PREFLIGHT_RESULT:
@dataclass(frozen=True, slots=True)
class AgentPreflightResult:
    """Cheap runner readiness check result, with no model invocation."""

    ok: bool
    output: str = ""
    error_message: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)


# :END_RUNNER_PREFLIGHT_RESULT


# START_RUNNER_PROTOCOL:
class AgentRunner(Protocol):
    """Structural interface for runtime agent runners."""

    name: str
    version: str

    async def run(self, context: AgentContext) -> AgentResult:
        """Run one AgentJob context and return the final result."""
        ...

    def stream(self, context: AgentContext) -> AsyncIterator[AgentEvent]:
        """Yield progress events for one AgentJob context."""
        ...


# :END_RUNNER_PROTOCOL
