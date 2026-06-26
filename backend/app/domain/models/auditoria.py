import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy import Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("usuario.id"))
    empresa_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("empresa.id"))
    tabla: Mapped[str] = mapped_column(String(50), nullable=False)
    registro_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    accion: Mapped[str] = mapped_column(String(10), nullable=False)
    valor_anterior: Mapped[dict | None] = mapped_column(JSON)
    valor_nuevo: Mapped[dict | None] = mapped_column(JSON)
    direccion_ip: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
