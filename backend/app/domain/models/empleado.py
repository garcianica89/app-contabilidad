import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class Cargo(Base):
    __tablename__ = "cargo"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    empleados = relationship("Empleado", back_populates="cargo")


class Empleado(Base):
    __tablename__ = "empleado"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("empresa.id"), nullable=False)
    departamento_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("departamento.id"))
    cargo_id: Mapped[uuid.UUID] = mapped_column(Uuid(), ForeignKey("cargo.id"))
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    cedula: Mapped[str | None] = mapped_column(String(20), unique=True)
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)
    fecha_contratacion: Mapped[date] = mapped_column(Date, nullable=False)
    salario_base: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    tipo_contrato: Mapped[str] = mapped_column(String(20), default="INDEFINIDO")
    estado: Mapped[str] = mapped_column(String(20), default="ACTIVO")
    direccion: Mapped[str | None] = mapped_column(Text)
    telefono: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    departamento = relationship("Departamento", back_populates="empleados")
    cargo = relationship("Cargo", back_populates="empleados")
