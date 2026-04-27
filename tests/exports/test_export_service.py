from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from observatory.exports.service import generate_markdown_exports, write_legacy_archive_manifest
from observatory.models import ComparisonCell, EvidenceItem, Harness, Insight, Topic


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    harness = Harness(name="OpenCode", slug="opencode", language="TypeScript", source_model="multi-provider")
    topic = Topic(name="Instruction Files", slug="instruction-files", definition="Instruction loading")
    session.add_all([harness, topic])
    session.commit()
    session.refresh(harness)
    session.refresh(topic)
    insight = Insight(
        short_title="Instruction files change authority",
        body="Project instructions enter a stronger runtime channel.",
        why_it_matters="Channel placement changes authority.",
        engagement_hook="Wait for this instruction-file detail.",
        joke_or_telegram_seed="Telegram seed: instruction files are not equal.",
        harness_id=harness.id,
        topic_id=topic.id,
    )
    cell = ComparisonCell(
        harness_id=harness.id or 0,
        topic_id=topic.id or 0,
        state="present",
        cell_summary="Instructions are loaded into the runtime context.",
    )
    evidence = EvidenceItem(
        claim_summary="Instruction loader uses runtime context.",
        harness_id=harness.id,
        topic_id=topic.id,
        insight_id=insight.id,
    )
    session.add_all([insight, cell, evidence])
    session.commit()
    return session


def test_generate_markdown_exports_writes_required_files(tmp_path: Path) -> None:
    session = make_session()
    source = tmp_path / "harness-architecture"
    (source / "topics" / "instruction-files").mkdir(parents=True)
    (source / "topics" / "instruction-files" / "topic.md").write_text("# Topic\n", encoding="utf-8")
    (source / "comparisons").mkdir()
    (source / "comparisons" / "harness-map.md").write_text("# Map\n", encoding="utf-8")

    result = generate_markdown_exports(
        session,
        output_dir=tmp_path / "generated-docs",
        legacy_source_path=source,
        generated_at=datetime(2026, 4, 26, tzinfo=UTC),
    )

    names = {file.relative_path for file in result.files}
    assert names == {
        "comparison-report.md",
        "harness-summaries.md",
        "lecturer-brief.md",
        "onboarding-checklist.md",
        "legacy-data/ARCHIVE-MANIFEST.md",
    }
    assert "OpenCode" in (tmp_path / "generated-docs" / "comparison-report.md").read_text(encoding="utf-8")
    assert "Instruction files change authority" in (tmp_path / "generated-docs" / "lecturer-brief.md").read_text(
        encoding="utf-8"
    )
    assert "uv run alembic upgrade head" in (tmp_path / "generated-docs" / "onboarding-checklist.md").read_text(
        encoding="utf-8"
    )
    assert result.manifest.markdown_file_count == 2


def test_legacy_archive_manifest_records_source_and_counts_without_mutation(tmp_path: Path) -> None:
    source = tmp_path / "harness-architecture"
    (source / "registry").mkdir(parents=True)
    (source / "topics" / "memory").mkdir(parents=True)
    (source / "registry" / "harnesses.md").write_text("# Harnesses\n", encoding="utf-8")
    (source / "topics" / "memory" / "topic.md").write_text("# Memory\n", encoding="utf-8")
    before = sorted(path.relative_to(source).as_posix() for path in source.rglob("*"))

    manifest = write_legacy_archive_manifest(
        output_dir=tmp_path / "generated-docs",
        source_path=source,
        generated_at=datetime(2026, 4, 26, tzinfo=UTC),
    )

    after = sorted(path.relative_to(source).as_posix() for path in source.rglob("*"))
    text = (tmp_path / "generated-docs" / "legacy-data" / "ARCHIVE-MANIFEST.md").read_text(encoding="utf-8")
    assert before == after
    assert manifest.source_path == source.resolve()
    assert manifest.counted_paths["registry"] == 1
    assert manifest.counted_paths["topics"] == 1
    assert "archive-policy: no source files copied or mutated by default" in text
