"""
app/domain/entities/lokasi.py
Model LokasiLaporan — lokasi kejadian permasalahan (Komposisi).
"""
import uuid
from typing import TYPE_CHECKING, Any, Optional

from geoalchemy2 import Geography
from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.base import Base

if TYPE_CHECKING:
    from app.domain.entities.laporan import Laporan


class LokasiLaporan(Base):
    __tablename__ = "lokasi_laporan"
    __table_args__ = (
        UniqueConstraint("laporan_id", name="uq_lokasi_satu_per_laporan"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    laporan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laporan.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="FK ke Laporan (1:1, CASCADE DELETE — komposisi)",
    )
    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Koordinat lintang [-90, 90] (KF-05)",
    )
    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Koordinat bujur [-180, 180] (KF-05)",
    )
    alamat: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Alamat tekstual lokasi kejadian",
    )
    koordinat: Mapped[Optional[Any]] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
        comment="PostGIS Geography POINT (SRID 4326)",
    )

    laporan: Mapped["Laporan"] = relationship(
        "Laporan",
        back_populates="lokasi",
    )

    def __repr__(self) -> str:
        return f"<LokasiLaporan laporan_id={self.laporan_id} lat={self.latitude} lng={self.longitude}>"
