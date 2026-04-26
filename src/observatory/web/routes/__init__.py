# FILE: src/observatory/web/routes/__init__.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Central router registration for the web app.
# PRD_REF: docs/PRD.md §26.2, §26.6, §1162
# WHY_REF: docs/why-graph.xml MOD-WEB-APP
# SCOPE: include route modules without adding feature logic
# INVARIANTS:
# - Route registration is declarative; feature behavior stays in route modules.
# :END_MODULE_CONTRACT

from fastapi import FastAPI

from observatory.web.routes import dashboard, harness, jobs, matrix, topic


def register_routes(app: FastAPI) -> None:
    """Attach web routers to the application."""
    app.include_router(dashboard.router)
    app.include_router(harness.router)
    app.include_router(topic.router)
    app.include_router(matrix.router)
    app.include_router(jobs.router)
