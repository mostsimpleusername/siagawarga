"""
app/domain/entities/penugasan.py
Model Penugasan — penugasan laporan ke Tim Petugas.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.base import Base

if TYPE_CHECKING:
    from app.domain.entities.laporan import Laporan
    from app.domain.entities.tim_petugas import TimPetugas


class Penugasan(Base):
    __tablename__ = "penugasan"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="idPenugasan dari Class Diagram",
    )
    laporan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laporan.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK ke Laporan yang ditugaskan",
    )
    tim_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tim_petugas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK ke TimPetugas penerima (penerima dari Class Diagram)",
    )
    ditugaskan_pada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="ditugaskanPada dari Class Diagram (timestamp penugasan)",
    )
    catatan_penugasan: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Instruksi atau catatan dari petugas yang menugaskan",
    )
    diselesaikan_pada: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Waktu penugasan diselesaikan (NULL jika masih aktif)",
    )
    is_aktif: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="True = penugasan aktif saat ini (False jika sudah selesai/diganti)",
    )

    laporan: Mapped["Laporan"] = relationship(
        "Laporan",
        back_populates="penugasan",
    )
    tim_penerima: Mapped[Optional["TimPetugas"]] = relationship(
        "TimPetugas",
        back_populates="penugasan",
    )

    def __repr__(self) -> str:
        return f"<Penugasan id={self.id} laporan={self.laporan_id} tim={self.tim_id} aktif={self.is_aktif}>"
