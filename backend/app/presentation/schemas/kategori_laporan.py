"""
app/schemas/kategori_laporan.py
Pydantic schemas untuk pengelolaan Master Data Kategori Laporan (KNF-09).
Dapat dikelola sepenuhnya oleh Petugas Command Center.
"""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class KategoriLaporanBase(BaseModel):
    nama: str = Field(..., min_length=2, max_length=100, description="Nama kategori permasalahan")
    deskripsi: Optional[str] = Field(None, max_length=255)
    ikon: Optional[str] = Field(None, max_length=100)
    bobot_bahaya_default: float = Field(
        default=1.0, ge=1.0, le=5.0,
        description="Bobot default tingkat bahaya kategori (1.0 - 5.0) untuk perhitungan Priority Score"
    )
    is_aktif: bool = Field(default=True, description="Status aktif kategori")


class KategoriLaporanCreate(KategoriLaporanBase):
    pass


class KategoriLaporanUpdate(BaseModel):
    nama: Optional[str] = Field(None, min_length=2, max_length=100)
    deskripsi: Optional[str] = Field(None, max_length=255)
    ikon: Optional[str] = Field(None, max_length=100)
    bobot_bahaya_default: Optional[float] = Field(None, ge=1.0, le=5.0)
    is_aktif: Optional[bool] = None


class KategoriLaporanResponse(KategoriLaporanBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dibuat_pada: datetime
    diperbarui_pada: datetime
