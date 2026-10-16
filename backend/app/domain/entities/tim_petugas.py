"""
app/domain/entities/tim_petugas.py
Model TimPetugas - kelompok petugas yang menerima penugasan laporan.
"""
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.domain.entities.pengguna import Petugas
    from app.domain.entities.penugasan import Penugasan


class TimPetugas(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tim_petugas"

    nama_tim: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Nama tim petugas (unik)",
    )
    deskripsi: Mapped[Optional[str]] = mapped_column(
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

    anggota: Mapped[List["Petugas"]] = relationship(
        "Petugas",
        back_populates="tim",
        foreign_keys="Pengguna.tim_id",
    )
    penugasan: Mapped[List["Penugasan"]] = relationship(
        "Penugasan",
        back_populates="tim_penerima",
    )

    def __repr__(self) -> str:
        return f"<TimPetugas id={self.id} nama='{self.nama_tim}'>"
