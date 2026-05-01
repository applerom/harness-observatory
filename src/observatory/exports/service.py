# FILE: src/observatory/exports/service.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Generate derived Markdown artifacts from the observatory database.
# PRD_REF: docs/PRD.md §13, §24.1
# WHY_REF: docs/why-graph.xml#MOD-DOC-EXPORT-SERVICE
# SCOPE: comparison report; harness summaries; lecturer brief; onboarding checklist; legacy archive manifest
# INVARIANTS:
# - Generated docs are derived artifacts; database state remains canonical.
# - Legacy archive support records source coverage metadata and never mutates sibling repositories.
# - Export paths stay under the configured generated-docs output directory.
# START_MODULE_MAP:
# - generate_markdown_exports: writes the complete v1.0-minimal generated-docs set.
# - write_legacy_archive_manifest: writes legacy-data/ARCHIVE-MANIFEST.md without copying source files.
# - list_generated_files: returns inspectable generated Markdown files for the web route.
# :END_MODULE_MAP
# :END_MODULE_CONTRACT

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, select

from observatory.models import ComparisonCell, EvidenceItem, Harness, Insight, Topic


GENERATED_DOCS_DIR = Path("generated-docs")
EXPORT_FILE_NAMES = (
    "comparison-report.md",
    "harness-summaries.md",
    "lecturer-brief.md",
    "onboarding-checklist.md",
)
ARCHIVE_MANIFEST_PATH = Path("legacy-data") / "ARCHIVE-MANIFEST.md"


@dataclass(frozen=True, slots=True)
class GeneratedFile:
    """Metadata for one generated Markdown file."""

    path: Path
    relative_path: str
    size_bytes: int
    modified_at: datetime


@dataclass(frozen=True, slots=True)
class LegacyArchiveManifest:
    """Metadata recorded for the legacy Markdown archive manifest."""

    generated_at: datetime
    source_path: Path | None
    markdown_file_count: int
    counted_paths: dict[str, int]


@dataclass(frozen=True, slots=True)
class MarkdownExportResult:
    """Result returned after writing the generated docs set."""

    output_dir: Path
    files: tuple[GeneratedFile, ...]
    manifest: LegacyArchiveManifest


# START_MARKDOWN_EXPORT:
def generate_markdown_exports(
    session: Session,
    *,
    output_dir: Path = GENERATED_DOCS_DIR,
    legacy_source_path: Path | None = None,
    generated_at: datetime | None = None,
) -> MarkdownExportResult:
    """Write all v1.0-minimal generated Markdown artifacts from DB state."""
    generated_at = generated_at or datetime.now(UTC)
    output_dir.mkdir(parents=True, exist_ok=True)

    harnesses = list(session.exec(select(Harness).order_by(Harness.name)).all())
    topics = list(session.exec(select(Topic).order_by(Topic.name)).all())
    cells = list(session.exec(select(ComparisonCell)).all())
    insights = list(session.exec(select(Insight).order_by(Insight.short_title)).all())
    evidence_items = list(session.exec(select(EvidenceItem)).all())

    write_markdown(output_dir / "comparison-report.md", render_comparison_report(harnesses, topics, cells))
    write_markdown(output_dir / "harness-summaries.md", render_harness_summaries(harnesses, insights, evidence_items))
    write_markdown(output_dir / "lecturer-brief.md", render_lecturer_brief(insights))
    write_markdown(output_dir / "onboarding-checklist.md", render_onboarding_checklist())
    manifest = write_legacy_archive_manifest(
        output_dir=output_dir,
        source_path=legacy_source_path,
        generated_at=generated_at,
    )

    return MarkdownExportResult(
        output_dir=output_dir,
        files=tuple(list_generated_files(output_dir)),
        manifest=manifest,
    )


def list_generated_files(output_dir: Path = GENERATED_DOCS_DIR) -> list[GeneratedFile]:
    """Return generated Markdown files under output_dir, sorted for stable UI/tests."""
    if not output_dir.exists():
        return []
    files: list[GeneratedFile] = []
    for path in sorted(output_dir.rglob("*.md")):
        if not path.is_file():
            continue
        stat = path.stat()
        files.append(
            GeneratedFile(
                path=path,
                relative_path=path.relative_to(output_dir).as_posix(),
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime, UTC),
            )
        )
    return files


# :END_MARKDOWN_EXPORT


# START_LEGACY_ARCHIVE_MANIFEST:
def write_legacy_archive_manifest(
    *,
    output_dir: Path = GENERATED_DOCS_DIR,
    source_path: Path | None = None,
    generated_at: datetime | None = None,
) -> LegacyArchiveManifest:
    """Write a manifest describing legacy Markdown coverage without mutating it."""
    generated_at = generated_at or datetime.now(UTC)
    resolved_source = resolve_legacy_source_path(source_path)
    counted_paths = count_markdown_files(resolved_source)
    manifest = LegacyArchiveManifest(
        generated_at=generated_at,
        source_path=resolved_source,
        markdown_file_count=sum(counted_paths.values()),
        counted_paths=counted_paths,
    )
    manifest_path = output_dir / ARCHIVE_MANIFEST_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(manifest_path, render_archive_manifest(manifest))
    return manifest


