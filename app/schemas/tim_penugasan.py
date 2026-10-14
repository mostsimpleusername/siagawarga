"""
app/schemas/tim_penugasan.py
Pydantic schemas untuk TimPetugas dan Penugasan Laporan.
"""
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


# --- Tim Petugas ---

class TimPetugasBase(BaseModel):
    nama_tim: str = Field(..., min_length=2, max_length=255, description="Nama tim lapangan")
    deskripsi: Optional[str] = Field(None, max_length=500)
    is_aktif: bool = Field(default=True)


class TimPetugasCreate(TimPetugasBase):
    pass


class TimPetugasUpdate(BaseModel):
    nama_tim: Optional[str] = Field(None, min_length=2, max_length=255)
    deskripsi: Optional[str] = Field(None, max_length=500)
    is_aktif: Optional[bool] = None


class TimPetugasResponse(TimPetugasBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dibuat_pada: datetime
    diperbarui_pada: datetime


# --- Penugasan ---

class PenugasanCreate(BaseModel):
    laporan_id: uuid.UUID
    tim_id: uuid.UUID
    catatan_penugasan: Optional[str] = Field(None, description="Instruksi penanganan bagi tim")


class PenugasanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    laporan_id: uuid.UUID
    tim_id: Optional[uuid.UUID]
    ditugaskan_pada: datetime
    catatan_penugasan: Optional[str]
    diselesaikan_pada: Optional[datetime]
    is_aktif: bool
    tim_penerima: Optional[TimPetugasResponse] = None
