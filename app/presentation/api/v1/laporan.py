"""
app/presentation/api/v1/laporan.py
Router API untuk pengelolaan Laporan Warga:
- POST /laporan/assist-ai  : Rekomendasi kategori AI Multimodal (KF-11)
- POST /laporan            : Membuat laporan baru (KF-03, KF-04, KF-05, KF-06)
- GET  /laporan/saya       : Melihat riwayat laporan milik sendiri (KF-07)
- GET  /laporan/sekitar    : Melihat laporan publik di sekitar GPS dengan privasi (KF-07, KNF-04)
- GET  /laporan/{id}/status: Melacak timeline status laporan (KF-08)
"""
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.domain.entities.pengguna import Pengguna
from app.infrastructure.database.session import get_db
from app.presentation.dependencies.auth import require_warga
from app.presentation.schemas.laporan import (
    LaporanCreate,
    LaporanResponse,
    LaporanSayaResponse,
    LaporanSekitarResponse,
    LaporanStatusTrackingResponse,
)
from app.use_cases.laporan import LaporanUseCase

router = APIRouter(prefix="/laporan", tags=["Laporan Warga"])


@router.post(
    "/assist-ai",
    summary="Rekomendasi Kategori Berbantuan AI (KF-11)",
    description=(
        "Menganalisis foto dan/atau deskripsi laporan warga menggunakan model multimodal "
        "(CLIP Vision & Horizon Multilingual Text). Mengembalikan rekomendasi kategori master DB."
    ),
)
async def rekomendasi_ai(
    file: Optional[UploadFile] = File(None),
    deskripsi: Optional[str] = Form(None),
    db: Annotated[Session, Depends(get_db)] = None,
):
    return await LaporanUseCase.assist_ai(db=db, file=file, deskripsi=deskripsi)


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
    return LaporanUseCase.buat_laporan(db=db, payload=payload, current_user=current_user)


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
    return LaporanUseCase.get_laporan_saya(db=db, current_user=current_user)


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
    return LaporanUseCase.get_laporan_sekitar(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_meter=radius_meter,
        limit=limit,
    )


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
    return LaporanUseCase.pantau_status_laporan(db=db, id=id)
