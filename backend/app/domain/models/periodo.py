import uuid
from datetime import datetime, date
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class PeriodoContable(Base):
    __tablename__ = "periodo_contable"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(10), nullable=False)
    nombre: Mapped[str | None] = mapped_column(String(100))
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    cerrado: Mapped[bool] = mapped_column(Boolean, default=False)
    cerrado_por: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("usuario.id"))
    cerrado_en: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
