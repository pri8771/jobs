"""Database engine and session management."""

from __future__ import annotations

import time
from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.core.config import AppSettings
from jobs_automation.db.base import Base


def get_engine(database_url: str | None = None, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine supporting PostgreSQL and SQLite."""
    if database_url is None:
        settings = AppSettings()
        database_url = settings.database_url

    # Handle SQLite connect_args if testing with sqlite
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            echo=echo,
            connect_args={"check_same_thread": False},
        )

    return create_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,
    )


def get_sessionmaker(engine: Engine | None = None) -> sessionmaker[Session]:
    if engine is None:
        engine = get_engine()
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db(engine: Engine | None = None) -> Generator[Session, None, None]:
    maker = get_sessionmaker(engine)
    session = maker()
    try:
        yield session
    finally:
        session.close()


def init_db(engine: Engine) -> None:
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


def check_db_connection(engine: Engine) -> tuple[bool, str, float]:
    """Check connectivity to the database and measure latency in milliseconds."""
    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000
        return True, "Connected successfully", latency_ms
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        return False, str(e), latency_ms
