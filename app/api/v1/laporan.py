"""
app/api/v1/laporan.py
Router API untuk pengelolaan Laporan Warga:
- POST /laporan          : Membuat laporan baru (KF-03, KF-04, KF-05, KF-06)
- GET  /laporan/saya     : Melihat riwayat laporan milik sendiri (KF-07)
- GET  /laporan/sekitar  : Melihat laporan publik di sekitar titik GPS dengan privasi pelapor (KF-07, KNF-04)
- GET  /laporan/{id}/status : Melacak kronologi status laporan (KF-08)
"""
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from geoalchemy2.functions import ST_Distance, ST_DWithin, ST_MakePoint, ST_SetSRID
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import get_current_user, get_db, require_warga
from app.models.foto_laporan import FotoLaporan
from app.models.kategori_laporan import KategoriLaporan
from app.models.laporan import Laporan
from app.models.pengguna import Pengguna
from app.models.riwayat_status import RiwayatStatus
from app.schemas.laporan import (
    FotoLaporanItem,
    LaporanCreate,
    LaporanResponse,
    LaporanSayaResponse,
    LaporanSekitarResponse,
    LaporanStatusTrackingResponse,
    RiwayatStatusItem,
)
from app.schemas.pengguna import PelaporPublikResponse
from app.services.prioritas import hitung_priority_score

router = APIRouter(prefix="/laporan", tags=["Laporan Warga"])


# ==========================================================
# 1. Pembuatan Laporan
# ==========================================================

@router.post(
    "",
    response_model=LaporanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat Laporan Baru Warga (KF-03 s/d KF-06)",
)
def buat_laporan(
    payload: LaporanCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Pengguna, Depends(require_warga)],
):
    # Validasi eksistensi kategori master
    kategori = db.scalar(
        select(KategoriLaporan).where(KategoriLaporan.id == payload.kategori_id)
    )
    if not kategori or not kategori.is_aktif:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kategori laporan tidak valid atau tidak aktif.",
        )

    # Hitung Priority Score melalui Service Layer murni
    hasil_prioritas = hitung_priority_score(
        tingkat_bahaya=payload.tingkat_bahaya,
        faktor_lokasi=payload.faktor_lokasi,
        dampak=payload.dampak,
        jumlah_pelapor=payload.jumlah_pelapor,
        waktu_tunggu_jam=payload.waktu_tunggu_jam,
    )

    # Koordinat PostGIS POINT (SRID 4326)
    titik_spasial = ST_SetSRID(
        ST_MakePoint(payload.longitude, payload.latitude),
        4326,
    )

    # Simpan Laporan
    laporan_baru = Laporan(
        warga_id=current_user.id,
        kategori_id=payload.kategori_id,
        judul=payload.judul,
        deskripsi=payload.deskripsi,
        alamat_lokasi=payload.alamat_lokasi,
        latitude=payload.latitude,
        longitude=payload.longitude,
        titik_koordinat=titik_spasial,
        severity=payload.severity,
        tingkat_bahaya=payload.tingkat_bahaya,
        faktor_lokasi=payload.faktor_lokasi,
        dampak=payload.dampak,
        jumlah_pelapor=payload.jumlah_pelapor,
        waktu_tunggu_jam=payload.waktu_tunggu_jam,
        skor_prioritas=hasil_prioritas.skor_prioritas,
        kategori_prioritas=hasil_prioritas.kategori_prioritas,
    )
    db.add(laporan_baru)
    db.flush()

    # Simpan Foto jika ada
    if payload.foto_urls:
        for idx, url in enumerate(payload.foto_urls):
            foto = FotoLaporan(
                laporan_id=laporan_baru.id,
                url=url,
                urutan=idx,
            )
            db.add(foto)

    # Catat audit trail status awal (KNF-12)
    riwayat_awal = RiwayatStatus(
        laporan_id=laporan_baru.id,
        status_lama=None,
        status_baru=laporan_baru.status,
        catatan="Laporan berhasil dibuat oleh warga.",
    )
    db.add(riwayat_awal)

    db.commit()
    db.refresh(laporan_baru)

    return laporan_baru


# ==========================================================
# 2. KF-07: Melihat Laporan Milik Sendiri (Warga)
# ==========================================================

