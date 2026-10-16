"""
app/presentation/api/v1/__init__.py
Ekspor semua router API v1 terpadu.
"""
from app.presentation.api.v1.auth import router as auth_router
from app.presentation.api.v1.laporan import router as laporan_router
from app.presentation.api.v1.petugas import router as petugas_router
from app.presentation.api.v1.prioritas import router as prioritas_router
from app.presentation.api.v1.analitik_spasial import router as analitik_spasial_router

__all__ = [
    "auth_router",
    "laporan_router",
    "petugas_router",
    "prioritas_router",
    "analitik_spasial_router",
]
