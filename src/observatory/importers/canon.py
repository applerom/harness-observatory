# FILE: src/observatory/importers/canon.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Import the harness-architecture markdown canon into the v0.1 SQLite schema.
# PRD_REF: docs/PRD.md §26.1
# WHY_REF: docs/why-graph.xml#MOD-IMPORTER
# SCOPE: registry import; topic import; evidence import; insight import; comparison matrix import
# INVARIANTS:
# - Imported Insights default to status=proposed and confidence_band=unverified.
# - Harness, Topic, EcosystemObject, and ComparisonCell imports are idempotent by stable keys.
# - Ambiguous rows are logged to import-ambiguous.log instead of being silently discarded.
# START_MODULE_MAP:
# - import_canon: orchestrates a full canonical source import.
# - import_harnesses: imports registry rows into Harness or EcosystemObject.
# - import_topics: imports topic markdown and per-topic evidence.
# - import_insights: preserves teaching, comparison, and investigation markdown as Insight rows.
# - export_markdown: anchored v0.1 non-implementation stub.
# :END_MODULE_MAP
# :END_MODULE_CONTRACT

from __future__ import annotations

import argparse
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, select

from observatory import db
from observatory.importers.markdown_table import MarkdownTable, parse_pipe_tables
from observatory.models import (
    ComparisonCell,
    EcosystemObject,
    EvidenceItem,
    Harness,
    Insight,
    Topic,
)


@dataclass(frozen=True)
class ImportCounts:
    harnesses: int = 0
    topics: int = 0
    ecosystem_objects: int = 0
    evidence_items: int = 0
    insights: int = 0
    comparison_cells: int = 0


@dataclass(frozen=True)
class Ambiguity:
    source: Path
    line: int | None
    message: str
    raw: str


HARNESS_ALIASES = {
    "copilot-chat": "copilot-chat",
    "codex": "codex-cli",
    "gemini": "gemini-cli",
}

TOPIC_ALIASES = {
    "agent-loop": "agent-loop",
    "compaction": "compaction",
    "context-pressure-management": "context-management",
    "file-editing": "file-editing",
    "hooks-events": "hooks-and-events",
    "hooks-and-events": "hooks-and-events",
    "instruction-files": "instruction-files",
    "memory": "memory",
    "multi-agent": "multi-agent",
    "prompt-system": "prompt-system",
    "system-prompt": "prompt-system",
    "skill-mechanism": "skills",
    "skills": "skills",
    "sandboxing": "sandboxing",
    "safety-boundary": "sandboxing",
    "transport": "transport-api",
    "transport-surface": "transport-api",
    "transport-api": "transport-api",
    "runtime-context": "runtime-context",
}


def import_canon(
    source: Path,
    session: Session,
    *,
    ambiguous_log_path: Path | None = Path("import-ambiguous.log"),
) -> ImportCounts:
    source = source.resolve()
    ambiguities: list[Ambiguity] = []
    import_harnesses(source, session, ambiguities)
    import_topics(source, session, ambiguities)
    import_insights(source, session, ambiguities)
    import_harness_map(source, session, ambiguities)
    session.commit()
    if ambiguous_log_path is not None:
        write_ambiguities(ambiguous_log_path, ambiguities)
    return count_imported(session)


# START_IMPORT_HARNESSES:
def import_harnesses(source: Path, session: Session, ambiguities: list[Ambiguity]) -> None:
    registry = source / "registry" / "harnesses.md"
    tables = parse_pipe_tables(read_utf8(registry))
    for table in tables:
        first_header = table.headers[0].strip().lower()
        if first_header == "harness":
            for row in table.rows:
                name = clean_inline(row.get("Harness", ""))
                if not name:
                    ambiguities.append(Ambiguity(registry, table.start_line, "empty harness name", str(row)))
                    continue
                if _registry_row_kind(row) != "harness":
                    ambiguities.append(
                        Ambiguity(registry, table.start_line, "unclear non-harness registry row", str(row))
                    )
                    continue
                upsert_harness(
                    session,
                    name=name,
                    project_path=clean_inline(row.get("Project", "")),
                    upstream=clean_inline(row.get("Upstream", "")),
                    language=clean_inline(row.get("Language", "")),
                    status_note=clean_inline(row.get("Research state", "")),
                )
        elif first_header == "tool":
            for row in table.rows:
                name = clean_inline(row.get("Tool", ""))
                if not name:
                    ambiguities.append(Ambiguity(registry, table.start_line, "empty tool name", str(row)))
                    continue
                upsert_ecosystem_object(
                    session,
                    name=name,
                    kind="agent-tool",
                    project_path=clean_inline(row.get("Project", "")),
                    upstream=clean_inline(row.get("Upstream", "")),
                    language=clean_inline(row.get("Language", "")),
                    status_note=clean_inline(row.get("Category", "")),
                )
    session.flush()


