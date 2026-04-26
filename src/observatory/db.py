# FILE: src/observatory/db.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: SQLite engine and SQLModel session helpers for the local observatory database.
# PRD_REF: docs/PRD.md §26.6
# WHY_REF: docs/why-graph.xml#MOD-MODELS
# SCOPE: database URL selection; engine construction; session dependency; testable schema initialization
# INVARIANTS:
# - Default database path is ./observatory.sqlite for local-first development.
# - Importing this module does not create tables; migrations own persistent schema creation.
# :END_MODULE_CONTRACT

from collections.abc import Generator

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from observatory import models  # noqa: F401  # ensure metadata registration

DEFAULT_DATABASE_URL = "sqlite:///./observatory.sqlite"


# START_DB_ENGINE:
def make_engine(database_url: str = DEFAULT_DATABASE_URL) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


engine = make_engine()
# :END_DB_ENGINE


# START_DB_SESSION:
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def init_db(bind: Engine | None = None) -> None:
    SQLModel.metadata.create_all(bind or engine)


# :END_DB_SESSION

