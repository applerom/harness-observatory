# FILE: src/observatory/jobs/service.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Minimal v0.2a AgentJob creation and execution service.
# PRD_REF: docs/PRD.md §24, §1162
# WHY_REF: docs/why-graph.xml MOD-RUNNER-BASE
# SCOPE: OpenCode refresh job spine; prompt template seed; raw log persistence
# INVARIANTS:
# - Only OpenCode refresh is enabled in v0.2a.
# - Freeform runner output is preserved as a raw log; it is not parsed into Insights yet.
# - Web/routes call this service rather than a concrete runner subprocess.
# :END_MODULE_CONTRACT

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, select

from observatory.models import AgentJob, Harness, PromptTemplate
from observatory.runners.base import AgentContext, AgentResult, AgentRunner


REFRESH_TEMPLATE_NAME = "opencode-refresh-v0.2a"
REFRESH_TEMPLATE_VERSION = "0.2a"
DEFAULT_LOG_DIR = Path("live-sessions")


class RefreshNotAvailableError(ValueError):
    """Raised when a harness is outside the current v0.2a refresh slice."""


class RefreshJobService:
    """Create and run one manual refresh AgentJob."""

    def __init__(self, runner: AgentRunner, log_dir: Path = DEFAULT_LOG_DIR) -> None:
        self.runner = runner
        self.log_dir = log_dir

    # START_JOB_REFRESH:
    def refresh_harness(self, session: Session, harness: Harness) -> AgentJob:
        """Run a minimal manual refresh job for the current v0.2a target."""
        if harness.slug != "opencode":
            raise RefreshNotAvailableError("v0.2a enables manual refresh only for OpenCode")

        template = ensure_refresh_prompt_template(session)
        job = AgentJob(
            type="refresh",
            target_kind="Harness",
            target_id=harness.id,
            prompt_template_id=template.id,
            runner_name=self.runner.name,
            runner_version=self.runner.version,
            trigger="manual",
            status="queued",
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        job.started_at = utc_now()
        job.status = "running"
        session.add(job)
        session.commit()
        session.refresh(job)

        context = AgentContext(
            job_id=job.id or 0,
            job_type=job.type,
            prompt=render_refresh_prompt(template, harness),
            target_kind=job.target_kind,
            target_id=job.target_id,
            metadata={"cwd": harness.local_upstream_path or "."},
        )
        try:
            result = asyncio.run(self.runner.run(context))
        except Exception as exc:
            result = AgentResult(
                status="failed",
                output="",
                error_message=(
                    f"AgentRunner {self.runner.name} raised unexpected exception: "
                    f"{type(exc).__name__}: {exc}"
                ),
            )

        log_path = write_job_log(self.log_dir, job, result.output, result.error_message)
        job.finished_at = utc_now()
        job.status = result.status
        job.stdout_log_path = log_path.as_posix()
        job.produced_artifact_ids = list(result.artifact_ids)
        job.error_message = result.error_message
        session.add(job)
        session.commit()
        session.refresh(job)
        return job

    # :END_JOB_REFRESH


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_refresh_prompt_template(session: Session) -> PromptTemplate:
    existing = session.exec(
        select(PromptTemplate)
        .where(PromptTemplate.name == REFRESH_TEMPLATE_NAME)
        .where(PromptTemplate.version == REFRESH_TEMPLATE_VERSION)
    ).first()
    if existing is not None:
        return existing

    template = PromptTemplate(
        name=REFRESH_TEMPLATE_NAME,
        type="refresh",
        version=REFRESH_TEMPLATE_VERSION,
        expected_artifact_kind="raw-refresh-log",
        body=(
            "Inspect the {harness_name} harness for fresh implementation or documentation changes. "
            "Return a concise markdown report with: summary, notable changes, evidence paths, and uncertainty. "
            "Do not edit files."
        ),
        notes="v0.2a preserves raw output only; parser/import into Insights is deferred.",
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


def render_refresh_prompt(template: PromptTemplate, harness: Harness) -> str:
    return template.body.format(
        harness_name=harness.name,
        harness_slug=harness.slug,
        upstream_url=harness.upstream_url or "unknown upstream",
    )


def write_job_log(log_dir: Path, job: AgentJob, output: str, error_message: str | None) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    job_id = job.id or 0
    path = log_dir / f"agent-job-{job_id:05d}.log"
    chunks = [output.rstrip()]
    if error_message:
        chunks.extend(["", "[error]", error_message.rstrip()])
    path.write_text("\n".join(chunks).strip() + "\n", encoding="utf-8")
    return path
