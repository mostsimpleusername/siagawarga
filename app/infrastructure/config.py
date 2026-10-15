"""
app/infrastructure/config.py
Konfigurasi aplikasi menggunakan Pydantic Settings.
Nilai dibaca dari file .env secara otomatis.
"""
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

    # --- App ---
    APP_NAME: str = "SiagaWarga"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # --- AI Service ---
    AI_SERVICE_URL: str = "http://localhost:8001"
    AI_SERVICE_TIMEOUT: int = 30

    # --- SMTP / Email Configuration ---
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@siagawarga.id"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False


# Singleton instance yang digunakan di seluruh aplikasi
settings = Settings()
