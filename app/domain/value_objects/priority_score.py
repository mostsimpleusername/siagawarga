from dataclasses import dataclass
from app.domain.enums import KategoriPrioritas

@dataclass(frozen=True)
class PriorityScoreResult:
    skor_prioritas: float
    kategori_prioritas: KategoriPrioritas
    tingkat_bahaya: float
    faktor_lokasi: float
    dampak: float
    jumlah_pelapor: int
    waktu_tunggu_jam: float
    rincian_skor: dict
