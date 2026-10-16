"""
app/schemas/laporan.py
Skema validasi Pydantic untuk Laporan Warga, 5 Parameter Priority Score,
serta respon pelacakan status (KF-08) dan laporan sekitar dengan privasi (KF-07, KNF-04).
"""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import KategoriPrioritas, Severity, StatusLaporan
from app.presentation.schemas.pengguna import PelaporPublikResponse
from app.presentation.schemas.kategori_laporan import KategoriLaporanResponse


# --- Schema Komponen Foto & Status ---

class FotoLaporanItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    urutan: int


class RiwayatStatusItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status_lama: Optional[StatusLaporan]
    status_baru: StatusLaporan
    catatan: Optional[str]
    waktu: datetime


# --- Input Pembuatan Laporan ---

class ParameterPrioritasInput(BaseModel):
    """5 Parameter PRD untuk Priority Score (Otomatis/Opsional dengan Default Cerdas)"""
    tingkat_bahaya: Optional[float] = Field(
        default=None, ge=0.0, le=100.0, description="Tingkat bahaya (skala 0 - 100, opsional/otomatis)"
    )
    faktor_lokasi: Optional[float] = Field(
        default=50.0, ge=0.0, le=100.0, description="Faktor strategis lokasi (skala 0 - 100)"
    )
    dampak: Optional[float] = Field(
        default=50.0, ge=0.0, le=100.0, description="Besaran dampak gangguan publik (skala 0 - 100)"
    )
    jumlah_pelapor: Optional[int] = Field(
        default=1, ge=1, description="Jumlah pelapor atau akumulasi keluhan serupa"
    )
    waktu_tunggu_jam: Optional[float] = Field(
        default=0.0, ge=0.0, description="Waktu tunggu laporan dalam jam"
    )


class LaporanCreate(ParameterPrioritasInput):
    """Payload saat warga membuat laporan baru"""
    judul: str = Field(..., min_length=3, max_length=255, description="Judul laporan")
    deskripsi: str = Field(..., min_length=10, description="Deskripsi rinci keluhan")
    kategori_id: uuid.UUID = Field(..., description="ID Kategori Master")
    severity: Optional[Severity] = Field(default=Severity.SEDANG)

    # Koordinat Spasial
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Lintang titik kejadian")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Bujur titik kejadian")
    alamat_lokasi: Optional[str] = Field(None, max_length=500, description="Alamat/patokan lokasi")

    foto_urls: Optional[List[str]] = Field(default=[], description="Daftar tautan foto lampiran")


class LaporanResponse(BaseModel):
    """Response data laporan setelah tersimpan"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    warga_id: uuid.UUID
    kategori_id: uuid.UUID
    judul: str
    deskripsi: str
    severity: Severity
    status: StatusLaporan

    latitude: float
    longitude: float
    alamat_lokasi: Optional[str]

    # 5 Parameter PRD & Hasil Skor
    tingkat_bahaya: float
    faktor_lokasi: float
    dampak: float
    jumlah_pelapor: int
    waktu_tunggu_jam: float
    skor_prioritas: float
    kategori_prioritas: KategoriPrioritas

    dibuat_pada: datetime
    diperbarui_pada: datetime


# ==========================================================
# Schema Respon Khusus KF-07 & KF-08
# ==========================================================

class LaporanSayaResponse(BaseModel):
    """
    KF-07: Respon untuk daftar laporan milik warga sendiri.
    Menampilkan detail lengkap riwayat & foto.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    judul: str
    deskripsi: str
    status: StatusLaporan
    severity: Severity
    kategori_prioritas: KategoriPrioritas
    alamat_lokasi: Optional[str]
    latitude: float
    longitude: float
    dibuat_pada: datetime
    diperbarui_pada: datetime

    kategori: Optional[KategoriLaporanResponse] = None
    foto: List[FotoLaporanItem] = []
    riwayat_status: List[RiwayatStatusItem] = []


class LaporanSekitarResponse(BaseModel):
    """
    KF-07 & KNF-04: Respon publik untuk laporan di sekitar warga.
    Identitas pelapor disamarkan demi privasi (tanpa NIK, tanpa nomor HP, tanpa email).
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    judul: str
    deskripsi: str
    status: StatusLaporan
    severity: Severity
    alamat_lokasi: Optional[str]
    latitude: float
    longitude: float
    jarak_meter: Optional[float] = None
    dibuat_pada: datetime

    kategori: Optional[KategoriLaporanResponse] = None
    foto: List[FotoLaporanItem] = []
    pelapor: PelaporPublikResponse


class LaporanStatusTrackingResponse(BaseModel):
    """
    KF-08: Respon pelacakan perkembangan status laporan.
    Menampilkan status saat ini dan kronologi perubahan status beserta catatan penanganan.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    judul: str
    status_terkini: StatusLaporan
    dibuat_pada: datetime
    diperbarui_pada: datetime
    timeline: List[RiwayatStatusItem]

class LaporanDetailPetugasResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    judul: str
    deskripsi: str
    status: StatusLaporan
    skor_prioritas: float
    kategori_prioritas: KategoriPrioritas