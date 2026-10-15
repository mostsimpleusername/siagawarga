"""
app/api/v1/prioritas.py
Router Antrean Prioritas Petugas (Sesuai Sequence Diagram 'Petugas - Mesin Prioritas'):
- GET /prioritas: Mengambil laporan aktif, menghitung ulang skor prioritas (waktu tunggu bertambah),
  dan mengembalikan daftar terurut serta ringkasan level P1, P2, P3.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_petugas
from app.models.enums import KategoriPrioritas, StatusLaporan
from app.models.laporan import Laporan
from app.models.pengguna import Pengguna
from app.schemas.laporan import LaporanDetailPetugasResponse
from app.use_cases.prioritas.priority_engine import DomainPriorityEngine

router = APIRouter(prefix="/prioritas", tags=["Manajemen & Antrean Prioritas"])


@router.get(
    "",
    summary="Ambil Antrean Prioritas Laporan (Sequence Diagram 2)",
    description=(
        "Mengambil semua laporan aktif (DIKIRIM / DIPROSES), memperbarui kalkulasi "
        "Priority Score secara real-time berdasarkan 5 parameter (termasuk pertambahan waktu tunggu), "
        "dan mengurutkannya dari skor tertinggi (P1)."
    ),
)
def get_antrean_prioritas(
    db: Annotated[Session, Depends(get_db)],
    current_petugas: Annotated[Pengguna, Depends(require_petugas)],
    q: Optional[str] = Query(None, description="Pencarian kata kunci deskripsi"),
    kategori_prioritas: Optional[KategoriPrioritas] = Query(None, description="Filter P1, P2, atau P3"),
):
    # 1. Query laporan aktif
    stmt = (
        select(Laporan)
        .where(Laporan.status.in_([StatusLaporan.DIKIRIM, StatusLaporan.DIPROSES]))
    )

    if q:
        stmt = stmt.where(Laporan.deskripsi.ilike(f"%{q}%"))

    laporan_list = db.scalars(stmt).all()

    # 2. Mesin Prioritas: Hitung ulang skor setiap laporan aktif secara on-the-fly
    for lap in laporan_list:
        DomainPriorityEngine.kalkulasi_laporan_db(db, lap)

    db.commit()  # Simpan hasil skor dan waktu tunggu terbaru

    # 3. Urutkan berdasarkan skor prioritas tertinggi (descending)
    laporan_terurut = sorted(
        laporan_list,
        key=lambda x: (x.skor_prioritas or 0.0),
        reverse=True,
    )

    # 4. Filter kategori prioritas jika diminta oleh query params
    if kategori_prioritas:
        laporan_terurut = [
            l for l in laporan_terurut if l.kategori_prioritas == kategori_prioritas
        ]

    # 5. Hitung ringkasan clustering per level untuk tampilan peta / dashboard
    cluster_summary = {
        "P1": sum(1 for l in laporan_terurut if l.kategori_prioritas == KategoriPrioritas.P1),
        "P2": sum(1 for l in laporan_terurut if l.kategori_prioritas == KategoriPrioritas.P2),
        "P3": sum(1 for l in laporan_terurut if l.kategori_prioritas == KategoriPrioritas.P3),
        "total_antrean": len(laporan_terurut),
    }

    return {
        "status": "success",
        "cluster_per_level": cluster_summary,
        "antrean": [
            LaporanDetailPetugasResponse.model_validate(l) for l in laporan_terurut
        ],
    }
