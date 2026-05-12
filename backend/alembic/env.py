"""Alembic 环境配置，提供最小迁移上下文"""

import os
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.database import Base

config = context.config

database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def ensure_sqlite_directory() -> None:
    """在执行迁移前确保 SQLite 数据目录已经存在"""

    url = config.get_main_option("sqlalchemy.url")
    if url.startswith("sqlite:///"):
        database_path = url.replace("sqlite:///", "", 1)
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)


def run_migrations_offline() -> None:
    """离线模式执行迁移"""

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
    """在线模式执行迁移"""

    ensure_sqlite_directory()
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
