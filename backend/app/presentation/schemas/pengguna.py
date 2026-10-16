"""
app/schemas/pengguna.py
Pydantic schemas untuk Pengguna, Warga, dan Petugas.
Memastikan kepatuhan terhadap KNF-04 (Privacy): Identitas pelapor disembunyikan/dibatasi untuk tampilan umum.
Serta skema Lupa & Reset Kata Sandi (KNF-03).
"""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.domain.enums import Peran


# --- Schema Registrasi & Autentikasi ---

class RegistrasiWargaRequest(BaseModel):
    """
    Registrasi akun Warga (KF-01).
    Wajib nama & kata_sandi.
    Email ATAU nomor_hp harus diisi salah satu (tanpa NIK).
    """
    nama: str = Field(..., min_length=2, max_length=255, description="Nama lengkap")
    email: Optional[EmailStr] = Field(None, description="Email aktif")
    nomor_hp: Optional[str] = Field(None, min_length=8, max_length=20, description="Nomor HP aktif")
    kata_sandi: str = Field(..., min_length=6, max_length=128, description="Kata sandi minimal 6 karakter")

    @model_validator(mode="after")
    def periksa_kontak(self) -> "RegistrasiWargaRequest":
        if not self.email and not self.nomor_hp:
            raise ValueError("Minimal salah satu dari email atau nomor HP harus diisi.")
        return self


class RegistrasiPetugasRequest(BaseModel):
    """
    Registrasi akun Petugas oleh Command Center.
    """
    nama: str = Field(..., min_length=2, max_length=255)
    email: EmailStr = Field(..., description="Email kedinasan petugas")
    nomor_hp: Optional[str] = Field(None, min_length=8, max_length=20)
    kata_sandi: str = Field(..., min_length=6, max_length=128)
    tim_id: Optional[uuid.UUID] = Field(None, description="ID TimPetugas (opsional)")


class LoginRequest(BaseModel):
    """
    Login menggunakan email/nomor_hp dan kata sandi (KF-02).
    """
    identitas: str = Field(..., description="Email atau nomor HP")
    kata_sandi: str = Field(..., description="Kata sandi")


class TokenResponse(BaseModel):
    """
    Format token respon JWT.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# --- Schema Lupa & Reset Kata Sandi (KNF-03) ---

class LupaPasswordRequest(BaseModel):
    """Permintaan lupa kata sandi dengan memasukkan email atau nomor telepon"""
    identitas: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Alamat email terdaftar atau nomor telepon",
    )


class LupaPasswordResponse(BaseModel):
    pesan: str
    token_reset_simulasi: Optional[str] = Field(
        None,
        description="Token pemulihan untuk pengujian lokal / simulasi pengiriman",
    )


class ResetPasswordRequest(BaseModel):
    """Permintaan penggantian kata sandi dengan token pemulihan"""
    token: str = Field(..., description="Token pemulihan yang diperoleh dari permintaan lupa password")
    password_baru: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="Kata sandi baru (minimal 6 karakter)",
    )


# --- Schema Pengguna Response & DTO ---

class PenggunaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nama: str
    peran: Peran
    is_aktif: bool
    is_verified: bool


class ProfilPenggunaResponse(PenggunaBase):
    """
    Profil lengkap yang hanya boleh dilihat oleh pemilik akun atau Petugas.
    """
    email: Optional[str] = None
    nomor_hp: Optional[str] = None
    tim_id: Optional[uuid.UUID] = None
    dibuat_pada: datetime


class RegistrasiResponse(BaseModel):
    """Respon pendaftaran akun warga dengan informasi verifikasi email"""
    pesan: str
    pengguna: ProfilPenggunaResponse
    tautan_verifikasi_simulasi: Optional[str] = Field(
        None,
        description="Tautan verifikasi email (disimulasikan di konsol/respons karena belum ada SMTP)",
    )


class PelaporPublikResponse(BaseModel):
    """
    Tampilan pelapor untuk publik (KNF-04 Privacy).
    Hanya menampilkan inisial atau label anonim, tanpa email dan nomor HP.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nama_anonim: str

    @classmethod
    def dari_warga(cls, warga_id: uuid.UUID, nama_asli: str) -> "PelaporPublikResponse":
        parts = nama_asli.split()
        masked_parts = [p[0] + "***" if len(p) > 1 else p for p in parts]
        return cls(id=warga_id, nama_anonim=" ".join(masked_parts))