# :END_IMPORT_HARNESSES


# START_IMPORT_TOPICS:
def import_topics(source: Path, session: Session, ambiguities: list[Ambiguity]) -> None:
    topics_dir = source / "topics"
    if not topics_dir.exists():
        ambiguities.append(Ambiguity(topics_dir, None, "topics directory missing", ""))
        return

    for topic_dir in sorted(path for path in topics_dir.iterdir() if path.is_dir()):
        topic_path = topic_dir / "topic.md"
        if topic_path.exists():
            topic = upsert_topic_from_markdown(session, topic_dir.name, topic_path)
        else:
            topic = upsert_topic(
                session,
                name=title_from_slug(topic_dir.name),
                slug=topic_dir.name,
                definition=None,
                why_it_matters=None,
                body_markdown=None,
            )
            ambiguities.append(Ambiguity(topic_dir, None, "topic.md missing", ""))
        session.flush()
        evidence_path = topic_dir / "evidence.md"
        if evidence_path.exists():
            import_topic_evidence(source, topic, evidence_path, session, ambiguities)
        else:
            ambiguities.append(Ambiguity(topic_dir, None, "evidence.md missing", ""))
    session.flush()


def import_topic_evidence(
    source: Path,
    topic: Topic,
    evidence_path: Path,
    session: Session,
    ambiguities: list[Ambiguity],
) -> None:
    tables = parse_pipe_tables(read_utf8(evidence_path))
    for table in tables:
        harness_header = first_matching_header(table, ["Harness", "Tool"])
        evidence_header = first_matching_header(table, ["Primary evidence", "Evidence", "Key Evidence"])
        if harness_header is None or evidence_header is None:
            continue
        for row in table.rows:
            harness_name = clean_inline(row.get(harness_header, ""))
            harness = find_harness(session, harness_name)
            if harness is None:
                ambiguities.append(
                    Ambiguity(
                        evidence_path,
                        table.start_line,
                        "evidence row references unknown harness",
                        str(row),
                    )
                )
                continue
            evidence_text = row.get(evidence_header, "").strip()
            if not evidence_text:
                ambiguities.append(Ambiguity(evidence_path, table.start_line, "empty evidence cell", str(row)))
                continue
            claim = evidence_claim(row, evidence_header)
            citation = first_citation(evidence_text)
            file_path, line_number, snippet = resolve_citation(source, citation)
            evidence = upsert_evidence(
                session,
                harness=harness,
                topic=topic,
                claim_summary=claim,
                evidence_text=evidence_text,
                file_path=file_path,
                line_number=line_number,
                code_snippet=snippet,
            )
            upsert_comparison_cell(
                session,
                harness=harness,
                topic=topic,
                state="present",
                cell_summary=f"Evidence imported from {relative_to_source(evidence_path, source)}",
            )
            if evidence.id is None:
                session.flush()


# :END_IMPORT_TOPICS


# START_IMPORT_INSIGHTS:
def import_insights(source: Path, session: Session, ambiguities: list[Ambiguity]) -> None:
    topics_dir = source / "topics"
    for topic_dir in sorted(path for path in topics_dir.iterdir() if path.is_dir()):
        teaching_path = topic_dir / "teaching.md"
        if not teaching_path.exists():
            continue
        topic = find_topic(session, topic_dir.name)
        if topic is None:
            ambiguities.append(Ambiguity(teaching_path, None, "teaching file has no imported topic", ""))
            continue
        markdown = read_utf8(teaching_path)
        upsert_insight(
            session,
            short_title=f"{topic.name} teaching hooks",
            body=first_paragraph(markdown) or f"Teaching hooks for {topic.name}.",
            body_markdown=markdown,
            why_it_matters=section_body(markdown, "Почему это запоминается"),
            audience="lecturer-only",
            topic=topic,
            engagement_hook=first_quote_or_bullet(markdown),
            joke_or_telegram_seed=section_body(markdown, "Telegram Post Seeds"),
        )

    comparisons_dir = source / "comparisons"
    for comparison_path in sorted(comparisons_dir.glob("*.md")):
        if comparison_path.name == "harness-map.md":
            continue
        markdown = read_utf8(comparison_path)
        topic = find_topic(session, TOPIC_ALIASES.get(slugify(comparison_path.stem), comparison_path.stem))
        upsert_insight(
            session,
            short_title=first_heading(markdown) or title_from_slug(comparison_path.stem),
            body=first_paragraph(markdown) or "Free-form comparison imported from markdown.",
            body_markdown=markdown,
            why_it_matters=None,
            audience="developer-deep-dive",
            topic=topic,
        )

    investigations_dir = comparisons_dir / "investigations"
    if investigations_dir.exists():
        for investigation_path in sorted(investigations_dir.glob("*.md")):
            markdown = read_utf8(investigation_path)
            upsert_insight(
                session,
                short_title=first_heading(markdown) or title_from_slug(investigation_path.stem),
                body=first_paragraph(markdown) or "Investigation imported from markdown.",
                body_markdown=markdown,
                why_it_matters=None,
                audience="developer-deep-dive",
            )
    session.flush()


