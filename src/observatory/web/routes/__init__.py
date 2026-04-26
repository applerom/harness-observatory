# FILE: src/observatory/web/routes/__init__.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Central router registration for the web app.
# PRD_REF: docs/PRD.md §26.2, §26.6
# WHY_REF: docs/why-graph.xml MOD-WEB-APP
# SCOPE: include route modules without adding feature logic
# INVARIANTS:
# - v0.1 registers only read-only routes owned by the current slice.
# :END_MODULE_CONTRACT

from fastapi import FastAPI

from observatory.web.routes import dashboard


def register_routes(app: FastAPI) -> None:
    """Attach v0.1 routers to the application."""
    app.include_router(dashboard.router)
