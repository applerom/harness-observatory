# FILE: src/observatory/jobs/service.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Manual refresh AgentJob creation and execution service.
# PRD_REF: docs/PRD.md §24 v0.2-v1.1, §4.10, §4.11
# WHY_REF: docs/why-graph.xml#MOD-JOBS-SERVICE
# SCOPE: manual refresh job spine; prompt template seed; target cwd preflight; raw log persistence; semantic event logging; successful log parsing
# INVARIANTS:
# - Manual refresh is target-generic; unsupported local paths fail during preflight.
# - Freeform runner output is preserved as a raw log before successful logs are parsed into Insights.
# - Jobs with existing produced artifacts are not parsed again.
# - Web/routes call this service rather than a concrete runner subprocess.
# :END_MODULE_CONTRACT

import asyncio
from datetime import UTC, datetime
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Protocol, cast

from sqlmodel import Session, select

from observatory.jobs.log_parser import parse_job_log
from observatory.models import (
    AGENT_JOB_STATUS_DONE,
    AGENT_JOB_STATUS_DONE_NO_FINDINGS,
    AGENT_JOB_STATUS_FAILED,
    AGENT_JOB_STATUS_QUEUED,
    AGENT_JOB_STATUS_RUNNING,
    AgentJob,
    Harness,
    PromptTemplate,
)
from observatory.runners.base import AgentContext, AgentPreflightResult, AgentResult, AgentRunner
from observatory.runtime.semantic_log import SemanticLogWriter


REFRESH_TEMPLATE_NAME = "harness-refresh-v0.3a"
REFRESH_TEMPLATE_VERSION = "0.3a"
DEFAULT_LOG_DIR = Path("live-sessions")


@dataclass(frozen=True, slots=True)
class ResolvedTargetCwd:
    """Resolved cwd with metadata about whether preflight repaired a stale configured path."""

    path: str
    repaired_from: str | None = None


