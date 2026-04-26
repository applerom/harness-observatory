import json
from pathlib import Path

from observatory.runtime.semantic_log import SemanticLogWriter


def test_semantic_log_writer_appends_structured_jsonl(tmp_path: Path) -> None:
    log_path = tmp_path / "live-sessions" / "semantic-events.jsonl"
    writer = SemanticLogWriter(log_path)

    writer.emit(
        level="info",
        code="job_queued",
        anchor="START_JOB_REFRESH",
        expected="job queued",
        actual="queued refresh job 1",
        job_id=1,
        component="RefreshJobService",
        metadata={"harness_slug": "opencode"},
    )

    rows = log_path.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    payload = json.loads(rows[0])
    assert payload["timestamp"]
    assert payload["level"] == "info"
    assert payload["code"] == "job_queued"
    assert payload["anchor"] == "START_JOB_REFRESH"
    assert payload["expected"] == "job queued"
    assert payload["actual"] == "queued refresh job 1"
    assert payload["job_id"] == 1
    assert payload["component"] == "RefreshJobService"
    assert payload["metadata"] == {"harness_slug": "opencode"}
