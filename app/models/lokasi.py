"""
app/models/lokasi.py
Model LokasiLaporan — lokasi kejadian permasalahan.

Relasi (dari Class Diagram):
  Laporan (1) --berlokasi-->◆ LokasiLaporan (1)   [KOMPOSISI]

Komposisi: LokasiLaporan TIDAK dapat eksis tanpa Laporan.
  → ondelete="CASCADE" pada FK laporan_id
  → cascade="all, delete-orphan" di sisi relasi Laporan

PostGIS:
  Kolom `koordinat` menggunakan Geography(POINT, SRID 4326) untuk:
  - Menampilkan persebaran laporan di peta (KF-14)
  - Menghitung radius laporan serupa (KF-17, deteksi duplikasi)
  - Kalkulasi parameter dampak lokasi Priority Score (KF-12)

  ST_DWithin() dapat digunakan langsung pada kolom Geography
  tanpa konversi manual karena unit sudah dalam meter.
"""
import uuid
from typing import TYPE_CHECKING, Any, Optional

from geoalchemy2 import Geography
from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.laporan import Laporan


class LokasiLaporan(Base):
    """
    Lokasi kejadian laporan (KOMPOSISI dengan Laporan).
    Satu laporan memiliki tepat satu lokasi.

    Atribut (dari Class Diagram):
      + latitude  : Double
      + longitude : Double
      + alamat    : String
    Method:
      + jarakKe(lokasi) : Double  → diimplementasikan via PostGIS ST_Distance()
    """
    __tablename__ = "lokasi_laporan"
    __table_args__ = (
        # Penegasan relasi 1:1 di level database
        UniqueConstraint("laporan_id", name="uq_lokasi_satu_per_laporan"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # FK ke Laporan (komposisi — CASCADE DELETE)
    laporan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laporan.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="FK ke Laporan (1:1, CASCADE DELETE — komposisi)",
    )

    # Koordinat eksplisit (dari Class Diagram)
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
        comment="Alamat tekstual (reverse geocoding atau input manual warga)",
    )

    # PostGIS Geography POINT — untuk query spasial (KF-14, KF-17)
    # Diisi otomatis via trigger atau service layer dari lat/lng
    # Format: ST_GeographyFromText('SRID=4326;POINT(longitude latitude)')
    koordinat: Mapped[Optional[Any]] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
        comment=(
            "PostGIS Geography POINT (SRID 4326). "
            "Gunakan ST_DWithin() untuk query radius meter, "
            "ST_Distance() untuk implementasi jarakKe() dari Class Diagram."
        ),
    )

    # -------------------------------------------------------
    # Relasi
    # -------------------------------------------------------
    laporan: Mapped["Laporan"] = relationship(
        "Laporan",
        back_populates="lokasi",
    )

    def __repr__(self) -> str:
        return (
            f"<LokasiLaporan laporan_id={self.laporan_id} "
            f"lat={self.latitude} lng={self.longitude}>"
        )