def import_harness_map(source: Path, session: Session, ambiguities: list[Ambiguity]) -> None:
    map_path = source / "comparisons" / "harness-map.md"
    if not map_path.exists():
        ambiguities.append(Ambiguity(map_path, None, "harness-map.md missing", ""))
        return
    tables = parse_pipe_tables(read_utf8(map_path))
    for table in tables:
        if table.headers[:1] != ["Axis"]:
            continue
        for row in table.rows:
            topic = topic_from_axis(session, row.get("Axis", ""))
            if topic is None:
                continue
            for header in table.headers[1:]:
                harness = find_harness(session, header)
                if harness is None:
                    ambiguities.append(
                        Ambiguity(map_path, table.start_line, "harness-map column has no registry harness", header)
                    )
                    continue
                cell_text = row.get(header, "").strip()
                upsert_comparison_cell(
                    session,
                    harness=harness,
                    topic=topic,
                    state=state_from_cell(cell_text),
                    cell_summary=cell_text,
                )
    session.flush()


# :END_IMPORT_INSIGHTS


# START_EXPORT_MARKDOWN:
def export_markdown() -> None:
    raise NotImplementedError("Markdown export is outside v0.1; import-only canon lands first.")


# :END_EXPORT_MARKDOWN


def upsert_harness(
    session: Session,
    *,
    name: str,
    project_path: str | None,
    upstream: str | None,
    language: str | None,
    status_note: str | None,
) -> Harness:
    slug = canonical_harness_slug(name)
    harness = find_harness(session, slug)
    now = datetime.now(UTC)
    if harness is None:
        harness = Harness(name=name, slug=slug)
    harness.name = name
    harness.local_upstream_path = project_path or None
    harness.upstream_url = upstream or None
    harness.language = language or None
    harness.status_note = status_note or None
    harness.updated_at = now
    session.add(harness)
    return harness


def upsert_ecosystem_object(
    session: Session,
    *,
    name: str,
    kind: str,
    project_path: str | None,
    upstream: str | None,
    language: str | None,
    status_note: str | None,
) -> EcosystemObject:
    slug = slugify(name)
    statement = select(EcosystemObject).where(EcosystemObject.slug == slug)
    obj = session.exec(statement).first()
    if obj is None:
        obj = EcosystemObject(name=name, slug=slug, kind=kind)
    obj.name = name
    obj.kind = kind
    obj.local_upstream_path = project_path or None
    obj.upstream_url = upstream or None
    obj.language = language or None
    obj.status_note = status_note or None
    session.add(obj)
    return obj


def upsert_topic_from_markdown(session: Session, slug: str, topic_path: Path) -> Topic:
    markdown = read_utf8(topic_path)
    heading = first_heading(markdown) or title_from_slug(slug)
    name = re.sub(r"^Topic:\s*", "", heading, flags=re.IGNORECASE).strip()
    return upsert_topic(
        session,
        name=name,
        slug=slug,
        definition=first_paragraph(markdown),
        why_it_matters=section_body(markdown, "Почему это важно") or section_body(markdown, "Why It Matters"),
        body_markdown=markdown,
    )


def upsert_topic(
    session: Session,
    *,
    name: str,
    slug: str,
    definition: str | None,
    why_it_matters: str | None,
    body_markdown: str | None,
) -> Topic:
    topic = find_topic(session, slug)
    now = datetime.now(UTC)
    if topic is None:
        topic = Topic(name=name, slug=slug)
    topic.name = name
    topic.definition = definition
    topic.why_it_matters = why_it_matters
    topic.body_markdown = body_markdown
    topic.updated_at = now
    session.add(topic)
    return topic


