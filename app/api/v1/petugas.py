"""
app/api/v1/petugas.py
Router API untuk modul pengelolaan operasional Petugas:
- KF-09: Mengelola & melihat seluruh laporan masuk
- KF-10: Memverifikasi laporan sebelum ditindaklanjuti
- KF-15 & KF-16: Memperbarui status dan mencatat hasil penanganan
- KF-18 & KNF-12: Rekam jejak audit trail (waktu dan identitas petugas)
- KNF-03: Diproteksi ketat dengan dependency require_petugas
"""
import math
import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import get_db, require_petugas
from app.models.enums import KategoriPrioritas, Severity, StatusLaporan
from app.models.laporan import Laporan
from app.models.pengguna import Pengguna
from app.models.riwayat_status import RiwayatStatus
from app.schemas.petugas import (
    LaporanPetugasDetailResponse,
    LaporanPetugasListItem,
    PaginatedLaporanPetugasResponse,
    PelaporDetail,
    UpdateStatusLaporanRequest,
    VerifikasiLaporanRequest,
)

router = APIRouter(prefix="/petugas/laporan", tags=["Manajemen Petugas"])


# ==========================================================
# 1. KF-09: Melihat & Memeriksa Seluruh Laporan Masuk
# ==========================================================

@router.get(
    "",
    response_model=PaginatedLaporanPetugasResponse,
    status_code=status.HTTP_200_OK,
    summary="Lihat & Kelola Seluruh Laporan (KF-09)",
    description=(
        "Menampilkan seluruh laporan masuk untuk petugas Command Center. "
        "Mendukung filter berdasarkan status, prioritas, kategori, pencarian kata kunci, "
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
    # Base query
    stmt = select(Laporan)

    # Filter conditions
    if status_filter:
        stmt = stmt.where(Laporan.status == status_filter)
    if kategori_prioritas:
        stmt = stmt.where(Laporan.kategori_prioritas == kategori_prioritas)
    if kategori_id:
        stmt = stmt.where(Laporan.kategori_id == kategori_id)
    if q:
        stmt = stmt.where(
            (Laporan.judul.ilike(f"%{q}%")) | (Laporan.deskripsi.ilike(f"%{q}%"))
        )

    # Hitung total data
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    # Sorting: Urutkan dari skor prioritas tertinggi, kemudian waktu terbaru
    stmt = (
        stmt.options(
            joinedload(Laporan.kategori),
            joinedload(Laporan.warga),
            selectinload(Laporan.foto),
        )
        .order_by(desc(Laporan.skor_prioritas), desc(Laporan.dibuat_pada))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    laporan_list = db.scalars(stmt).all()

    items = []
    for lap in laporan_list:
        pelapor_dto = None
        if lap.warga:
            pelapor_dto = PelaporDetail(
                id=lap.warga.id,
                nama=lap.warga.nama,
                email=lap.warga.email,
                nomor_hp=lap.warga.nomor_hp,
            )

        items.append(
            LaporanPetugasListItem(
                id=lap.id,
                judul=lap.judul,
                deskripsi=lap.deskripsi,
                status=lap.status,
                severity=lap.severity,
                kategori_prioritas=lap.kategori_prioritas,
                skor_prioritas=lap.skor_prioritas,
                alamat_lokasi=lap.alamat_lokasi,
                latitude=lap.latitude,
                longitude=lap.longitude,
                dibuat_pada=lap.dibuat_pada,
                diperbarui_pada=lap.diperbarui_pada,
                kategori=lap.kategori,
                pelapor=pelapor_dto,
                foto=lap.foto,
            )
        )

    return PaginatedLaporanPetugasResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )


# ==========================================================
# 2. KF-09 & KF-18: Detail Laporan Lengkap dengan Audit Trail
# ==========================================================

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
    stmt = (
        select(Laporan)
        .where(Laporan.id == id)
        .options(
            joinedload(Laporan.kategori),
            joinedload(Laporan.warga),
            selectinload(Laporan.foto),
            selectinload(Laporan.riwayat_status).joinedload(RiwayatStatus.petugas),
        )
    )
    laporan = db.scalar(stmt)

    if not laporan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Laporan tidak ditemukan.",
        )

    pelapor_dto = None
    if laporan.warga:
        pelapor_dto = PelaporDetail(
            id=laporan.warga.id,
            nama=laporan.warga.nama,
            email=laporan.warga.email,
            nomor_hp=laporan.warga.nomor_hp,
        )

    # Urutkan riwayat status kronologis
    riwayat_sorted = sorted(laporan.riwayat_status, key=lambda r: r.waktu)

    return LaporanPetugasDetailResponse(
        id=laporan.id,
        judul=laporan.judul,
        deskripsi=laporan.deskripsi,
        status=laporan.status,
        severity=laporan.severity,
        kategori_prioritas=laporan.kategori_prioritas,
        skor_prioritas=laporan.skor_prioritas,
        alamat_lokasi=laporan.alamat_lokasi,
        latitude=laporan.latitude,
        longitude=laporan.longitude,
        dibuat_pada=laporan.dibuat_pada,
        diperbarui_pada=laporan.diperbarui_pada,
        tingkat_bahaya=laporan.tingkat_bahaya,
        faktor_lokasi=laporan.faktor_lokasi,
        dampak=laporan.dampak,
        jumlah_pelapor=laporan.jumlah_pelapor,
        waktu_tunggu_jam=laporan.waktu_tunggu_jam,
        kategori=laporan.kategori,
        pelapor=pelapor_dto,
        foto=laporan.foto,
        riwayat_status=riwayat_sorted,
    )


# ==========================================================
# 3. KF-10: Memverifikasi Laporan Masuk
# ==========================================================

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
    laporan = db.scalar(
        select(Laporan)
        .where(Laporan.id == id)
        .options(
            joinedload(Laporan.kategori),
            joinedload(Laporan.warga),
            selectinload(Laporan.foto),
            selectinload(Laporan.riwayat_status).joinedload(RiwayatStatus.petugas),
        )
    )

    if not laporan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Laporan tidak ditemukan.",
        )

    if laporan.status != StatusLaporan.DIKIRIM:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Laporan sudah dalam status '{laporan.status.value}', verifikasi hanya untuk laporan baru (DIKIRIM).",
        )

    status_lama = laporan.status
    status_baru = StatusLaporan.DIPROSES if payload.terima else StatusLaporan.DITOLAK

    # Opsional: Penyesuaian severity dari petugas
    if payload.sesuaikan_severity:
        laporan.severity = payload.sesuaikan_severity
        # Hitung ulang prioritas jika severity berubah (Clean Architecture)
        from app.use_cases.prioritas.priority_engine import DomainPriorityEngine
        skor_baru = DomainPriorityEngine.kalkulasi_laporan_db(db, laporan)
        laporan.skor_prioritas = skor_baru.skor_prioritas
        laporan.kategori_prioritas = skor_baru.kategori_prioritas

    laporan.status = status_baru

    # Audit Trail: Rekam riwayat perubahan status (KF-18, KNF-12)
    audit_entry = RiwayatStatus(
        laporan_id=laporan.id,
        petugas_id=current_petugas.id,
        status_lama=status_lama,
        status_baru=status_baru,
        catatan=f"[VERIFIKASI] {payload.catatan}",
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(laporan)

    return get_detail_laporan_petugas(id=laporan.id, db=db, current_petugas=current_petugas)


# ==========================================================
# 4. KF-15 & KF-16: Memperbarui Status & Mencatat Penanganan
# ==========================================================

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
    laporan = db.scalar(
        select(Laporan)
        .where(Laporan.id == id)
        .options(
            joinedload(Laporan.kategori),
            joinedload(Laporan.warga),
            selectinload(Laporan.foto),
            selectinload(Laporan.riwayat_status).joinedload(RiwayatStatus.petugas),
        )
    )

    if not laporan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Laporan tidak ditemukan.",
        )

    if laporan.status == payload.status_baru:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Laporan sudah berada pada status '{payload.status_baru.value}'.",
        )

    status_lama = laporan.status
    laporan.status = payload.status_baru

    # Audit Trail: Rekam riwayat perubahan status (KF-18, KNF-12)
    audit_entry = RiwayatStatus(
        laporan_id=laporan.id,
        petugas_id=current_petugas.id,
        status_lama=status_lama,
        status_baru=payload.status_baru,
        catatan=payload.catatan,
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(laporan)

    return get_detail_laporan_petugas(id=laporan.id, db=db, current_petugas=current_petugas)
