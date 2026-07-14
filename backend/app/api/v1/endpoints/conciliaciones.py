from typing import Annotated
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.banco import CuentaBanco, MovimientoBanco
from app.domain.models.conciliacion import ConciliacionBancaria, PartidaConciliacion
from app.domain.models.periodo import PeriodoContable

router = APIRouter()


class ConciliacionCreate(BaseModel):
    cuenta_id: uuid.UUID
    periodo_id: uuid.UUID
    saldo_inicial_banco: float = 0
    saldo_inicial_libro: float = 0
    saldo_final_banco: float
    observaciones: str | None = None


class PartidaResponse(BaseModel):
    id: str
    conciliacion_id: str
    movimiento_banco_id: str | None
    tipo: str
    concepto: str
    referencia: str | None
    fecha: date
    monto: float
    conciliado: bool
    observacion: str | None

    class Config:
        from_attributes = True


class ConciliacionResponse(BaseModel):
    id: str
    cuenta_id: str
    cuenta_nombre: str | None = None
    periodo_id: str | None = None
    periodo_nombre: str | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    saldo_inicial_banco: float = 0
    saldo_inicial_libro: float = 0
    saldo_final_banco: float
    saldo_final_libro: float
    diferencia: float
    estado: str
    observaciones: str | None
    created_at: datetime
    cerrada_at: datetime | None
    partidas: list[PartidaResponse] = []

    class Config:
        from_attributes = True


@router.get("/", response_model=list[ConciliacionResponse])
async def listar_conciliaciones(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    cuenta_id: uuid.UUID | None = None,
):
    query = select(ConciliacionBancaria).where(
        ConciliacionBancaria.empresa_id == current_user.empresa_id
    ).order_by(ConciliacionBancaria.fecha_fin.desc().nulls_last())
    if cuenta_id:
        query = query.where(ConciliacionBancaria.cuenta_id == cuenta_id)

    result = await db.execute(query)
    conciliaciones = result.scalars().all()

    response = []
    for c in conciliaciones:
        cuenta = await db.get(CuentaBanco, c.cuenta_id)
        periodo = await db.get(PeriodoContable, c.periodo_id) if c.periodo_id else None
        partidas = await db.execute(
            select(PartidaConciliacion).where(PartidaConciliacion.conciliacion_id == c.id)
        )
        response.append(ConciliacionResponse(
            id=str(c.id),
            cuenta_id=str(c.cuenta_id),
            cuenta_nombre=f"{cuenta.banco} - {cuenta.numero_cuenta}" if cuenta else None,
            periodo_id=str(c.periodo_id) if c.periodo_id else None,
            periodo_nombre=periodo.nombre if periodo else None,
            fecha_inicio=c.fecha_inicio,
            fecha_fin=c.fecha_fin,
            saldo_inicial_banco=float(c.saldo_inicial_banco),
            saldo_inicial_libro=float(c.saldo_inicial_libro),
            saldo_final_banco=float(c.saldo_final_banco),
            saldo_final_libro=float(c.saldo_final_libro),
            diferencia=float(c.diferencia),
            estado=c.estado,
            observaciones=c.observaciones,
            created_at=c.created_at,
            cerrada_at=c.cerrada_at,
            partidas=[PartidaResponse(
                id=str(p.id),
                conciliacion_id=str(p.conciliacion_id),
                movimiento_banco_id=str(p.movimiento_banco_id) if p.movimiento_banco_id else None,
                tipo=p.tipo,
                concepto=p.concepto,
                referencia=p.referencia,
                fecha=p.fecha,
                monto=float(p.monto),
                conciliado=p.conciliado,
                observacion=p.observacion,
            ) for p in partidas.scalars().all()],
        ))
    return response


