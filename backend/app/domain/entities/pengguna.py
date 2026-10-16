"""
app/domain/entities/pengguna.py
Model Pengguna menggunakan Single Table Inheritance (STI).
"""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.base import Base, TimestampMixin
from app.domain.enums import Peran

if TYPE_CHECKING:
    from app.domain.entities.tim_petugas import TimPetugas
    from app.domain.entities.laporan import Laporan
    from app.domain.entities.riwayat_status import RiwayatStatus


class Pengguna(Base, TimestampMixin):
    __tablename__ = "pengguna"
    __mapper_args__ = {
        "polymorphic_on": "peran",
    }

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Primary key UUID pengguna",
    )
    nama: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nama lengkap pengguna",
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        comment="Email (wajib jika tidak ada nomor HP) — tanpa verifikasi NIK (KF-01)",
    )
    nomor_hp: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        index=True,
        comment="Nomor HP (wajib jika tidak ada email) — KF-01",
    )
    kata_sandi_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Hash bcrypt dari kata sandi (KNF-03)",
    )
    peran: Mapped[Peran] = mapped_column(
        SAEnum(Peran, name="peran_enum", create_type=False),
        nullable=False,
        index=True,
        comment="Discriminator STI: WARGA atau PETUGAS",
    )
    is_aktif: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Status keaktifan akun",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Status verifikasi email (True jika email telah diverifikasi via tautan)",
    )

    tim_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tim_petugas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK ke TimPetugas (hanya digunakan oleh Petugas)",
    )

    token_sesi: Mapped[List["TokenSesi"]] = relationship(
        "TokenSesi",
        back_populates="pengguna",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Pengguna id={self.id} nama='{self.nama}' peran={self.peran}>"


class Warga(Pengguna):
    __mapper_args__ = {
        "polymorphic_identity": Peran.WARGA,
    }

    laporan: Mapped[List["Laporan"]] = relationship(
        "Laporan",
        back_populates="warga",
        foreign_keys="Laporan.warga_id",
    )


class Petugas(Pengguna):
    __mapper_args__ = {
        "polymorphic_identity": Peran.PETUGAS,
    }

    tim: Mapped[Optional["TimPetugas"]] = relationship(
        "TimPetugas",
        back_populates="anggota",
        foreign_keys="Pengguna.tim_id",
    )
    riwayat_diubah: Mapped[List["RiwayatStatus"]] = relationship(
        "RiwayatStatus",
        back_populates="petugas",
        foreign_keys="RiwayatStatus.petugas_id",
    )


class TokenSesi(Base, TimestampMixin):
    __tablename__ = "token_sesi"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    pengguna_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pengguna.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK ke pemilik token",
    )
    token: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
        index=True,
        comment="JWT refresh token (hashed atau raw)",
    )
    kedaluwarsa: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Waktu kedaluwarsa token",
    )
    is_dicabut: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True setelah logout atau pencabutan paksa",
    )

    pengguna: Mapped["Pengguna"] = relationship(
        "Pengguna",
        back_populates="token_sesi",
    )

    def masih_valid(self) -> bool:
        now = datetime.now(timezone.utc)
        exp = self.kedaluwarsa
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return not self.is_dicabut and now < exp

    def __repr__(self) -> str:
        return f"<TokenSesi pengguna_id={self.pengguna_id} valid={self.masih_valid()}>"
