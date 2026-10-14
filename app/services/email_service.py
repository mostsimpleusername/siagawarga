"""
app/services/email_service.py
Service pengiriman email modular menggunakan fastapi-mail.
Menangani pembuatan template HTML dan pengiriman email verifikasi pendaftaran akun via SMTP.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_mail_config() -> ConnectionConfig:
    """
    Menghasilkan objek ConnectionConfig fastapi-mail berdasarkan konfigurasi di app/core/config.py.
    """
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
    """
    Merender template HTML responsif untuk email verifikasi akun Siaga Warga.
    """
    tahun_sekarang = datetime.now().year
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verifikasi Akun Siaga Warga</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f1f5f9;
            margin: 0;
            padding: 0;
            color: #334155;
            -webkit-text-size-adjust: 100%;
        }}
        .wrapper {{
            width: 100%;
            table-layout: fixed;
            background-color: #f1f5f9;
            padding: 40px 0;
        }}
        .main-card {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }}
        .header {{
            background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
            padding: 36px 24px;
            text-align: center;
            color: #ffffff;
        }}
        .header h1 {{
            margin: 0;
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        .header p {{
            margin: 8px 0 0 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .content {{
            padding: 36px 32px;
            line-height: 1.6;
        }}
        .content h2 {{
            margin-top: 0;
            color: #0f172a;
            font-size: 20px;
            font-weight: 600;
        }}
        .content p {{
            margin: 12px 0;
            font-size: 15px;
            color: #334155;
        }}
        .button-wrapper {{
            text-align: center;
            margin: 32px 0;
        }}
        .verify-btn {{
            display: inline-block;
            background-color: #16a34a;
            color: #ffffff !important;
            text-decoration: none;
            padding: 14px 32px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 15px;
            box-shadow: 0 4px 6px -1px rgba(22, 163, 74, 0.3);
        }}
        .divider {{
            height: 1px;
            background-color: #e2e8f0;
            margin: 28px 0;
        }}
        .alternative-box {{
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 14px;
            font-size: 13px;
            word-break: break-all;
            color: #475569;
            font-family: monospace;
        }}
        .notice {{
            font-size: 13px;
            color: #64748b;
            margin-top: 24px;
        }}
        .footer {{
            border-top: 1px solid #f1f5f9;
            padding: 24px 32px;
            background-color: #fafafa;
            font-size: 12px;
            color: #94a3b8;
            text-align: center;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="main-card">
            <div class="header">
                <h1>Siaga Warga</h1>
                <p>Platform Laporan & Pengaduan Lingkungan Warga</p>
            </div>
            <div class="content">
                <h2>Halo {nama},</h2>
                <p>Terima kasih telah mendaftar di <strong>Siaga Warga</strong>. Langkah terakhir sebelum Anda dapat melaporkan keluhan lingkungan dan memantau penanganan di wilayah Anda adalah memverifikasi alamat email ini.</p>
                <div class="button-wrapper">
                    <a href="{tautan_verifikasi}" class="verify-btn" target="_blank">Aktivasi Akun Saya</a>
                </div>
                <div class="divider"></div>
                <p style="font-size: 13px; color: #64748b; margin-bottom: 8px;">
                    Tautan ini berlaku selama <strong>24 jam</strong>. Jika tombol di atas tidak dapat diklik, silakan salin dan buka tautan berikut di peramban (browser) Anda:
                </p>
                <div class="alternative-box">
                    {tautan_verifikasi}
                </div>
                <p class="notice">
                    Jika Anda tidak pernah mendaftar di Siaga Warga, silakan abaikan email ini dengan aman.
                </p>
            </div>
            <div class="footer">
                &copy; {tahun_sekarang} Siaga Warga. Seluruh hak cipta dilindungi undang-undang.<br>
                Email otomatis, mohon tidak membalas email ini.
            </div>
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
    """
    Mengirimkan email verifikasi akun secara asynchronous menggunakan fastapi-mail.
    
    Args:
        email_tujuan: Alamat email penerima.
        nama: Nama lengkap pengguna / warga.
        token: JWT verification token yang telah di-generate.
        base_url: Alamat endpoint verifikasi email (default: http://127.0.0.1:8000/api/v1/auth/verify-email).
    """
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

        # Jika konfigurasi username SMTP masih kosong (misal mode pengujian lokal murni)
        if not settings.MAIL_USERNAME:
            logger.warning(
                f"[EMAIL SERVICE] MAIL_USERNAME belum dikonfigurasi di .env. "
                f"Pengiriman SMTP fisik ke '{email_tujuan}' dilewati. "
                f"Tautan aktivasi: {tautan_verifikasi}"
            )
            return

        fm = FastMail(mail_config)
        await fm.send_message(message)
        logger.info(f"[EMAIL SERVICE] Email verifikasi berhasil dikirimkan via SMTP ke {email_tujuan}")
    except Exception as exc:
        logger.error(
            f"[EMAIL SERVICE] Terjadi kesalahan saat mengirimkan email via SMTP ke {email_tujuan}: {exc}",
            exc_info=True,
        )


# Alias untuk kemudahan penggunaan
send_verification_email = kirim_email_verifikasi
