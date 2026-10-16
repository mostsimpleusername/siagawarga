"""
app/domain/entities/kategori_laporan.py
Model KategoriLaporan - kategori permasalahan yang dapat dikonfigurasi (KNF-09).
"""
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.domain.entities.laporan import Laporan


class KategoriLaporan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "kategori_laporan"

    nama: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Nama kategori (unik, dapat diperbarui - KNF-09)",
    )
    deskripsi: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Deskripsi singkat kategori",
    )
    ikon: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Kode ikon untuk frontend (opsional)",
    )
    bobot_bahaya_default: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
        comment="Bobot default tingkat bahaya kategori ini (skala 1.0 - 5.0)",
    )
    is_aktif: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Aktifkan/nonaktifkan kategori tanpa menghapus data",
    )

    laporan: Mapped[List["Laporan"]] = relationship(
        "Laporan",
        back_populates="kategori",
    )

    def __repr__(self) -> str:
        return f"<KategoriLaporan id={self.id} nama='{self.nama}'>"
