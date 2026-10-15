"""
app/use_cases/spasial/spasial_use_cases.py
Use Cases untuk Analitik Geospasial, Prioritas, & Deteksi Duplikasi (KF-13, KF-14, KF-17).
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from geoalchemy2.functions import (
    ST_Distance,
    ST_DWithin,
    ST_MakeEnvelope,
    ST_MakePoint,
    ST_SetSRID,
)
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.domain.entities.laporan import Laporan
from app.domain.enums import KategoriPrioritas, StatusLaporan
from app.presentation.schemas.spasial import (
    DeteksiSerupaResponse,
    GeoJsonFeature,
    GeoJsonFeatureCollection,
    GeoJsonGeometry,
    LaporanSerupaItem,
    PetaMarkerItem,
)


class DeteksiSerupaResult:
    def __init__(self, laporan: Laporan, jarak_meter: float, selisih_jam: float):
        self.laporan = laporan
        self.jarak_meter = round(jarak_meter, 1)
        self.selisih_jam = round(selisih_jam, 1)


class SpasialUseCase:
    """Use case layer untuk seluruh operasi geospasial, visualisasi peta, dan deteksi duplikasi."""

    @staticmethod
    def get_urutan_prioritas(
        db: Session,
        kategori_prioritas: Optional[KategoriPrioritas] = None,
        kategori_id: Optional[uuid.UUID] = None,
        limit: int = 50,
    ) -> List[Laporan]:
        stmt = (
            select(Laporan)
            .where(Laporan.status.in_([StatusLaporan.DIKIRIM, StatusLaporan.DIPROSES]))
            .options(joinedload(Laporan.kategori))
            .order_by(desc(Laporan.skor_prioritas), desc(Laporan.dibuat_pada))
        )

        if kategori_prioritas:
            stmt = stmt.where(Laporan.kategori_prioritas == kategori_prioritas)
        if kategori_id:
            stmt = stmt.where(Laporan.kategori_id == kategori_id)

        stmt = stmt.limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_laporan_dalam_bbox(
        db: Session,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        hanya_aktif: bool = True,
    ) -> List[Laporan]:
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

        return list(db.scalars(stmt).all())

    @staticmethod
    def get_peta_markers(
        db: Session,
        min_lon: Optional[float] = None,
        min_lat: Optional[float] = None,
        max_lon: Optional[float] = None,
        max_lat: Optional[float] = None,
        kategori_prioritas: Optional[KategoriPrioritas] = None,
        status_laporan: Optional[StatusLaporan] = None,
    ) -> List[PetaMarkerItem]:
        if None not in (min_lon, min_lat, max_lon, max_lat):
            laporan_list = SpasialUseCase.get_laporan_dalam_bbox(
                db=db,
                min_lon=min_lon,
                min_lat=min_lat,
                max_lon=max_lon,
                max_lat=max_lat,
                hanya_aktif=status_laporan is None,
            )
        else:
            stmt = (
                select(Laporan)
                .options(joinedload(Laporan.kategori))
                .order_by(desc(Laporan.skor_prioritas))
            )
            if status_laporan:
                stmt = stmt.where(Laporan.status == status_laporan)
            else:
                stmt = stmt.where(Laporan.status.in_([StatusLaporan.DIKIRIM, StatusLaporan.DIPROSES]))

            if kategori_prioritas:
                stmt = stmt.where(Laporan.kategori_prioritas == kategori_prioritas)

            laporan_list = list(db.scalars(stmt).all())

        markers: List[PetaMarkerItem] = []
        for lap in laporan_list:
            markers.append(
                PetaMarkerItem(
                    id=lap.id,
                    judul=lap.judul,
                    latitude=lap.latitude,
                    longitude=lap.longitude,
                    kategori_nama=lap.kategori.nama if lap.kategori else "Lainnya",
                    kategori_prioritas=lap.kategori_prioritas,
                    skor_prioritas=lap.skor_prioritas,
                    status=lap.status,
                    severity=lap.severity,
                    dibuat_pada=lap.dibuat_pada,
                )
            )

        return markers

    @staticmethod
    def get_peta_geojson(
        db: Session,
        kategori_prioritas: Optional[KategoriPrioritas] = None,
    ) -> GeoJsonFeatureCollection:
        stmt = (
            select(Laporan)
            .where(Laporan.status.in_([StatusLaporan.DIKIRIM, StatusLaporan.DIPROSES]))
            .options(joinedload(Laporan.kategori))
        )
        if kategori_prioritas:
            stmt = stmt.where(Laporan.kategori_prioritas == kategori_prioritas)

        laporan_list = db.scalars(stmt).all()

        features: List[GeoJsonFeature] = []
        for lap in laporan_list:
            features.append(
                GeoJsonFeature(
                    geometry=GeoJsonGeometry(
                        type="Point",
                        coordinates=[lap.longitude, lap.latitude],
                    ),
                    properties={
                        "id": str(lap.id),
                        "judul": lap.judul,
                        "kategori": lap.kategori.nama if lap.kategori else "Lainnya",
                        "skor_prioritas": lap.skor_prioritas,
                        "kategori_prioritas": lap.kategori_prioritas.value,
                        "status": lap.status.value,
                        "severity": lap.severity.value,
                        "dibuat_pada": lap.dibuat_pada.isoformat(),
                    },
                )
            )

        return GeoJsonFeatureCollection(features=features)

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
        if waktu_kejadian is None:
            waktu_kejadian = datetime.now(timezone.utc)
        elif waktu_kejadian.tzinfo is None:
            waktu_kejadian = waktu_kejadian.replace(tzinfo=timezone.utc)

        waktu_mulai = waktu_kejadian - timedelta(hours=rentang_waktu_jam)
        waktu_selesai = waktu_kejadian + timedelta(hours=rentang_waktu_jam)

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
    def deteksi_laporan_serupa_response(
        db: Session,
        kategori_id: uuid.UUID,
        latitude: float,
        longitude: float,
        radius_meter: float = 100.0,
        rentang_waktu_jam: int = 72,
        abaikan_laporan_id: Optional[uuid.UUID] = None,
    ) -> DeteksiSerupaResponse:
        hasil_serupa = SpasialUseCase.cari_laporan_serupa(
            db=db,
            kategori_id=kategori_id,
            latitude=latitude,
            longitude=longitude,
            radius_meter=radius_meter,
            rentang_waktu_jam=rentang_waktu_jam,
            abaikan_laporan_id=abaikan_laporan_id,
        )

        items: List[LaporanSerupaItem] = []
        for r in hasil_serupa:
            lap = r.laporan
            items.append(
                LaporanSerupaItem(
                    id=lap.id,
                    judul=lap.judul,
                    deskripsi=lap.deskripsi,
                    status=lap.status,
                    severity=lap.severity,
                    kategori_prioritas=lap.kategori_prioritas,
                    skor_prioritas=lap.skor_prioritas,
                    latitude=lap.latitude,
                    longitude=lap.longitude,
                    alamat_lokasi=lap.alamat_lokasi,
                    jarak_meter=r.jarak_meter,
                    selisih_jam=r.selisih_jam,
                    dibuat_pada=lap.dibuat_pada,
                    kategori=lap.kategori,
                )
            )

        return DeteksiSerupaResponse(
            total_ditemukan=len(items),
            indikasi_duplikasi=len(items) > 0,
            laporan_serupa=items,
        )
