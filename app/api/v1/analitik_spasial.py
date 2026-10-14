"""
app/api/v1/analitik_spasial.py
Router Analitik Geospasial, Prioritas, & Deteksi Duplikasi:
- KF-13: Menampilkan urutan prioritas laporan (skor tertinggi ke terendah)
- KF-14: Menampilkan persebaran laporan pada peta dengan penanda tingkat prioritas (GeoJSON / Marker)
- KF-17: Mendeteksi laporan serupa berdasarkan kategori, radius spasial, dan rentang waktu
"""
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.models.enums import KategoriPrioritas, StatusLaporan
from app.models.laporan import Laporan
from app.schemas.spasial import (
    DeteksiSerupaResponse,
    GeoJsonFeature,
    GeoJsonFeatureCollection,
    GeoJsonGeometry,
    LaporanSerupaItem,
    PetaMarkerItem,
)
from app.schemas.laporan import LaporanResponse
from app.services.spasial import SpasialService

router = APIRouter(prefix="/spasial", tags=["Analitik Spasial & Prioritas"])


# ==========================================================
# 1. KF-13: Menampilkan Urutan Prioritas Laporan
# ==========================================================

@router.get(
    "/prioritas",
    response_model=List[LaporanResponse],
    status_code=status.HTTP_200_OK,
    summary="Urutan Prioritas Laporan (KF-13)",
    description=(
        "Menampilkan daftar laporan aktif yang diurutkan secara deterministik "
        "berdasarkan skor prioritas tertinggi (P1 > P2 > P3) agar petugas dapat mengeksekusi isu paling mendesak."
    ),
)
def get_urutan_prioritas(
    db: Annotated[Session, Depends(get_db)],
    kategori_prioritas: Optional[KategoriPrioritas] = Query(None, description="Filter tingkatan prioritas (P1, P2, P3)"),
    kategori_id: Optional[uuid.UUID] = Query(None, description="Filter ID kategori masalah"),
    limit: int = Query(default=50, ge=1, le=200, description="Jumlah laporan maksimal"),
):
    stmt = (
        select(Laporan)
        .where(Laporan.status.in_([StatusLaporan.DIKIRIM, StatusLaporan.DIPROSES]))
        .options(joinedload(Laporan.kategori))
        .order_by(desc(Laporan.skor_prioritas), desc(Laporan.dibuat_pada))
    )

    if kategori_prioritas:
        stmt = stmt.where(Laporan.kategori_prioritas == kategori_prioritas)
    if kategori_id:
        stmt = stmt.where(Laporan.kategori_id == kategori_id)

    stmt = stmt.limit(limit)
    return db.scalars(stmt).all()


# ==========================================================
# 2. KF-14: Menampilkan Persebaran Peta Laporan (Marker & GeoJSON)
# ==========================================================

@router.get(
    "/peta",
    response_model=List[PetaMarkerItem],
    status_code=status.HTTP_200_OK,
    summary="Data Marker Peta Laporan (KF-14)",
    description=(
        "Menyediakan data titik koordinat spasial laporan untuk visualisasi peta. "
        "Mendukung filter Bounding Box (min_lon, min_lat, max_lon, max_lat) untuk performa optimal pada viewport peta."
    ),
)
def get_peta_markers(
    db: Annotated[Session, Depends(get_db)],
    min_lon: Optional[float] = Query(None, ge=-180.0, le=180.0),
    min_lat: Optional[float] = Query(None, ge=-90.0, le=90.0),
    max_lon: Optional[float] = Query(None, ge=-180.0, le=180.0),
    max_lat: Optional[float] = Query(None, ge=-90.0, le=90.0),
    kategori_prioritas: Optional[KategoriPrioritas] = Query(None),
    status_laporan: Optional[StatusLaporan] = Query(None),
):
    # Jika parameter bbox lengkap, gunakan fungsi ST_MakeEnvelope spasial berindeks
    if None not in (min_lon, min_lat, max_lon, max_lat):
        laporan_list = SpasialService.get_laporan_dalam_bbox(
            db=db,
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            hanya_aktif=status_laporan is None,
        )
    else:
        stmt = (
            select(Laporan)
            .options(joinedload(Laporan.kategori))
            .order_by(desc(Laporan.skor_prioritas))
        )
        if status_laporan:
            stmt = stmt.where(Laporan.status == status_laporan)
        else:
            stmt = stmt.where(Laporan.status.in_([StatusLaporan.DIKIRIM, StatusLaporan.DIPROSES]))

        if kategori_prioritas:
            stmt = stmt.where(Laporan.kategori_prioritas == kategori_prioritas)

        laporan_list = db.scalars(stmt).all()

    markers: List[PetaMarkerItem] = []
    for lap in laporan_list:
        markers.append(
            PetaMarkerItem(
                id=lap.id,
                judul=lap.judul,
                latitude=lap.latitude,
                longitude=lap.longitude,
                kategori_nama=lap.kategori.nama if lap.kategori else "Lainnya",
                kategori_prioritas=lap.kategori_prioritas,
                skor_prioritas=lap.skor_prioritas,
                status=lap.status,
                severity=lap.severity,
                dibuat_pada=lap.dibuat_pada,
            )
        )

    return markers


