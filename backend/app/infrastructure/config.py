"""
app/infrastructure/config.py
Konfigurasi aplikasi menggunakan Pydantic Settings.
Nilai dibaca dari file .env secara otomatis.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Database ---
    DATABASE_URL: str = "postgresql://postgres:123@localhost:5432/siaga_warga"

    # --- Security ---
    SECRET_KEY: str = "ganti-dengan-secret-key-yang-kuat-di-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- App URLs & CORS ---
    APP_NAME: str = "SiagaWarga"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    BACKEND_PUBLIC_URL: str = "http://127.0.0.1:8000"
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    EXPOSE_VERIFICATION_LINK: bool = False

    # --- Email Provider Configuration ---
    EMAIL_PROVIDER: str = "brevo"  # "brevo", "resend", "smtp", atau "console"
    BREVO_API_KEY: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None
    MAIL_FROM: str = "noreply@siagawarga.id"
    MAIL_FROM_NAME: str = "SiagaWarga"

    # --- Legacy SMTP Configuration (fallback if EMAIL_PROVIDER=smtp) ---
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # --- AI Service ---
    AI_SERVICE_URL: str = "https://steadfast-strength-production-e4b7.up.railway.app/"
    AI_SERVICE_TIMEOUT: int = 30


# Singleton instance yang digunakan di seluruh aplikasi
settings = Settings()
