import uuid
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Uuid
from app.core.database import Base

usuario_rol = Table(
    "usuario_rol",
    Base.metadata,
    Column("usuario_id", Uuid(), ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True),
    Column("rol_id", Uuid(), ForeignKey("rol.id", ondelete="CASCADE"), primary_key=True),
)

rol_permiso = Table(
    "rol_permiso",
    Base.metadata,
    Column("rol_id", Uuid(), ForeignKey("rol.id", ondelete="CASCADE"), primary_key=True),
    Column("permiso_id", Uuid(), ForeignKey("permiso.id", ondelete="CASCADE"), primary_key=True),
)
