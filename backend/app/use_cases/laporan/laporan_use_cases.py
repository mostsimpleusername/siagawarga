"""
app/use_cases/laporan/laporan_use_cases.py
Use Cases untuk Pengelolaan Laporan Warga:
- Buat Laporan (KF-03, KF-04, KF-05, KF-06)
- Riwayat Laporan Pribadi (KF-07)
- Persebaran Laporan Sekitar dengan Privasi (KF-07, KNF-04)
- Pantau Status & Timeline (KF-08)
- Asisten Rekomendasi AI Multimodal (KF-11)
"""
import uuid
from typing import List, Optional

from fastapi import HTTPException, UploadFile, status
from geoalchemy2.functions import ST_Distance, ST_DWithin, ST_MakePoint, ST_SetSRID
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.domain.entities.foto_laporan import FotoLaporan
from app.domain.entities.kategori_laporan import KategoriLaporan
from app.domain.entities.laporan import Laporan
from app.domain.entities.pengguna import Pengguna
from app.domain.entities.riwayat_status import RiwayatStatus
from app.infrastructure.ai_client.client import AIServiceClient
from app.infrastructure.config import settings
from app.presentation.schemas.laporan import (
    FotoLaporanItem,
    LaporanCreate,
    LaporanResponse,
    LaporanSayaResponse,
    LaporanSekitarResponse,
    LaporanStatusTrackingResponse,
    RiwayatStatusItem,
)
from app.presentation.schemas.pengguna import PelaporPublikResponse
from app.use_cases.prioritas.priority_engine import DomainPriorityEngine


