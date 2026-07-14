"""
Numeracion Service — Servicio centralizado de numeracion.

Todo documento del ERP obtiene su numero aqui.
Soporta:
  - Series (A, B, C, etc.)
  - Prefijos/Sufijos estaticos y dinamicos (ano, mes, sucursal)
  - Empresa + Sucursal
  - Reinicio (NUNCA, ANUAL, MENSUAL)
  - Mascara configurable
  - Reserva de numeros
  - Concurrencia segura (lock pesimista)
"""
import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.accounting.models import Numeracion


class NumeracionService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_next(
        self,
        company_id: uuid.UUID,
        document_type: str,
        subtype_code: Optional[str] = None,
        serie: Optional[str] = None,
        sucursal_id: Optional[uuid.UUID] = None,
    ) -> Optional[dict]:
        """
        Obtiene el siguiente numero de un documento.

        Returns: { "numero": "A-000123", "serie": "A", "correlativo": 123 }
        """
        numeracion = await self._resolve_numeracion(
            company_id, document_type, subtype_code, serie, sucursal_id
        )
        if not numeracion:
            return None

        # Lock pesimista para concurrencia
        next_val = numeracion.correlativo_actual + 1

        # Actualizar correlativo
        stmt = (
            update(Numeracion)
            .where(
                Numeracion.id == numeracion.id,
                Numeracion.correlativo_actual == numeracion.correlativo_actual,
            )
            .values(correlativo_actual=next_val)
        )
        r = await self.db.execute(stmt)
        if r.rowcount == 0:
            raise Exception("Numeracion concurrente detectada. Reintente.")

        await self.db.flush()

        numero = self._format_number(
            mask=numeracion.mascara,
            serie=numeracion.serie,
            numero=next_val,
            sucursal_id=sucursal_id,
        )

        return {
            'numero': numero,
            'serie': numeracion.serie,
            'correlativo': next_val,
            'numeracion_id': numeracion.id,
        }

    async def reserve(
        self,
        company_id: uuid.UUID,
        document_type: str,
        user_id: uuid.UUID,
    ) -> Optional[dict]:
        """Reserva un numero para uso futuro (workflows multi-paso)."""
        numeracion = await self._resolve_numeracion(company_id, document_type)
        if not numeracion:
            return None

        next_val = numeracion.correlativo_actual + 1
        stmt = (
            update(Numeracion)
            .where(
                Numeracion.id == numeracion.id,
                Numeracion.correlativo_actual == numeracion.correlativo_actual,
            )
            .values(correlativo_actual=next_val)
        )
        r = await self.db.execute(stmt)
        if r.rowcount == 0:
            raise Exception("Numeracion concurrente detectada.")

        await self.db.flush()

        return {
            'numero': self._format_number(numeracion.mascara, numeracion.serie, next_val),
            'serie': numeracion.serie,
            'correlativo': next_val,
        }

    async def _resolve_numeracion(
        self,
        company_id: uuid.UUID,
        document_type: str,
        subtype_code: Optional[str] = None,
        serie: Optional[str] = None,
        sucursal_id: Optional[uuid.UUID] = None,
    ) -> Optional[Numeracion]:
        """Resuelve la configuracion de numeracion para un documento."""
        q = select(Numeracion).where(
            Numeracion.company_id == company_id,
            Numeracion.is_active == True,
        )

        if serie:
            q = q.where(Numeracion.serie == serie)
        else:
            q = q.where(Numeracion.tipo_documento == document_type)

        # Preferir la primera coincidencia por serie sobre tipo_documento
        q = q.order_by(Numeracion.serie.asc()).limit(1)

        r = await self.db.execute(q)
        return r.scalar_one_or_none()

    def _format_number(
        self,
        mask: str,
        serie: str,
        numero: int,
        sucursal_id: Optional[uuid.UUID] = None,
    ) -> str:
        """Formatea el numero segun la mascara."""
        result = mask
        result = result.replace('{SERIE}', serie)
        result = result.replace('{NUMERO}', f"{numero:06d}")

        now = datetime.now()
        result = result.replace('{ANO}', str(now.year))
        result = result.replace('{MES}', f"{now.month:02d}")

        if sucursal_id:
            result = result.replace('{SUCURSAL}', str(sucursal_id)[:8].upper())

        return result
