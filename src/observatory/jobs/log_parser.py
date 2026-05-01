# FILE: src/observatory/jobs/log_parser.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Parse real AgentJob raw refresh logs into proposed Insight and EvidenceItem rows.
# PRD_REF: docs/PRD.md §14.2 Job types
# WHY_REF: docs/why-graph.xml#MOD-JOB-LOG-PARSER
# SCOPE: markdown-ish refresh report parsing; conservative evidence path extraction; DB application
# INVARIANTS:
# - Raw job logs are read-only inputs and are never mutated by this module.
# - Parsed agent output is published as proposed/unverified content.
# - Parser rules stay conservative and evidence-backed; ambiguous topics remain harness-level.
# - Parsed rows attach to the AgentJob target harness; there is no default target fallback.
# START_MODULE_MAP:
# - parse_refresh_report: extracts the first useful Insight candidate and evidence links.
# - parse_job_log: reads an AgentJob log and persists Insight/EvidenceItem rows.
# :END_MODULE_MAP
# :END_MODULE_CONTRACT

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sqlmodel import Session, select

from observatory.models import AgentJob, EvidenceItem, Harness, Insight, Topic


SECTION_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.MULTILINE)
EVIDENCE_LINK_RE = re.compile(r"-\s*(?P<label>.+?):\s*\[(?P<link_text>[^\]]+)\]\((?P<target>[^)]+)\)")
PLAIN_EVIDENCE_PATH_RE = re.compile(
    r"^-\s*`?(?P<target>(?:[A-Za-z]:)?[/\\][^`—\n]+?)"
    r"(?P<line_suffix>:\d+(?:-\d+)?)?`?\s+[—-]\s*(?P<label>.+)$",
    re.MULTILINE,
)
PATH_LINE_RE = re.compile(r"^(?P<path>.+?)(?::(?P<line>\d+))?$")

TOPIC_PATH_HINTS = {
    "prompt-system": ("prompt-system", "gpt.txt", "codex.txt", "prompt-routing"),
    "instruction-files": ("agents.md", "claude.md", "instruction"),
    "file-editing": ("edit", "formatting", "lsp"),
    "multi-agent": ("multi-agent", "subagent", "parallelism", "hierarchy"),
    "sandboxing": ("permission", "settings.local.json", "safety"),
}


@dataclass(frozen=True)
class ParsedEvidence:
    claim_summary: str
    file_path: str
    source_location: str
    line_number: int | None
    topic_slug: str | None


@dataclass(frozen=True)
class ParsedRefreshReport:
    short_title: str
    body: str
    why_it_matters: str | None
    evidence: tuple[ParsedEvidence, ...]


@dataclass(frozen=True)
class JobLogParseResult:
    insight_ids: tuple[int, ...]
    evidence_item_ids: tuple[int, ...]


# START_JOB_LOG_PARSE:
def parse_refresh_report(markdown: str) -> ParsedRefreshReport | None:
    """Extract one conservative Insight candidate from a Codex refresh markdown report."""
    sections = split_sections(markdown)
    summary = sections.get("summary", "").strip()
    notable_changes = sections.get("notable changes", "").strip()
    evidence_section = sections.get("evidence paths", "")
    evidence = tuple(parse_evidence_links(evidence_section))

    if not summary and not notable_changes:
        return None

    short_title = infer_short_title(summary, notable_changes)
    body_parts = [part for part in (summary, notable_changes) if part]
    body = "\n\n".join(body_parts)
    why_it_matters = infer_why_it_matters(summary, notable_changes)
    return ParsedRefreshReport(
        short_title=short_title,
        body=body,
        why_it_matters=why_it_matters,
        evidence=evidence,
    )


def parse_job_log(session: Session, job: AgentJob) -> JobLogParseResult:
    """Read an AgentJob raw log and persist proposed Insight/EvidenceItem rows."""
    if not job.stdout_log_path:
        return JobLogParseResult(insight_ids=(), evidence_item_ids=())
    if job.produced_artifact_ids:
        return JobLogParseResult(insight_ids=(), evidence_item_ids=())

    log_path = Path(job.stdout_log_path)
    report = parse_refresh_report(log_path.read_text(encoding="utf-8"))
    if report is None:
        return JobLogParseResult(insight_ids=(), evidence_item_ids=())

    harness = resolve_job_harness(session, job)
    try:
        insight = Insight(
            short_title=report.short_title,
            body=report.body,
            why_it_matters=report.why_it_matters,
            status="proposed",
            confidence_band="unverified",
            audience="developer-deep-dive",
            format="text",
            agent_model=job.model,
            agent_runner=job.runner_name,
            harness_id=harness.id if harness else None,
        )
        session.add(insight)
        session.flush()

        evidence_items: list[EvidenceItem] = []
        for parsed_evidence in report.evidence:
            topic = resolve_topic(session, parsed_evidence.topic_slug)
            evidence_item = EvidenceItem(
                claim_summary=parsed_evidence.claim_summary,
                evidence_class="agent-reported-path",
                source_type="raw-job-log",
                source_location=parsed_evidence.source_location,
                file_path=parsed_evidence.file_path,
                line_number=parsed_evidence.line_number,
                exact_citation=parsed_evidence.claim_summary,
                confidence="agent-reported",
                harness_id=harness.id if harness else None,
                topic_id=topic.id if topic else None,
                insight_id=insight.id,
                verifier_agents=[job.runner_name] if job.runner_name else [],
            )
            session.add(evidence_item)
            evidence_items.append(evidence_item)

        session.flush()
        insight_ids = (insight.id,) if insight.id is not None else ()
        evidence_ids = tuple(item.id for item in evidence_items if item.id is not None)
        job.produced_artifact_ids = [*insight_ids, *evidence_ids]
        session.add(job)
        session.commit()
    except Exception:
        session.rollback()
        raise

    return JobLogParseResult(
        insight_ids=insight_ids,
        evidence_item_ids=evidence_ids,
    )


