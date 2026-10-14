"""
app/api/v1/auth.py
Router Autentikasi Pengguna:
- Registrasi Warga (KF-01, KNF-04): Hanya nama, email atau no HP, kata sandi (TANPA NIK).
- Verifikasi Email via Tautan (Link): Aktivasi akun menggunakan token JWT 24 jam.
- Login (KF-02): Verifikasi kata sandi dengan bcrypt & pemeriksaan status verifikasi email.
- Lupa & Reset Password (KNF-03): Pemulihan kata sandi stateless berbasis JWT.
- Logout: Pencabutan token sesi.
- Me: Mengambil profil pengguna yang sedang login.
"""
import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.services.email_service import kirim_email_verifikasi
from app.core.security import (
    buat_access_token,
    buat_refresh_token,
    buat_reset_password_token,
    buat_verifikasi_email_token,
    get_password_hash,
    hash_kata_sandi,
    verifikasi_kata_sandi,
    verifikasi_reset_password_token,
    verifikasi_token_email,
)
from app.models.enums import Peran
from app.models.pengguna import Pengguna, TokenSesi, Warga
from app.schemas.pengguna import (
    LoginRequest,
    LupaPasswordRequest,
    LupaPasswordResponse,
    ProfilPenggunaResponse,
    RegistrasiResponse,
    RegistrasiWargaRequest,
    ResetPasswordRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Autentikasi"])


# ==========================================================
# 1. Registrasi Akun Warga & Pengiriman Email Verifikasi via SMTP
# ==========================================================

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

    # 3. Hash kata sandi menggunakan bcrypt
    sandi_hash = hash_kata_sandi(payload.kata_sandi)

    # 4. Status verifikasi: jika ada email, set False (wajib verifikasi link); jika hanya nomor HP, set True
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
        # Buat token JWT verifikasi email (berlaku 24 jam)
        token_verifikasi = buat_verifikasi_email_token(
            subyek=warga_baru.id,
            email=warga_baru.email,
        )
        # Format tautan verifikasi lengkap
        tautan_verifikasi = f"http://127.0.0.1:8000/api/v1/auth/verify-email?token={token_verifikasi}"

        # Kirim email verifikasi HTML via BackgroundTasks menggunakan modul email_service
        background_tasks.add_task(
            kirim_email_verifikasi,
            email_tujuan=warga_baru.email,
            nama=warga_baru.nama,
            token=token_verifikasi,
        )

        # Log konsol informatif untuk kemudahan observasi & debugging
        print("\n" + "=" * 80)
        print(f"[VERIFIKASI EMAIL DISPATCHED KE BACKGROUND TASKS - SIAGA WARGA]")
        print(f"Kepada : {warga_baru.email}")
        print(f"Subjek : Verifikasi Akun Siaga Warga Anda")
        print(f"Halo {warga_baru.nama},")
        print(f"Tautan Verifikasi: {tautan_verifikasi}")
        print(f"(Tautan ini berlaku selama 24 jam)")
        print("=" * 80 + "\n")

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


# ==========================================================
# 2. Endpoint Verifikasi Email via Tautan (Link)
# ==========================================================

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
    # 1. Validasi token JWT
    payload = verifikasi_token_email(token)
    if not payload:
        return HTMLResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content="""
            <!DOCTYPE html>
            <html lang="id">
            <head>
                <meta charset="UTF-8">
                <title>Verifikasi Gagal - Siaga Warga</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f8fafc; }
                    .card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); text-align: center; max-width: 420px; }
                    h2 { color: #dc2626; margin-bottom: 12px; }
                    p { color: #4b5563; line-height: 1.5; font-size: 15px; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h2>❌ Tautan Tidak Valid atau Kedaluwarsa</h2>
                    <p>Tautan verifikasi email Anda tidak sah atau masa berlakunya (24 jam) telah habis. Silakan daftar ulang atau hubungi layanan bantuan.</p>
                </div>
            </body>
            </html>
            """,
        )

    user_id_str = payload.get("user_id")
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Identitas pengguna dalam token tidak valid.")

    # 2. Cari pengguna di database
    pengguna = db.scalar(select(Pengguna).where(Pengguna.id == user_id))
    if not pengguna:
        raise HTTPException(status_code=404, detail="Akun pengguna tidak ditemukan.")

    # 3. Update status verifikasi
    pengguna.is_verified = True
    db.commit()

    # 4. Tampilkan halaman HTML konfirmasi sukses
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
            <a href="http://127.0.0.1:8000/docs#/Autentikasi/login_api_v1_auth_login_post" class="btn">Masuk ke Aplikasi</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)


# ==========================================================
# 3. Login Pengguna & Pengecekan Verifikasi Email
# ==========================================================

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
    # 1. Cari pengguna berdasarkan email ATAU nomor HP
    pengguna = db.scalar(
        select(Pengguna).where(
            or_(
                Pengguna.email == payload.identitas,
                Pengguna.nomor_hp == payload.identitas,
            )
        )
    )

    # 2. Verifikasi keberadaan user dan kecocokan kata sandi
    if not pengguna or not verifikasi_kata_sandi(payload.kata_sandi, pengguna.kata_sandi_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identitas (Email/No HP) atau kata sandi tidak valid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Periksa status keaktifan akun
    if not pengguna.is_aktif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun ini telah dinonaktifkan. Hubungi petugas.",
        )

    # 4. Pengecekan status verifikasi email: jika mendaftar dengan email namun belum klik tautan verifikasi
    if pengguna.email and not pengguna.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email belum diverifikasi. Silakan periksa kotak masuk email Anda dan klik tautan verifikasi sebelum masuk.",
        )

    # 5. Buat token JWT (access token & refresh token)
    access_token = buat_access_token(
        subyek=pengguna.id,
        peran=pengguna.peran.value,
    )
    refresh_token_str, waktu_kedaluwarsa = buat_refresh_token(
        subyek=pengguna.id,
        peran=pengguna.peran.value,
    )

    # 6. Catat TokenSesi ke database (sesuai relasi Class Diagram)
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


# ==========================================================
# 4. Lupa & Reset Kata Sandi (KNF-03)
# ==========================================================

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

    # Buat token reset berbasis JWT (berlaku 15 menit)
    reset_token = buat_reset_password_token(subyek=pengguna.id)

    return LupaPasswordResponse(
        pesan="Token pemulihan kata sandi berhasil dibuat (berlaku selama 15 menit).",
        token_reset_simulasi=reset_token,
    )


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
    # 1. Verifikasi tanda tangan kriptografi token reset
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

    # 2. Cari pengguna di database
    pengguna = db.scalar(select(Pengguna).where(Pengguna.id == user_id))
    if not pengguna or not pengguna.is_aktif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pengguna tidak ditemukan atau telah dinonaktifkan.",
        )

    # 3. Hash kata sandi baru
    pengguna.kata_sandi_hash = get_password_hash(payload.password_baru)

    # 4. Cabut semua token sesi lama
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


# ==========================================================
# 5. Profil & Sesi
# ==========================================================

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
    # Cabut semua sesi token aktif milik pengguna ini
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
