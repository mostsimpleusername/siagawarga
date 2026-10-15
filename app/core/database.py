"""
app/core/database.py
Setup koneksi database PostgreSQL dengan SQLAlchemy.
"""
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.models.base import Base

# Pastikan menggunakan driver psycopg (psycopg 3)
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

# Engine utama dengan connection pooling
engine = create_engine(
    db_url,
    pool_pre_ping=True,   # Verifikasi koneksi sebelum digunakan (KNF-05)
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,  # Log SQL hanya saat DEBUG=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency untuk mendapatkan sesi database per-request.
    Sesi ditutup otomatis setelah request selesai.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """
    Membuat semua tabel dari metadata (untuk development/testing).
    Untuk production, gunakan Alembic migrations.
    """
    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """Cek koneksi ke database (untuk health check endpoint)."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