class LaporanUseCase:
    """Use case layer untuk pengelolaan laporan oleh warga dan asisten AI."""

    @staticmethod
    async def assist_ai(
        db: Session,
        file: Optional[UploadFile] = None,
        deskripsi: Optional[str] = None,
    ) -> dict:
        client = AIServiceClient(
            base_url=settings.AI_SERVICE_URL,
            timeout=settings.AI_SERVICE_TIMEOUT,
        )
        img_bytes = None
        filename = None
        content_type = None

        if (not file or not file.filename) and (not deskripsi or not deskripsi.strip()):
            return {
                "success": False,
                "message": "Mohon pilih file foto atau ketikkan deskripsi masalah terlebih dahulu untuk dianalisis oleh AI.",
                "data": None,
            }

        if file and file.filename:
            img_bytes = await file.read()
            filename = file.filename
            content_type = file.content_type

        ai_res = await client.classify_report(
            image_bytes=img_bytes,
            image_filename=filename,
            content_type=content_type,
            deskripsi=deskripsi,
        )

        if not ai_res:
            return {
                "success": False,
                "message": "AI service offline atau tidak merespons. Silakan pilih kategori secara manual.",
                "data": None,
            }

        nama_kat = ai_res.get("recommended_db_category", "Lainnya")
        kat_db = db.scalar(select(KategoriLaporan).where(KategoriLaporan.nama == nama_kat))

        return {
            "success": True,
            "message": "Analisis AI berhasil.",
            "data": {
                "ai_raw": ai_res,
                "kategori_rekomendasi": {
                    "id": str(kat_db.id) if kat_db else None,
                    "nama": kat_db.nama if kat_db else nama_kat,
                    "bobot_bahaya_default": kat_db.bobot_bahaya_default if kat_db else 1.0,
                },
                "review_required": ai_res.get("review_required", False),
                "review_reason": ai_res.get("review_reason"),
            },
        }

    @staticmethod
    def buat_laporan(
        db: Session,
        payload: LaporanCreate,
        current_user: Pengguna,
    ) -> Laporan:
        kategori = db.scalar(
            select(KategoriLaporan).where(KategoriLaporan.id == payload.kategori_id)
        )
        if not kategori or not kategori.is_aktif:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kategori laporan tidak valid atau tidak aktif.",
            )

        hasil_prioritas = DomainPriorityEngine.hitung(
            severity=payload.severity,
            bobot_kategori=kategori.bobot_bahaya_default,
            faktor_lokasi=payload.faktor_lokasi or 50.0,
            dampak=payload.dampak or 50.0,
            jumlah_pelapor=payload.jumlah_pelapor or 1,
            waktu_tunggu_jam=payload.waktu_tunggu_jam or 0.0,
        )

        titik_spasial = ST_SetSRID(
            ST_MakePoint(payload.longitude, payload.latitude),
            4326,
        )

        laporan_baru = Laporan(
            warga_id=current_user.id,
            kategori_id=payload.kategori_id,
            judul=payload.judul,
            deskripsi=payload.deskripsi,
            alamat_lokasi=payload.alamat_lokasi,
            latitude=payload.latitude,
            longitude=payload.longitude,
            titik_koordinat=titik_spasial,
            severity=payload.severity,
            tingkat_bahaya=payload.tingkat_bahaya,
            faktor_lokasi=payload.faktor_lokasi,
            dampak=payload.dampak,
            jumlah_pelapor=payload.jumlah_pelapor,
            waktu_tunggu_jam=payload.waktu_tunggu_jam,
            skor_prioritas=hasil_prioritas.skor_prioritas,
            kategori_prioritas=hasil_prioritas.kategori_prioritas,
        )
        db.add(laporan_baru)
        db.flush()

        if payload.foto_urls:
            for idx, url in enumerate(payload.foto_urls):
                foto = FotoLaporan(
                    laporan_id=laporan_baru.id,
                    url=url,
                    urutan=idx,
                )
                db.add(foto)

        riwayat_awal = RiwayatStatus(
            laporan_id=laporan_baru.id,
            status_lama=None,
            status_baru=laporan_baru.status,
            catatan="Laporan berhasil dibuat oleh warga.",
        )
        db.add(riwayat_awal)

        db.commit()
        db.refresh(laporan_baru)
        return laporan_baru

    @staticmethod
    def get_laporan_saya(
        db: Session,
        current_user: Pengguna,
    ) -> List[Laporan]:
        stmt = (
            select(Laporan)
            .where(Laporan.warga_id == current_user.id)
            .options(
                joinedload(Laporan.kategori),
                selectinload(Laporan.foto),
                selectinload(Laporan.riwayat_status),
            )
            .order_by(desc(Laporan.dibuat_pada))
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_laporan_sekitar(
        db: Session,
        latitude: float,
        longitude: float,
        radius_meter: float = 1000.0,
        limit: int = 50,
    ) -> List[LaporanSekitarResponse]:
        titik_pusat = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        jarak_expr = ST_Distance(Laporan.titik_koordinat, titik_pusat).label("jarak_meter")

        stmt = (
            select(Laporan, jarak_expr)
            .where(ST_DWithin(Laporan.titik_koordinat, titik_pusat, radius_meter))
            .options(
                joinedload(Laporan.kategori),
                joinedload(Laporan.warga),
                selectinload(Laporan.foto),
            )
            .order_by(jarak_expr)
            .limit(limit)
        )

        hasil = db.execute(stmt).all()

        response: List[LaporanSekitarResponse] = []
        for lap, jarak in hasil:
            pelapor_anonim = PelaporPublikResponse.dari_warga(
                warga_id=lap.warga_id,
                nama_asli=lap.warga.nama if lap.warga else "Warga",
            )

            response.append(
                LaporanSekitarResponse(
                    id=lap.id,
                    judul=lap.judul,
                    deskripsi=lap.deskripsi,
                    status=lap.status,
                    severity=lap.severity,
                    alamat_lokasi=lap.alamat_lokasi,
                    latitude=lap.latitude,
                    longitude=lap.longitude,
                    jarak_meter=round(float(jarak), 1) if jarak is not None else None,
                    dibuat_pada=lap.dibuat_pada,
                    kategori=lap.kategori,
                    foto=[FotoLaporanItem.model_validate(f) for f in lap.foto],
                    pelapor=pelapor_anonim,
                )
            )

        return response

    @staticmethod
    def pantau_status_laporan(
        db: Session,
        id: uuid.UUID,
    ) -> LaporanStatusTrackingResponse:
        stmt = (
            select(Laporan)
            .where(Laporan.id == id)
            .options(selectinload(Laporan.riwayat_status))
        )
        laporan = db.scalar(stmt)

        if not laporan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Laporan tidak ditemukan.",
            )

        timeline_sorted = sorted(
            laporan.riwayat_status,
            key=lambda r: r.waktu,
        )

        return LaporanStatusTrackingResponse(
            id=laporan.id,
            judul=laporan.judul,
            status_terkini=laporan.status,
            dibuat_pada=laporan.dibuat_pada,
            diperbarui_pada=laporan.diperbarui_pada,
            timeline=[RiwayatStatusItem.model_validate(r) for r in timeline_sorted],
        )
