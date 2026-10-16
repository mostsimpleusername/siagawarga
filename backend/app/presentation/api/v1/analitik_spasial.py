"""
app/presentation/api/v1/analitik_spasial.py
Router Analitik Geospasial, Prioritas, & Deteksi Duplikasi:
- KF-13: Menampilkan urutan prioritas laporan (skor tertinggi ke terendah)
- KF-14: Menampilkan persebaran laporan pada peta dengan penanda tingkat prioritas (GeoJSON / Marker)
- KF-17: Mendeteksi laporan serupa berdasarkan kategori, radius spasial, dan rentang waktu
"""
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.domain.enums import KategoriPrioritas, StatusLaporan
from app.infrastructure.database.session import get_db
from app.presentation.schemas.laporan import LaporanResponse
from app.presentation.schemas.spasial import (
    DeteksiSerupaResponse,
    GeoJsonFeatureCollection,
    PetaMarkerItem,
)
from app.use_cases.spasial import SpasialUseCase

router = APIRouter(prefix="/spasial", tags=["Analitik Spasial & Prioritas"])


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
    return SpasialUseCase.get_urutan_prioritas(
        db=db,
        kategori_prioritas=kategori_prioritas,
        kategori_id=kategori_id,
        limit=limit,
    )


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
    return SpasialUseCase.get_peta_markers(
        db=db,
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat,
        kategori_prioritas=kategori_prioritas,
        status_laporan=status_laporan,
    )


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
    return SpasialUseCase.get_peta_geojson(
        db=db,
        kategori_prioritas=kategori_prioritas,
    )


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
    return SpasialUseCase.deteksi_laporan_serupa_response(
        db=db,
        kategori_id=kategori_id,
        latitude=latitude,
        longitude=longitude,
        radius_meter=radius_meter,
        rentang_waktu_jam=rentang_waktu_jam,
        abaikan_laporan_id=abaikan_laporan_id,
    )
