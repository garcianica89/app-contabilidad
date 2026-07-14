from typing import Annotated
import uuid
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.domain.models.usuario import Usuario
from app.domain.accounting.models import CierreMensual, CierreFiscal, Account, AccountType, JournalType
from app.domain.models.periodo import PeriodoContable
from app.domain.models.ejercicio import EjercicioFiscal
from app.domain.models.asiento import Asiento, AsientoLinea
from app.service.balance_service import BalanceService

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

    # Recalcular saldos automaticamente al cerrar periodo
    try:
        svc = BalanceService(db, current_user.empresa_id)
        await svc.recalcular_saldos(periodo_id=periodo.id)
    except Exception:
        pass  # No debe impedir el cierre

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

    # Obtener periodo abierto para la fecha de cierre
    periodo = await _get_periodo_cierre(db, current_user.empresa_id, ejercicio.fecha_fin)
    if not periodo:
        raise HTTPException(400, "No hay periodo contable abierto para la fecha de cierre")

    # Generar asiento de cierre
    jt = await db.execute(
        select(JournalType).where(
            JournalType.company_id == current_user.empresa_id,
            JournalType.code == 'CI',
            JournalType.is_active == True,
        )
    )
    jt = jt.scalar_one_or_none()

    asiento_cierre = None
    if jt:
        prefijo = jt.prefijo or 'CI'
        digitos = jt.digitos or 8
        old_corr = jt.correlativo_actual
        new_corr = old_corr + 1
        await db.execute(
            text("UPDATE journal_type SET correlativo_actual = :new WHERE id = :id AND correlativo_actual = :old"),
            {"new": new_corr, "id": jt.id, "old": old_corr},
        )
        numero_asiento = f"{prefijo}{new_corr:0{digitos}d}"

        asiento_cierre = Asiento(
            empresa_id=current_user.empresa_id,
            periodo_id=periodo.id,
            numero=numero_asiento,
            fecha=ejercicio.fecha_fin,
            concepto=f"Cierre ejercicio {ejercicio.codigo}",
            journal_type_id=jt.id,
            documento_tipo='CIERRE',
            estado='CONTABILIZADO',
            creado_por=current_user.id,
        )
        db.add(asiento_cierre)
        await db.flush()

        # Saldos de cuentas de resultado (INCOME, EXPENSE, COST)
        saldos = await db.execute(
            text("""
                SELECT acct.id AS account_id, acct.code, aty.financial_statement,
                       COALESCE(SUM(al.debe - al.haber), 0) AS saldo
                FROM asiento_linea al
                JOIN asiento a ON a.id = al.asiento_id
                JOIN account acct ON acct.id = al.cuenta_id
                JOIN account_type aty ON aty.id = acct.account_type_id
                WHERE a.empresa_id = :emp_id
                  AND aty.financial_statement IN ('INCOME', 'EXPENSE', 'COST')
                  AND a.fecha >= :fecha_ini AND a.fecha <= :fecha_fin
                GROUP BY acct.id, acct.code, aty.financial_statement
                HAVING ABS(COALESCE(SUM(al.debe - al.haber), 0)) > 0.005
            """),
            {
                "emp_id": current_user.empresa_id,
                "fecha_ini": ejercicio.fecha_inicio,
                "fecha_fin": ejercicio.fecha_fin,
            },
        )
        rows = saldos.fetchall()
        total_debe = 0
        total_haber = 0

        for row in rows:
            saldo = float(row.saldo)
            fs = row.financial_statement
            # INCOME accounts normally have credit balance → DEBIT to close
            # EXPENSE/COST accounts normally have debit balance → CREDIT to close
            if fs == 'INCOME' and saldo > 0:
                debe = saldo
                haber = 0
            elif fs in ('EXPENSE', 'COST') and saldo > 0:
                debe = 0
                haber = saldo
            elif fs == 'INCOME' and saldo < 0:
                debe = 0
                haber = abs(saldo)
            else:
                debe = abs(saldo) if saldo < 0 else 0
                haber = saldo if saldo > 0 else 0

            if debe > 0 or haber > 0:
                db.add(AsientoLinea(
                    asiento_id=asiento_cierre.id,
                    cuenta_id=row.account_id,
                    debe=debe,
                    haber=haber,
                    descripcion=f"Cierre {row.code}",
                ))
                total_debe += debe
                total_haber += haber

        # Contra-partida a cuenta_resultado_id
        diff = round(total_debe - total_haber, 2)
        if abs(diff) > 0.005:
            if diff > 0:
                db.add(AsientoLinea(
                    asiento_id=asiento_cierre.id,
                    cuenta_id=data.cuenta_resultado_id,
                    debe=0,
                    haber=diff,
                    descripcion="Contrapartida cierre resultado",
                ))
            else:
                db.add(AsientoLinea(
                    asiento_id=asiento_cierre.id,
                    cuenta_id=data.cuenta_resultado_id,
                    debe=abs(diff),
                    haber=0,
                    descripcion="Contrapartida cierre resultado",
                ))

        # Trasladar de cuenta_resultado a cuenta_utilidad
        db.add(AsientoLinea(
            asiento_id=asiento_cierre.id,
            cuenta_id=data.cuenta_resultado_id,
            debe=abs(diff) if diff < 0 else 0,
            haber=diff if diff > 0 else 0,
            descripcion="Traslado a utilidad",
        ))
        db.add(AsientoLinea(
            asiento_id=asiento_cierre.id,
            cuenta_id=data.cuenta_utilidad_id,
            debe=diff if diff > 0 else 0,
            haber=abs(diff) if diff < 0 else 0,
            descripcion=f"Utilidad/Perdida ejercicio {ejercicio.codigo}",
        ))

        await db.flush()

    cierre = CierreFiscal(
        empresa_id=current_user.empresa_id,
        ejercicio_id=data.ejercicio_id,
        estado='CERRADO',
        resultado_ejercicio=resultado,
        cuenta_resultado_id=data.cuenta_resultado_id,
        cuenta_utilidad_id=data.cuenta_utilidad_id,
        asiento_cierre_id=asiento_cierre.id if asiento_cierre else None,
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


@router.post("/fiscal/{cierre_id}/reabrir", response_model=CierreFiscalResponse)
async def reabrir_cierre_fiscal(
    cierre_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("CONTABILIDAD_CREAR"))],
):
    cierre = await db.get(CierreFiscal, cierre_id)
    if not cierre or cierre.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Cierre fiscal no encontrado")
    if cierre.estado != 'CERRADO':
        raise HTTPException(400, "El cierre fiscal no esta en estado CERRADO")

    ejercicio = await db.get(EjercicioFiscal, cierre.ejercicio_id)
    if ejercicio:
        ejercicio.cerrado = False

    cierre.estado = 'REABIERTO'
    cierre.reabierto_por = current_user.id
    cierre.reabierto_en = datetime.now()
    await db.commit()
    await db.refresh(cierre)
    return cierre


async def _calcular_resultado_ejercicio(
    db: AsyncSession, empresa_id: uuid.UUID, ejercicio_id: uuid.UUID
) -> float:
    from app.domain.models.asiento import AsientoLinea, Asiento
    from app.domain.accounting.models import Account, AccountType
    from app.domain.models.ejercicio import EjercicioFiscal

    ej = await db.get(EjercicioFiscal, ejercicio_id)
    if not ej:
        return 0

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
            Asiento.fecha >= ej.fecha_inicio,
            Asiento.fecha <= ej.fecha_fin,
        )
    )
    return float(r.scalar() or 0)


async def _get_periodo_cierre(
    db: AsyncSession, empresa_id: uuid.UUID, fecha: date
) -> PeriodoContable | None:
    r = await db.execute(
        select(PeriodoContable).where(
            PeriodoContable.empresa_id == empresa_id,
            PeriodoContable.cerrado == False,
            PeriodoContable.fecha_inicio <= fecha,
            PeriodoContable.fecha_fin >= fecha,
        ).limit(1)
    )
    return r.scalar_one_or_none()
