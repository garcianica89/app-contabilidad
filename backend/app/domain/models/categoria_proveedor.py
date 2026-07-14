import uuid
from sqlalchemy import String, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Uuid
from app.core.database import Base


class CategoriaProveedor(Base):
    __tablename__ = "categoria_proveedor"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    cuenta_tercero_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("cuenta_contable.id"))
    cuenta_banco_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("cuenta_contable.id"))
    cuenta_caja_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), ForeignKey("cuenta_contable.id"))
