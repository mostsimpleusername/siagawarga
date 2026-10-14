"""
app/services/prioritas.py
Service logika bisnis murni perhitungan Priority Score (0-100) dan klasifikasi P1/P2/P3.
"""
from dataclasses import dataclass
from app.models.enums import KategoriPrioritas


@dataclass(frozen=True)
class HasilPerhitunganPrioritas:
    skor_prioritas: float
    kategori_prioritas: KategoriPrioritas
    rincian_skor: dict


def hitung_priority_score(
    tingkat_bahaya: float,
    faktor_lokasi: float,
    dampak: float,
    jumlah_pelapor: int,
    waktu_tunggu_jam: float,
) -> HasilPerhitunganPrioritas:
    """
    Menghitung Priority Score (0-100) berdasarkan 5 parameter PRD:
    - Tingkat Bahaya (Bobot 30%)
    - Faktor Lokasi (Bobot 20%)
    - Dampak (Bobot 20%)
    - Jumlah Pelapor (Bobot 15%)
    - Waktu Tunggu (Bobot 15%)
    """
    # 1. Normalisasi parameter pelapor (1=20, 2=50, 3=75, >=5=100)
    if jumlah_pelapor <= 1:
        skor_pelapor = 20.0
    elif jumlah_pelapor == 2:
        skor_pelapor = 50.0
    elif jumlah_pelapor == 3:
        skor_pelapor = 75.0
    elif jumlah_pelapor == 4:
        skor_pelapor = 90.0
    else:
        skor_pelapor = 100.0

    # 2. Normalisasi waktu tunggu (kenaikan 2.5 poin/jam, max 100 pada 40 jam)
    skor_waktu = min(waktu_tunggu_jam * 2.5, 100.0)

    # 3. Validasi batas 0 - 100 untuk parameter input
    skor_bahaya = min(max(tingkat_bahaya, 0.0), 100.0)
    skor_lokasi = min(max(faktor_lokasi, 0.0), 100.0)
    skor_dampak = min(max(dampak, 0.0), 100.0)

    # 4. Pembobotan Multi-Kriteria
    bobot_bahaya = 0.30
    bobot_lokasi = 0.20
    bobot_dampak = 0.20
    bobot_pelapor = 0.15
    bobot_waktu = 0.15

    total_skor = (
        (skor_bahaya * bobot_bahaya)
        + (skor_lokasi * bobot_lokasi)
        + (skor_dampak * bobot_dampak)
        + (skor_pelapor * bobot_pelapor)
        + (skor_waktu * bobot_waktu)
    )
    total_skor = round(min(max(total_skor, 0.0), 100.0), 2)

    # 5. Klasifikasi Kategori Prioritas PRD
    if total_skor >= 70.0:
        kategori = KategoriPrioritas.P1
    elif total_skor >= 40.0:
        kategori = KategoriPrioritas.P2
    else:
        kategori = KategoriPrioritas.P3

    return HasilPerhitunganPrioritas(
        skor_prioritas=total_skor,
        kategori_prioritas=kategori,
        rincian_skor={
            "bahaya": skor_bahaya,
            "lokasi": skor_lokasi,
            "dampak": skor_dampak,
            "pelapor": skor_pelapor,
            "waktu": skor_waktu,
        },
    )
