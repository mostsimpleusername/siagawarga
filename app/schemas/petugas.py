"""
app/schemas/petugas.py
Skema Pydantic untuk modul pengelolaan laporan oleh Petugas:
- KF-09: Melihat seluruh laporan
- KF-10: Memverifikasi laporan
- KF-15 & KF-16: Memperbarui status dan mencatat penanganan
- KF-18 & KNF-12: Riwayat audit trail lengkap
"""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import KategoriPrioritas, Severity, StatusLaporan
from app.schemas.kategori_laporan import KategoriLaporanResponse
from app.schemas.laporan import FotoLaporanItem


# --- Audit Trail Riwayat Status (KF-18, KNF-12) ---

class PetugasRingkas(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nama: str
    email: Optional[str] = None


class RiwayatStatusAuditItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status_lama: Optional[StatusLaporan]
    status_baru: StatusLaporan
    catatan: Optional[str]
    waktu: datetime
    petugas_id: Optional[uuid.UUID]
    petugas: Optional[PetugasRingkas] = None


# --- Pelapor untuk Tampilan Petugas (KF-09) ---

class PelaporDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nama: str
    email: Optional[str] = None
    nomor_hp: Optional[str] = None


# --- Request DTO Petugas ---

class VerifikasiLaporanRequest(BaseModel):
    """
    KF-10: Memverifikasi laporan masuk sebelum ditindaklanjuti.
    Jika diterima, status menjadi DIPROSES. Jika ditolak, status menjadi DITOLAK.
    """
    terima: bool = Field(..., description="True untuk menerima dan memproses, False untuk menolak laporan")
    catatan: str = Field(..., min_length=5, description="Catatan verifikasi atau alasan penolakan")
    sesuaikan_severity: Optional[Severity] = Field(
        None, description="Opsional: penyesuaian tingkat keparahan jika berbeda dari pelapor"
    )


class UpdateStatusLaporanRequest(BaseModel):
    """
    KF-15 & KF-16: Memperbarui status laporan dan mencatat tindak lanjut.
    """
    status_baru: StatusLaporan = Field(..., description="Status baru laporan (DIPROSES, SELESAI, DITOLAK)")
    catatan: str = Field(..., min_length=5, description="Catatan tindakan penanganan atau penyelesaian")


# --- Response DTO Petugas ---

class LaporanPetugasListItem(BaseModel):
    """KF-09: Ringkasan item laporan pada daftar kelola petugas"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    judul: str
    deskripsi: str
    status: StatusLaporan
    severity: Severity
    kategori_prioritas: KategoriPrioritas
    skor_prioritas: float
    alamat_lokasi: Optional[str]
    latitude: float
    longitude: float
    dibuat_pada: datetime
    diperbarui_pada: datetime

    kategori: Optional[KategoriLaporanResponse] = None
    pelapor: Optional[PelaporDetail] = None
    foto: List[FotoLaporanItem] = []


class LaporanPetugasDetailResponse(LaporanPetugasListItem):
    """KF-09 & KF-18: Detail komprehensif laporan termasuk audit trail riwayat status"""
    tingkat_bahaya: float
    faktor_lokasi: float
    dampak: float
    jumlah_pelapor: int
    waktu_tunggu_jam: float
    riwayat_status: List[RiwayatStatusAuditItem] = []


class PaginatedLaporanPetugasResponse(BaseModel):
    """Respon daftar laporan terpaginasi untuk Command Center Petugas"""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[LaporanPetugasListItem]
