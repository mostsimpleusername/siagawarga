from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID

from app.domain.enums import KategoriPrioritas, Severity, StatusLaporan
from app.domain.value_objects.priority_score import PriorityScoreResult
from app.domain.entities.kategori_laporan import KategoriLaporan
from app.domain.entities.laporan import Laporan


class DomainPriorityEngine:
    """
    Mesin Prioritas Terpadu SiagaWarga (PRD KF-12, KNF-10).
    Menghitung Priority Score (0-100) secara transparan dan deterministik dari 5 parameter:
    1. Tingkat Bahaya (30%) - Dihitung dari Severity pelapor & Bobot Kategori
    2. Faktor Lokasi (20%) - Standar 50.0 atau zonasi strategis
    3. Dampak Publik (20%) - Berdasarkan estimasi gangguan fasilitas umum
    4. Jumlah Pelapor (15%) - Dihitung dinamis via PostGIS ST_DWithin (laporan serupa)
    5. Waktu Tunggu (15%) - Kenaikan otomatis 2.5 poin per jam (mencegah starvation)
    """

    BOBOT_BAHAYA = 0.30
    BOBOT_LOKASI = 0.20
    BOBOT_DAMPAK = 0.20
    BOBOT_PELAPOR = 0.15
    BOBOT_WAKTU = 0.15

    AMBANG_P1 = 70.0
    AMBANG_P2 = 40.0

    @classmethod
    def normalisasi_tingkat_bahaya(cls, severity: Severity, bobot_kategori: float = 1.0) -> float:
        base_skor = {
            Severity.RENDAH: 30.0,
            Severity.SEDANG: 65.0,
            Severity.TINGGI: 100.0,
        }.get(severity, 50.0)

        pengali = min(max(bobot_kategori, 1.0), 5.0) / 2.5
        skor = base_skor * pengali
        return round(min(max(skor, 0.0), 100.0), 2)

    @classmethod
    def normalisasi_pelapor(cls, jumlah_pelapor: int) -> float:
        if jumlah_pelapor <= 1:
            return 20.0
        elif jumlah_pelapor == 2:
            return 50.0
        elif jumlah_pelapor == 3:
            return 75.0
        elif jumlah_pelapor == 4:
            return 90.0
        else:
            return 100.0

    @classmethod
    def hitung_waktu_tunggu_jam(cls, waktu_dibuat: datetime) -> float:
        now = datetime.now(timezone.utc)
        if waktu_dibuat.tzinfo is None:
            waktu_dibuat = waktu_dibuat.replace(tzinfo=timezone.utc)
        selisih = max((now - waktu_dibuat).total_seconds(), 0.0)
        return round(selisih / 3600.0, 2)

    @classmethod
    def normalisasi_waktu_tunggu(cls, waktu_tunggu_jam: float) -> float:
        return round(min(waktu_tunggu_jam * 2.5, 100.0), 2)

    @classmethod
    def tentukan_kategori(cls, skor: float) -> KategoriPrioritas:
        if skor >= cls.AMBANG_P1:
            return KategoriPrioritas.P1
        elif skor >= cls.AMBANG_P2:
            return KategoriPrioritas.P2
        return KategoriPrioritas.P3

    @classmethod
    def hitung(
        cls,
        severity: Severity,
        bobot_kategori: float = 1.0,
        faktor_lokasi: float = 50.0,
        dampak: float = 50.0,
        jumlah_pelapor: int = 1,
        waktu_tunggu_jam: float = 0.0,
    ) -> PriorityScoreResult:
        p_bahaya = cls.normalisasi_tingkat_bahaya(severity, bobot_kategori)
        p_lokasi = min(max(faktor_lokasi, 0.0), 100.0)
        p_dampak = min(max(dampak, 0.0), 100.0)
        p_pelapor = cls.normalisasi_pelapor(jumlah_pelapor)
        p_waktu = cls.normalisasi_waktu_tunggu(waktu_tunggu_jam)

        total = (
            (p_bahaya * cls.BOBOT_BAHAYA)
            + (p_lokasi * cls.BOBOT_LOKASI)
            + (p_dampak * cls.BOBOT_DAMPAK)
            + (p_pelapor * cls.BOBOT_PELAPOR)
            + (p_waktu * cls.BOBOT_WAKTU)
        )
        total_skor = round(min(max(total, 0.0), 100.0), 2)
        kat = cls.tentukan_kategori(total_skor)

        return PriorityScoreResult(
            skor_prioritas=total_skor,
            kategori_prioritas=kat,
            tingkat_bahaya=p_bahaya,
            faktor_lokasi=p_lokasi,
            dampak=p_dampak,
            jumlah_pelapor=jumlah_pelapor,
            waktu_tunggu_jam=waktu_tunggu_jam,
            rincian_skor={
                "bahaya": p_bahaya,
                "lokasi": p_lokasi,
                "dampak": p_dampak,
                "pelapor": p_pelapor,
                "waktu": p_waktu,
            },
        )

    @classmethod
    def kalkulasi_laporan_db(
        cls,
        db: Session,
        laporan: Laporan,
        radius_meter: float = 100.0,
    ) -> PriorityScoreResult:
        bobot_kategori = 1.0
        if laporan.kategori:
            bobot_kategori = laporan.kategori.bobot_bahaya_default
        else:
            kat = db.scalar(select(KategoriLaporan).where(KategoriLaporan.id == laporan.kategori_id))
            if kat:
                bobot_kategori = kat.bobot_bahaya_default

        # Hitung laporan serupa via PostGIS
        laporan_serupa = 0
        if laporan.titik_koordinat is not None:
            laporan_serupa = db.scalar(
                select(func.count(Laporan.id)).where(
                    Laporan.kategori_id == laporan.kategori_id,
                    Laporan.id != laporan.id,
                    Laporan.status.in_([StatusLaporan.DIKIRIM, StatusLaporan.DIPROSES]),
                    ST_DWithin(Laporan.titik_koordinat, laporan.titik_koordinat, radius_meter),
                )
            ) or 0

        total_pelapor = 1 + laporan_serupa
        waktu_jam = cls.hitung_waktu_tunggu_jam(laporan.dibuat_pada)

        hasil = cls.hitung(
            severity=laporan.severity,
            bobot_kategori=bobot_kategori,
            faktor_lokasi=laporan.faktor_lokasi or 50.0,
            dampak=laporan.dampak or 50.0,
            jumlah_pelapor=total_pelapor,
            waktu_tunggu_jam=waktu_jam,
        )

        laporan.skor_prioritas = hasil.skor_prioritas
        laporan.kategori_prioritas = hasil.kategori_prioritas
        laporan.tingkat_bahaya = hasil.tingkat_bahaya
        laporan.jumlah_pelapor = hasil.jumlah_pelapor
        laporan.waktu_tunggu_jam = hasil.waktu_tunggu_jam

        return hasil
