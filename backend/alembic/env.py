"""
alembic/env.py
Konfigurasi Alembic untuk migrasi database SiagaWarga.
Mendukung mode online dan offline.
"""
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Import settings dan semua model domain agar metadata terdeteksi
from app.infrastructure.config import settings
import app.domain.entities  # noqa: F401 — pastikan semua model domain terdaftar ke Base.metadata
from app.domain.entities.base import Base

# Konfigurasi Alembic
config = context.config

# Override URL database dari settings (bukan dari alembic.ini)
# Pastikan menggunakan driver psycopg (psycopg 3)
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
config.set_main_option("sqlalchemy.url", db_url)

# Setup logging dari alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata target untuk autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Mode offline: generate SQL script tanpa koneksi database.
    Jalankan: alembic upgrade --sql head
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Render ENUM types dengan nama eksplisit
        render_as_batch=False,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Mode online: jalankan migrasi langsung ke database.
    Jalankan: alembic upgrade head
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,       # Deteksi perubahan tipe kolom
            compare_server_default=True,  # Deteksi perubahan default value
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
