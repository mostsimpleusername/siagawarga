"""
app/services/priority_engine.py
Service Layer: Mesin Prioritas (Priority Score Engine).
Mengimplementasikan perhitungan skor 0-100 secara deterministik dan transparan (KNF-10).

5 Parameter Spesifik (PRD 1.2b, KF-12):
1. Tingkat Bahaya (30%)
2. Lokasi (20%)
3. Dampak (20%)
4. Jumlah Pelapor / Frekuensi Serupa (15%)
5. Waktu Tunggu (15%)

Pengelompokan (Kategori Prioritas):
- P1 (Kritis)  : Skor >= 70.0
- P2 (Sedang)  : 40.0 <= Skor < 70.0
- P3 (Rendah)  : Skor < 40.0
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from geoalchemy2.functions import ST_DWithin
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import KategoriPrioritas, Severity, StatusLaporan
from app.models.kategori_laporan import KategoriLaporan
from app.models.laporan import Laporan
from app.models.lokasi import LokasiLaporan


@dataclass
class HasilKalkulasiPrioritas:
    """Hasil kalkulasi skor prioritas beserta rincian parameter untuk auditability (KNF-10, KNF-12)."""
    skor_akhir: float
    kategori_prioritas: KategoriPrioritas
    param_tingkat_bahaya: float
    param_dampak_lokasi: float
    param_jumlah_pelapor: int
    param_frekuensi_serupa: int
    param_waktu_tunggu_jam: float


class PriorityEngine:
    # Bobot masing-masing parameter (Total = 1.0)
    BOBOT_BAHAYA = 0.30
    BOBOT_LOKASI = 0.20
    BOBOT_DAMPAK = 0.20
    BOBOT_PELAPOR = 0.15
    BOBOT_WAKTU = 0.15

    # Threshold Kategori Prioritas
    AMBANG_P1 = 70.0
    AMBANG_P2 = 40.0

    @classmethod
    def normalisasi_tingkat_bahaya(cls, severity: Severity, bobot_kategori: float = 1.0) -> float:
        """
        Parameter 1: Tingkat Bahaya (Skala 0-100).
        Dihitung dari severity laporan dikalikan pengali bobot kategori bahaya (1.0 - 5.0).
        """
        base_skor = {
            Severity.RENDAH: 30.0,
            Severity.SEDANG: 65.0,
            Severity.TINGGI: 100.0,
        }.get(severity, 50.0)

        # Pengali kategori dinormalisasi: 1.0 (standar) s/d 5.0 (ekstrem bahaya)
        pengali = min(max(bobot_kategori, 1.0), 5.0) / 2.5
        skor = base_skor * pengali
        return round(min(max(skor, 0.0), 100.0), 2)

    @classmethod
    def normalisasi_lokasi(cls, skor_dampak_lokasi: Optional[float] = None) -> float:
        """
        Parameter 2: Lokasi (Skala 0-100).
        Tingkat kepentingan strategis titik lokasi (jalan utama, sekolah, pemukiman, dll).
        Default bernilai 50.0 jika belum ada zonasi spesifik.
        """
        if skor_dampak_lokasi is not None:
            return round(min(max(skor_dampak_lokasi, 0.0), 100.0), 2)
        return 50.0

    @classmethod
    def normalisasi_dampak(cls, skor_dampak: Optional[float] = None) -> float:
        """
        Parameter 3: Dampak (Skala 0-100).
        Besaran gangguan terhadap kelancaran aktivitas umum.
        Default bernilai 50.0 jika tidak dispesifikasikan.
        """
        if skor_dampak is not None:
            return round(min(max(skor_dampak, 0.0), 100.0), 2)
        return 50.0

    @classmethod
    def normalisasi_pelapor(cls, jumlah_pelapor: int) -> float:
        """
        Parameter 4: Jumlah Pelapor / Frekuensi Laporan Serupa (Skala 0-100).
        Menunjukkan tingkat keresahan/urgensi sosial warga.
        - 1 pelapor  : 20
        - 2 pelapor  : 45
        - 3 pelapor  : 65
        - 4 pelapor  : 85
        - >=5 pelapor: 100
        """
        if jumlah_pelapor <= 1:
            return 20.0
        elif jumlah_pelapor == 2:
            return 45.0
        elif jumlah_pelapor == 3:
            return 65.0
        elif jumlah_pelapor == 4:
            return 85.0
        else:
            return 100.0

    @classmethod
    def hitung_waktu_tunggu_jam(cls, waktu_dibuat: datetime) -> float:
        """Menghitung selisih waktu dibuat laporan dengan waktu saat ini (dalam jam)."""
        now = datetime.now(timezone.utc)
        if waktu_dibuat.tzinfo is None:
            waktu_dibuat = waktu_dibuat.replace(tzinfo=timezone.utc)
        selisih_detik = max((now - waktu_dibuat).total_seconds(), 0.0)
        return round(selisih_detik / 3600.0, 2)

    @classmethod
    def normalisasi_waktu_tunggu(cls, waktu_tunggu_jam: float) -> float:
        """
        Parameter 5: Waktu Tunggu (Skala 0-100).
        Mencegah starvation: Laporan yang lama tidak ditangani akan naik prioritasnya secara bertahap.
        Laju kenaikan: 2.5 poin per jam (mencapai skor 100 setelah 40 jam).
        """
        skor = waktu_tunggu_jam * 2.5
        return round(min(skor, 100.0), 2)

    @classmethod
    def tentukan_kategori_prioritas(cls, skor: float) -> KategoriPrioritas:
        """Mengelompokkan skor (0-100) menjadi P1, P2, atau P3."""
        if skor >= cls.AMBANG_P1:
            return KategoriPrioritas.P1
        elif skor >= cls.AMBANG_P2:
            return KategoriPrioritas.P2
        return KategoriPrioritas.P3

    @classmethod
    def hitung_skor(
        cls,
        severity: Severity,
        bobot_kategori: float,
        skor_lokasi: Optional[float],
        skor_dampak: Optional[float],
        jumlah_pelapor: int,
        waktu_tunggu_jam: float,
    ) -> HasilKalkulasiPrioritas:
        """
        Menghitung Priority Score 0-100 dari 5 parameter spesifik.
        """
        p_bahaya = cls.normalisasi_tingkat_bahaya(severity, bobot_kategori)
        p_lokasi = cls.normalisasi_lokasi(skor_lokasi)
        p_dampak = cls.normalisasi_dampak(skor_dampak)
        p_pelapor = cls.normalisasi_pelapor(jumlah_pelapor)
        p_waktu = cls.normalisasi_waktu_tunggu(waktu_tunggu_jam)

        # Perhitungan pembobotan
        total_skor = (
            (p_bahaya * cls.BOBOT_BAHAYA) +
            (p_lokasi * cls.BOBOT_LOKASI) +
            (p_dampak * cls.BOBOT_DAMPAK) +
            (p_pelapor * cls.BOBOT_PELAPOR) +
            (p_waktu * cls.BOBOT_WAKTU)
        )
        total_skor = round(min(max(total_skor, 0.0), 100.0), 2)
        kategori = cls.tentukan_kategori_prioritas(total_skor)

        return HasilKalkulasiPrioritas(
            skor_akhir=total_skor,
            kategori_prioritas=kategori,
            param_tingkat_bahaya=p_bahaya,
            param_dampak_lokasi=p_lokasi,
            param_jumlah_pelapor=jumlah_pelapor,
            param_frekuensi_serupa=jumlah_pelapor,
            param_waktu_tunggu_jam=waktu_tunggu_jam,
        )

    @classmethod
    def kalkulasi_laporan(
        cls,
        db: Session,
        laporan: Laporan,
        radius_meter: float = 100.0,
    ) -> HasilKalkulasiPrioritas:
        """
        Menghitung dan memperbarui skor prioritas suatu laporan langsung dari database.
        Mencakup pencarian laporan serupa via PostGIS ST_DWithin (KF-17).
        """
        # 1. Bobot kategori dari tabel master
        bobot_kategori = 1.0
        if laporan.kategori:
            bobot_kategori = laporan.kategori.bobot_bahaya_default
        else:
            kat = db.scalar(select(KategoriLaporan).where(KategoriLaporan.id == laporan.kategori_id))
            if kat:
                bobot_kategori = kat.bobot_bahaya_default

        # 2. Deteksi jumlah laporan serupa di lokasi berdekatan (radius spasial PostGIS)
        jumlah_pelapor = 1
        if laporan.lokasi and laporan.lokasi.koordinat is not None:
            laporan_serupa_count = db.scalar(
                select(func.count(Laporan.id))
                .join(LokasiLaporan, Laporan.id == LokasiLaporan.laporan_id)
                .where(
                    Laporan.kategori_id == laporan.kategori_id,
                    Laporan.id != laporan.id,
                    Laporan.status.in_([StatusLaporan.DIKIRIM, StatusLaporan.DIPROSES]),
                    ST_DWithin(LokasiLaporan.koordinat, laporan.lokasi.koordinat, radius_meter),
                )
            ) or 0
            # Total pelapor = 1 (laporan ini) + laporan aktif di sekitarnya
            jumlah_pelapor = 1 + laporan_serupa_count

        # 3. Hitung waktu tunggu
        waktu_jam = cls.hitung_waktu_tunggu_jam(laporan.dibuat_pada)

        # 4. Kalkulasi skor
        hasil = cls.hitung_skor(
            severity=laporan.severity,
            bobot_kategori=bobot_kategori,
            skor_lokasi=laporan.param_dampak_lokasi,
            skor_dampak=None,  # dapat diisi berdasarkan klasifikasi lanjutan
            jumlah_pelapor=jumlah_pelapor,
            waktu_tunggu_jam=waktu_jam,
        )

        # 5. Tuliskan kembali ke entitas Laporan
        laporan.skor_prioritas = hasil.skor_akhir
        laporan.kategori_prioritas = hasil.kategori_prioritas
        laporan.param_tingkat_bahaya = hasil.param_tingkat_bahaya
        laporan.param_dampak_lokasi = hasil.param_dampak_lokasi
        laporan.param_jumlah_pelapor = hasil.param_jumlah_pelapor
        laporan.param_frekuensi_serupa = hasil.param_frekuensi_serupa
        laporan.param_waktu_tunggu_jam = hasil.param_waktu_tunggu_jam

        return hasil
