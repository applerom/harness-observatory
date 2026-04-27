# FILE: src/observatory/runtime/semantic_log.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Structured JSONL semantic event writer for live AgentJob sessions.
# PRD_REF: docs/PRD.md §24
# WHY_REF: docs/why-graph.xml MOD-JOBS-SERVICE
# SCOPE: semantic event envelope; append-only JSONL persistence
# INVARIANTS:
# - Events are append-only JSON objects, one per line.
# - Log writes create the parent live-sessions directory when needed.
# - Metadata stays structured JSON and defaults to an empty object.
# START_MODULE_MAP:
# - SemanticEvent: structured event payload.
# - SemanticLogWriter: append-only JSONL writer.
# :END_MODULE_MAP
# :END_MODULE_CONTRACT

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_SEMANTIC_EVENT_LOG = Path("live-sessions") / "semantic-events.jsonl"


@dataclass(frozen=True, slots=True)
class SemanticEvent:
    """One structured operational event for the live-session semantic log."""

    level: str
    code: str
    anchor: str
    expected: str
    actual: str
    job_id: int | None = None
    component: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def as_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "code": self.code,
            "anchor": self.anchor,
            "expected": self.expected,
            "actual": self.actual,
            "job_id": self.job_id,
            "component": self.component,
            "metadata": self.metadata,
        }


class SemanticLogWriter:
    """Append semantic events to a JSONL file."""

    def __init__(self, path: Path = DEFAULT_SEMANTIC_EVENT_LOG) -> None:
        self.path = path

    # START_SEMANTIC_EVENT_LOG:
    def emit(
        self,
        *,
        level: str,
        code: str,
        anchor: str,
        expected: str,
        actual: str,
        job_id: int | None = None,
        component: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SemanticEvent:
        event = SemanticEvent(
            level=level,
            code=code,
            anchor=anchor,
            expected=expected,
            actual=actual,
            job_id=job_id,
            component=component,
            metadata=metadata or {},
        )
        self.write(event)
        return event

    def write(self, event: SemanticEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(event.as_dict(), ensure_ascii=False, sort_keys=True))
            log_file.write("\n")

    # :END_SEMANTIC_EVENT_LOG
