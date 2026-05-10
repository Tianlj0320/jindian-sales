"""
SQLAlchemy 基类与 Mixin
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """自动时间戳 Mixin"""

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SoftDeleteMixin:
    """软删除 Mixin"""

    is_deleted = Column(Integer, default=0, nullable=False, comment="软删除标记: 0=正常, 1=删除")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