@router.post("/", response_model=ConciliacionResponse, status_code=201)
async def crear_conciliacion(
    data: ConciliacionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    cuenta = await db.get(CuentaBanco, data.cuenta_id)
    if not cuenta or cuenta.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    periodo = await db.get(PeriodoContable, data.periodo_id)
    if not periodo or periodo.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")

    # Validate anterior periodo mes is EN_FIRME
    anterior = await db.execute(select(PeriodoContable).where(
        PeriodoContable.empresa_id == current_user.empresa_id,
        PeriodoContable.fecha_fin == periodo.fecha_inicio - __import__('datetime').timedelta(days=1),
    ))
    anterior_periodo = anterior.scalar_one_or_none()
    if anterior_periodo:
        conc_anterior = await db.execute(select(ConciliacionBancaria).where(
            ConciliacionBancaria.cuenta_id == data.cuenta_id,
            ConciliacionBancaria.periodo_id == anterior_periodo.id,
        ))
        c_ant = conc_anterior.scalar_one_or_none()
        if c_ant and c_ant.estado != "EN_FIRME":
            raise HTTPException(status_code=400, detail=f"El periodo anterior ({anterior_periodo.nombre}) debe estar en estado EN_FIRME")

    # Check no existing conciliacion for this cuenta+periodo
    exist = await db.execute(select(ConciliacionBancaria).where(
        ConciliacionBancaria.cuenta_id == data.cuenta_id,
        ConciliacionBancaria.periodo_id == data.periodo_id,
    ))
    if exist.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe una conciliacion para esta cuenta y periodo")

    fecha_inicio = periodo.fecha_inicio
    fecha_fin = periodo.fecha_fin

    # Pull LIBRO movements (from system)
    movs_libro = await db.execute(
        select(MovimientoBanco).where(
            MovimientoBanco.empresa_id == current_user.empresa_id,
            MovimientoBanco.cuenta_id == data.cuenta_id,
            MovimientoBanco.origen == 'LIBRO',
            MovimientoBanco.fecha.between(fecha_inicio, fecha_fin),
        ).order_by(MovimientoBanco.fecha)
    )
    libro_movs = movs_libro.scalars().all()

    # Pull BANCO movements (imported)
    movs_banco = await db.execute(
        select(MovimientoBanco).where(
            MovimientoBanco.empresa_id == current_user.empresa_id,
            MovimientoBanco.cuenta_id == data.cuenta_id,
            MovimientoBanco.origen == 'BANCO',
            MovimientoBanco.fecha.between(fecha_inicio, fecha_fin),
        ).order_by(MovimientoBanco.fecha)
    )
    banco_movs = movs_banco.scalars().all()

    saldo_final_libro = float(libro_movs[-1].saldo) if libro_movs else data.saldo_inicial_libro
    diferencia = round(abs(data.saldo_final_banco - saldo_final_libro), 2)

    conciliacion = ConciliacionBancaria(
        empresa_id=current_user.empresa_id,
        cuenta_id=data.cuenta_id,
        periodo_id=data.periodo_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        saldo_inicial_banco=data.saldo_inicial_banco,
        saldo_inicial_libro=data.saldo_inicial_libro,
        saldo_final_banco=data.saldo_final_banco,
        saldo_final_libro=saldo_final_libro,
        diferencia=diferencia,
        estado="TEMPORAL",
        observaciones=data.observaciones,
    )
    db.add(conciliacion)
    await db.flush()

    # Create partidas from LIBRO movements
    for mov in libro_movs:
        partida = PartidaConciliacion(
            conciliacion_id=conciliacion.id,
            movimiento_banco_id=mov.id,
            tipo="LIBRO",
            concepto=mov.concepto,
            referencia=mov.numero_documento,
            fecha=mov.fecha.date() if hasattr(mov.fecha, 'date') else mov.fecha,
            monto=float(mov.entrada - mov.salida),
            conciliado=False,
        )
        db.add(partida)

    # Create partidas from BANCO movements
    for mov in banco_movs:
        partida = PartidaConciliacion(
            conciliacion_id=conciliacion.id,
            movimiento_banco_id=mov.id,
            tipo="BANCO",
            concepto=mov.concepto,
            referencia=mov.numero_documento,
            fecha=mov.fecha.date() if hasattr(mov.fecha, 'date') else mov.fecha,
            monto=float(mov.entrada - mov.salida),
            conciliado=False,
        )
        db.add(partida)

    await db.commit()
    await db.refresh(conciliacion)

    partidas = await db.execute(
        select(PartidaConciliacion).where(PartidaConciliacion.conciliacion_id == conciliacion.id)
    )
    return ConciliacionResponse(
        id=str(conciliacion.id),
        cuenta_id=str(conciliacion.cuenta_id),
        cuenta_nombre=f"{cuenta.banco} - {cuenta.numero_cuenta}",
        periodo_id=str(conciliacion.periodo_id) if conciliacion.periodo_id else None,
        periodo_nombre=periodo.nombre,
        fecha_inicio=conciliacion.fecha_inicio,
        fecha_fin=conciliacion.fecha_fin,
        saldo_inicial_banco=float(conciliacion.saldo_inicial_banco),
        saldo_inicial_libro=float(conciliacion.saldo_inicial_libro),
        saldo_final_banco=float(conciliacion.saldo_final_banco),
        saldo_final_libro=float(conciliacion.saldo_final_libro),
        diferencia=float(conciliacion.diferencia),
        estado=conciliacion.estado,
        observaciones=conciliacion.observaciones,
        created_at=conciliacion.created_at,
        cerrada_at=conciliacion.cerrada_at,
        partidas=[PartidaResponse(
            id=str(p.id),
            conciliacion_id=str(p.conciliacion_id),
            movimiento_banco_id=str(p.movimiento_banco_id) if p.movimiento_banco_id else None,
            tipo=p.tipo,
            concepto=p.concepto,
            referencia=p.referencia,
            fecha=p.fecha,
            monto=float(p.monto),
            conciliado=p.conciliado,
            observacion=p.observacion,
        ) for p in partidas.scalars().all()],
    )


@router.get("/{conciliacion_id}", response_model=ConciliacionResponse)
async def obtener_conciliacion(
    conciliacion_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(ConciliacionBancaria).where(
            ConciliacionBancaria.id == conciliacion_id,
            ConciliacionBancaria.empresa_id == current_user.empresa_id,
        )
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Conciliacion no encontrada")

    cuenta = await db.get(CuentaBanco, c.cuenta_id)
    periodo = await db.get(PeriodoContable, c.periodo_id) if c.periodo_id else None
    partidas = await db.execute(
        select(PartidaConciliacion).where(PartidaConciliacion.conciliacion_id == c.id)
    )
    return ConciliacionResponse(
        id=str(c.id),
        cuenta_id=str(c.cuenta_id),
        cuenta_nombre=f"{cuenta.banco} - {cuenta.numero_cuenta}" if cuenta else None,
        periodo_id=str(c.periodo_id) if c.periodo_id else None,
        periodo_nombre=periodo.nombre if periodo else None,
        fecha_inicio=c.fecha_inicio,
        fecha_fin=c.fecha_fin,
        saldo_inicial_banco=float(c.saldo_inicial_banco),
        saldo_inicial_libro=float(c.saldo_inicial_libro),
        saldo_final_banco=float(c.saldo_final_banco),
        saldo_final_libro=float(c.saldo_final_libro),
        diferencia=float(c.diferencia),
        estado=c.estado,
        observaciones=c.observaciones,
        created_at=c.created_at,
        cerrada_at=c.cerrada_at,
        partidas=[PartidaResponse(
            id=str(p.id),
            conciliacion_id=str(p.conciliacion_id),
            movimiento_banco_id=str(p.movimiento_banco_id) if p.movimiento_banco_id else None,
            tipo=p.tipo,
            concepto=p.concepto,
            referencia=p.referencia,
            fecha=p.fecha,
            monto=float(p.monto),
            conciliado=p.conciliado,
            observacion=p.observacion,
        ) for p in partidas.scalars().all()],
    )


class ToggleConciliarPartida(BaseModel):
    partida_ids: list[uuid.UUID]
    conciliado: bool = True


@router.post("/{conciliacion_id}/conciliar")
async def toggle_conciliar_partidas(
    conciliacion_id: uuid.UUID,
    data: ToggleConciliarPartida,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(ConciliacionBancaria).where(
            ConciliacionBancaria.id == conciliacion_id,
            ConciliacionBancaria.empresa_id == current_user.empresa_id,
        )
    )
    conciliacion = result.scalar_one_or_none()
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliacion no encontrada")
    if conciliacion.estado == "EN_FIRME":
        raise HTTPException(status_code=400, detail="Conciliacion ya esta en firme")

    for pid in data.partida_ids:
        partida = await db.get(PartidaConciliacion, pid)
        if partida and partida.conciliacion_id == conciliacion_id:
            partida.conciliado = data.conciliado
            if data.conciliado and partida.movimiento_banco_id:
                mov = await db.get(MovimientoBanco, partida.movimiento_banco_id)
                if mov:
                    mov.conciliado = True
            elif not data.conciliado and partida.movimiento_banco_id:
                mov = await db.get(MovimientoBanco, partida.movimiento_banco_id)
                if mov:
                    mov.conciliado = False

    await db.commit()
    return {"mensaje": "Partidas actualizadas"}


@router.post("/{conciliacion_id}/cerrar")
async def cerrar_conciliacion(
    conciliacion_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(ConciliacionBancaria).where(
            ConciliacionBancaria.id == conciliacion_id,
            ConciliacionBancaria.empresa_id == current_user.empresa_id,
        )
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Conciliacion no encontrada")
    if c.estado == "EN_FIRME":
        raise HTTPException(status_code=400, detail="Conciliacion ya esta en firme")

    partidas = await db.execute(
        select(PartidaConciliacion).where(
            PartidaConciliacion.conciliacion_id == c.id,
            PartidaConciliacion.conciliado == False,
        )
    )
    no_conciliadas = partidas.scalars().all()

    c.estado = "EN_FIRME" if len(no_conciliadas) == 0 else "EN_FIRME"
    c.cerrada_at = datetime.now()
    await db.commit()

    return {
        "mensaje": "Conciliacion cerrada en firme",
        "partidas_no_conciliadas": len(no_conciliadas),
        "estado": c.estado,
    }


class PartidaManualCreate(BaseModel):
    tipo: str = "BANCO"
    concepto: str
    referencia: str | None = None
    fecha: date
    monto: float
    observacion: str | None = None


@router.post("/{conciliacion_id}/partidas", status_code=201)
async def agregar_partida_manual(
    conciliacion_id: uuid.UUID,
    data: PartidaManualCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(ConciliacionBancaria).where(
            ConciliacionBancaria.id == conciliacion_id,
            ConciliacionBancaria.empresa_id == current_user.empresa_id,
        )
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Conciliacion no encontrada")
    if c.estado == "EN_FIRME":
        raise HTTPException(status_code=400, detail="Conciliacion ya esta en firme")

    partida = PartidaConciliacion(
        conciliacion_id=conciliacion_id,
        movimiento_banco_id=None,
        tipo=data.tipo,
        concepto=data.concepto,
        referencia=data.referencia,
        fecha=data.fecha,
        monto=data.monto,
        conciliado=False,
        observacion=data.observacion,
    )
    db.add(partida)
    await db.commit()
    await db.refresh(partida)

    return PartidaResponse(
        id=str(partida.id),
        conciliacion_id=str(partida.conciliacion_id),
        movimiento_banco_id=None,
        tipo=partida.tipo,
        concepto=partida.concepto,
        referencia=partida.referencia,
        fecha=partida.fecha,
        monto=float(partida.monto),
        conciliado=partida.conciliado,
        observacion=partida.observacion,
    )


@router.delete("/{conciliacion_id}/partidas/{partida_id}", status_code=204)
async def eliminar_partida(
    conciliacion_id: uuid.UUID,
    partida_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(ConciliacionBancaria).where(
            ConciliacionBancaria.id == conciliacion_id,
            ConciliacionBancaria.empresa_id == current_user.empresa_id,
        )
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Conciliacion no encontrada")
    if c.estado == "EN_FIRME":
        raise HTTPException(status_code=400, detail="Conciliacion ya esta en firme")

    partida = await db.get(PartidaConciliacion, partida_id)
    if not partida or partida.conciliacion_id != conciliacion_id:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    if partida.movimiento_banco_id:
        raise HTTPException(status_code=400, detail="No se puede eliminar una partida vinculada a un movimiento bancario")

    await db.delete(partida)
    await db.commit()