def upsert_evidence(
    session: Session,
    *,
    harness: Harness,
    topic: Topic,
    claim_summary: str,
    evidence_text: str,
    file_path: str | None,
    line_number: int | None,
    code_snippet: str | None,
) -> EvidenceItem:
    statement = (
        select(EvidenceItem)
        .where(EvidenceItem.harness_id == harness.id)
        .where(EvidenceItem.topic_id == topic.id)
        .where(EvidenceItem.claim_summary == claim_summary)
        .where(EvidenceItem.exact_citation == evidence_text)
    )
    evidence = session.exec(statement).first()
    if evidence is None:
        evidence = EvidenceItem(
            claim_summary=claim_summary,
            harness_id=harness.id,
            topic_id=topic.id,
        )
    evidence.evidence_class = "markdown-citation"
    evidence.source_type = "markdown"
    evidence.source_location = evidence_text
    evidence.exact_citation = evidence_text
    evidence.file_path = file_path
    evidence.line_number = line_number
    evidence.code_snippet = code_snippet
    evidence.code_snippet_pulled_at = datetime.now(UTC) if code_snippet else None
    session.add(evidence)
    return evidence


def upsert_insight(
    session: Session,
    *,
    short_title: str,
    body: str,
    body_markdown: str,
    why_it_matters: str | None,
    audience: str,
    topic: Topic | None = None,
    harness: Harness | None = None,
    engagement_hook: str | None = None,
    joke_or_telegram_seed: str | None = None,
) -> Insight:
    statement = (
        select(Insight)
        .where(Insight.short_title == short_title)
        .where(Insight.audience == audience)
        .where(Insight.topic_id == (topic.id if topic else None))
        .where(Insight.harness_id == (harness.id if harness else None))
    )
    insight = session.exec(statement).first()
    if insight is None:
        insight = Insight(short_title=short_title, body=body)
    insight.body = body
    insight.body_markdown = body_markdown
    insight.why_it_matters = why_it_matters
    insight.audience = audience
    insight.format = "text"
    insight.status = "proposed"
    insight.confidence_band = "unverified"
    insight.topic_id = topic.id if topic else None
    insight.harness_id = harness.id if harness else None
    insight.engagement_hook = engagement_hook
    insight.joke_or_telegram_seed = joke_or_telegram_seed
    session.add(insight)
    return insight


def upsert_comparison_cell(
    session: Session,
    *,
    harness: Harness,
    topic: Topic,
    state: str,
    cell_summary: str,
) -> ComparisonCell:
    statement = (
        select(ComparisonCell)
        .where(ComparisonCell.harness_id == harness.id)
        .where(ComparisonCell.topic_id == topic.id)
    )
    cell = session.exec(statement).first()
    if cell is None:
        cell = ComparisonCell(harness_id=harness.id, topic_id=topic.id)
    cell.state = state
    cell.cell_summary = cell_summary
    cell.confidence_band = "unverified"
    cell.updated_at = datetime.now(UTC)
    session.add(cell)
    return cell


def count_imported(session: Session) -> ImportCounts:
    return ImportCounts(
        harnesses=len(session.exec(select(Harness)).all()),
        topics=len(session.exec(select(Topic)).all()),
        ecosystem_objects=len(session.exec(select(EcosystemObject)).all()),
        evidence_items=len(session.exec(select(EvidenceItem)).all()),
        insights=len(session.exec(select(Insight)).all()),
        comparison_cells=len(session.exec(select(ComparisonCell)).all()),
    )


