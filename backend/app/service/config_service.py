from decimal import Decimal
from datetime import date, datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.moneda import Moneda
from app.domain.models.tipo_cambio_hist import TipoCambioHist
from app.domain.models.parametro import Parametro


async def convert_currency(
    db: AsyncSession,
    amount: Decimal,
    from_currency_id: uuid.UUID,
    to_currency_id: uuid.UUID,
    empresa_id: uuid.UUID,
    fecha: date | None = None,
) -> Decimal:
    if from_currency_id == to_currency_id:
        return amount

    rate = await get_exchange_rate(db, from_currency_id, to_currency_id, empresa_id, fecha)
    return amount * rate


async def get_exchange_rate(
    db: AsyncSession,
    from_currency_id: uuid.UUID,
    to_currency_id: uuid.UUID,
    empresa_id: uuid.UUID,
    fecha: date | None = None,
) -> Decimal:
    from_curr = await db.get(Moneda, from_currency_id)
    to_curr = await db.get(Moneda, to_currency_id)
    if not from_curr or not to_curr:
        raise ValueError("Moneda no encontrada")

    if fecha:
        result = await db.execute(
            select(TipoCambioHist)
            .where(
                TipoCambioHist.empresa_id == empresa_id,
                TipoCambioHist.moneda_id == from_currency_id,
                TipoCambioHist.fecha <= fecha,
            )
            .order_by(TipoCambioHist.fecha.desc())
            .limit(1)
        )
        hist = result.scalar_one_or_none()
        if hist:
            return hist.tasa_compra / to_curr.tasa_cambio if to_curr.tasa_cambio else Decimal("1.0")

    return Decimal(str(from_curr.tasa_cambio)) / Decimal(str(to_curr.tasa_cambio)) if to_curr.tasa_cambio else Decimal("1.0")


async def get_parameter(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    grupo: str,
    clave: str,
    default: str | None = None,
) -> str | None:
    result = await db.execute(
        select(Parametro).where(
            Parametro.empresa_id == empresa_id,
            Parametro.grupo == grupo,
            Parametro.clave == clave,
        )
    )
    p = result.scalar_one_or_none()
    return p.valor if p else default
