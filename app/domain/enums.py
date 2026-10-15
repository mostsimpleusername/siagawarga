"""
app/domain/enums.py
Semua enumerasi domain untuk SiagaWarga.
Diambil langsung dari Class Diagram PRD.
"""
import enum


class Peran(str, enum.Enum):
    """
    Peran pengguna (discriminator untuk STI Pengguna).
    - WARGA   : warga yang membuat laporan
    - PETUGAS : petugas yang mengelola laporan
    """
    WARGA = "WARGA"
    PETUGAS = "PETUGAS"


class StatusLaporan(str, enum.Enum):
    """
    Alur status laporan dari pengiriman hingga selesai (KF-08, KF-15).
    DIKIRIM -> DIPROSES -> SELESAI
                       -> DITOLAK
    """
    DIKIRIM = "DIKIRIM"      # Laporan baru, belum diverifikasi
    DIPROSES = "DIPROSES"    # Laporan sedang dalam penanganan
    SELESAI = "SELESAI"      # Laporan selesai ditangani
    DITOLAK = "DITOLAK"      # Laporan ditolak (duplikat / tidak valid)


class Severity(str, enum.Enum):
    """
    Tingkat keparahan permasalahan (Parameter 1 Priority Score - KF-12).
    Digunakan sebagai salah satu input kalkulasi skor prioritas.
    """
    RENDAH = "RENDAH"
    SEDANG = "SEDANG"
    TINGGI = "TINGGI"


class KategoriPrioritas(str, enum.Enum):
    """
    Kategori hasil kalkulasi Priority Score (KF-13).
    - P1 : Kritis  (skor 70-100) -> Tangani segera
    - P2 : Sedang  (skor 40-69)  -> Tangani dalam 24 jam
    - P3 : Rendah  (skor 0-39)   -> Antrean normal
    """
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


__all__ = ["Peran", "StatusLaporan", "Severity", "KategoriPrioritas"]