class RefreshJobService:
    """Create and run one manual refresh AgentJob."""

    def __init__(
        self,
        runner: AgentRunner,
        log_dir: Path = DEFAULT_LOG_DIR,
        semantic_log: SemanticLogWriter | None = None,
    ) -> None:
        self.runner = runner
        self.log_dir = log_dir
        self.semantic_log = semantic_log or SemanticLogWriter(log_dir / "semantic-events.jsonl")

    # START_JOB_REFRESH:
    def refresh_harness(self, session: Session, harness: Harness, trigger: str = "manual") -> AgentJob:
        """Run a minimal refresh job for any configured harness target."""
        template = ensure_refresh_prompt_template(session)
        rendered_prompt = render_refresh_prompt(template, harness)
        job = AgentJob(
            type="refresh",
            target_kind="Harness",
            target_id=harness.id,
            prompt_template_id=template.id,
            prompt_text=rendered_prompt,
            runner_name=self.runner.name,
            runner_version=self.runner.version,
            trigger=trigger,
            status=AGENT_JOB_STATUS_QUEUED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        self.emit_event(
            level="info",
            code="job_queued",
            anchor="START_JOB_REFRESH",
            expected="AgentJob queued before runner execution",
            actual=f"queued refresh job {job.id}",
            job=job,
            metadata={"harness_slug": harness.slug, "trigger": trigger},
        )

        job.started_at = utc_now()
        job.status = AGENT_JOB_STATUS_RUNNING
        session.add(job)
        session.commit()
        session.refresh(job)
        self.emit_event(
            level="info",
            code="job_running",
            anchor="START_JOB_REFRESH",
            expected="AgentJob enters running state before preflight",
            actual=f"running refresh job {job.id}",
            job=job,
            metadata={"harness_slug": harness.slug, "trigger": trigger},
        )

        # START_JOB_PREFLIGHT:
        resolved_cwd = resolve_target_cwd(harness)
        target_preflight_error = validate_target_cwd(resolved_cwd.path, harness.local_upstream_path)
        if target_preflight_error is not None:
            result = AgentResult(status="failed", output="", error_message=target_preflight_error)
            log_path = write_job_log(self.log_dir, job, result.output, result.error_message)
            job.finished_at = utc_now()
            job.status = result.status
            job.stdout_log_path = log_path.as_posix()
            job.error_message = result.error_message
            session.add(job)
            session.commit()
            session.refresh(job)
            self.emit_event(
                level="error",
                code="target_cwd_preflight_failed",
                anchor="START_JOB_REFRESH",
                expected="harness.local_upstream_path exists before runner execution",
                actual=target_preflight_error,
                job=job,
                metadata={
                    "configured_cwd": harness.local_upstream_path or "",
                    "harness_slug": harness.slug,
                },
            )
            return job

        self.emit_event(
            level="info",
            code="target_cwd_preflight_succeeded",
            anchor="START_JOB_REFRESH",
            expected="target cwd is available before runner execution",
            actual=f"target cwd available: {resolved_cwd.path}",
            job=job,
            metadata={
                "cwd": resolved_cwd.path,
                "configured_cwd": harness.local_upstream_path or "",
                "harness_slug": harness.slug,
                "resolved_from_stale_path": resolved_cwd.repaired_from or "",
            },
        )

        runner_preflight = run_optional_runner_preflight(self.runner)
        if runner_preflight is not None and not runner_preflight.ok:
            error_message = runner_preflight.error_message or "AgentRunner preflight failed"
            result = AgentResult(
                status="failed",
                output=runner_preflight.output,
                error_message=error_message,
            )
            log_path = write_job_log(self.log_dir, job, result.output, result.error_message)
            job.finished_at = utc_now()
            job.status = result.status
            job.stdout_log_path = log_path.as_posix()
            job.error_message = result.error_message
            session.add(job)
            session.commit()
            session.refresh(job)
            self.emit_event(
                level="error",
                code="runner_preflight_failed",
                anchor="START_JOB_REFRESH",
                expected="runner cheap preflight succeeds before model execution",
                actual=error_message,
                job=job,
                metadata=dict(runner_preflight.metadata),
            )
            return job

        if runner_preflight is not None:
            self.emit_event(
                level="info",
                code="runner_preflight_succeeded",
                anchor="START_JOB_REFRESH",
                expected="runner cheap preflight succeeds before model execution",
                actual=runner_preflight.output or "runner preflight succeeded",
                job=job,
                metadata=dict(runner_preflight.metadata),
            )
        # :END_JOB_PREFLIGHT

        context = AgentContext(
            job_id=job.id or 0,
            job_type=job.type,
            prompt=job.prompt_text or rendered_prompt,
            target_kind=job.target_kind,
            target_id=job.target_id,
            metadata={"cwd": resolved_cwd.path, "harness_slug": harness.slug},
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
        self.emit_event(
            level="info" if result.status == AGENT_JOB_STATUS_DONE else "error",
            code="runner_result",
            anchor="START_JOB_REFRESH",
            expected="runner returns a terminal AgentResult",
            actual=f"runner status: {result.status}",
            job=job,
            metadata={
                "runner_name": self.runner.name,
                "error_message": result.error_message or "",
            },
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
        if job.status == AGENT_JOB_STATUS_DONE and job.stdout_log_path and not job.produced_artifact_ids:
            try:
                parse_result = parse_job_log(session, job)
                # START_PARSER_EMPTY_GUARD:
                if not parse_result.insight_ids and not parse_result.evidence_item_ids:
                    job.status = AGENT_JOB_STATUS_DONE_NO_FINDINGS
                    session.add(job)
                    session.commit()
                    session.refresh(job)
                    self.emit_event(
                        level="warning",
                        code="parser_returned_no_findings",
                        anchor="START_PARSER_EMPTY_GUARD",
                        expected="successful runner output yields at least one parsed artifact",
                        actual="parser returned zero Insights and zero EvidenceItems",
                        job=job,
                        metadata={"stdout_log_path": job.stdout_log_path},
                    )
                else:
                    self.emit_event(
                        level="info",
                        code="parser_succeeded",
                        anchor="START_JOB_REFRESH",
                        expected="successful refresh raw log is parsed without crashing",
                        actual=(
                            f"parsed {len(parse_result.insight_ids)} insights and "
                            f"{len(parse_result.evidence_item_ids)} evidence items"
                        ),
                        job=job,
                        metadata={
                            "insight_ids": list(parse_result.insight_ids),
                            "evidence_item_ids": list(parse_result.evidence_item_ids),
                        },
                    )
                # :END_PARSER_EMPTY_GUARD
            except Exception as exc:
                parser_error = (
                    f"Parser failed after successful runner output: {type(exc).__name__}: {exc}"
                )
                append_job_log_error(Path(job.stdout_log_path), "[parser error]", parser_error)
                job.status = AGENT_JOB_STATUS_FAILED
                job.error_message = parser_error
                session.add(job)
                session.commit()
                self.emit_event(
                    level="error",
                    code="parser_failed",
                    anchor="START_JOB_REFRESH",
                    expected="successful refresh raw log is parsed without crashing",
                    actual=parser_error,
                    job=job,
                )
            session.refresh(job)
        return job

    def emit_event(
        self,
        *,
        level: str,
        code: str,
        anchor: str,
        expected: str,
        actual: str,
        job: AgentJob,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.semantic_log.emit(
            level=level,
            code=code,
            anchor=anchor,
            expected=expected,
            actual=actual,
            job_id=job.id,
            component="RefreshJobService",
            metadata=metadata,
        )

    # :END_JOB_REFRESH


class PreflightCapableRunner(Protocol):
    async def preflight(self) -> AgentPreflightResult:
        """Run a cheap readiness check without invoking a model."""
        ...


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
            "Use upstream URL {upstream_url} when helpful. "
            "Return a concise markdown report with: summary, notable changes, evidence paths, and uncertainty. "
            "Do not edit files."
        ),
        notes="v0.3a target-generic manual refresh prompt.",
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


def resolve_target_cwd(harness: Harness) -> ResolvedTargetCwd:
    configured_path = harness.local_upstream_path
    if configured_path is not None:
        configured = Path(configured_path)
        if configured.exists():
            return ResolvedTargetCwd(str(configured))

    for candidate in target_cwd_candidates(harness):
        if candidate.exists():
            return ResolvedTargetCwd(str(candidate), repaired_from=configured_path)

    return ResolvedTargetCwd(configured_path or "")


def target_cwd_candidates(harness: Harness) -> list[Path]:
    workspace_root = Path.cwd().parent
    repo_names: list[str] = []
    if harness.local_upstream_path:
        repo_names.append(Path(harness.local_upstream_path).name)
    repo_names.extend(repo_name_candidates(harness))

    candidates: list[Path] = []
    seen: set[str] = set()
    for repo_name in repo_names:
        if not repo_name or repo_name in seen:
            continue
        seen.add(repo_name)
        candidates.append(workspace_root / repo_name)
    return candidates


def repo_name_candidates(harness: Harness) -> list[str]:
    slug = harness.slug.strip().lower()
    name_slug = slugify(harness.name)
    bases = [slug, name_slug]
    for suffix in ("-cli", "-code"):
        if slug.endswith(suffix):
            bases.append(slug.removesuffix(suffix))
        if name_slug.endswith(suffix):
            bases.append(name_slug.removesuffix(suffix))
    return [f"{base}-architecture" for base in bases if base]


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")


def validate_target_cwd(cwd: str, configured_path: str | None) -> str | None:
    if not cwd:
        return "Target cwd preflight failed: harness.local_upstream_path is not recorded and no sibling architecture directory was found"
    if Path(cwd).exists():
        return None
    return f"Target cwd preflight failed: harness.local_upstream_path does not exist: {cwd}"


def run_optional_runner_preflight(runner: AgentRunner) -> AgentPreflightResult | None:
    preflight = getattr(runner, "preflight", None)
    if preflight is None:
        return None
    capable_runner = cast(PreflightCapableRunner, runner)
    return asyncio.run(capable_runner.preflight())


def write_job_log(log_dir: Path, job: AgentJob, output: str, error_message: str | None) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    job_id = job.id or 0
    path = log_dir / f"agent-job-{job_id:05d}.log"
    chunks = [output.rstrip()]
    if error_message:
        chunks.extend(["", "[error]", error_message.rstrip()])
    path.write_text("\n".join(chunks).strip() + "\n", encoding="utf-8")
    return path


def append_job_log_error(path: Path, heading: str, error_message: str) -> None:
    with path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"\n{heading}\n{error_message.rstrip()}\n")
