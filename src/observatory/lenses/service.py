# FILE: src/observatory/lenses/service.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Deterministic default lens seeding and score refresh service.
# PRD_REF: docs/PRD.md §15, §24.1
# WHY_REF: docs/why-graph.xml MOD-LENS-SERVICE
# SCOPE: default Lens rows; Score upserts from current DB signals
# INVARIANTS:
# - Scores are per-lens, per-harness, per-topic; no universal winner is computed.
# - Refresh is deterministic and idempotent for unchanged ComparisonCell/Insight/Evidence state.
# - The heuristic uses only current DB signals and can be replaced after real feedback.
# :END_MODULE_CONTRACT

from dataclasses import dataclass

from sqlmodel import Session, select

from observatory.models import ComparisonCell, EvidenceItem, Harness, Insight, Lens, Score, Topic


@dataclass(frozen=True)
class DefaultLens:
    name: str
    slug: str
    description: str
    weights: dict[str, float]


@dataclass(frozen=True)
class LensScoreInput:
    state_score: float
    confidence_score: float
    evidence_score: float
    insight_score: float
    evidence_count: int
    insight_count: int
    cell_state: str
    confidence_band: str


DEFAULT_LENSES: tuple[DefaultLens, ...] = (
    DefaultLens(
        name="Research",
        slug="research",
        description="Rewards evidence density and confidence for deeper investigation.",
        weights={"state": 0.10, "confidence": 0.25, "evidence": 0.40, "insight": 0.25},
    ),
    DefaultLens(
        name="Lecturer",
        slug="lecturer",
        description="Rewards teachable insight density with enough proof to support a lesson.",
        weights={"state": 0.20, "confidence": 0.15, "evidence": 0.25, "insight": 0.40},
    ),
    DefaultLens(
        name="Practical Selection",
        slug="practical-selection",
        description="Rewards clear comparison state, confidence, and practical proof.",
        weights={"state": 0.40, "confidence": 0.25, "evidence": 0.25, "insight": 0.10},
    ),
    DefaultLens(
        name="Ecosystem",
        slug="ecosystem",
        description="Balances comparison coverage, evidence, confidence, and reusable insight.",
        weights={"state": 0.25, "confidence": 0.20, "evidence": 0.25, "insight": 0.30},
    ),
)


@dataclass(frozen=True)
class ScoreRefreshResult:
    lenses_seeded: int
    scores_written: int


# START_SEED_DEFAULT_LENSES:
def seed_default_lenses(session: Session) -> int:
    """Create the starting v1.0 lens rows if they do not already exist."""
    created = 0
    for default in DEFAULT_LENSES:
        lens = session.exec(select(Lens).where(Lens.slug == default.slug)).first()
        if lens is None:
            session.add(
                Lens(
                    name=default.name,
                    slug=default.slug,
                    description=default.description,
                )
            )
            created += 1
        else:
            lens.name = default.name
            lens.description = default.description
            session.add(lens)
    session.commit()
    return created


# :END_SEED_DEFAULT_LENSES


# START_REFRESH_LENS_SCORES:
def refresh_lens_scores(session: Session) -> ScoreRefreshResult:
    """Refresh deterministic Score rows for every observed harness/topic pair."""
    lenses_seeded = seed_default_lenses(session)
    lenses = list(session.exec(select(Lens).order_by(Lens.name)).all())
    harnesses = list(session.exec(select(Harness).order_by(Harness.name)).all())
    topics = list(session.exec(select(Topic).order_by(Topic.name)).all())
    pairs = _observed_pairs(session, harnesses, topics)
    scores_written = 0

    for harness, topic in pairs:
        score_input = _score_input(session, harness, topic)
        for lens in lenses:
            default = _default_lens_for_slug(lens.slug)
            if default is None:
                continue
            value = _weighted_value(score_input, default.weights)
            rationale = _rationale(score_input)
            score = _existing_score(session, lens, harness, topic)
            if score is None:
                score = Score(lens_id=lens.id, harness_id=harness.id, topic_id=topic.id)
            score.value = value
            score.rationale = rationale
            session.add(score)
            scores_written += 1

    session.commit()
    return ScoreRefreshResult(lenses_seeded=lenses_seeded, scores_written=scores_written)


