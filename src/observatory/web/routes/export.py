# FILE: src/observatory/web/routes/export.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Web route for generated Markdown exports.
# PRD_REF: docs/PRD.md §24 v1.0
# WHY_REF: docs/why-graph.xml#MOD-WEB-ROUTES-EXPORTS
# SCOPE: generated file listing; manual generation action
# INVARIANTS:
# - Route delegates export writes to observatory.exports.service.
# - Export generation writes only under generated-docs and never mutates legacy source repositories.
# :END_MODULE_CONTRACT

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from observatory.db import get_session
from observatory.exports.service import GENERATED_DOCS_DIR, generate_markdown_exports, list_generated_files


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"

templates = Jinja2Templates(directory=TEMPLATE_DIR)
router = APIRouter(prefix="/exports", tags=["exports"])


# START_ROUTE_EXPORT_LIST:
@router.get("", response_class=HTMLResponse)
def list_exports(request: Request) -> HTMLResponse:
    files = list_generated_files(GENERATED_DOCS_DIR)
    generated = request.query_params.get("generated") == "1"
    return templates.TemplateResponse(
        request,
        "export/index.html",
        {
            "active_nav": "exports",
            "files": files,
            "output_dir": GENERATED_DOCS_DIR.as_posix(),
            "generated": generated,
        },
    )


# :END_ROUTE_EXPORT_LIST


# START_ROUTE_EXPORT_GENERATE:
@router.post("/generate", response_class=RedirectResponse)
def generate_exports(
    session: Session = Depends(get_session),
    legacy_source_path: str = Form(default=""),
) -> RedirectResponse:
    source = Path(legacy_source_path) if legacy_source_path.strip() else None
    generate_markdown_exports(session, output_dir=GENERATED_DOCS_DIR, legacy_source_path=source)
    return RedirectResponse("/exports?generated=1", status_code=303)


# :END_ROUTE_EXPORT_GENERATE
