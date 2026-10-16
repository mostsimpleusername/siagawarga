"""
app/infrastructure/email/smtp_service.py
Pengiriman email verifikasi via SMTP (fastapi-mail).
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.infrastructure.config import settings

logger = logging.getLogger(__name__)


# >>> render_email_verifikasi_html: PERTAHANKAN fungsi yang lama persis <<<


def buat_tautan_verifikasi(token: str) -> str:
    return f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}/api/v1/auth/verify-email?token={token}"


def get_mail_config() -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
        TIMEOUT=20,
    )


async def kirim_email_verifikasi(
    email_tujuan: str,
    nama: str,
    token: str,
    base_url: Optional[str] = None,
) -> bool:
    if base_url:
        tautan = f"{base_url}?token={token}"
    else:
        tautan = buat_tautan_verifikasi(token)

    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        logger.error("[EMAIL] MAIL_USERNAME/MAIL_PASSWORD kosong. Email TIDAK dikirim ke %s", email_tujuan)
        return False

    html = render_email_verifikasi_html(nama=nama, tautan_verifikasi=tautan)
    teks = (
        f"Halo {nama},\n\n"
        "Buka tautan berikut untuk mengaktifkan akun SiagaWarga Anda (berlaku 24 jam):\n\n"
        f"{tautan}\n\n"
        "Jika Anda tidak merasa mendaftar, abaikan email ini."
    )

    message = MessageSchema(
        subject="Aktifkan akun SiagaWarga Anda",
        recipients=[email_tujuan],
        body=html,
        subtype=MessageType.html,
        alternative_body=teks,
    )

    try:
        await FastMail(get_mail_config()).send_message(message)
        logger.info("[EMAIL] Terkirim via SMTP ke %s", email_tujuan)
        return True
    except Exception as exc:
        logger.error("[EMAIL] Gagal kirim ke %s via %s:%s -> %s",
                     email_tujuan, settings.MAIL_SERVER, settings.MAIL_PORT, exc, exc_info=True)
        return False


send_verification_email = kirim_email_verifikasi
