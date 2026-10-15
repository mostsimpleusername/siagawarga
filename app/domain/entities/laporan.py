"""
app/domain/entities/laporan.py
Model database SQLAlchemy untuk Laporan Warga dengan PostGIS Geometry.
"""
import uuid
from typing import TYPE_CHECKING, List, Optional

from geoalchemy2 import Geometry
from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.base import Base, TimestampMixin
from app.domain.enums import KategoriPrioritas, Severity, StatusLaporan

if TYPE_CHECKING:
    from app.domain.entities.foto_laporan import FotoLaporan
    from app.domain.entities.kategori_laporan import KategoriLaporan
    from app.domain.entities.lokasi import LokasiLaporan
    from app.domain.entities.pengguna import Warga
    from app.domain.entities.penugasan import Penugasan
    from app.domain.entities.riwayat_status import RiwayatStatus


class Laporan(Base, TimestampMixin):
    __tablename__ = "laporan"
    __table_args__ = (
        CheckConstraint(
            "skor_prioritas IS NULL OR (skor_prioritas >= 0 AND skor_prioritas <= 100)",
            name="ck_laporan_skor_prioritas_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Primary key UUID laporan",
    )

    warga_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pengguna.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="FK ke Warga pelapor",
    )
    kategori_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kategori_laporan.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="FK ke Kategori master",
    )

    judul: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="Laporan Warga",
        comment="Judul singkat laporan",
    )
    deskripsi: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Deskripsi lengkap permasalahan",
    )
    alamat_lokasi: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Alamat tekstual lokasi kejadian",
    )

    titik_koordinat: Mapped[Optional[str]] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
        comment="Titik spasial PostGIS POINT(longitude latitude)",
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    severity: Mapped[Severity] = mapped_column(
        SAEnum(Severity, name="severity_enum", create_type=False),
        nullable=False,
        default=Severity.SEDANG,
    )
    status: Mapped[StatusLaporan] = mapped_column(
        SAEnum(StatusLaporan, name="status_laporan_enum", create_type=False),
        nullable=False,
        default=StatusLaporan.DIKIRIM,
        index=True,
    )

    # 5 Parameter Priority Score & Hasil
    tingkat_bahaya: Mapped[float] = mapped_column(
        Float, nullable=False, default=50.0, comment="Parameter 1: Tingkat Bahaya (0-100)"
    )
    faktor_lokasi: Mapped[float] = mapped_column(
        Float, nullable=False, default=50.0, comment="Parameter 2: Faktor Lokasi strategis (0-100)"
    )
    dampak: Mapped[float] = mapped_column(
        Float, nullable=False, default=50.0, comment="Parameter 3: Dampak gangguan aktivitas (0-100)"
    )
    jumlah_pelapor: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="Parameter 4: Jumlah pelapor / laporan serupa"
    )
    waktu_tunggu_jam: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="Parameter 5: Lama waktu tunggu (jam)"
    )

    skor_prioritas: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, index=True, comment="Total Priority Score (0-100)"
    )
    kategori_prioritas: Mapped[KategoriPrioritas] = mapped_column(
        SAEnum(KategoriPrioritas, name="kategori_prioritas_enum", create_type=False),
        nullable=False,
        default=KategoriPrioritas.P3,
        index=True,
        comment="Klasifikasi: P1, P2, atau P3",
    )

    # Relasi ORM
    warga: Mapped["Warga"] = relationship("Warga", back_populates="laporan")
    kategori: Mapped["KategoriLaporan"] = relationship("KategoriLaporan", back_populates="laporan")
    lokasi: Mapped[Optional["LokasiLaporan"]] = relationship(
        "LokasiLaporan",
        back_populates="laporan",
        uselist=False,
        cascade="all, delete-orphan",
    )
    foto: Mapped[List["FotoLaporan"]] = relationship(
        "FotoLaporan", back_populates="laporan", cascade="all, delete-orphan"
    )
    riwayat_status: Mapped[List["RiwayatStatus"]] = relationship(
        "RiwayatStatus", back_populates="laporan", cascade="all, delete-orphan"
    )
    penugasan: Mapped[List["Penugasan"]] = relationship(
        "Penugasan", back_populates="laporan", cascade="all, delete-orphan"
    )
