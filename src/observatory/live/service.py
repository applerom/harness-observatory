# FILE: src/observatory/live/service.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Live Agent Studio AgentJob creation and SSE execution helpers.
# PRD_REF: docs/PRD.md §11.8, §24
# WHY_REF: docs/why-graph.xml#FEAT-LIVE-AGENT-STUDIO
# SCOPE: live discover job creation; per-job prompt storage; streamed runner execution; raw log persistence
# INVARIANTS:
# - Live jobs execute only when the SSE stream endpoint is consumed.
# - Runtime execution stays behind the AgentRunner.stream abstraction.
# - Raw live session output is preserved in live-sessions/agent-job-*.log.
# :END_MODULE_CONTRACT

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session

from observatory.jobs.service import DEFAULT_LOG_DIR, resolve_target_cwd, validate_target_cwd
from observatory.models import AgentJob, Harness
from observatory.runners.base import AgentContext, AgentEvent, AgentRunner
from observatory.runtime.semantic_log import SemanticLogWriter


LiveRunnerFactory = Callable[[str], AgentRunner]


def utc_now() -> datetime:
    return datetime.now(UTC)


# START_LIVE_JOB_CREATE:
def create_live_discover_job(
    session: Session,
    *,
    harness: Harness,
    runner: AgentRunner,
    task_prompt: str,
) -> AgentJob:
    """Persist a queued live discover job without executing the runner."""
    job = AgentJob(
        type="discover",
        target_kind="Harness",
        target_id=harness.id,
        prompt_text=task_prompt.strip(),
        runner_name=runner.name,
        runner_version=runner.version,
        trigger="live",
        status="queued",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


# :END_LIVE_JOB_CREATE


# START_LIVE_JOB_STREAM:
async def stream_live_job(
    session: Session,
    *,
    job_id: int,
    runner_factory: LiveRunnerFactory,
    log_dir: Path = DEFAULT_LOG_DIR,
    semantic_log: SemanticLogWriter | None = None,
) -> AsyncIterator[str]:
    """Execute a queued live job and emit Server-Sent Events."""
    semantic_log = semantic_log or SemanticLogWriter(log_dir / "semantic-events.jsonl")
    job = session.get(AgentJob, job_id)
    if job is None:
        yield sse("error", {"message": "AgentJob not found"})
        return
    if job.trigger != "live":
        yield sse("error", {"message": "AgentJob is not a live job"})
        return
    if job.status != "queued":
        yield sse("status", {"message": f"job is {job.status}", "job_status": job.status})
        return

    harness = session.get(Harness, job.target_id) if job.target_kind == "Harness" else None
    if harness is None or not job.prompt_text:
        await fail_job(session, job, log_dir, "Live job target or prompt text is missing")
        yield sse("error", {"message": job.error_message or "Live job is incomplete"})
        yield sse("status", {"message": "failed", "job_status": "failed"})
        return

    runner = runner_factory(job.runner_name or "")
    log_path = live_log_path(log_dir, job)
    job.started_at = utc_now()
    job.status = "running"
    job.stdout_log_path = log_path.as_posix()
    session.add(job)
    session.commit()
    session.refresh(job)
    emit_live_event(
        semantic_log,
        level="info",
        code="live_job_running",
        expected="Live AgentJob enters running state when SSE is consumed",
        actual=f"running live job {job.id}",
        job=job,
        metadata={"runner_name": runner.name, "harness_slug": harness.slug},
    )
    yield sse("status", {"message": "running", "job_status": "running"})

    resolved_cwd = resolve_target_cwd(harness)
    target_error = validate_target_cwd(resolved_cwd.path, harness.local_upstream_path)
    if target_error is not None:
        append_live_log(log_path, target_error)
        job.finished_at = utc_now()
        job.status = "failed"
        job.error_message = target_error
        session.add(job)
        session.commit()
        emit_live_event(
            semantic_log,
            level="error",
            code="live_target_cwd_preflight_failed",
            expected="live harness target cwd exists before runner stream",
            actual=target_error,
            job=job,
            metadata={
                "configured_cwd": harness.local_upstream_path or "",
                "harness_slug": harness.slug,
            },
        )
        yield sse("error", {"message": target_error})
        yield sse("status", {"message": "failed", "job_status": "failed"})
        return

    emit_live_event(
        semantic_log,
        level="info",
        code="live_target_cwd_preflight_succeeded",
        expected="live target cwd is available before runner stream",
        actual=f"target cwd available: {resolved_cwd.path}",
        job=job,
        metadata={
            "cwd": resolved_cwd.path,
            "configured_cwd": harness.local_upstream_path or "",
            "harness_slug": harness.slug,
            "resolved_from_stale_path": resolved_cwd.repaired_from or "",
        },
    )

    terminal_status = "done"
    context = AgentContext(
        job_id=job.id or 0,
        job_type=job.type,
        prompt=job.prompt_text,
        target_kind=job.target_kind,
        target_id=job.target_id,
        metadata={"cwd": resolved_cwd.path, "harness_slug": harness.slug},
    )
    try:
        async for event in runner.stream(context):
            append_live_event(log_path, event)
            if event.kind == "status" and event.message in {"done", "failed", "timeout"}:
                terminal_status = event.message
            yield sse(event.kind, {"kind": event.kind, "message": event.message})
    except asyncio.CancelledError:
        terminal_status = "failed"
        error_message = "Live stream cancelled before terminal runner status"
        append_live_log(log_path, f"[error]\n{error_message}")
        job.finished_at = utc_now()
        job.status = terminal_status
        job.error_message = error_message
        session.add(job)
        session.commit()
        emit_live_event(
            semantic_log,
            level="error",
            code="live_runner_stream_cancelled",
            expected="client stream remains connected until terminal runner status",
            actual=error_message,
            job=job,
            metadata={"runner_name": runner.name},
        )
        return
    except Exception as exc:
        terminal_status = "failed"
        error_message = f"AgentRunner {runner.name} stream failed: {type(exc).__name__}: {exc}"
        append_live_log(log_path, f"[error]\n{error_message}")
        job.error_message = error_message
        emit_live_event(
            semantic_log,
            level="error",
            code="live_runner_stream_failed",
            expected="runner.stream emits events and reaches a terminal status",
            actual=error_message,
            job=job,
            metadata={"runner_name": runner.name},
        )
        yield sse("error", {"message": error_message})

    job.finished_at = utc_now()
    job.status = terminal_status
    if terminal_status != "done" and not job.error_message:
        job.error_message = f"Live stream ended with status {terminal_status}"
    session.add(job)
    session.commit()
    emit_live_event(
        semantic_log,
        level="info" if terminal_status == "done" else "error",
        code="live_runner_stream_result",
        expected="live runner stream ends with a terminal AgentJob status",
        actual=f"runner stream status: {terminal_status}",
        job=job,
        metadata={
            "runner_name": runner.name,
            "error_message": job.error_message or "",
        },
    )
    yield sse("status", {"message": terminal_status, "job_status": terminal_status})


# :END_LIVE_JOB_STREAM


async def fail_job(session: Session, job: AgentJob, log_dir: Path, error_message: str) -> None:
    log_path = live_log_path(log_dir, job)
    append_live_log(log_path, f"[error]\n{error_message}")
    job.finished_at = utc_now()
    job.status = "failed"
    job.stdout_log_path = log_path.as_posix()
    job.error_message = error_message
    session.add(job)
    session.commit()


def live_log_path(log_dir: Path, job: AgentJob) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"agent-job-{job.id or 0:05d}.log"


def append_live_event(path: Path, event: AgentEvent) -> None:
    if event.message:
        append_live_log(path, event.message)


def append_live_log(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as log_file:
        log_file.write(text.rstrip() + "\n")


def sse(event: str, payload: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def emit_live_event(
    semantic_log: SemanticLogWriter,
    *,
    level: str,
    code: str,
    expected: str,
    actual: str,
    job: AgentJob,
    metadata: dict[str, object] | None = None,
) -> None:
    semantic_log.emit(
        level=level,
        code=code,
        anchor="START_ROUTE_LIVE_STREAM",
        expected=expected,
        actual=actual,
        job_id=job.id,
        component="LiveAgentStudio",
        metadata=metadata,
    )
