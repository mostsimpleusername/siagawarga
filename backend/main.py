"""
main.py
Entry point aplikasi FastAPI SiagaWarga.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from multipart.exceptions import MultipartParseError

from app.presentation.api.v1 import (
    auth_router,
    prioritas_router,
    laporan_router,
    petugas_router,
    analitik_spasial_router,
)
from app.infrastructure.config import settings
from app.infrastructure.database.session import check_db_connection

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
cors_origins_raw = settings.CORS_ORIGINS.strip()
if cors_origins_raw == "*" or not cors_origins_raw:
    cors_origins = ["*"]
    cors_credentials = False
else:
    cors_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
    cors_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(MultipartParseError)
async def multipart_parse_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Data form multipart tidak valid atau kosong. Pastikan memilih file foto atau mengisi kolom teks.",
            "error_type": "MultipartParseError"
        }
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
