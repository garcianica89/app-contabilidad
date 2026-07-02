from typing import Annotated
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.domain.models.usuario import Usuario
from app.domain.accounting.models import CierreMensual, CierreFiscal
from app.domain.models.periodo import PeriodoContable
from app.domain.models.ejercicio import EjercicioFiscal

router = APIRouter()


# ─── Schemas ───

class CierreMensualCreate(BaseModel):
    periodo_id: uuid.UUID
    observaciones: str | None = None

class CierreMensualResponse(BaseModel):
    id: str
    empresa_id: str
    periodo_id: str
    estado: str
    cerrado_por: str | None
    cerrado_en: datetime | None
    reabierto_por: str | None
    reabierto_en: datetime | None
    observaciones: str | None
    created_at: datetime
    class Config: from_attributes = True

class CierreFiscalCreate(BaseModel):
    ejercicio_id: uuid.UUID
    cuenta_resultado_id: uuid.UUID
    cuenta_utilidad_id: uuid.UUID
    observaciones: str | None = None

class CierreFiscalResponse(BaseModel):
    id: str
    empresa_id: str
    ejercicio_id: str
    estado: str
    resultado_ejercicio: float | None
    cuenta_resultado_id: str | None
    cuenta_utilidad_id: str | None
    asiento_cierre_id: str | None
    asiento_apertura_id: str | None
    cerrado_por: str | None
    cerrado_en: datetime | None
    observaciones: str | None
    created_at: datetime
    class Config: from_attributes = True


# ─── Cierre Mensual ───

@router.get("/mensual", response_model=list[CierreMensualResponse])
async def listar_cierres_mensuales(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("CONTABILIDAD_VER"))],
):
    r = await db.execute(
        select(CierreMensual)
        .where(CierreMensual.empresa_id == current_user.empresa_id)
        .order_by(CierreMensual.created_at.desc())
    )
    return r.scalars().all()


@router.post("/mensual", response_model=CierreMensualResponse, status_code=201)
async def crear_cierre_mensual(
    data: CierreMensualCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("CONTABILIDAD_CREAR"))],
):
    periodo = await db.get(PeriodoContable, data.periodo_id)
    if not periodo or periodo.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Periodo no encontrado")
    if periodo.cerrado:
        raise HTTPException(400, "Periodo ya esta cerrado")

    existing = await db.execute(
        select(CierreMensual).where(
            CierreMensual.periodo_id == data.periodo_id,
            CierreMensual.estado.in_(['ABIERTO', 'CERRADO']),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Ya existe un cierre activo para este periodo")

    cierre = CierreMensual(
        empresa_id=current_user.empresa_id,
        periodo_id=data.periodo_id,
        estado='CERRADO',
        cerrado_por=current_user.id,
        cerrado_en=datetime.now(),
        observaciones=data.observaciones,
    )
    db.add(cierre)
    periodo.cerrado = True
    await db.commit()
    await db.refresh(cierre)
    return cierre


@router.post("/mensual/{cierre_id}/reabrir", response_model=CierreMensualResponse)
async def reabrir_cierre_mensual(
    cierre_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("CONTABILIDAD_CREAR"))],
):
    cierre = await db.get(CierreMensual, cierre_id)
    if not cierre or cierre.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Cierre no encontrado")
    if cierre.estado != 'CERRADO':
        raise HTTPException(400, "El cierre no esta en estado CERRADO")

    periodo = await db.get(PeriodoContable, cierre.periodo_id)
    if not periodo:
        raise HTTPException(404, "Periodo no encontrado")

    cierre.estado = 'REABIERTO'
    cierre.reabierto_por = current_user.id
    cierre.reabierto_en = datetime.now()
    periodo.cerrado = False
    await db.commit()
    await db.refresh(cierre)
    return cierre


# ─── Cierre Fiscal ───

@router.get("/fiscal", response_model=list[CierreFiscalResponse])
async def listar_cierres_fiscales(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("CONTABILIDAD_VER"))],
):
    r = await db.execute(
        select(CierreFiscal)
        .where(CierreFiscal.empresa_id == current_user.empresa_id)
        .order_by(CierreFiscal.created_at.desc())
    )
    return r.scalars().all()


@router.post("/fiscal", response_model=CierreFiscalResponse, status_code=201)
async def crear_cierre_fiscal(
    data: CierreFiscalCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("CONTABILIDAD_CREAR"))],
):
    ejercicio = await db.get(EjercicioFiscal, data.ejercicio_id)
    if not ejercicio or ejercicio.company_id != current_user.empresa_id:
        raise HTTPException(404, "Ejercicio fiscal no encontrado")
    if ejercicio.cerrado:
        raise HTTPException(400, "Ejercicio fiscal ya esta cerrado")

    existing = await db.execute(
        select(CierreFiscal).where(
            CierreFiscal.ejercicio_id == data.ejercicio_id,
            CierreFiscal.estado.in_(['EN_PROCESO', 'CERRADO']),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Ya existe un cierre fiscal activo para este ejercicio")

    resultado = await _calcular_resultado_ejercicio(db, current_user.empresa_id, data.ejercicio_id)

    cierre = CierreFiscal(
        empresa_id=current_user.empresa_id,
        ejercicio_id=data.ejercicio_id,
        estado='CERRADO',
        resultado_ejercicio=resultado,
        cuenta_resultado_id=data.cuenta_resultado_id,
        cuenta_utilidad_id=data.cuenta_utilidad_id,
        cerrado_por=current_user.id,
        cerrado_en=datetime.now(),
        observaciones=data.observaciones,
    )
    db.add(cierre)
    ejercicio.cerrado = True

    nuevo_ano = ejercicio.fecha_inicio.year + 1
    nuevo_ejercicio = EjercicioFiscal(
        company_id=current_user.empresa_id,
        codigo=str(nuevo_ano),
        nombre=f"Ejercicio {nuevo_ano}",
        fecha_inicio=ejercicio.fecha_fin.replace(year=nuevo_ano, month=1, day=1),
        fecha_fin=ejercicio.fecha_fin.replace(year=nuevo_ano),
        cerrado=False,
    )
    db.add(nuevo_ejercicio)

    await db.commit()
    await db.refresh(cierre)
    return cierre


async def _calcular_resultado_ejercicio(
    db: AsyncSession, empresa_id: uuid.UUID, ejercicio_id: uuid.UUID
) -> float:
    """Calcula resultado del ejercicio sumando saldos de cuentas de resultado."""
    from app.domain.models.asiento import AsientoLinea, Asiento, EjercicioFiscal
    from app.domain.accounting.models import Account, AccountType

    subq = select(Account.id).join(
        AccountType, Account.account_type_id == AccountType.id
    ).where(
        AccountType.financial_statement.in_(['INCOME', 'EXPENSE', 'COST']),
        Account.company_id == empresa_id,
    )

    r = await db.execute(
        select(func.sum(AsientoLinea.debe - AsientoLinea.haber))
        .select_from(AsientoLinea)
        .join(Asiento, AsientoLinea.asiento_id == Asiento.id)
        .where(
            Asiento.empresa_id == empresa_id,
            AsientoLinea.cuenta_id.in_(subq),
        )
    )
    return float(r.scalar() or 0)
