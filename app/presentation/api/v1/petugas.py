"""
app/presentation/api/v1/petugas.py
Router API untuk modul pengelolaan operasional Petugas:
- KF-09: Mengelola & melihat seluruh laporan masuk
- KF-10: Memverifikasi laporan sebelum ditindaklanjuti
- KF-15 & KF-16: Memperbarui status dan mencatat hasil penanganan
- KF-18 & KNF-12: Rekam jejak audit trail (waktu dan identitas petugas)
- KNF-03: Diproteksi ketat dengan dependency require_petugas
"""
import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.domain.entities.pengguna import Pengguna
from app.domain.enums import KategoriPrioritas, StatusLaporan
from app.infrastructure.database.session import get_db
from app.presentation.dependencies.auth import require_petugas
from app.presentation.schemas.petugas import (
    LaporanPetugasDetailResponse,
    PaginatedLaporanPetugasResponse,
    UpdateStatusLaporanRequest,
    VerifikasiLaporanRequest,
)
from app.use_cases.petugas import PetugasUseCase

router = APIRouter(prefix="/petugas/laporan", tags=["Manajemen Petugas"])


@router.get(
    "",
    response_model=PaginatedLaporanPetugasResponse,
    status_code=status.HTTP_200_OK,
    summary="Lihat & Kelola Seluruh Laporan (KF-09)",
    description=(
        "Menampilkan seluruh laporan masuk untuk petugas Command Center. "
        "Mendukung filter status, prioritas, kategori, pencarian kata kunci, "
        "dan diurutkan berdasarkan skor prioritas tertinggi secara default."
    ),
)
def get_semua_laporan(
    db: Annotated[Session, Depends(get_db)],
    current_petugas: Annotated[Pengguna, Depends(require_petugas)],
    status_filter: Optional[StatusLaporan] = Query(None, alias="status", description="Filter status laporan"),
    kategori_prioritas: Optional[KategoriPrioritas] = Query(None, description="Filter level prioritas (P1, P2, P3)"),
    kategori_id: Optional[uuid.UUID] = Query(None, description="Filter ID kategori masalah"),
    q: Optional[str] = Query(None, description="Pencarian kata kunci pada judul/deskripsi"),
    page: int = Query(default=1, ge=1, description="Nomor halaman"),
    page_size: int = Query(default=10, ge=1, le=100, description="Jumlah data per halaman"),
):
    return PetugasUseCase.get_semua_laporan(
        db=db,
        status_filter=status_filter,
        kategori_prioritas=kategori_prioritas,
        kategori_id=kategori_id,
        q=q,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{id}",
    response_model=LaporanPetugasDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Detail Lengkap Laporan & Audit Trail (KF-09, KF-18)",
    description="Melihat rincian komprehensif satu laporan beserta log riwayat penanganan dan petugas terkait (KNF-12).",
)
def get_detail_laporan_petugas(
    id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_petugas: Annotated[Pengguna, Depends(require_petugas)],
):
    return PetugasUseCase.get_detail_laporan(db=db, id=id)


@router.post(
    "/{id}/verifikasi",
    response_model=LaporanPetugasDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Verifikasi Laporan Masuk (KF-10)",
    description=(
        "Petugas memvalidasi laporan yang baru masuk. "
        "Jika diterima, status menjadi DIPROSES. Jika ditolak, status menjadi DITOLAK. "
        "Mencatat identitas petugas dan catatan verifikasi ke audit trail (KF-18, KNF-12)."
    ),
)
def verifikasi_laporan(
    id: uuid.UUID,
    payload: VerifikasiLaporanRequest,
    db: Annotated[Session, Depends(get_db)],
    current_petugas: Annotated[Pengguna, Depends(require_petugas)],
):
    return PetugasUseCase.verifikasi_laporan(
        db=db,
        id=id,
        payload=payload,
        current_petugas=current_petugas,
    )


@router.patch(
    "/{id}/status",
    response_model=LaporanPetugasDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Perbarui Status & Catat Penanganan Laporan (KF-15, KF-16)",
    description=(
        "Petugas memperbarui status laporan (misal: DIPROSES, SELESAI, DITOLAK) "
        "dan mencatat hasil penanganan di lapangan. "
        "Merekam otomatis waktu dan petugas penanggung jawab ke audit trail (KF-18, KNF-12)."
    ),
)
def update_status_laporan(
    id: uuid.UUID,
    payload: UpdateStatusLaporanRequest,
    db: Annotated[Session, Depends(get_db)],
    current_petugas: Annotated[Pengguna, Depends(require_petugas)],
):
    return PetugasUseCase.update_status_laporan(
        db=db,
        id=id,
        payload=payload,
        current_petugas=current_petugas,
    )
