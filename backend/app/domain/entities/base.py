"""
app/domain/entities/base.py
Kelas dasar deklaratif dan mixin audit timestamp / UUID untuk seluruh entitas domain.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class untuk seluruh model entitas SQLAlchemy."""
    pass


class UUIDPrimaryKeyMixin:
    """Mixin: Primary key UUID v4, auto-generated."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Primary key UUID (auto-generated)",
    )


class TimestampMixin:
    """Mixin audit timestamp otomatis (KNF-12)."""
    dibuat_pada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp pembuatan record (UTC)",
    )
    diperbarui_pada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp pembaruan terakhir (UTC)",
    )
