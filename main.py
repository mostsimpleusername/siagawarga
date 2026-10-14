"""
main.py
Entry point aplikasi FastAPI SiagaWarga.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.prioritas import router as prioritas_router
from app.api.v1.laporan import router as laporan_router
from app.api.v1.petugas import router as petugas_router
from app.api.v1.analitik_spasial import router as analitik_spasial_router
from app.core.config import settings
from app.core.database import check_db_connection

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Platform Intelligent Citizen Reporting & Response Prioritization. "
        "Memungkinkan warga melaporkan permasalahan lingkungan dan "
        "membantu petugas memprioritaskan penanganan berdasarkan Priority Score."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# Konfigurasi CORS agar frontend web/mobile dapat mengakses API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Daftarkan Router API v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(prioritas_router, prefix="/api/v1")
app.include_router(laporan_router, prefix="/api/v1")
app.include_router(petugas_router, prefix="/api/v1")
app.include_router(analitik_spasial_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root():
    """Endpoint root untuk konfirmasi API berjalan."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint — cek koneksi database."""
    db_ok = check_db_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
    }
