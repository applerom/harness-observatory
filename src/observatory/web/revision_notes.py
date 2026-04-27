# FILE: src/observatory/web/revision_notes.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Shared RevisionNote lookup helpers for Insight rendering routes.
# PRD_REF: docs/PRD.md §24 v0.7
# WHY_REF: docs/why-graph.xml#FEAT-ASK-AGENT-WHY
# SCOPE: route helper only; no writes; maps persisted Insight ids to RevisionNotes
# INVARIANTS:
# - Explain results stored as RevisionNotes must be renderable from every Insight surface.
# :END_MODULE_CONTRACT

from sqlmodel import Session, select

from observatory.models import Insight, RevisionNote


def revision_notes_by_insight_id(
    session: Session,
    insights: list[Insight],
) -> dict[int, list[RevisionNote]]:
    insight_ids = {insight.id for insight in insights if insight.id is not None}
    notes_by_id: dict[int, list[RevisionNote]] = {insight_id: [] for insight_id in insight_ids}
    if not insight_ids:
        return notes_by_id
    notes = sorted(
        session.exec(select(RevisionNote)).all(),
        key=lambda note: note.created_at,
    )
    for note in notes:
        if note.insight_id in notes_by_id:
            notes_by_id[note.insight_id].append(note)
    return notes_by_id
