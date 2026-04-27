from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from observatory.importers.canon import import_canon
from observatory.models import ComparisonCell, EcosystemObject, EvidenceItem, Harness, Insight, Topic


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def write_fixture_source(tmp_path: Path) -> Path:
    source = tmp_path / "harness-architecture"
    registry = source / "registry"
    topics = source / "topics" / "instruction-files"
    comparisons = source / "comparisons"
    investigations = comparisons / "investigations"
    upstream = tmp_path / "opencode-upstream" / "src"
    registry.mkdir(parents=True)
    topics.mkdir(parents=True)
    investigations.mkdir(parents=True)
    upstream.mkdir(parents=True)

    (registry / "harnesses.md").write_text(
        """
# Harness Registry

| Harness | Project | Upstream | Language | Research state | Distinct signature |
|---|---|---|---|---|---|
| OpenCode | `d:/ai/opencode-architecture/` | `d:/ai/opencode-upstream/` | TypeScript | Complete | loop |
| Codex CLI | `d:/ai/codex-architecture/` | `d:/ai/codex-upstream/` | Rust | Complete | sandbox |

## Agent Tools

| Tool | Project | Upstream | Language | Category | Distinct signature |
|---|---|---|---|---|---|
| MiniMax CLI | `d:/ai/minimax-architecture/` | `d:/ai/minimax-upstream/` | TypeScript/Bun | Media generation API client | skill-first |
""",
        encoding="utf-8",
    )
    (topics / "topic.md").write_text(
        """
# Topic: Instruction Files

Project instruction files enter different runtime channels.

## Почему это важно

Channel placement changes authority and locality.
""",
        encoding="utf-8",
    )
    (topics / "evidence.md").write_text(
        """
# Instruction Files - Evidence Map

| Harness | Root mechanism | Primary evidence |
|---|---|---|
| OpenCode | system layer | `opencode-upstream/src/session.ts:2` |
| Codex CLI | user message | `codex-upstream/codex-rs/core.rs` |
""",
        encoding="utf-8",
    )
    (topics / "teaching.md").write_text(
        """
# Instruction Files - Teaching Hooks

## Главный hook

"Same filename, different authority."

## Telegram Post Seeds

1. `AGENTS.md` is an interface name, not one universal mechanism.
""",
        encoding="utf-8",
    )
    (comparisons / "harness-map.md").write_text(
        """
# Harness Map

| Axis | OpenCode | Codex CLI |
|---|---|---|
| **Instruction files** | system layer | contextual user |
""",
        encoding="utf-8",
    )
    (comparisons / "instruction-files.md").write_text(
        """
# Instruction Files Comparison

The same file name carries different runtime semantics.
""",
        encoding="utf-8",
    )
    (investigations / "case.md").write_text(
        """
# Case Study

Raw investigation markdown should survive import.
""",
        encoding="utf-8",
    )
    (upstream / "session.ts").write_text("line one\nwhile (true) {}\n", encoding="utf-8")
    return source


def test_registry_import_splits_harnesses_and_agent_tools(tmp_path: Path) -> None:
    source = write_fixture_source(tmp_path)
    with make_session() as session:
        import_canon(source, session, ambiguous_log_path=None)

        harnesses = session.exec(select(Harness).order_by(Harness.slug)).all()
        objects = session.exec(select(EcosystemObject)).all()

        assert [harness.slug for harness in harnesses] == ["codex-cli", "opencode"]
        assert objects[0].slug == "minimax-cli"
        assert objects[0].kind == "agent-tool"


def test_topic_evidence_insight_and_matrix_import(tmp_path: Path) -> None:
    source = write_fixture_source(tmp_path)
    with make_session() as session:
        counts = import_canon(source, session, ambiguous_log_path=None)

        topic = session.exec(select(Topic).where(Topic.slug == "instruction-files")).one()
        evidence = session.exec(select(EvidenceItem).where(EvidenceItem.file_path != None)).all()  # noqa: E711
        insights = session.exec(select(Insight)).all()
        cells = session.exec(select(ComparisonCell)).all()

        assert counts.topics == 1
        assert topic.definition == "Project instruction files enter different runtime channels."
        assert any(item.code_snippet == "while (true) {}" for item in evidence)
        assert len(insights) == 3
        assert {insight.audience for insight in insights} == {"lecturer-only", "developer-deep-dive"}
        assert len(cells) == 2
        assert all(cell.state == "present" for cell in cells)


def test_import_is_idempotent_for_core_rows(tmp_path: Path) -> None:
    source = write_fixture_source(tmp_path)
    with make_session() as session:
        import_canon(source, session, ambiguous_log_path=None)
        import_canon(source, session, ambiguous_log_path=None)

        assert len(session.exec(select(Harness)).all()) == 2
        assert len(session.exec(select(Topic)).all()) == 1
        assert len(session.exec(select(EcosystemObject)).all()) == 1
        assert len(session.exec(select(EvidenceItem)).all()) == 2
        assert len(session.exec(select(Insight)).all()) == 3
        assert len(session.exec(select(ComparisonCell)).all()) == 2


def test_real_source_smoke_if_available() -> None:
    source = Path("D:/ai/harnesses/harness-architecture")
    if not source.exists():
        pytest.skip("real harness-architecture checkout is not available")

    with make_session() as session:
        counts = import_canon(source, session, ambiguous_log_path=None)

        assert counts.harnesses >= 8
        assert counts.topics >= 11
        assert counts.ecosystem_objects >= 1
        assert counts.evidence_items > 0
        assert counts.insights > 0
        assert counts.comparison_cells > 0

