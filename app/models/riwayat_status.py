"""
app/models/riwayat_status.py
Model RiwayatStatus — audit trail perubahan status laporan.

Relasi (dari Class Diagram):
  Laporan (1) --mencatat-->◇ RiwayatStatus (0..*)  [AGREGASI]
  RiwayatStatus (0..*) --diubah oleh--> Petugas (0..1)

Agregasi: RiwayatStatus terkait erat dengan Laporan.
  → ondelete="CASCADE" pada FK laporan_id (dihapus jika laporan dihapus)
  → FK petugas_id ondelete="SET NULL" (riwayat tetap ada jika petugas dihapus)

Memenuhi KNF-12 (Auditability):
  Setiap perubahan status mencatat: waktu, identitas petugas,
  status sebelum, status sesudah, dan catatan.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import StatusLaporan

if TYPE_CHECKING:
    from app.models.laporan import Laporan
    from app.models.pengguna import Petugas


class RiwayatStatus(Base):
    """
    Riwayat perubahan status laporan (AGREGASI dengan Laporan).

    Atribut (dari Class Diagram):
      + statusLama  : StatusLaporan  (nullable untuk status awal DIKIRIM)
      + statusBaru  : StatusLaporan
      + catatan     : String
      + waktu       : DateTime
    """
    __tablename__ = "riwayat_status"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # FK ke Laporan (agregasi — CASCADE DELETE)
    laporan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laporan.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK ke Laporan yang statusnya berubah (CASCADE DELETE)",
    )

    # FK ke Petugas yang melakukan perubahan (KNF-12)
    # NULL jika perubahan dilakukan oleh sistem (misal: status awal DIKIRIM)
    petugas_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pengguna.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK ke Petugas pelaku perubahan (SET NULL jika petugas dihapus — KNF-12)",
    )

    # Atribut dari Class Diagram
    status_lama: Mapped[Optional[StatusLaporan]] = mapped_column(
        SAEnum(StatusLaporan, name="status_laporan_enum", create_type=False),
        nullable=True,
        comment="statusLama: status sebelum perubahan (NULL untuk entri pertama/DIKIRIM)",
    )
    status_baru: Mapped[StatusLaporan] = mapped_column(
        SAEnum(StatusLaporan, name="status_laporan_enum", create_type=False),
        nullable=False,
        comment="statusBaru: status setelah perubahan",
    )
    catatan: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="catatan: tindak lanjut atau alasan perubahan status (KF-16)",
    )
    waktu: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="waktu: timestamp perubahan status (KNF-12 — tidak dapat diubah)",
    )

    # -------------------------------------------------------
    # Relasi
    # -------------------------------------------------------
    laporan: Mapped["Laporan"] = relationship(
        "Laporan",
        back_populates="riwayat_status",
    )
    petugas: Mapped[Optional["Petugas"]] = relationship(
        "Petugas",
        back_populates="riwayat_diubah",
        foreign_keys=[petugas_id],
    )

    def __repr__(self) -> str:
        return (
            f"<RiwayatStatus laporan_id={self.laporan_id} "
            f"{self.status_lama} → {self.status_baru} "
            f"oleh={self.petugas_id}>"
        )
