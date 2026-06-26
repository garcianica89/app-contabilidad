import uuid
from sqlalchemy import String, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Moneda(Base):
    __tablename__ = "moneda"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    simbolo: Mapped[str] = mapped_column(String(5), nullable=False)
    tasa_cambio: Mapped[float] = mapped_column(Numeric(14, 6), default=1.0)
    es_base: Mapped[bool] = mapped_column(Boolean, default=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
