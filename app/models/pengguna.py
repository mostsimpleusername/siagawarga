"""
app/models/pengguna.py
Model Pengguna menggunakan Single Table Inheritance (STI).

Hierarki (dari Class Diagram):
  Pengguna (abstract/base) — discriminator: kolom `peran`
    ├── Warga   (peran = WARGA)
    └── Petugas (peran = PETUGAS)

Keputusan arsitektur - STI dipilih karena:
  - Warga dan Petugas tidak memiliki kolom tambahan yang berbeda secara signifikan
  - Satu query JOIN tidak diperlukan untuk mendapatkan data pengguna
  - Kolom `tim_id` (khusus Petugas) disimpan di tabel yang sama dengan nilai NULL
    untuk semua record Warga

Catatan PRD:
  - Tidak mewajibkan NIK (KF-01, Out-of-Scope)
  - Email ATAU nomor HP wajib diisi salah satu (KF-01)
  - Identitas pelapor tidak ditampilkan ke umum (KNF-04)
"""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import Peran

if TYPE_CHECKING:
    from app.models.tim_petugas import TimPetugas
    from app.models.laporan import Laporan
    from app.models.riwayat_status import RiwayatStatus


# ==============================================================
#  PENGGUNA (Base — Single Table Inheritance)
# ==============================================================

class Pengguna(Base, TimestampMixin):
    """
    Entitas dasar pengguna. Tidak diinstansiasi langsung —
    gunakan subkelas Warga atau Petugas.

    Kolom `peran` adalah discriminator SQLAlchemy untuk STI.
    """
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
        SAEnum(Peran, name="peran_enum", create_type=True),
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

    # Kolom khusus Petugas (NULL untuk semua Warga — trade-off STI)
    tim_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tim_petugas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK ke TimPetugas (hanya digunakan oleh Petugas)",
    )

    # -------------------------------------------------------
    # Relasi bersama
    # -------------------------------------------------------
    token_sesi: Mapped[List["TokenSesi"]] = relationship(
        "TokenSesi",
        back_populates="pengguna",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Pengguna id={self.id} nama='{self.nama}' peran={self.peran}>"


# ==============================================================
#  WARGA (STI subclass — polymorphic_identity = WARGA)
# ==============================================================

class Warga(Pengguna):
    """
    Warga: pengguna yang membuat dan memantau laporan.
    Semua data tersimpan di tabel `pengguna` (STI).

    Kemampuan (dari Class Diagram):
      + buatLaporan()
      + lihatLaporanSaya()
      + lihatLaporanSekitar()
      + lihatStatus(idLaporan)
    """
    __mapper_args__ = {
        "polymorphic_identity": Peran.WARGA,
    }

    # Relasi: Warga (1) membuat Laporan (0..*)
    laporan: Mapped[List["Laporan"]] = relationship(
        "Laporan",
        back_populates="warga",
        foreign_keys="Laporan.warga_id",
        # Tidak cascade delete: laporan warga dipertahankan (data historis)
        # Jika Warga dihapus, DB akan RESTRICT karena FK ondelete="RESTRICT"
    )


# ==============================================================
#  PETUGAS (STI subclass — polymorphic_identity = PETUGAS)
# ==============================================================

class Petugas(Pengguna):
    """
    Petugas: pengguna yang memverifikasi, memprioritaskan, dan mengelola laporan.
    Semua data tersimpan di tabel `pengguna` (STI).

    Kemampuan (dari Class Diagram):
      + ubahStatus(idLaporan, status, catatan)
      + tugaskan(idLaporan, penerima)
      + lihatAntrean(filter)
    """
    __mapper_args__ = {
        "polymorphic_identity": Peran.PETUGAS,
    }

    # Relasi: Petugas (0..*) bergabung di TimPetugas (0..1)
    tim: Mapped[Optional["TimPetugas"]] = relationship(
        "TimPetugas",
        back_populates="anggota",
        foreign_keys="Pengguna.tim_id",
    )

    # Relasi: Petugas mengubah status (RiwayatStatus) -- KNF-12
    riwayat_diubah: Mapped[List["RiwayatStatus"]] = relationship(
        "RiwayatStatus",
        back_populates="petugas",
        foreign_keys="RiwayatStatus.petugas_id",
    )


# ==============================================================
#  TOKEN SESI (dari Class Diagram — relasi 1 Pengguna : 0..* Token)
# ==============================================================

class TokenSesi(Base, TimestampMixin):
    """
    Token sesi / refresh token untuk autentikasi (KF-02, KNF-03).
    Mendukung logout dengan pencabutan token (is_dicabut).

    Relasi (dari Class Diagram):
      Pengguna (1) memiliki TokenSesi (0..*)
    Method: masihValid() → Boolean
    """
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

    # -------------------------------------------------------
    # Relasi
    # -------------------------------------------------------
    pengguna: Mapped["Pengguna"] = relationship(
        "Pengguna",
        back_populates="token_sesi",
    )

    def masih_valid(self) -> bool:
        """
        Implementasi method masihValid() dari Class Diagram.
        Token valid jika belum kedaluwarsa DAN belum dicabut.
        """
        now = datetime.now(timezone.utc)
        exp = self.kedaluwarsa
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return not self.is_dicabut and now < exp

    def __repr__(self) -> str:
        return (
            f"<TokenSesi pengguna_id={self.pengguna_id} "
            f"valid={self.masih_valid()}>"
        )
