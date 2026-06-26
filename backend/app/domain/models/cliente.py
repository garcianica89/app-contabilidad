import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class Cliente(Base):
    __tablename__ = "cliente"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    codigo: Mapped[str | None] = mapped_column(String(20))
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    ruc: Mapped[str | None] = mapped_column(String(20))
    direccion: Mapped[str | None] = mapped_column(Text)
    telefono: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(100))
    saldo: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    limite_credito: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    activo: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
