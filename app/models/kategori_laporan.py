"""
app/models/kategori_laporan.py
Model KategoriLaporan - kategori permasalahan yang dapat dikonfigurasi.

Keputusan desain (KNF-09):
  Class Diagram menampilkan `kategori` sebagai String di Laporan.
  Namun demi maintainability, diimplementasikan sebagai tabel terpisah
  dengan FK, sehingga kategori dapat diperbarui tanpa mengubah kode.
  Seed data awal diisi via Alembic migration.
"""
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.laporan import Laporan


class KategoriLaporan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Kategori laporan yang dapat dikonfigurasi (KNF-09).

    Contoh data awal (seed):
      - Jalan Rusak
      - Sampah Menumpuk
      - Lampu Jalan Mati
      - Saluran Air Tersumbat
      - Pohon Tumbang
      - Lainnya
    """
    __tablename__ = "kategori_laporan"

    nama: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Nama kategori (unik, dapat diperbarui - KNF-09)",
    )
    deskripsi: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Deskripsi singkat kategori",
    )
    ikon: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Kode ikon untuk frontend (opsional)",
    )
    # Bobot default untuk Parameter 1 Priority Score (dapat diperbarui - KNF-09)
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

    # -------------------------------------------------------
    # Relasi
    # -------------------------------------------------------
    laporan: Mapped[List["Laporan"]] = relationship(
        "Laporan",
        back_populates="kategori",
    )

    def __repr__(self) -> str:
        return f"<KategoriLaporan id={self.id} nama='{self.nama}'>"
