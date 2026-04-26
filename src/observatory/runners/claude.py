# FILE: src/observatory/runners/claude.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: v0.1 ClaudeRunner placeholder satisfying AgentRunner dependency boundaries.
# PRD_REF: docs/PRD.md §24, §26.3
# WHY_REF: docs/why-graph.xml MOD-RUNNER-BASE
# SCOPE: concrete type registration; loud v0.1 non-implementation
# INVARIANTS:
# - No concrete subprocess invocation text or behavior exists in src/ during v0.1.
# - Every public execution method fails loudly until PRD §24 v0.2 work lands.
# :END_MODULE_CONTRACT

from collections.abc import AsyncIterator

from observatory.runners.base import AgentContext, AgentEvent, AgentResult


STUB_ERROR = "ClaudeRunner is a v0.1 stub; concrete subprocess invocation lands in v0.2 per PRD §24"


class ClaudeRunner:
    """v0.1 placeholder for the future Claude-backed runner."""

    name = "claude"
    version = "0.1-stub"

    async def run(self, context: AgentContext) -> AgentResult:
        """Fail loudly because v0.1 must not execute AgentJobs."""
        raise NotImplementedError(STUB_ERROR)

    def stream(self, context: AgentContext) -> AsyncIterator[AgentEvent]:
        """Fail loudly because v0.1 must not stream AgentJob execution."""
        raise NotImplementedError(STUB_ERROR)
