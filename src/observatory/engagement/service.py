# FILE: src/observatory/engagement/service.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Deterministic v0.6 engagement service for Insight hooks and first-observer claims.
# PRD_REF: docs/PRD.md §7 Insight, §14.2 Job types
# WHY_REF: docs/why-graph.xml#MOD-ENGAGEMENT-SERVICE
# SCOPE: engagement AgentJob creation; missing engagement field generation; first-observer attribution
# INVARIANTS:
# - v0.6a generation is deterministic and never calls a real model.
# - First-observer attribution stores a free-text handle, not a user account reference.
# :END_MODULE_CONTRACT

from sqlmodel import Session, select

from observatory.models import AgentJob, Insight, PromptTemplate, utc_now


ENGAGEMENT_TEMPLATE_NAME = "insight-engagement-v0.6a"
ENGAGEMENT_TEMPLATE_VERSION = "0.6a"


# START_ENGAGEMENT_JOB:
def create_engagement_job(session: Session, insight: Insight, trigger: str = "manual") -> AgentJob:
    """Create a deterministic engagement job and fill missing Insight copy."""
    template = ensure_engagement_prompt_template(session)
    hook, seed = deterministic_engagement_copy(insight)
    changed = False
    if not insight.engagement_hook:
        insight.engagement_hook = hook
        changed = True
    if not insight.joke_or_telegram_seed:
        insight.joke_or_telegram_seed = seed
        changed = True

    now = utc_now()
    job = AgentJob(
        type="engagement",
        target_kind="Insight",
        target_id=insight.id,
        prompt_template_id=template.id,
        prompt_text=render_engagement_prompt(template, insight),
        runner_name="deterministic",
        runner_version=ENGAGEMENT_TEMPLATE_VERSION,
        trigger=trigger,
        status="done",
        created_at=now,
        started_at=now,
        finished_at=now,
        produced_artifact_ids=[insight.id] if insight.id is not None else [],
    )
    session.add(job)
    if changed:
        session.add(insight)
    session.commit()
    session.refresh(job)
    session.refresh(insight)
    return job


def ensure_engagement_prompt_template(session: Session) -> PromptTemplate:
    existing = session.exec(
        select(PromptTemplate)
        .where(PromptTemplate.name == ENGAGEMENT_TEMPLATE_NAME)
        .where(PromptTemplate.version == ENGAGEMENT_TEMPLATE_VERSION)
    ).first()
    if existing is not None:
        return existing

    template = PromptTemplate(
        name=ENGAGEMENT_TEMPLATE_NAME,
        type="engagement",
        version=ENGAGEMENT_TEMPLATE_VERSION,
        expected_artifact_kind="engagement-copy",
        body=(
            "Create a short teaching hook and Telegram seed for Insight #{insight_id}: "
            "{short_title}. Keep the claim evidence-backed and classroom-friendly."
        ),
        notes="v0.6a deterministic local seed; no model invocation.",
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


def render_engagement_prompt(template: PromptTemplate, insight: Insight) -> str:
    return template.body.format(
        insight_id=insight.id or "new",
        short_title=insight.short_title,
    )


def deterministic_engagement_copy(insight: Insight) -> tuple[str, str]:
    title = insight.short_title.strip().rstrip(".")
    audience = insight.audience or "mixed audience"
    hook = f"Wait for this: {title} changes how {audience} should read the tool."
    seed = (
        f"Telegram seed: {title}. "
        f"Why it matters: {insight.why_it_matters or insight.body}"
    )
    return hook, seed


# :END_ENGAGEMENT_JOB


# START_FIRST_OBSERVER_CLAIM:
def claim_first_observer(session: Session, insight: Insight, observer_name: str) -> Insight:
    """Store the first observer for an Insight if it has not already been claimed."""
    cleaned_name = observer_name.strip()
    if not cleaned_name:
        raise ValueError("Observer name is required")
    if insight.first_observed_by is None:
        insight.first_observed_by = cleaned_name
        session.add(insight)
        session.commit()
        session.refresh(insight)
    return insight


# :END_FIRST_OBSERVER_CLAIM
