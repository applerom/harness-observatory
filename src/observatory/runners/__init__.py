# FILE: src/observatory/runners/__init__.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Public package surface for AgentRunner abstractions and v0.1 runner stubs.
# PRD_REF: docs/PRD.md §26.3
# WHY_REF: docs/why-graph.xml MOD-RUNNER-BASE
# SCOPE: runner type exports
# INVARIANTS:
# - Importing observatory.runners never dispatches AgentJobs or starts subprocesses.
# :END_MODULE_CONTRACT

from observatory.runners.base import AgentContext, AgentEvent, AgentResult, AgentRunner
from observatory.runners.claude import ClaudeRunner

__all__ = [
    "AgentContext",
    "AgentEvent",
    "AgentResult",
    "AgentRunner",
    "ClaudeRunner",
]
