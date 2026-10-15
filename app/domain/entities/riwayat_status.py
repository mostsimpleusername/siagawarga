"""
app/domain/entities/riwayat_status.py
Model RiwayatStatus — audit trail perubahan status laporan (Agregasi).
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.base import Base
from app.domain.enums import StatusLaporan

if TYPE_CHECKING:
    from app.domain.entities.laporan import Laporan
    from app.domain.entities.pengguna import Petugas


class RiwayatStatus(Base):
    __tablename__ = "riwayat_status"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    laporan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laporan.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK ke Laporan yang statusnya berubah (CASCADE DELETE)",
    )
    petugas_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pengguna.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK ke Petugas pelaku perubahan (SET NULL jika petugas dihapus — KNF-12)",
    )
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
        return f"<RiwayatStatus laporan_id={self.laporan_id} {self.status_lama} → {self.status_baru} oleh={self.petugas_id}>"
