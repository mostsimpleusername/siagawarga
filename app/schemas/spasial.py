"""
app/schemas/spasial.py
Skema Pydantic untuk data spasial, peta laporan (KF-14),
dan deteksi laporan serupa (KF-17).
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import KategoriPrioritas, Severity, StatusLaporan
from app.schemas.kategori_laporan import KategoriLaporanResponse


# --- Deteksi Laporan Serupa (KF-17) ---

class LaporanSerupaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    judul: str
    deskripsi: str
    status: StatusLaporan
    severity: Severity
    kategori_prioritas: KategoriPrioritas
    skor_prioritas: float
    latitude: float
    longitude: float
    alamat_lokasi: Optional[str] = None
    jarak_meter: float
    selisih_jam: float
    dibuat_pada: datetime
    kategori: Optional[KategoriLaporanResponse] = None


class DeteksiSerupaResponse(BaseModel):
    total_ditemukan: int
    indikasi_duplikasi: bool
    laporan_serupa: List[LaporanSerupaItem]


# --- Data Peta & GeoJSON (KF-14) ---

class PetaMarkerItem(BaseModel):
    """Representasi titik marker ringan untuk peta (KF-14)"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    judul: str
    latitude: float
    longitude: float
    kategori_nama: str
    kategori_prioritas: KategoriPrioritas
    skor_prioritas: float
    status: StatusLaporan
    severity: Severity
    dibuat_pada: datetime


class GeoJsonGeometry(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]


class GeoJsonFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJsonGeometry
    properties: Dict[str, Any]


class GeoJsonFeatureCollection(BaseModel):
    """Format GeoJSON standar (RFC 7946) untuk Leaflet / Mapbox / Google Maps"""
    type: str = "FeatureCollection"
    features: List[GeoJsonFeature]
