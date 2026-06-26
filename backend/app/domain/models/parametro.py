import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class Parametro(Base):
    __tablename__ = "parametro"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    grupo: Mapped[str] = mapped_column(String(50), nullable=False)
    clave: Mapped[str] = mapped_column(String(100), nullable=False)
    valor: Mapped[str | None] = mapped_column(Text)
    tipo_dato: Mapped[str] = mapped_column(String(20), default="TEXTO")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
