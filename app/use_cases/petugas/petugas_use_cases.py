"""
app/use_cases/petugas/petugas_use_cases.py
Use Cases untuk Manajemen Operasional Petugas:
- Melihat & Mengelola Seluruh Laporan Masuk (KF-09)
- Detail Lengkap & Audit Trail (KF-09, KF-18, KNF-12)
- Verifikasi Laporan Masuk (KF-10)
- Perbarui Status & Catat Penanganan (KF-15, KF-16)
- Antrean Prioritas Dinamis (KF-13, Sequence Diagram 2)
"""
import math
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.domain.entities.laporan import Laporan
from app.domain.entities.pengguna import Pengguna
from app.domain.entities.riwayat_status import RiwayatStatus
from app.domain.enums import KategoriPrioritas, StatusLaporan
from app.presentation.schemas.laporan import LaporanDetailPetugasResponse
from app.presentation.schemas.petugas import (
    LaporanPetugasDetailResponse,
    LaporanPetugasListItem,
    PaginatedLaporanPetugasResponse,
    PelaporDetail,
    UpdateStatusLaporanRequest,
    VerifikasiLaporanRequest,
)
from app.use_cases.prioritas.priority_engine import DomainPriorityEngine


class PetugasUseCase:
    """Use case layer untuk seluruh workflow petugas dan Command Center."""

    @staticmethod
    def get_semua_laporan(
        db: Session,
        status_filter: Optional[StatusLaporan] = None,
        kategori_prioritas: Optional[KategoriPrioritas] = None,
        kategori_id: Optional[uuid.UUID] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedLaporanPetugasResponse:
        stmt = select(Laporan)

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

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 1

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

    @staticmethod
    def get_detail_laporan(
        db: Session,
        id: uuid.UUID,
    ) -> LaporanPetugasDetailResponse:
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

    @staticmethod
    def verifikasi_laporan(
        db: Session,
        id: uuid.UUID,
        payload: VerifikasiLaporanRequest,
        current_petugas: Pengguna,
    ) -> LaporanPetugasDetailResponse:
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

        if payload.sesuaikan_severity:
            laporan.severity = payload.sesuaikan_severity
            skor_baru = DomainPriorityEngine.kalkulasi_laporan_db(db, laporan)
            laporan.skor_prioritas = skor_baru.skor_prioritas
            laporan.kategori_prioritas = skor_baru.kategori_prioritas

        laporan.status = status_baru

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

        return PetugasUseCase.get_detail_laporan(db=db, id=laporan.id)

    @staticmethod
    def update_status_laporan(
        db: Session,
        id: uuid.UUID,
        payload: UpdateStatusLaporanRequest,
        current_petugas: Pengguna,
    ) -> LaporanPetugasDetailResponse:
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

        return PetugasUseCase.get_detail_laporan(db=db, id=laporan.id)

    @staticmethod
    def get_antrean_prioritas(
        db: Session,
        q: Optional[str] = None,
        kategori_prioritas: Optional[KategoriPrioritas] = None,
    ) -> dict:
        stmt = (
            select(Laporan)
            .where(Laporan.status.in_([StatusLaporan.DIKIRIM, StatusLaporan.DIPROSES]))
        )

        if q:
            stmt = stmt.where(Laporan.deskripsi.ilike(f"%{q}%"))

        laporan_list = list(db.scalars(stmt).all())

        for lap in laporan_list:
            DomainPriorityEngine.kalkulasi_laporan_db(db, lap)

        db.commit()

        laporan_terurut = sorted(
            laporan_list,
            key=lambda x: (x.skor_prioritas or 0.0),
            reverse=True,
        )

        if kategori_prioritas:
            laporan_terurut = [
                l for l in laporan_terurut if l.kategori_prioritas == kategori_prioritas
            ]

        cluster_summary = {
            "P1": sum(1 for l in laporan_terurut if l.kategori_prioritas == KategoriPrioritas.P1),
            "P2": sum(1 for l in laporan_terurut if l.kategori_prioritas == KategoriPrioritas.P2),
            "P3": sum(1 for l in laporan_terurut if l.kategori_prioritas == KategoriPrioritas.P3),
            "total_antrean": len(laporan_terurut),
        }

        return {
            "status": "success",
            "cluster_per_level": cluster_summary,
            "antrean": [
                LaporanDetailPetugasResponse.model_validate(l) for l in laporan_terurut
            ],
        }
