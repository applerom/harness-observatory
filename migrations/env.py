# FILE: migrations/env.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Alembic environment wiring SQLModel metadata to migration execution.
# PRD_REF: docs/PRD.md §26.6
# WHY_REF: docs/why-graph.xml#MOD-MODELS
# SCOPE: offline migrations; online migrations; model metadata registration
# INVARIANTS:
# - Import observatory.models before exposing target_metadata.
# - Migrations run against the configured Alembic URL unless a caller overrides it.
# :END_MODULE_CONTRACT

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from observatory import models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