# :END_JOB_LOG_PARSE


def split_sections(markdown: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(markdown))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        sections[match.group("title").strip().lower()] = markdown[start:end].strip()
    return sections


def parse_evidence_links(markdown: str) -> list[ParsedEvidence]:
    evidence: list[ParsedEvidence] = []
    seen_locations: set[str] = set()
    for match in EVIDENCE_LINK_RE.finditer(markdown):
        label = clean_text(match.group("label"))
        link_text = clean_text(match.group("link_text"))
        target = match.group("target").strip()
        file_path, line_number = parse_markdown_link_target(target)
        claim_summary = label or link_text or file_path
        source_location = format_source_location(file_path, line_number)
        seen_locations.add(source_location)
        evidence.append(
            ParsedEvidence(
                claim_summary=claim_summary,
                file_path=file_path,
                source_location=source_location,
                line_number=line_number,
                topic_slug=infer_topic_slug(f"{claim_summary} {file_path}"),
            )
        )
    for match in PLAIN_EVIDENCE_PATH_RE.finditer(markdown):
        target = f"{match.group('target').strip()}{match.group('line_suffix') or ''}"
        file_path, line_number = parse_plain_path_target(target)
        source_location = format_source_location(file_path, line_number)
        if source_location in seen_locations:
            continue
        seen_locations.add(source_location)
        claim_summary = clean_text(match.group("label")) or file_path
        evidence.append(
            ParsedEvidence(
                claim_summary=claim_summary,
                file_path=file_path,
                source_location=source_location,
                line_number=line_number,
                topic_slug=infer_topic_slug(f"{claim_summary} {file_path}"),
            )
        )
    return evidence


def parse_markdown_link_target(target: str) -> tuple[str, int | None]:
    path_target = target
    if target.startswith("/D:/"):
        path_target = target[1:]
    path_match = PATH_LINE_RE.match(path_target)
    if path_match is None:
        return path_target, None

    file_path = path_match.group("path")
    line_number = path_match.group("line")
    return trim_known_repo_prefix(file_path), int(line_number) if line_number else None


def parse_plain_path_target(target: str) -> tuple[str, int | None]:
    stripped = target.strip().strip("`")
    range_match = re.match(r"^(?P<path>.+):(?P<line>\d+)(?:-\d+)?$", stripped)
    if range_match is None:
        return trim_known_repo_prefix(stripped), None
    return trim_known_repo_prefix(range_match.group("path")), int(range_match.group("line"))


def trim_known_repo_prefix(file_path: str) -> str:
    normalized = file_path.replace("\\", "/")
    marker_match = re.search(r"/[^/]+-architecture/", normalized, flags=re.IGNORECASE)
    if marker_match is not None:
        return normalized[marker_match.end() :]
    return normalized


def format_source_location(file_path: str, line_number: int | None) -> str:
    if line_number is None:
        return file_path
    return f"{file_path}:{line_number}"


def infer_topic_slug(text: str) -> str | None:
    lowered = text.lower()
    for slug, hints in TOPIC_PATH_HINTS.items():
        if any(hint in lowered for hint in hints):
            return slug
    return None


def infer_short_title(summary: str, notable_changes: str) -> str:
    combined = f"{summary}\n{notable_changes}".lower()
    if "teaching" in combined or "curriculum" in combined:
        return "Refresh found curriculum-focused changes"
    if "prompt" in combined:
        return "Refresh found prompt-system changes"
    return "Refresh produced a new finding"


def infer_why_it_matters(summary: str, notable_changes: str) -> str | None:
    combined = f"{summary}\n{notable_changes}".lower()
    if "documentation" in combined or "curriculum" in combined or "teaching" in combined:
        return "This affects what the observatory should show as current teaching material."
    return None


def clean_text(text: str) -> str:
    return " ".join(text.strip().split())


def resolve_job_harness(session: Session, job: AgentJob) -> Harness | None:
    if job.target_kind == "Harness" and job.target_id is not None:
        harness = session.get(Harness, job.target_id)
        if harness is not None:
            return harness
    return None


def resolve_topic(session: Session, slug: str | None) -> Topic | None:
    if slug is None:
        return None
    return session.exec(select(Topic).where(Topic.slug == slug)).first()