def write_ambiguities(path: Path, ambiguities: Sequence[Ambiguity]) -> None:
    if not ambiguities:
        if path.exists():
            path.unlink()
        return
    lines = []
    for item in ambiguities:
        location = str(item.source)
        if item.line is not None:
            location = f"{location}:{item.line}"
        lines.append(f"{location}\t{item.message}\t{item.raw}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def first_matching_header(table: MarkdownTable, candidates: Iterable[str]) -> str | None:
    candidate_set = {candidate.lower() for candidate in candidates}
    for header in table.headers:
        if header.lower() in candidate_set:
            return header
    return None


def find_harness(session: Session, name_or_slug: str) -> Harness | None:
    slug = canonical_harness_slug(name_or_slug)
    return session.exec(select(Harness).where(Harness.slug == slug)).first()


def find_topic(session: Session, slug: str) -> Topic | None:
    canonical = TOPIC_ALIASES.get(slugify(slug), slugify(slug))
    return session.exec(select(Topic).where(Topic.slug == canonical)).first()


def topic_from_axis(session: Session, axis: str) -> Topic | None:
    axis_slug = TOPIC_ALIASES.get(slugify(clean_inline(axis)))
    if axis_slug is None:
        return None
    return find_topic(session, axis_slug)


def state_from_cell(cell_text: str) -> str:
    text = clean_inline(cell_text).lower()
    if not text or text in {"-", "—", "n/a", "na"}:
        return "unknown"
    if "❌" in text or "absent" in text or "none" in text or " нет" in f" {text}":
        return "absent"
    if "partial" in text or "limited" in text or "some" in text or "🟡" in text:
        return "partial"
    if "historical" in text or "removed" in text:
        return "historical"
    return "present"


def evidence_claim(row: dict[str, str], evidence_header: str) -> str:
    for key, value in row.items():
        if key not in {"Harness", "Tool", evidence_header} and value.strip():
            return clean_inline(value)[:240]
    return clean_inline(row[evidence_header])[:240]


def first_citation(text: str) -> str | None:
    backticked = re.findall(r"`([^`]+)`", text)
    if backticked:
        return cast(str, backticked[0])
    match = re.search(r"([\w./-]+(?:\.[A-Za-z0-9]+)(?::\d+(?:-\d+)?)?)", text)
    return cast(str, match.group(1)) if match else None


def resolve_citation(source: Path, citation: str | None) -> tuple[str | None, int | None, str | None]:
    if citation is None:
        return None, None, None
    match = re.match(r"(?P<path>.+?)(?::(?P<line>\d+)(?:-\d+)?)?$", citation)
    if match is None:
        return citation, None, None
    file_path = match.group("path")
    line_number = int(match.group("line")) if match.group("line") else None
    snippet = pull_code_snippet(source, file_path, line_number)
    return file_path, line_number, snippet


def pull_code_snippet(source: Path, citation_path: str, line_number: int | None) -> str | None:
    normalized = citation_path.replace("/", "\\")
    candidates = [
        source / citation_path,
        source.parent / normalized,
        source.parent / citation_path,
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            lines = read_utf8(candidate).splitlines()
            if not lines:
                return None
            if line_number is None:
                return "\n".join(lines[:5])
            index = max(line_number - 1, 0)
            if index < len(lines):
                return lines[index]
    return None


def read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def clean_inline(text: str) -> str:
    cleaned = re.sub(r"`([^`]+)`", r"\1", text)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    return cleaned.strip()


def first_heading(markdown: str) -> str | None:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return clean_inline(line[2:])
    return None


def first_paragraph(markdown: str) -> str | None:
    paragraphs = paragraph_blocks(markdown)
    return paragraphs[0] if paragraphs else None


def paragraph_blocks(markdown: str) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith("|")
            or stripped.startswith(">")
            or stripped.startswith("- ")
            or re.match(r"\d+\. ", stripped)
        ):
            if current:
                paragraphs.append(clean_inline(" ".join(current)))
                current = []
            continue
        current.append(stripped)
    if current:
        paragraphs.append(clean_inline(" ".join(current)))
    return paragraphs


def section_body(markdown: str, heading: str) -> str | None:
    lines = markdown.splitlines()
    capture = False
    body: list[str] = []
    heading_pattern = re.compile(r"^#{2,6}\s+" + re.escape(heading) + r"\s*$", re.IGNORECASE)
    for line in lines:
        if heading_pattern.match(line.strip()):
            capture = True
            continue
        if capture and line.startswith("#"):
            break
        if capture:
            body.append(line)
    text = "\n".join(body).strip()
    return text or None


def first_quote_or_bullet(markdown: str) -> str | None:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith(">"):
            return clean_inline(stripped.lstrip(">").strip())
        if stripped.startswith("- "):
            return clean_inline(stripped[2:])
    return None


def title_from_slug(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("-"))


def slugify(value: str) -> str:
    value = clean_inline(value).lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def canonical_harness_slug(value: str) -> str:
    slug = slugify(value)
    return HARNESS_ALIASES.get(slug, slug)


def relative_to_source(path: Path, source: Path) -> str:
    try:
        return path.relative_to(source).as_posix()
    except ValueError:
        return path.as_posix()


def _registry_row_kind(row: dict[str, str]) -> str:
    kind = clean_inline(row.get("Kind", row.get("Category", "harness"))).lower()
    if kind in {"harness", ""}:
        return "harness"
    if "agent tool" in kind:
        return "agent-tool"
    return "ambiguous"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import harness-architecture markdown into SQLite.")
    parser.add_argument("--source", required=True, type=Path, help="Path to harness-architecture source repo.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine: Engine = db.engine
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        counts = import_canon(args.source, session)
    print(
        "Imported "
        f"{counts.harnesses} harnesses, "
        f"{counts.topics} topics, "
        f"{counts.ecosystem_objects} ecosystem objects, "
        f"{counts.evidence_items} evidence items, "
        f"{counts.insights} insights, "
        f"{counts.comparison_cells} comparison cells."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
