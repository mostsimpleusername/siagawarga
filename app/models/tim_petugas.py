"""
app/models/tim_petugas.py
Model TimPetugas - kelompok petugas yang menerima penugasan laporan.

Relasi (dari Class Diagram):
  - TimPetugas (1) <-- anggota -- Petugas (1..*)
  - TimPetugas (0..1) <-- penerima -- Penugasan (0..*)
"""
import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.pengguna import Petugas
    from app.models.penugasan import Penugasan


class TimPetugas(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Tim Petugas: kelompok petugas yang menangani laporan bersama.
    Relasi 1 Tim -> 1..* anggota (Petugas).
    """
    __tablename__ = "tim_petugas"

    nama_tim: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Nama tim petugas (unik)",
    )
    deskripsi: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Deskripsi tim dan area tanggung jawab",
    )
    is_aktif: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Status aktif tim",
    )

    # -------------------------------------------------------
    # Relasi
    # -------------------------------------------------------

    # anggota: TimPetugas (1) -> Petugas (1..*) [dari Class Diagram]
    anggota: Mapped[List["Petugas"]] = relationship(
        "Petugas",
        back_populates="tim",
        foreign_keys="Pengguna.tim_id",
    )

    # penerima: TimPetugas (0..1) -> Penugasan (0..*) [dari Class Diagram]
    penugasan: Mapped[List["Penugasan"]] = relationship(
        "Penugasan",
        back_populates="tim_penerima",
    )

    def __repr__(self) -> str:
        return f"<TimPetugas id={self.id} nama='{self.nama_tim}'>"
