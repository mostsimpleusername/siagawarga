"""
app/use_cases/auth/auth_use_cases.py
Use Cases untuk Autentikasi Pengguna:
- Registrasi Warga (KF-01, KNF-04): Hanya nama, email atau no HP, kata sandi (TANPA NIK).
- Verifikasi Email via Tautan (Link): Aktivasi akun menggunakan token JWT 24 jam.
- Login (KF-02): Verifikasi kata sandi dengan bcrypt & pemeriksaan status verifikasi email.
- Lupa & Reset Password (KNF-03): Pemulihan kata sandi stateless berbasis JWT.
- Logout: Pencabutan token sesi.
"""
import uuid
from typing import Optional

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.domain.entities.pengguna import Pengguna, TokenSesi, Warga
from app.domain.enums import Peran
from app.infrastructure.config import settings
from app.infrastructure.email.smtp_service import kirim_email_verifikasi
from app.infrastructure.security.hashing import (
    get_password_hash,
    hash_kata_sandi,
    verifikasi_kata_sandi,
)
from app.infrastructure.security.jwt_handler import (
    buat_access_token,
    buat_refresh_token,
    buat_reset_password_token,
    buat_verifikasi_email_token,
    verifikasi_reset_password_token,
    verifikasi_token_email,
)
from app.presentation.schemas.pengguna import (
    LoginRequest,
    LupaPasswordRequest,
    LupaPasswordResponse,
    ProfilPenggunaResponse,
    RegistrasiResponse,
    RegistrasiWargaRequest,
    ResetPasswordRequest,
    TokenResponse,
)