def resolve_legacy_source_path(source_path: Path | None) -> Path | None:
    if source_path is not None:
        return source_path.resolve()
    candidates = [
        Path.cwd().parent / "harness-architecture",
        Path(__file__).resolve().parents[3].parent / "harness-architecture",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate.resolve()
    return None


def count_markdown_files(source_path: Path | None) -> dict[str, int]:
    sections = {
        "registry": 0,
        "topics": 0,
        "comparisons": 0,
        "lessons": 0,
        "other": 0,
    }
    if source_path is None or not source_path.exists():
        return sections
    for path in source_path.rglob("*.md"):
        if not path.is_file():
            continue
        try:
            first_part = path.relative_to(source_path).parts[0]
        except (IndexError, ValueError):
            first_part = "other"
        key = first_part if first_part in sections else "other"
        sections[key] += 1
    return sections


# :END_LEGACY_ARCHIVE_MANIFEST


def render_comparison_report(
    harnesses: list[Harness],
    topics: list[Topic],
    cells: list[ComparisonCell],
) -> str:
    harness_by_id = {harness.id: harness for harness in harnesses}
    topic_by_id = {topic.id: topic for topic in topics}
    lines = [
        "# Comparison Report",
        "",
        "Generated from the Harness Observatory database.",
        "",
        f"- Harnesses: {len(harnesses)}",
        f"- Topics: {len(topics)}",
        f"- Comparison cells: {len(cells)}",
        "",
        "## Cells",
        "",
    ]
    if cells:
        lines.extend(["| Harness | Topic | State | Summary |", "|---|---|---|---|"])
        for cell in sorted(cells, key=lambda item: (label_for(harness_by_id.get(item.harness_id)), label_for(topic_by_id.get(item.topic_id)))):
            lines.append(
                "| "
                + " | ".join(
                    [
                        escape_table(label_for(harness_by_id.get(cell.harness_id))),
                        escape_table(label_for(topic_by_id.get(cell.topic_id))),
                        escape_table(cell.state),
                        escape_table(cell.cell_summary or ""),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No comparison cells have been generated yet.")
    return "\n".join(lines) + "\n"


def render_harness_summaries(
    harnesses: list[Harness],
    insights: list[Insight],
    evidence_items: list[EvidenceItem],
) -> str:
    lines = ["# Harness Summaries", ""]
    for harness in harnesses:
        insight_count = sum(1 for insight in insights if insight.harness_id == harness.id)
        evidence_count = sum(1 for evidence in evidence_items if evidence.harness_id == harness.id)
        lines.extend(
            [
                f"## {harness.name}",
                "",
                f"- Slug: `{harness.slug}`",
                f"- Language: {harness.language or 'unknown'}",
                f"- Source model: {harness.source_model or 'unknown'}",
                f"- Status: {harness.status_note or 'unknown'}",
                f"- Insights: {insight_count}",
                f"- EvidenceItems: {evidence_count}",
                "",
            ]
        )
    if not harnesses:
        lines.append("No harnesses have been imported yet.")
    return "\n".join(lines).rstrip() + "\n"


def render_lecturer_brief(insights: list[Insight]) -> str:
    lecturer_insights = [
        insight
        for insight in insights
        if insight.audience == "lecturer-only" or insight.engagement_hook or insight.joke_or_telegram_seed
    ]
    lines = ["# Lecturer Brief", "", "Teaching hooks and engagement seeds derived from current Insights.", ""]
    for insight in lecturer_insights:
        lines.extend([f"## {insight.short_title}", "", insight.body, ""])
        if insight.engagement_hook:
            lines.extend([f"- Hook: {insight.engagement_hook}"])
        if insight.joke_or_telegram_seed:
            lines.extend([f"- Telegram seed: {insight.joke_or_telegram_seed}"])
        if insight.why_it_matters:
            lines.extend([f"- Why it matters: {insight.why_it_matters}"])
        lines.append("")
    if not lecturer_insights:
        lines.append("No lecturer-only or engagement Insights are available yet.")
    return "\n".join(lines).rstrip() + "\n"


def render_onboarding_checklist() -> str:
    return "\n".join(
        [
            "# Onboarding Checklist",
            "",
            "- [ ] Clone `harness-observatory` and enter the repo root.",
            "- [ ] Install dependencies with `uv sync`.",
            "- [ ] Apply migrations with `uv run alembic upgrade head`.",
            "- [ ] Import legacy canon with `uv run python -m observatory.importers.canon --source ../harness-architecture`.",
            "- [ ] Start the server with `uv run uvicorn observatory.web.app:create_app --factory --reload`.",
            "- [ ] Open `/harnesses`, choose a harness, and use its refresh action for the first AgentJob.",
            "- [ ] Run validation with `uv run pytest` and `uv run python scripts/validate_anchors.py` before claiming done.",
            "",
        ]
    )


def render_archive_manifest(manifest: LegacyArchiveManifest) -> str:
    lines = [
        "# Legacy Archive Manifest",
        "",
        f"- generated-at: {manifest.generated_at.isoformat()}",
        f"- source-path: {manifest.source_path.as_posix() if manifest.source_path else 'not detected'}",
        "- archive-policy: no source files copied or mutated by default",
        f"- markdown-file-count: {manifest.markdown_file_count}",
        "",
        "## Markdown Counts",
        "",
    ]
    for section, count in manifest.counted_paths.items():
        lines.append(f"- {section}: {count}")
    return "\n".join(lines) + "\n"


def write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def label_for(item: Harness | Topic | None) -> str:
    return item.name if item is not None else "unknown"


def escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()
