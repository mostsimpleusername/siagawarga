"""
app/infrastructure/database/session.py
Setup engine dan session database SQLAlchemy untuk PostgreSQL/Supabase.
Dioptimalkan untuk serverless (pool kecil / NullPool, Supabase pooler compatibility).
"""
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from app.infrastructure.config import settings

# Pastikan driver psycopg (psycopg 3)
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

# Jika menggunakan pooler Supabase (port 6543 / pooler domain), gunakan NullPool
is_supabase_pooler = "pooler.supabase.com" in db_url or ":6543" in db_url

engine_kwargs = {
    "pool_pre_ping": True,
    "echo": settings.DEBUG,
    "connect_args": {
        "prepare_threshold": None,  # Kompatibel dengan Supabase transaction pooler (port 6543)
    },
}

if is_supabase_pooler:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = 2
    engine_kwargs["max_overflow"] = 3

engine = create_engine(db_url, **engine_kwargs)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency FastAPI untuk database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Health check koneksi database."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
