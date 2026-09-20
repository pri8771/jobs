"""SQLAlchemy declarative base and common column utilities."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import DateTime, types
from sqlalchemy.orm import DeclarativeBase


class UTCDateTime(types.TypeDecorator[datetime.datetime]):
    """Ensure datetime values are timezone-aware UTC."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is not None:
            if not isinstance(value, datetime.datetime):
                raise TypeError(f"Expected datetime.datetime, got {type(value)}")
            if value.tzinfo is None:
                value = value.replace(tzinfo=datetime.UTC)
            else:
                value = value.astimezone(datetime.UTC)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=datetime.UTC)
        return value


class Base(DeclarativeBase):
    """Base declarative class for all ORM models."""


def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)
