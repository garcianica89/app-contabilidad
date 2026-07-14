import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from datetime import date
from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.domain.models.nomina import NominaConfig, NominaPeriodo, NominaDetalle
from app.domain.models.empleado import Empleado
from app.domain.models.usuario import Usuario
from app.service.accounting.accounting_engine import AccountingEngine

router = APIRouter()

# ─── Schemas ───
class NominaConfigCreate(BaseModel):
    salario_minimo: float = 0
    inss_patronal_rate: float = 0.225
    inss_laboral_rate: float = 0.07
    ir_tramos: dict | None = None
    aguinaldo_dias: int = 30

class NominaConfigResponse(NominaConfigCreate):
    id: str
    class Config: from_attributes = True

class NominaPeriodoCreate(BaseModel):
    codigo: str = Field(max_length=20)
    fecha_inicio: date
    fecha_fin: date
    fecha_pago: date

class NominaDetalleResponse(BaseModel):
    id: str
    empleado_id: str
    dias_trabajados: int
    salario_base: float
    horas_extra: float
    bonos: float
    comisiones: float
    total_devengado: float
    inss_laboral: float
    ir: float
    otras_deducciones: float
    total_deducciones: float
    neto: float
    class Config: from_attributes = True

class NominaPeriodoResponse(BaseModel):
    id: str
    codigo: str
    fecha_inicio: date
    fecha_fin: date
    fecha_pago: date
    estado: str
    total_devengado: float
    total_deducciones: float
    total_neto: float
    detalles: list[NominaDetalleResponse] = []
    class Config: from_attributes = True

class ProcesarNominaRequest(BaseModel):
    horas_extra: dict[str, float] = {}  # empleado_id -> monto
    bonos: dict[str, float] = {}
    comisiones: dict[str, float] = {}
    otras_deducciones: dict[str, float] = {}

# ─── Config ───
@router.get("/config", response_model=NominaConfigResponse)
async def get_nomina_config(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_VER"))],
):
    r = await db.execute(select(NominaConfig).where(NominaConfig.empresa_id == user.empresa_id))
    obj = r.scalar_one_or_none()
    if not obj:
        obj = NominaConfig(empresa_id=user.empresa_id)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
    return obj

@router.put("/config", response_model=NominaConfigResponse)
async def update_nomina_config(
    data: NominaConfigCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_EDITAR"))],
):
    r = await db.execute(select(NominaConfig).where(NominaConfig.empresa_id == user.empresa_id))
    obj = r.scalar_one_or_none()
    if not obj:
        obj = NominaConfig(empresa_id=user.empresa_id)
        db.add(obj)
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj

# ─── Periodos ───
@router.get("/periodos", response_model=list[NominaPeriodoResponse])
async def list_periodos(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_VER"))],
    estado: str | None = Query(None),
):
    q = select(NominaPeriodo).where(NominaPeriodo.empresa_id == user.empresa_id)
    if estado:
        q = q.where(NominaPeriodo.estado == estado)
    q = q.order_by(NominaPeriodo.fecha_inicio.desc())
    r = await db.execute(q)
    return r.scalars().all()

