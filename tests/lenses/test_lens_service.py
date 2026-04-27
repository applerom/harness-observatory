from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from observatory.lenses.service import refresh_lens_scores, seed_default_lenses
from observatory.models import ComparisonCell, EvidenceItem, Harness, Insight, Lens, Score, Topic


@contextmanager
def make_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_seed_default_lenses_is_idempotent() -> None:
    with make_session() as session:
        first_created = seed_default_lenses(session)
        second_created = seed_default_lenses(session)

        lenses = session.exec(select(Lens).order_by(Lens.name)).all()

    assert first_created == 4
    assert second_created == 0
    assert [lens.name for lens in lenses] == [
        "Ecosystem",
        "Lecturer",
        "Practical Selection",
        "Research",
    ]


def test_refresh_lens_scores_is_idempotent_and_updates_from_signals() -> None:
    with make_session() as session:
        harness, topic = seed_scored_pair(session)
        harness_id = harness.id
        topic_id = topic.id

        first_result = refresh_lens_scores(session)
        first_scores = sorted(session.exec(select(Score)).all(), key=lambda score: score.lens_id or 0)
        first_values = [score.value for score in first_scores]

        second_result = refresh_lens_scores(session)
        second_scores = sorted(session.exec(select(Score)).all(), key=lambda score: score.lens_id or 0)
        second_values = [score.value for score in second_scores]

        cell = session.exec(select(ComparisonCell)).one()
        cell.confidence_band = "verified"
        session.add(
            EvidenceItem(
                claim_summary="Second proof",
                evidence_class="markdown-citation",
                file_path="README.md",
                harness_id=harness.id,
                topic_id=topic.id,
            )
        )
        session.add(cell)
        session.commit()

        refresh_lens_scores(session)
        updated_scores = sorted(session.exec(select(Score)).all(), key=lambda score: score.lens_id or 0)
        updated_values = [score.value for score in updated_scores]

    assert first_result.lenses_seeded == 4
    assert first_result.scores_written == 4
    assert second_result.lenses_seeded == 0
    assert second_result.scores_written == 4
    assert len(first_scores) == 4
    assert len(second_scores) == 4
    assert len(updated_scores) == 4
    assert first_values == second_values
    assert updated_values != first_values
    assert all(score.harness_id == harness_id and score.topic_id == topic_id for score in updated_scores)
    assert all(score.rationale and "evidence=2" in score.rationale for score in updated_scores)


def seed_scored_pair(session: Session) -> tuple[Harness, Topic]:
    harness = Harness(name="OpenCode", slug="opencode")
    topic = Topic(name="Instruction Files", slug="instruction-files")
    session.add_all([harness, topic])
    session.commit()

    insight = Insight(
        short_title="Instruction files matter",
        body="Project instructions influence the runtime.",
        harness_id=harness.id,
        topic_id=topic.id,
    )
    cell = ComparisonCell(
        harness_id=harness.id,
        topic_id=topic.id,
        state="present",
        confidence_band="unverified",
    )
    evidence = EvidenceItem(
        claim_summary="Project instructions are loaded",
        evidence_class="markdown-citation",
        file_path="src/session.ts",
        harness_id=harness.id,
        topic_id=topic.id,
        insight_id=insight.id,
    )
    session.add_all([insight, cell, evidence])
    session.commit()
    return harness, topic
