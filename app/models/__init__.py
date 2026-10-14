"""
app/models/__init__.py
Import semua model agar:
1. Alembic dapat mendeteksi metadata secara otomatis
2. SQLAlchemy dapat meresoluasi semua relasi forward-reference

URUTAN IMPORT PENTING:
  Tabel dengan FK harus diimport setelah tabel yang direferensikan.
  STI (Pengguna → Warga, Petugas) diimport dalam satu file.
"""

# Base & Enums (tidak ada dependensi)
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin
from app.models.enums import Peran, StatusLaporan, Severity, KategoriPrioritas

# TimPetugas (direferensikan oleh Pengguna.tim_id)
from app.models.tim_petugas import TimPetugas

# Pengguna, Warga, Petugas, TokenSesi
# (Pengguna mereferensikan TimPetugas)
from app.models.pengguna import Pengguna, Warga, Petugas, TokenSesi

# KategoriLaporan (direferensikan oleh Laporan.kategori_id)
from app.models.kategori_laporan import KategoriLaporan

# Laporan (mereferensikan Pengguna dan KategoriLaporan)
from app.models.laporan import Laporan

# Entitas komposisi Laporan (FK → laporan.id, CASCADE)
from app.models.lokasi import LokasiLaporan
from app.models.foto_laporan import FotoLaporan
from app.models.riwayat_status import RiwayatStatus
from app.models.penugasan import Penugasan

__all__ = [
    # Base
    "Base",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    # Enums
    "Peran",
    "StatusLaporan",
    "Severity",
    "KategoriPrioritas",
    # Models
    "TimPetugas",
    "Pengguna",
    "Warga",
    "Petugas",
    "TokenSesi",
    "KategoriLaporan",
    "Laporan",
    "LokasiLaporan",
    "FotoLaporan",
    "RiwayatStatus",
    "Penugasan",
]
