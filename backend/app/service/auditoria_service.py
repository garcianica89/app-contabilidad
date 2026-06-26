import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.auditoria import Auditoria


class AuditoriaService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        usuario_id: uuid.UUID | None,
        empresa_id: uuid.UUID | None,
        tabla: str,
        registro_id: uuid.UUID,
        accion: str,
        valor_anterior: dict | None = None,
        valor_nuevo: dict | None = None,
        direccion_ip: str | None = None,
        user_agent: str | None = None,
    ) -> Auditoria:
        entry = Auditoria(
            usuario_id=usuario_id,
            empresa_id=empresa_id,
            tabla=tabla,
            registro_id=registro_id,
            accion=accion,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            direccion_ip=direccion_ip,
            user_agent=user_agent,
        )
        self.db.add(entry)
        return entry

    async def log_creacion(
        self, usuario_id: uuid.UUID, empresa_id: uuid.UUID,
        tabla: str, registro_id: uuid.UUID, valor: dict,
    ) -> Auditoria:
        return await self.log(
            usuario_id=usuario_id, empresa_id=empresa_id,
            tabla=tabla, registro_id=registro_id,
            accion="CREAR", valor_nuevo=valor,
        )

    async def log_actualizacion(
        self, usuario_id: uuid.UUID, empresa_id: uuid.UUID,
        tabla: str, registro_id: uuid.UUID,
        valor_anterior: dict, valor_nuevo: dict,
    ) -> Auditoria:
        return await self.log(
            usuario_id=usuario_id, empresa_id=empresa_id,
            tabla=tabla, registro_id=registro_id,
            accion="ACTUALIZAR",
            valor_anterior=valor_anterior, valor_nuevo=valor_nuevo,
        )

    async def log_eliminacion(
        self, usuario_id: uuid.UUID, empresa_id: uuid.UUID,
        tabla: str, registro_id: uuid.UUID, valor: dict,
    ) -> Auditoria:
        return await self.log(
            usuario_id=usuario_id, empresa_id=empresa_id,
            tabla=tabla, registro_id=registro_id,
            accion="ELIMINAR", valor_anterior=valor,
        )

    async def log_asiento(
        self, usuario_id: uuid.UUID, empresa_id: uuid.UUID,
        asiento_id: uuid.UUID, asiento_data: dict,
    ) -> Auditoria:
        return await self.log_creacion(
            usuario_id=usuario_id, empresa_id=empresa_id,
            tabla="asiento", registro_id=asiento_id,
            valor=asiento_data,
        )
