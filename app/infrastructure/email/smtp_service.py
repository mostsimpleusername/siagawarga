"""
app/infrastructure/email/smtp_service.py
Service pengiriman email modular menggunakan fastapi-mail.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.infrastructure.config import settings

logger = logging.getLogger(__name__)


def get_mail_config() -> ConnectionConfig:
    use_credentials = bool(settings.MAIL_USERNAME and settings.MAIL_PASSWORD)
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME or "",
        MAIL_PASSWORD=settings.MAIL_PASSWORD or "",
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=use_credentials,
        VALIDATE_CERTS=True,
    )


def render_email_verifikasi_html(nama: str, tautan_verifikasi: str) -> str:
    tahun_sekarang = datetime.now().year
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verifikasi Akun Siaga Warga</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f1f5f9; margin: 0; padding: 0; color: #334155; }}
        .wrapper {{ width: 100%; padding: 40px 0; }}
        .main-card {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); padding: 36px 24px; text-align: center; color: #ffffff; }}
        .content {{ padding: 36px 32px; line-height: 1.6; }}
        .verify-btn {{ display: inline-block; background: #16a34a; color: #ffffff !important; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 15px; }}
        .alternative-box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; font-size: 13px; word-break: break-all; color: #475569; font-family: monospace; }}
        .footer {{ border-top: 1px solid #f1f5f9; padding: 24px 32px; background: #fafafa; font-size: 12px; color: #94a3b8; text-align: center; }}
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="main-card">
            <div class="header">
                <h1 style="margin:0;font-size:26px;">Siaga Warga</h1>
                <p style="margin:8px 0 0 0;font-size:14px;opacity:0.9;">Platform Laporan & Pengaduan Lingkungan Warga</p>
            </div>
            <div class="content">
                <h2 style="margin-top:0;color:#0f172a;">Halo {nama},</h2>
                <p>Terima kasih telah mendaftar di <strong>Siaga Warga</strong>. Silakan klik tombol di bawah ini untuk mengaktifkan akun Anda:</p>
                <div style="text-align:center;margin:32px 0;">
                    <a href="{tautan_verifikasi}" class="verify-btn" target="_blank">Aktivasi Akun Saya</a>
                </div>
                <div style="height:1px;background:#e2e8f0;margin:28px 0;"></div>
                <p style="font-size:13px;color:#64748b;margin-bottom:8px;">Tautan ini berlaku selama <strong>24 jam</strong>:</p>
                <div class="alternative-box">{tautan_verifikasi}</div>
            </div>
            <div class="footer">&copy; {tahun_sekarang} Siaga Warga. Seluruh hak cipta dilindungi undang-undang.</div>
        </div>
    </div>
</body>
</html>
"""


async def kirim_email_verifikasi(
    email_tujuan: str,
    nama: str,
    token: str,
    base_url: Optional[str] = "http://127.0.0.1:8000/api/v1/auth/verify-email",
) -> None:
    tautan_verifikasi = f"{base_url}?token={token}"
    html_content = render_email_verifikasi_html(nama=nama, tautan_verifikasi=tautan_verifikasi)

    message = MessageSchema(
        subject="Verifikasi Akun Siaga Warga Anda",
        recipients=[email_tujuan],
        body=html_content,
        subtype=MessageType.html,
    )

    try:
        mail_config = get_mail_config()
        if not settings.MAIL_USERNAME:
            logger.warning(
                f"[EMAIL SERVICE] MAIL_USERNAME kosong. Tautan simulasi: {tautan_verifikasi}"
            )
            return

        fm = FastMail(mail_config)
        await fm.send_message(message)
        logger.info(f"[EMAIL SERVICE] Email verifikasi terkirim via SMTP ke {email_tujuan}")
    except Exception as exc:
        logger.error(f"[EMAIL SERVICE] Gagal mengirim email ke {email_tujuan}: {exc}", exc_info=True)


send_verification_email = kirim_email_verifikasi
