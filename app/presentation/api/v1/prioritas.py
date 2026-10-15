"""
app/presentation/api/v1/prioritas.py
Router Antrean Prioritas Petugas (Sesuai Sequence Diagram 'Petugas - Mesin Prioritas'):
- GET /prioritas: Mengambil laporan aktif, menghitung ulang skor prioritas (waktu tunggu bertambah),
  dan mengembalikan daftar terurut serta ringkasan level P1, P2, P3.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.domain.entities.pengguna import Pengguna
from app.domain.enums import KategoriPrioritas
from app.infrastructure.database.session import get_db
from app.presentation.dependencies.auth import require_petugas
from app.use_cases.petugas import PetugasUseCase

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
    return PetugasUseCase.get_antrean_prioritas(
        db=db,
        q=q,
        kategori_prioritas=kategori_prioritas,
    )
