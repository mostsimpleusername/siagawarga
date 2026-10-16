"""
app/presentation/api/v1/auth.py
Router Autentikasi Pengguna:
- Registrasi Warga (KF-01, KNF-04): Hanya nama, email atau no HP, kata sandi (TANPA NIK).
- Verifikasi Email via Tautan (Link): Aktivasi akun menggunakan token JWT 24 jam.
- Login (KF-02): Verifikasi kata sandi dengan bcrypt & pemeriksaan status verifikasi email.
- Lupa & Reset Password (KNF-03): Pemulihan kata sandi stateless berbasis JWT.
- Logout: Pencabutan token sesi.
- Me: Mengambil profil pengguna yang sedang login.
"""
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.domain.entities.pengguna import Pengguna
from app.infrastructure.config import settings
from app.infrastructure.database.session import get_db
from app.presentation.dependencies.auth import get_current_user
from app.presentation.schemas.pengguna import (
    KirimUlangVerifikasiRequest,
    LoginRequest,
    LupaPasswordRequest,
    LupaPasswordResponse,
    ProfilPenggunaResponse,
    RegistrasiResponse,
    RegistrasiWargaRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.use_cases.auth import AuthUseCase

router = APIRouter(prefix="/auth", tags=["Autentikasi"])


@router.post(
    "/register",
    response_model=RegistrasiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrasi Akun Warga (KF-01, KNF-04)",
    description=(
        "Pendaftaran warga baru dengan Nama, Email (atau No HP), dan Kata Sandi (tanpa NIK). "
        "Jika mendaftar dengan email, sistem akan mengirimkan email verifikasi akun secara nyata via SMTP."
    ),
)
def register_warga(
    payload: RegistrasiWargaRequest,
    db: Annotated[Session, Depends(get_db)],
    background_tasks: BackgroundTasks,
):
    return AuthUseCase.register_warga(db=db, payload=payload, background_tasks=background_tasks)


@router.get(
    "/verify-email",
    response_class=HTMLResponse,
    summary="Verifikasi Email via Tautan (Link)",
    description="Menerima token verifikasi email dari tautan, memvalidasinya, dan mengaktifkan akun pengguna.",
)
def verify_email(
    token: str = Query(..., description="Token JWT verifikasi email"),
    db: Annotated[Session, Depends(get_db)] = None,
):
    try:
        pengguna = AuthUseCase.verify_email(db=db, token=token)
    except HTTPException:
        login_url = f"{settings.FRONTEND_URL.rstrip('/')}/login"
        return HTMLResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"""
            <!DOCTYPE html>
            <html lang="id">
            <head>
                <meta charset="UTF-8">
                <title>Verifikasi Gagal - Siaga Warga</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f8fafc; }}
                    .card {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); text-align: center; max-width: 420px; }}
                    h2 {{ color: #dc2626; margin-bottom: 12px; }}
                    p {{ color: #4b5563; line-height: 1.5; font-size: 15px; margin-bottom: 24px; }}
                    .btn {{ display: inline-block; background: #0284c7; color: white; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h2>❌ Tautan Tidak Valid atau Kedaluwarsa</h2>
                    <p>Tautan verifikasi email Anda tidak sah atau masa berlakunya (24 jam) telah habis. Silakan minta tautan baru atau hubungi layanan bantuan.</p>
                    <a href="{login_url}" class="btn">Kembali ke Halaman Masuk</a>
                </div>
            </body>
            </html>
            """,
        )

    login_url = f"{settings.FRONTEND_URL.rstrip('/')}/login"
    html_content = f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Berhasil Diverifikasi - Siaga Warga</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f0fdf4; }}
            .card {{ background: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); text-align: center; max-width: 460px; }}
            .icon {{ font-size: 48px; margin-bottom: 16px; }}
            h2 {{ color: #16a34a; margin-bottom: 8px; font-size: 24px; }}
            p {{ color: #4b5563; line-height: 1.6; font-size: 15px; margin-bottom: 24px; }}
            .btn {{ display: inline-block; background: #16a34a; color: white; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; transition: background 0.2s; }}
            .btn:hover {{ background: #15803d; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">✅</div>
            <h2>Email Berhasil Diverifikasi!</h2>
            <p>Halo <strong>{pengguna.nama}</strong>, akun Siaga Warga Anda ({pengguna.email}) telah aktif. Sekarang Anda dapat masuk dan mulai melaporkan permasalahan lingkungan di sekitar Anda.</p>
            <a href="{login_url}" class="btn">Masuk ke Aplikasi</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)


@router.post(
    "/kirim-ulang-verifikasi",
    status_code=status.HTTP_200_OK,
    summary="Kirim Ulang Tautan Verifikasi Email",
    description="Mengirim ulang tautan aktivasi akun ke alamat email terdaftar.",
)
def kirim_ulang_verifikasi(
    payload: KirimUlangVerifikasiRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
):
    return AuthUseCase.kirim_ulang_verifikasi(
        db=db,
        email=payload.email,
        background_tasks=background_tasks,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login Pengguna (KF-02)",
    description="Masuk menggunakan email atau nomor HP serta kata sandi. Memeriksa status verifikasi email sebelum menerbitkan token.",
)
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
):
    return AuthUseCase.login(db=db, payload=payload)


@router.post(
    "/lupa-password",
    response_model=LupaPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Permintaan Pemulihan Kata Sandi (Lupa Password)",
    description=(
        "Mencari pengguna berdasarkan email atau nomor telepon. "
        "Menghasilkan token pemulihan (disertakan pada respons sebagai simulasi lokal/MVP)."
    ),
)
def lupa_password(
    payload: LupaPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
):
    return AuthUseCase.lupa_password(db=db, payload=payload)


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset Kata Sandi Baru",
    description="Memverifikasi token pemulihan dan memperbarui kata sandi pengguna ke database.",
)
def reset_password(
    payload: ResetPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
):
    return AuthUseCase.reset_password(db=db, payload=payload)


@router.get(
    "/me",
    response_model=ProfilPenggunaResponse,
    status_code=status.HTTP_200_OK,
    summary="Lihat Profil Pengguna yang Sedang Login",
)
def get_profil_saya(
    current_user: Annotated[Pengguna, Depends(get_current_user)],
):
    return current_user


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout Pengguna",
    description="Mencabut sesi login aktif pengguna.",
)
def logout(
    current_user: Annotated[Pengguna, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return AuthUseCase.logout(db=db, current_user=current_user)