@router.get(
    "/peta/geojson",
    response_model=GeoJsonFeatureCollection,
    status_code=status.HTTP_200_OK,
    summary="Data Peta Laporan dalam Format Standar GeoJSON (KF-14)",
)
def get_peta_geojson(
    db: Annotated[Session, Depends(get_db)],
    kategori_prioritas: Optional[KategoriPrioritas] = Query(None),
):
    stmt = (
        select(Laporan)
        .where(Laporan.status.in_([StatusLaporan.DIKIRIM, StatusLaporan.DIPROSES]))
        .options(joinedload(Laporan.kategori))
    )
    if kategori_prioritas:
        stmt = stmt.where(Laporan.kategori_prioritas == kategori_prioritas)

    laporan_list = db.scalars(stmt).all()

    features: List[GeoJsonFeature] = []
    for lap in laporan_list:
        features.append(
            GeoJsonFeature(
                geometry=GeoJsonGeometry(
                    type="Point",
                    coordinates=[lap.longitude, lap.latitude],
                ),
                properties={
                    "id": str(lap.id),
                    "judul": lap.judul,
                    "kategori": lap.kategori.nama if lap.kategori else "Lainnya",
                    "skor_prioritas": lap.skor_prioritas,
                    "kategori_prioritas": lap.kategori_prioritas.value,
                    "status": lap.status.value,
                    "severity": lap.severity.value,
                    "dibuat_pada": lap.dibuat_pada.isoformat(),
                },
            )
        )

    return GeoJsonFeatureCollection(features=features)


# ==========================================================
# 3. KF-17: Mendeteksi Laporan Serupa / Duplikasi Spasial
# ==========================================================

@router.get(
    "/deteksi-serupa",
    response_model=DeteksiSerupaResponse,
    status_code=status.HTTP_200_OK,
    summary="Deteksi Laporan Serupa / Duplikat (KF-17)",
    description=(
        "Membantu mengidentifikasi potensi laporan duplikasi berdasarkan kesamaan kategori, "
        "kedekatan radius spasial (meter), dan rentang waktu (jam) yang berdekatan."
    ),
)
def deteksi_laporan_serupa(
    kategori_id: uuid.UUID = Query(..., description="ID kategori permasalahan"),
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Koordinat lintang"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Koordinat bujur"),
    radius_meter: float = Query(default=100.0, ge=10.0, le=5000.0, description="Radius pencarian meter (default 100m)"),
    rentang_waktu_jam: int = Query(default=72, ge=1, le=720, description="Rentang waktu jam (default 72 jam)"),
    abaikan_laporan_id: Optional[uuid.UUID] = Query(None, description="Abaikan ID laporan ini (jika sedang memvalidasi laporan yang sudah ada)"),
    db: Annotated[Session, Depends(get_db)] = None,
):
    hasil_serupa = SpasialService.cari_laporan_serupa(
        db=db,
        kategori_id=kategori_id,
        latitude=latitude,
        longitude=longitude,
        radius_meter=radius_meter,
        rentang_waktu_jam=rentang_waktu_jam,
        abaikan_laporan_id=abaikan_laporan_id,
    )

    items: List[LaporanSerupaItem] = []
    for r in hasil_serupa:
        lap = r.laporan
        items.append(
            LaporanSerupaItem(
                id=lap.id,
                judul=lap.judul,
                deskripsi=lap.deskripsi,
                status=lap.status,
                severity=lap.severity,
                kategori_prioritas=lap.kategori_prioritas,
                skor_prioritas=lap.skor_prioritas,
                latitude=lap.latitude,
                longitude=lap.longitude,
                alamat_lokasi=lap.alamat_lokasi,
                jarak_meter=r.jarak_meter,
                selisih_jam=r.selisih_jam,
                dibuat_pada=lap.dibuat_pada,
                kategori=lap.kategori,
            )
        )

    return DeteksiSerupaResponse(
        total_ditemukan=len(items),
        indikasi_duplikasi=len(items) > 0,
        laporan_serupa=items,
    )