# :END_REFRESH_LENS_SCORES


def _observed_pairs(
    session: Session, harnesses: list[Harness], topics: list[Topic]
) -> list[tuple[Harness, Topic]]:
    harness_by_id = {harness.id: harness for harness in harnesses if harness.id is not None}
    topic_by_id = {topic.id: topic for topic in topics if topic.id is not None}
    pair_ids: set[tuple[int, int]] = set()

    for cell in session.exec(select(ComparisonCell)).all():
        pair_ids.add((cell.harness_id, cell.topic_id))
    for evidence in session.exec(select(EvidenceItem)).all():
        if evidence.harness_id is not None and evidence.topic_id is not None:
            pair_ids.add((evidence.harness_id, evidence.topic_id))
    for insight in session.exec(select(Insight)).all():
        if insight.harness_id is not None and insight.topic_id is not None:
            pair_ids.add((insight.harness_id, insight.topic_id))

    pairs = [
        (harness_by_id[harness_id], topic_by_id[topic_id])
        for harness_id, topic_id in sorted(pair_ids)
        if harness_id in harness_by_id and topic_id in topic_by_id
    ]
    return sorted(pairs, key=lambda pair: (pair[0].name, pair[1].name))


def _score_input(session: Session, harness: Harness, topic: Topic) -> LensScoreInput:
    cell = session.exec(
        select(ComparisonCell)
        .where(ComparisonCell.harness_id == harness.id)
        .where(ComparisonCell.topic_id == topic.id)
    ).first()
    evidence_count = len(
        session.exec(
            select(EvidenceItem.id)
            .where(EvidenceItem.harness_id == harness.id)
            .where(EvidenceItem.topic_id == topic.id)
        ).all()
    )
    insight_count = len(
        session.exec(
            select(Insight.id)
            .where(Insight.harness_id == harness.id)
            .where(Insight.topic_id == topic.id)
        ).all()
    )
    cell_state = cell.state if cell else "unknown"
    confidence_band = cell.confidence_band if cell else "unverified"
    return LensScoreInput(
        state_score=_state_score(cell_state),
        confidence_score=_confidence_score(confidence_band),
        evidence_score=min(evidence_count, 5) / 5,
        insight_score=min(insight_count, 3) / 3,
        evidence_count=evidence_count,
        insight_count=insight_count,
        cell_state=cell_state,
        confidence_band=confidence_band,
    )


def _weighted_value(score_input: LensScoreInput, weights: dict[str, float]) -> float:
    value = (
        score_input.state_score * weights["state"]
        + score_input.confidence_score * weights["confidence"]
        + score_input.evidence_score * weights["evidence"]
        + score_input.insight_score * weights["insight"]
    )
    return round(value * 100, 1)


def _rationale(score_input: LensScoreInput) -> str:
    return (
        f"state={score_input.cell_state}; confidence={score_input.confidence_band}; "
        f"evidence={score_input.evidence_count}; insights={score_input.insight_count}"
    )


def _existing_score(session: Session, lens: Lens, harness: Harness, topic: Topic) -> Score | None:
    return session.exec(
        select(Score)
        .where(Score.lens_id == lens.id)
        .where(Score.harness_id == harness.id)
        .where(Score.topic_id == topic.id)
    ).first()


def _default_lens_for_slug(slug: str) -> DefaultLens | None:
    for default in DEFAULT_LENSES:
        if default.slug == slug:
            return default
    return None


def _state_score(state: str) -> float:
    normalized = state.lower()
    if normalized in {"present", "strong", "supported", "yes", "done"}:
        return 1.0
    if normalized in {"partial", "mixed", "emerging"}:
        return 0.65
    if normalized in {"absent", "no"}:
        return 0.20
    return 0.35


def _confidence_score(confidence_band: str) -> float:
    normalized = confidence_band.lower()
    if normalized in {"verified", "human-verified", "corroborated"}:
        return 1.0
    if normalized in {"proposed", "unverified"}:
        return 0.55
    if normalized == "disputed":
        return 0.20
    if normalized == "corrected":
        return 0.75
    return 0.40
