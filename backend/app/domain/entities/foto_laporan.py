"""
app/domain/entities/foto_laporan.py
Model FotoLaporan — bukti foto yang dilampirkan pada laporan (Komposisi).
"""
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.domain.entities.laporan import Laporan


class FotoLaporan(Base, TimestampMixin):
    __tablename__ = "foto_laporan"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Primary key UUID foto (idFoto dari Class Diagram)",
    )
    laporan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laporan.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK ke Laporan pemilik foto (CASCADE DELETE — komposisi)",
    )
    url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        comment="URL foto di cloud storage (KF-04)",
    )
    hasil_analisis: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Rekomendasi AI dari foto (kategori & severity) — KF-11, KNF-10.",
    )
    nama_file_asli: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Nama file asli yang diunggah pengguna",
    )
    ukuran_byte: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Ukuran file dalam byte",
    )
    mime_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="MIME type (image/jpeg, image/png, dll.)",
    )
    urutan: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Urutan tampil foto (0 = foto utama/cover)",
    )

    laporan: Mapped["Laporan"] = relationship(
        "Laporan",
        back_populates="foto",
    )

    def __repr__(self) -> str:
        return f"<FotoLaporan id={self.id} laporan_id={self.laporan_id}>"
