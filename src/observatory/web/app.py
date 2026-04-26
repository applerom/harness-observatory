# FILE: src/observatory/web/app.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: FastAPI application factory for the v0.1 read-only web surface.
# PRD_REF: docs/PRD.md §20, §26.2, §26.6
# WHY_REF: docs/why-graph.xml MOD-WEB-APP
# SCOPE: app construction; router registration; static asset mounting
# INVARIANTS:
# - create_app is side-effect light and safe for uvicorn --factory and TestClient.
# - v0.1 registers no AgentJob execution, cron scheduler, Live Studio, or CLI surface.
# :END_MODULE_CONTRACT

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from observatory.web.routes import register_routes


PACKAGE_ROOT = Path(__file__).resolve().parent


# START_APP_FACTORY:
def create_app() -> FastAPI:
    """Create and configure the Harness Observatory FastAPI app."""
    app = FastAPI(title="Harness Observatory", version="0.1.0")

    # START_APP_DB_INIT:
    # Persistent schema creation is owned by Alembic/importer commands; the app only
    # opens read-only sessions against the configured local SQLite database.
    # :END_APP_DB_INIT

    static_dir = PACKAGE_ROOT / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # START_APP_ROUTERS:
    register_routes(app)
    # :END_APP_ROUTERS

    return app


# :END_APP_FACTORY
