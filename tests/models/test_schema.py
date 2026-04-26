from sqlmodel import Session, SQLModel, create_engine, select

from observatory.models import (
    AgentJob,
    ComparisonCell,
    EcosystemObject,
    EvidenceItem,
    Feature,
    Harness,
    Insight,
    Lens,
    MediaAttachment,
    ObservationReview,
    PromptTemplate,
    RefreshSchedule,
    RevisionNote,
    Score,
    Source,
    Topic,
)


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_core_entities_round_trip() -> None:
    with make_session() as session:
        harness = Harness(name="OpenCode", slug="opencode", language="TypeScript")
        topic = Topic(name="Agent loop", slug="agent-loop", definition="Loop shape")
        feature = Feature(name="Plan mode", slug="plan-mode")
        source = Source(name="Harness architecture", source_type="markdown")
        session.add_all([harness, topic, feature, source])
        session.commit()

        insight = Insight(
            short_title="Loop is explicit",
            body="OpenCode exposes an explicit agent loop.",
            why_it_matters="Students can inspect control flow.",
            harness_id=harness.id,
            topic_id=topic.id,
            feature_id=feature.id,
            agent_model="test-model",
            agent_runner="TestRunner",
        )
        session.add(insight)
        session.commit()

        evidence = EvidenceItem(
            claim_summary="The loop is visible in source.",
            evidence_class="code",
            file_path="src/loop.ts",
            line_number=42,
            code_snippet="while (true) { await step(); }",
            harness_id=harness.id,
            topic_id=topic.id,
            insight_id=insight.id,
            source_id=source.id,
            verifier_agents=["test-agent"],
        )
        cell = ComparisonCell(
            harness_id=harness.id,
            topic_id=topic.id,
            state="present",
            cell_summary="Explicit loop implementation.",
        )
        media = MediaAttachment(
            kind="image",
            path_or_url="media/loop.png",
            attached_to_kind="Insight",
            attached_to_id=insight.id,
        )
        ecosystem_object = EcosystemObject(
            name="MiniMax CLI",
            slug="minimax-cli",
            kind="agent-tool",
        )
        session.add_all([evidence, cell, media, ecosystem_object])
        session.commit()

        stored_insight = session.exec(select(Insight).where(Insight.short_title == "Loop is explicit")).one()
        assert stored_insight.status == "proposed"
        assert stored_insight.confidence_band == "unverified"
        assert stored_insight.harness is not None
        assert stored_insight.topic is not None
        stored_snippet = stored_insight.evidence_items[0].code_snippet
        assert stored_snippet is not None
        assert stored_snippet.startswith("while")

        stored_cell = session.exec(select(ComparisonCell)).one()
        assert stored_cell.harness_id == harness.id
        assert stored_cell.topic_id == topic.id

        stored_object = session.exec(select(EcosystemObject)).one()
        assert stored_object.kind == "agent-tool"


def test_future_stub_tables_round_trip() -> None:
    with make_session() as session:
        harness = Harness(name="Codex CLI", slug="codex-cli")
        topic = Topic(name="Sandboxing", slug="sandboxing")
        lens = Lens(name="Teaching Lens", slug="teaching-lens")
        prompt = PromptTemplate(
            name="Discover",
            type="discover",
            version="v0",
            body="Find one useful observation.",
        )
        session.add_all([harness, topic, lens, prompt])
        session.commit()

        job = AgentJob(
            type="discover",
            target_kind="Harness",
            target_id=harness.id,
            prompt_template_id=prompt.id,
            runner_name="StubRunner",
            status="queued",
            produced_artifact_ids=[],
        )
        score = Score(lens_id=lens.id, harness_id=harness.id, topic_id=topic.id, value=0.75)
        schedule = RefreshSchedule(
            harness_id=harness.id,
            enabled=True,
            runner_name="codex",
            interval_minutes=60,
            status="idle",
        )
        review = ObservationReview(reviewer="agent", change_summary="Initial review")
        revision = RevisionNote(note="Historical context placeholder")
        session.add_all([job, score, schedule, review, revision])
        session.commit()

        assert session.exec(select(AgentJob)).one().status == "queued"
        stored_schedule = session.exec(select(RefreshSchedule)).one()
        assert stored_schedule.harness_id == harness.id
        assert stored_schedule.enabled is True
        assert stored_schedule.runner_name == "codex"
        assert session.exec(select(Score)).one().value == 0.75
        assert session.exec(select(ObservationReview)).one().reviewer == "agent"
        assert session.exec(select(RevisionNote)).one().note == "Historical context placeholder"