@router.get(
    "/saya",
    response_model=List[LaporanSayaResponse],
    status_code=status.HTTP_200_OK,
    summary="Lihat Riwayat Laporan Pribadi (KF-07)",
    description="Mengambil seluruh daftar laporan yang pernah dibuat oleh akun warga yang sedang login.",
)
def get_laporan_saya(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Pengguna, Depends(require_warga)],
):
    stmt = (
        select(Laporan)
        .where(Laporan.warga_id == current_user.id)
        .options(
            joinedload(Laporan.kategori),
            selectinload(Laporan.foto),
            selectinload(Laporan.riwayat_status),
        )
        .order_by(desc(Laporan.dibuat_pada))
    )
    laporan_list = db.scalars(stmt).all()
    return laporan_list


# ==========================================================
# 3. KF-07 & KNF-04: Melihat Laporan Publik di Sekitar (GPS)
# ==========================================================

@router.get(
    "/sekitar",
    response_model=List[LaporanSekitarResponse],
    status_code=status.HTTP_200_OK,
    summary="Lihat Laporan di Sekitar dengan Privasi (KF-07, KNF-04)",
    description=(
        "Menampilkan persebaran laporan dalam radius tertentu berdasarkan koordinat GPS. "
        "Informasi pelapor disamarkan (tanpa NIK, nomor HP, atau email) sesuai KNF-04."
    ),
)
def get_laporan_sekitar(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Koordinat lintang pengguna"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Koordinat bujur pengguna"),
    radius_meter: float = Query(default=1000.0, ge=10.0, le=50000.0, description="Radius pencarian (meter), default 1000m"),
    limit: int = Query(default=50, ge=1, le=100, description="Batas jumlah hasil"),
    db: Annotated[Session, Depends(get_db)] = None,
):
    # Bentuk titik spasial acuan pengguna
    titik_pusat = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)

    # Query PostGIS ST_DWithin dan hitung jarak aktual via ST_Distance
    jarak_expr = ST_Distance(Laporan.titik_koordinat, titik_pusat).label("jarak_meter")

    stmt = (
        select(Laporan, jarak_expr)
        .where(ST_DWithin(Laporan.titik_koordinat, titik_pusat, radius_meter))
        .options(
            joinedload(Laporan.kategori),
            joinedload(Laporan.warga),
            selectinload(Laporan.foto),
        )
        .order_by(jarak_expr)
        .limit(limit)
    )

    hasil = db.execute(stmt).all()

    response: List[LaporanSekitarResponse] = []
    for lap, jarak in hasil:
        # Terapkan masking privasi KNF-04
        pelapor_anonim = PelaporPublikResponse.dari_warga(
            warga_id=lap.warga_id,
            nama_asli=lap.warga.nama if lap.warga else "Warga",
        )

        response.append(
            LaporanSekitarResponse(
                id=lap.id,
                judul=lap.judul,
                deskripsi=lap.deskripsi,
                status=lap.status,
                severity=lap.severity,
                alamat_lokasi=lap.alamat_lokasi,
                latitude=lap.latitude,
                longitude=lap.longitude,
                jarak_meter=round(float(jarak), 1) if jarak is not None else None,
                dibuat_pada=lap.dibuat_pada,
                kategori=lap.kategori,
                foto=[FotoLaporanItem.model_validate(f) for f in lap.foto],
                pelapor=pelapor_anonim,
            )
        )

    return response


# ==========================================================
# 4. KF-08: Memantau Status Terkini & Timeline Laporan
# ==========================================================

@router.get(
    "/{id}/status",
    response_model=LaporanStatusTrackingResponse,
    status_code=status.HTTP_200_OK,
    summary="Pantau Status & Timeline Laporan (KF-08)",
    description="Melacak perkembangan status terkini dan seluruh catatan kronologi penanganan laporan.",
)
def pantau_status_laporan(
    id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
):
    stmt = (
        select(Laporan)
        .where(Laporan.id == id)
        .options(selectinload(Laporan.riwayat_status))
    )
    laporan = db.scalar(stmt)

    if not laporan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Laporan tidak ditemukan.",
        )

    # Urutkan timeline riwayat status berdasarkan waktu
    timeline_sorted = sorted(
        laporan.riwayat_status,
        key=lambda r: r.waktu,
    )

    return LaporanStatusTrackingResponse(
        id=laporan.id,
        judul=laporan.judul,
        status_terkini=laporan.status,
        dibuat_pada=laporan.dibuat_pada,
        diperbarui_pada=laporan.diperbarui_pada,
        timeline=[RiwayatStatusItem.model_validate(r) for r in timeline_sorted],
    )