@router.post("/periodos", response_model=NominaPeriodoResponse, status_code=201)
async def create_periodo(
    data: NominaPeriodoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_CREAR"))],
):
    obj = NominaPeriodo(empresa_id=user.empresa_id, **data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.get("/periodos/{id}", response_model=NominaPeriodoResponse)
async def get_periodo(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_VER"))],
):
    r = await db.execute(
        select(NominaPeriodo).where(NominaPeriodo.id == id, NominaPeriodo.empresa_id == user.empresa_id)
    )
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(404)
    return obj

@router.post("/periodos/{id}/procesar", response_model=NominaPeriodoResponse)
async def procesar_nomina(
    id: uuid.UUID,
    data: ProcesarNominaRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_CREAR"))],
):
    r = await db.execute(
        select(NominaPeriodo).where(NominaPeriodo.id == id, NominaPeriodo.empresa_id == user.empresa_id)
    )
    periodo = r.scalar_one_or_none()
    if not periodo:
        raise HTTPException(404)
    if periodo.estado != "BORRADOR":
        raise HTTPException(400, "Solo se puede procesar periodos en BORRADOR")

    config_r = await db.execute(select(NominaConfig).where(NominaConfig.empresa_id == user.empresa_id))
    config = config_r.scalar_one_or_none()

    empleados_r = await db.execute(
        select(Empleado).where(Empleado.empresa_id == user.empresa_id, Empleado.estado == "ACTIVO")
    )
    empleados = empleados_r.scalars().all()

    inss_laboral_rate = float(config.inss_laboral_rate) if config else 0.07
    ir_tramos = config.ir_tramos if config and config.ir_tramos else []

    # Delete existing details
    await db.execute(
        select(NominaDetalle).where(NominaDetalle.nomina_periodo_id == periodo.id)
    )

    total_devengado = 0
    total_deducciones = 0

    for emp in empleados:
        sb = float(emp.salario_base)
        he = data.horas_extra.get(str(emp.id), 0)
        bn = data.bonos.get(str(emp.id), 0)
        cm = data.comisiones.get(str(emp.id), 0)
        od = data.otras_deducciones.get(str(emp.id), 0)

        devengado = sb + he + bn + cm
        inss_l = round(devengado * inss_laboral_rate, 2)

        # IR calculation
        ir = 0
        if ir_tramos:
            anual = devengado * 12
            for tramo in (ir_tramos if isinstance(ir_tramos, list) else []):
                desde = tramo.get("desde", 0)
                hasta = tramo.get("hasta", float("inf"))
                tasa = tramo.get("tasa", 0)
                if desde <= anual <= hasta:
                    ir_mensual = (anual * tasa / 12) if tramo.get("tipo") == "anual" else (anual - desde) * tasa / 12
                    ir = round(ir_mensual, 2)
                    break

        deducciones = inss_l + ir + od
        neto = round(devengado - deducciones, 2)

        detalle = NominaDetalle(
            nomina_periodo_id=periodo.id,
            empleado_id=emp.id,
            dias_trabajados=30,
            salario_base=sb,
            horas_extra=he,
            bonos=bn,
            comisiones=cm,
            total_devengado=round(devengado, 2),
            inss_laboral=inss_l,
            ir=ir,
            otras_deducciones=od,
            total_deducciones=round(deducciones, 2),
            neto=neto,
        )
        db.add(detalle)
        total_devengado += devengado
        total_deducciones += deducciones

    periodo.total_devengado = round(total_devengado, 2)
    periodo.total_deducciones = round(total_deducciones, 2)
    periodo.total_neto = round(total_devengado - total_deducciones, 2)
    periodo.estado = "PROCESADA"

    engine = AccountingEngine(db)
    data = {
        'periodo_codigo': periodo.codigo,
        'fecha_inicio': periodo.fecha_inicio.isoformat(),
        'fecha_fin': periodo.fecha_fin.isoformat(),
        'fecha_pago': periodo.fecha_pago.isoformat(),
        'total_devengado': periodo.total_devengado,
        'total_deducciones': periodo.total_deducciones,
        'total_neto': periodo.total_neto,
    }
    asiento_result = await engine.generate_from_event(
        event_type='NOMINA',
        module='nomina',
        data=data,
        company_id=user.empresa_id,
        document_id=periodo.id,
        user_id=user.id,
    )
    if asiento_result:
        periodo.asiento_id = asiento_result.get('asiento_id')

    await db.commit()
    await db.refresh(periodo)
    return periodo

@router.post("/periodos/{id}/pagar", response_model=NominaPeriodoResponse)
async def pagar_nomina(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(require_permission("CONFIG_CREAR"))],
):
    r = await db.execute(
        select(NominaPeriodo).where(NominaPeriodo.id == id, NominaPeriodo.empresa_id == user.empresa_id)
    )
    periodo = r.scalar_one_or_none()
    if not periodo:
        raise HTTPException(404)
    if periodo.estado != "PROCESADA":
        raise HTTPException(400, "Solo se puede pagar periodos procesados")

    from app.service.accounting.accounting_engine import AccountingEngine
    engine = AccountingEngine(db)
    data = {
        'periodo_codigo': periodo.codigo,
        'monto': periodo.total_neto,
        'fecha': periodo.fecha_pago.isoformat(),
    }
    await engine.generate_from_event(
        event_type='PAGO_NOMINA',
        module='nomina',
        data=data,
        company_id=user.empresa_id,
        document_id=periodo.id,
        user_id=user.id,
    )

    periodo.estado = "PAGADA"
    await db.commit()
    await db.refresh(periodo)
    return periodo
