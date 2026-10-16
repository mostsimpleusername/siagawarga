"""
app/infrastructure/email/smtp_service.py
Pengiriman email verifikasi multi-provider: brevo | resend | smtp | console.
Brevo/Resend memakai HTTPS (443) sehingga aman di Railway.
"""
import logging
from typing import Optional

import httpx

from app.infrastructure.config import settings

logger = logging.getLogger(__name__)


def render_email_verifikasi_html(nama: str, tautan_verifikasi: str) -> str:
    return f"""
    <div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:480px;margin:auto;padding:32px;border:1px solid #e5e7eb;border-radius:12px">
      <h2 style="color:#0d9488;margin-top:0">SiagaWarga</h2>
      <p>Halo <strong>{nama}</strong>,</p>
      <p>Klik tombol di bawah untuk mengaktifkan akun Anda (berlaku 24 jam).</p>
      <p style="text-align:center;margin:28px 0">
        <a href="{tautan_verifikasi}"
           style="background:#0d9488;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600">
          Aktifkan Akun
        </a>
      </p>
      <p style="font-size:12px;color:#6b7280">Jika tombol tidak berfungsi, salin tautan ini:<br>{tautan_verifikasi}</p>
      <p style="font-size:12px;color:#6b7280">Jika Anda tidak merasa mendaftar, abaikan email ini.</p>
    </div>
    """


def buat_tautan_verifikasi(token: str) -> str:
    return f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}/api/v1/auth/verify-email?token={token}"


async def _kirim_brevo(to_email: str, to_name: str, subject: str, html: str, teks: str) -> bool:
    if not settings.BREVO_API_KEY:
        logger.error("[EMAIL] BREVO_API_KEY kosong.")
        return False
    async with httpx.AsyncClient(timeout=20) as client:
        res = await client.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": settings.BREVO_API_KEY, "accept": "application/json"},
            json={
                "sender": {"name": settings.MAIL_FROM_NAME, "email": settings.MAIL_FROM},
                "to": [{"email": to_email, "name": to_name}],
                "subject": subject,
                "htmlContent": html,
                "textContent": teks,
            },
        )
    if res.status_code >= 300:
        logger.error("[EMAIL] Brevo %s: %s", res.status_code, res.text)
        return False
    return True


async def _kirim_resend(to_email: str, to_name: str, subject: str, html: str, teks: str) -> bool:
    if not settings.RESEND_API_KEY:
        logger.error("[EMAIL] RESEND_API_KEY kosong.")
        return False
    async with httpx.AsyncClient(timeout=20) as client:
        res = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
            json={
                "from": f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>",
                "to": [to_email],
                "subject": subject,
                "html": html,
                "text": teks,
            },
        )
    if res.status_code >= 300:
        logger.error("[EMAIL] Resend %s: %s", res.status_code, res.text)
        return False
    return True


async def _kirim_smtp(to_email: str, to_name: str, subject: str, html: str, teks: str) -> bool:
    from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        logger.error("[EMAIL] MAIL_USERNAME/MAIL_PASSWORD kosong.")
        return False
    conf = ConnectionConfig(
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
    msg = MessageSchema(
        subject=subject, recipients=[to_email], body=html,
        subtype=MessageType.html, alternative_body=teks,
    )
    await FastMail(conf).send_message(msg)
    return True


async def kirim_email_verifikasi(
    email_tujuan: str,
    nama: str,
    token: str,
    base_url: Optional[str] = None,
) -> bool:
    tautan = f"{base_url}?token={token}" if base_url else buat_tautan_verifikasi(token)
    subject = "Aktifkan akun SiagaWarga Anda"
    html = render_email_verifikasi_html(nama=nama, tautan_verifikasi=tautan)
    teks = (
        f"Halo {nama},\n\nBuka tautan berikut untuk mengaktifkan akun SiagaWarga "
        f"(berlaku 24 jam):\n\n{tautan}\n\nJika Anda tidak merasa mendaftar, abaikan email ini."
    )

    provider = (settings.EMAIL_PROVIDER or "console").lower()
    try:
        if provider == "brevo":
            ok = await _kirim_brevo(email_tujuan, nama, subject, html, teks)
        elif provider == "resend":
            ok = await _kirim_resend(email_tujuan, nama, subject, html, teks)
        elif provider == "smtp":
            ok = await _kirim_smtp(email_tujuan, nama, subject, html, teks)
        else:
            logger.warning("[EMAIL][console] Tautan verifikasi untuk %s: %s", email_tujuan, tautan)
            return True
    except Exception as exc:
        logger.error("[EMAIL] Gagal kirim ke %s via %s -> %s", email_tujuan, provider, exc, exc_info=True)
        return False

    if ok:
        logger.info("[EMAIL] Terkirim via %s ke %s", provider, email_tujuan)
    return ok


send_verification_email = kirim_email_verifikasi
