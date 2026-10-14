"""
app/schemas/__init__.py
Ekspor seluruh skema Pydantic untuk memudahkan impor di API router dan services.
"""
from app.schemas.pengguna import (
    RegistrasiWargaRequest,
    RegistrasiPetugasRequest,
    RegistrasiResponse,
    LoginRequest,
    TokenResponse,
    LupaPasswordRequest,
    LupaPasswordResponse,
    ResetPasswordRequest,
    PenggunaBase,
    ProfilPenggunaResponse,
    PelaporPublikResponse,
)
from app.schemas.kategori_laporan import (
    KategoriLaporanBase,
    KategoriLaporanCreate,
    KategoriLaporanUpdate,
    KategoriLaporanResponse,
)
from app.schemas.tim_penugasan import (
    TimPetugasBase,
    TimPetugasCreate,
    TimPetugasUpdate,
    TimPetugasResponse,
    PenugasanCreate,
    PenugasanResponse,
)
from app.schemas.laporan import (
    ParameterPrioritasInput,
    LaporanCreate,
    LaporanResponse,
    LaporanSayaResponse,
    LaporanSekitarResponse,
    LaporanStatusTrackingResponse,
    FotoLaporanItem,
    RiwayatStatusItem,
)
from app.schemas.petugas import (
    VerifikasiLaporanRequest,
    UpdateStatusLaporanRequest,
    LaporanPetugasListItem,
    LaporanPetugasDetailResponse,
    PaginatedLaporanPetugasResponse,
    RiwayatStatusAuditItem,
)
from app.schemas.spasial import (
    LaporanSerupaItem,
    DeteksiSerupaResponse,
    PetaMarkerItem,
    GeoJsonFeature,
    GeoJsonFeatureCollection,
)

__all__ = [
    # Pengguna & Auth
    "RegistrasiWargaRequest",
    "RegistrasiPetugasRequest",
    "RegistrasiResponse",
    "LoginRequest",
    "TokenResponse",
    "LupaPasswordRequest",
    "LupaPasswordResponse",
    "ResetPasswordRequest",
    "PenggunaBase",
    "ProfilPenggunaResponse",
    "PelaporPublikResponse",
    # Kategori
    "KategoriLaporanBase",
    "KategoriLaporanCreate",
    "KategoriLaporanUpdate",
    "KategoriLaporanResponse",
    # Tim & Penugasan
    "TimPetugasBase",
    "TimPetugasCreate",
    "TimPetugasUpdate",
    "TimPetugasResponse",
    "PenugasanCreate",
    "PenugasanResponse",
    # Laporan
    "ParameterPrioritasInput",
    "LaporanCreate",
    "LaporanResponse",
    "LaporanSayaResponse",
    "LaporanSekitarResponse",
    "LaporanStatusTrackingResponse",
    "FotoLaporanItem",
    "RiwayatStatusItem",
    # Petugas
    "VerifikasiLaporanRequest",
    "UpdateStatusLaporanRequest",
    "LaporanPetugasListItem",
    "LaporanPetugasDetailResponse",
    "PaginatedLaporanPetugasResponse",
    "RiwayatStatusAuditItem",
    # Spasial & Peta
    "LaporanSerupaItem",
    "DeteksiSerupaResponse",
    "PetaMarkerItem",
    "GeoJsonFeature",
    "GeoJsonFeatureCollection",
]
