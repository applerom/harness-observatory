# FILE: src/observatory/runtime/__init__.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Runtime support package for operational observability helpers.
# PRD_REF: docs/PRD.md §24
# WHY_REF: docs/why-graph.xml MOD-JOBS-SERVICE
# SCOPE: semantic event logging exports
# INVARIANTS:
# - Importing this package never starts runner subprocesses or writes logs.
# :END_MODULE_CONTRACT

from observatory.runtime.semantic_log import (
    DEFAULT_SEMANTIC_EVENT_LOG,
    SemanticEvent,
    SemanticLogWriter,
)

__all__ = [
    "DEFAULT_SEMANTIC_EVENT_LOG",
    "SemanticEvent",
    "SemanticLogWriter",
]
