"""
app/models/foto_laporan.py
Model FotoLaporan — bukti foto yang dilampirkan pada laporan.

Relasi (dari Class Diagram):
  Laporan (1) --berisi-->◆ FotoLaporan (0..*)  [KOMPOSISI]

Komposisi: FotoLaporan TIDAK dapat eksis tanpa Laporan.
  → ondelete="CASCADE" pada FK laporan_id
  → cascade="all, delete-orphan" di sisi relasi Laporan

Atribut (dari Class Diagram):
  + idFoto        : UUID
  + url           : String
  + hasilAnalisis : String  (hasil analisis AI KF-11 — rekomendasi, bukan keputusan final KNF-10)
"""
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.laporan import Laporan


class FotoLaporan(Base, TimestampMixin):
    """
    Foto bukti laporan (KOMPOSISI dengan Laporan).
    Satu laporan dapat memiliki banyak foto.

    URL foto disimpan sebagai referensi ke cloud storage
    (S3, Google Cloud Storage, atau objek storage lokal).
    """
    __tablename__ = "foto_laporan"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Primary key UUID foto (idFoto dari Class Diagram)",
    )

    # FK ke Laporan (komposisi — CASCADE DELETE)
    laporan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laporan.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK ke Laporan pemilik foto (CASCADE DELETE — komposisi)",
    )

    # Atribut dari Class Diagram
    url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        comment="URL foto di cloud storage (KF-04)",
    )
    hasil_analisis: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment=(
            "hasilAnalisis dari Class Diagram: rekomendasi AI dari foto "
            "(kategori & severity). Bukan keputusan final — KF-11, KNF-10."
        ),
    )

    # Metadata tambahan (tidak ada di Class Diagram, ditambahkan untuk kebutuhan teknis)
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

    # -------------------------------------------------------
    # Relasi
    # -------------------------------------------------------
    laporan: Mapped["Laporan"] = relationship(
        "Laporan",
        back_populates="foto",
    )

    def __repr__(self) -> str:
        return f"<FotoLaporan id={self.id} laporan_id={self.laporan_id}>"