class AuthUseCase:
    """Use case layer untuk seluruh operasi autentikasi dan otorisasi."""

    @staticmethod
    def register_warga(
        db: Session,
        payload: RegistrasiWargaRequest,
        background_tasks: BackgroundTasks,
    ) -> RegistrasiResponse:
        # 1. Validasi keunikan email jika diisi
        if payload.email:
            email_ada = db.scalar(
                select(Pengguna).where(Pengguna.email == payload.email)
            )
            if email_ada:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email sudah terdaftar. Silakan gunakan email lain atau masuk.",
                )

        # 2. Validasi keunikan nomor HP jika diisi
        if payload.nomor_hp:
            hp_ada = db.scalar(
                select(Pengguna).where(Pengguna.nomor_hp == payload.nomor_hp)
            )
            if hp_ada:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nomor HP sudah terdaftar. Silakan gunakan nomor lain atau masuk.",
                )

        # 3. Hash kata sandi menggunakan bcrypt native
        sandi_hash = hash_kata_sandi(payload.kata_sandi)

        # 4. Status verifikasi: jika ada email, wajib verifikasi link via email
        wajib_verifikasi = bool(payload.email)

        # 5. Buat entitas Warga baru
        warga_baru = Warga(
            nama=payload.nama,
            email=payload.email,
            nomor_hp=payload.nomor_hp,
            kata_sandi_hash=sandi_hash,
            peran=Peran.WARGA,
            is_aktif=True,
            is_verified=not wajib_verifikasi,
        )

        db.add(warga_baru)
        db.commit()
        db.refresh(warga_baru)

        tautan_verifikasi = None
        if wajib_verifikasi:
            token_verifikasi = buat_verifikasi_email_token(
                subyek=warga_baru.id,
                email=warga_baru.email,
            )
            tautan_verifikasi = f"http://127.0.0.1:8000/api/v1/auth/verify-email?token={token_verifikasi}"

            background_tasks.add_task(
                kirim_email_verifikasi,
                email_tujuan=warga_baru.email,
                nama=warga_baru.nama,
                token=token_verifikasi,
            )

        pesan_sukses = (
            "Registrasi berhasil! Tautan verifikasi telah dikirimkan ke email Anda. Silakan periksa kotak masuk atau spam email Anda."
            if wajib_verifikasi
            else "Registrasi berhasil! Akun Anda aktif dan siap digunakan."
        )

        return RegistrasiResponse(
            pesan=pesan_sukses,
            pengguna=ProfilPenggunaResponse.model_validate(warga_baru),
            tautan_verifikasi_simulasi=tautan_verifikasi,
        )

    @staticmethod
    def verify_email(db: Session, token: str) -> Pengguna:
        payload = verifikasi_token_email(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tautan verifikasi tidak valid atau telah kedaluwarsa.",
            )

        user_id_str = payload.get("user_id")
        try:
            user_id = uuid.UUID(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Identitas pengguna dalam token tidak valid.",
            )

        pengguna = db.scalar(select(Pengguna).where(Pengguna.id == user_id))
        if not pengguna:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Akun pengguna tidak ditemukan.",
            )

        pengguna.is_verified = True
        db.commit()
        db.refresh(pengguna)
        return pengguna

    @staticmethod
    def login(db: Session, payload: LoginRequest) -> TokenResponse:
        # Cari pengguna berdasarkan email ATAU nomor HP
        pengguna = db.scalar(
            select(Pengguna).where(
                or_(
                    Pengguna.email == payload.identitas,
                    Pengguna.nomor_hp == payload.identitas,
                )
            )
        )

        if not pengguna or not verifikasi_kata_sandi(payload.kata_sandi, pengguna.kata_sandi_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Identitas (Email/No HP) atau kata sandi tidak valid.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not pengguna.is_aktif:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akun ini telah dinonaktifkan. Hubungi petugas.",
            )

        if pengguna.email and not pengguna.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email belum diverifikasi. Silakan periksa kotak masuk email Anda dan klik tautan verifikasi sebelum masuk.",
            )

        access_token = buat_access_token(
            subyek=pengguna.id,
            peran=pengguna.peran.value,
        )
        refresh_token_str, waktu_kedaluwarsa = buat_refresh_token(
            subyek=pengguna.id,
            peran=pengguna.peran.value,
        )

        sesi = TokenSesi(
            pengguna_id=pengguna.id,
            token=refresh_token_str,
            kedaluwarsa=waktu_kedaluwarsa,
            is_dicabut=False,
        )
        db.add(sesi)
        db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    def lupa_password(db: Session, payload: LupaPasswordRequest) -> LupaPasswordResponse:
        pengguna = db.scalar(
            select(Pengguna).where(
                or_(
                    Pengguna.email == payload.identitas,
                    Pengguna.nomor_hp == payload.identitas,
                )
            )
        )

        if not pengguna or not pengguna.is_aktif:
            return LupaPasswordResponse(
                pesan="Jika akun terdaftar, token pemulihan kata sandi telah dibuat.",
                token_reset_simulasi=None,
            )

        reset_token = buat_reset_password_token(subyek=pengguna.id)

        return LupaPasswordResponse(
            pesan="Token pemulihan kata sandi berhasil dibuat (berlaku selama 15 menit).",
            token_reset_simulasi=reset_token,
        )

    @staticmethod
    def reset_password(db: Session, payload: ResetPasswordRequest) -> dict:
        user_id_str = verifikasi_reset_password_token(payload.token)
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token pemulihan tidak valid atau telah kedaluwarsa.",
            )

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format identitas dalam token tidak valid.",
            )

        pengguna = db.scalar(select(Pengguna).where(Pengguna.id == user_id))
        if not pengguna or not pengguna.is_aktif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pengguna tidak ditemukan atau telah dinonaktifkan.",
            )

        pengguna.kata_sandi_hash = get_password_hash(payload.password_baru)

        sesi_aktif = db.scalars(
            select(TokenSesi).where(
                TokenSesi.pengguna_id == pengguna.id,
                TokenSesi.is_dicabut.is_(False),
            )
        ).all()
        for s in sesi_aktif:
            s.is_dicabut = True

        db.commit()
        return {"message": "Kata sandi berhasil diperbarui. Silakan masuk kembali dengan kata sandi baru Anda."}

    @staticmethod
    def logout(db: Session, current_user: Pengguna) -> dict:
        sesi_list = db.scalars(
            select(TokenSesi).where(
                TokenSesi.pengguna_id == current_user.id,
                TokenSesi.is_dicabut.is_(False),
            )
        ).all()

        for s in sesi_list:
            s.is_dicabut = True

        db.commit()
        return {"message": "Berhasil keluar dari akun."}
