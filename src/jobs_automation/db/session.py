"""Database engine and session management."""

from __future__ import annotations

import time
from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.core.config import AppSettings
from jobs_automation.db.base import Base


def get_engine(database_url: str | URL | None = None, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine supporting PostgreSQL and SQLite.

    Accepts a ``sqlalchemy.engine.URL`` object as well as a string so callers that
    resolved credentials from trusted runtime configuration never have to render the
    password into a string (``str(URL)`` masks it; rendering it unmasked would put a
    secret into logs or evidence).
    """
    if database_url is None:
        settings = AppSettings()
        database_url = settings.database_url

    drivername = (
        database_url.drivername if isinstance(database_url, URL) else database_url.split(":", 1)[0]
    )
    # Handle SQLite connect_args if testing with sqlite
    if drivername.startswith("sqlite"):
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
