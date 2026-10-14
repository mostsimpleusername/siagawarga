"""
app/services/spasial.py
Service Analitik Geospasial & Deteksi Laporan Serupa (KF-17).
Menggunakan query PostGIS berindeks spasial (GeoAlchemy2) untuk performa optimal.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid

from geoalchemy2.functions import ST_Distance, ST_DWithin, ST_MakeEnvelope, ST_MakePoint, ST_SetSRID
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import StatusLaporan
from app.models.laporan import Laporan


class DeteksiSerupaResult:
    def __init__(self, laporan: Laporan, jarak_meter: float, selisih_jam: float):
        self.laporan = laporan
        self.jarak_meter = round(jarak_meter, 1)
        self.selisih_jam = round(selisih_jam, 1)


class SpasialService:
    """Service untuk operasi geospasial lanjutan dan deteksi laporan serupa (KF-17)."""

    @staticmethod
    def cari_laporan_serupa(
        db: Session,
        kategori_id: uuid.UUID,
        latitude: float,
        longitude: float,
        waktu_kejadian: Optional[datetime] = None,
        radius_meter: float = 100.0,
        rentang_waktu_jam: int = 72,
        abaikan_laporan_id: Optional[uuid.UUID] = None,
    ) -> List[DeteksiSerupaResult]:
        """
        KF-17: Mendeteksi laporan serupa berdasarkan 3 dimensi:
        1. Kategori yang sama
        2. Radius spasial berdekatan (ST_DWithin pada SRID 4326)
        3. Rentang waktu kejadian berdekatan (default: dalam 72 jam terakhir)

        Memanfaatkan Spatial Index (GiST) pada kolom titik_koordinat.
        """
        if waktu_kejadian is None:
            waktu_kejadian = datetime.now(timezone.utc)
        elif waktu_kejadian.tzinfo is None:
            waktu_kejadian = waktu_kejadian.replace(tzinfo=timezone.utc)

        waktu_mulai = waktu_kejadian - timedelta(hours=rentang_waktu_jam)
        waktu_selesai = waktu_kejadian + timedelta(hours=rentang_waktu_jam)

        # Bentuk titik geometri pengguna
        titik_pusat = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        jarak_expr = ST_Distance(Laporan.titik_koordinat, titik_pusat).label("jarak_meter")

        stmt = (
            select(Laporan, jarak_expr)
            .where(
                Laporan.kategori_id == kategori_id,
                Laporan.status.in_([StatusLaporan.DIKIRIM, StatusLaporan.DIPROSES]),
                Laporan.dibuat_pada.between(waktu_mulai, waktu_selesai),
                ST_DWithin(Laporan.titik_koordinat, titik_pusat, radius_meter),
            )
            .options(
                joinedload(Laporan.kategori),
                joinedload(Laporan.warga),
            )
            .order_by(jarak_expr)
        )

        if abaikan_laporan_id:
            stmt = stmt.where(Laporan.id != abaikan_laporan_id)

        records = db.execute(stmt).all()

        hasil: List[DeteksiSerupaResult] = []
        for lap, jarak in records:
            lap_waktu = lap.dibuat_pada
            if lap_waktu.tzinfo is None:
                lap_waktu = lap_waktu.replace(tzinfo=timezone.utc)
            selisih_jam = abs((waktu_kejadian - lap_waktu).total_seconds()) / 3600.0

            hasil.append(
                DeteksiSerupaResult(
                    laporan=lap,
                    jarak_meter=float(jarak) if jarak is not None else 0.0,
                    selisih_jam=selisih_jam,
                )
            )

        return hasil

    @staticmethod
    def get_laporan_dalam_bbox(
        db: Session,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        hanya_aktif: bool = True,
    ) -> List[Laporan]:
        """
        KF-14: Mengambil laporan yang berada di dalam area Bounding Box (Viewport Peta).
        Query spasial cepat menggunakan ST_MakeEnvelope.
        """
        bbox_envelope = ST_SetSRID(
            ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326),
            4326,
        )

        stmt = (
            select(Laporan)
            .where(Laporan.titik_koordinat.intersects(bbox_envelope))
            .options(joinedload(Laporan.kategori))
            .order_by(desc(Laporan.skor_prioritas))
        )

        if hanya_aktif:
            stmt = stmt.where(Laporan.status.in_([StatusLaporan.DIKIRIM, StatusLaporan.DIPROSES]))

        return db.scalars(stmt).all()
