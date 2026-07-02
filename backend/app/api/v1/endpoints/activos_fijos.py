from typing import Annotated
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.activo_fijo import CategoriaActivo, ActivoFijo, DepreciacionLinea
from app.domain.models.periodo import PeriodoContable
from app.service.activo_fijo_service import ActivoFijoService
from app.service.accounting.accounting_engine import AccountingEngine

router = APIRouter()


class CategoriaCreate(BaseModel):
    codigo: str
    nombre: str
    vida_util_default: int | None = None
    metodo_depreciacion_default: str | None = None


class CategoriaResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    vida_util_default: int | None
    metodo_depreciacion_default: str | None
    activa: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ActivoFijoCreate(BaseModel):
    categoria_id: uuid.UUID
    codigo: str
    nombre: str
    descripcion: str | None = None
    fecha_adquisicion: date
    costo_adquisicion: float
    valor_residual: float = 0
    vida_util_anos: int
    metodo_depreciacion: str
    cuenta_contable_id: uuid.UUID | None = None
    ubicacion: str | None = None


class ActivoFijoUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    valor_residual: float | None = None
    ubicacion: str | None = None
    estado: str | None = None


class ActivoFijoResponse(BaseModel):
    id: str
    categoria_id: str
    categoria_nombre: str | None = None
    codigo: str
    nombre: str
    descripcion: str | None
    fecha_adquisicion: date
    costo_adquisicion: float
    valor_residual: float
    vida_util_anos: int
    metodo_depreciacion: str
    estado: str
    valor_libros: float
    depreciacion_acumulada: float
    fecha_baja: date | None
    motivo_baja: str | None
    ubicacion: str | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class DepreciacionLineaResponse(BaseModel):
    id: str
    periodo_id: str
    fecha_depreciacion: date
    monto_depreciacion: float
    depreciacion_acumulada: float
    valor_libros_despues: float
    created_at: datetime

    class Config:
        from_attributes = True


# ----- CATEGORIAS -----

@router.get("/categorias", response_model=list[CategoriaResponse])
async def listar_categorias(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(CategoriaActivo).where(
            CategoriaActivo.empresa_id == current_user.empresa_id,
            CategoriaActivo.activa == True,
        ).order_by(CategoriaActivo.nombre)
    )
    return result.scalars().all()


@router.post("/categorias", response_model=CategoriaResponse, status_code=201)
async def crear_categoria(
    data: CategoriaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    cat = CategoriaActivo(empresa_id=current_user.empresa_id, **data.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


# ----- ACTIVOS FIJOS -----

@router.get("/", response_model=list[ActivoFijoResponse])
async def listar_activos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    categoria_id: uuid.UUID | None = None,
    estado: str | None = None,
):
    query = select(ActivoFijo).where(ActivoFijo.empresa_id == current_user.empresa_id)
    if categoria_id:
        query = query.where(ActivoFijo.categoria_id == categoria_id)
    if estado:
        query = query.where(ActivoFijo.estado == estado)
    query = query.order_by(ActivoFijo.codigo)

    result = await db.execute(query)
    activos = result.scalars().all()

    response = []
    for a in activos:
        cat = await db.get(CategoriaActivo, a.categoria_id)
        response.append(ActivoFijoResponse(
            id=str(a.id),
            categoria_id=str(a.categoria_id),
            categoria_nombre=cat.nombre if cat else None,
            codigo=a.codigo,
            nombre=a.nombre,
            descripcion=a.descripcion,
            fecha_adquisicion=a.fecha_adquisicion,
            costo_adquisicion=float(a.costo_adquisicion),
            valor_residual=float(a.valor_residual),
            vida_util_anos=a.vida_util_anos,
            metodo_depreciacion=a.metodo_depreciacion,
            estado=a.estado,
            valor_libros=float(a.valor_libros),
            depreciacion_acumulada=float(a.depreciacion_acumulada),
            fecha_baja=a.fecha_baja,
            motivo_baja=a.motivo_baja,
            ubicacion=a.ubicacion,
            created_at=a.created_at,
            updated_at=a.updated_at,
        ))
    return response


@router.post("/", response_model=ActivoFijoResponse, status_code=201)
async def crear_activo(
    data: ActivoFijoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    cat = await db.get(CategoriaActivo, data.categoria_id)
    if not cat or cat.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")

    activo = ActivoFijo(
        empresa_id=current_user.empresa_id,
        categoria_id=data.categoria_id,
        codigo=data.codigo,
        nombre=data.nombre,
        descripcion=data.descripcion,
        fecha_adquisicion=data.fecha_adquisicion,
        costo_adquisicion=data.costo_adquisicion,
        valor_residual=data.valor_residual,
        vida_util_anos=data.vida_util_anos,
        metodo_depreciacion=data.metodo_depreciacion,
        estado="ACTIVO",
        valor_libros=data.costo_adquisicion,
        depreciacion_acumulada=0,
        ubicacion=data.ubicacion,
    )
    db.add(activo)
    await db.commit()
    await db.refresh(activo)

    cat = await db.get(CategoriaActivo, activo.categoria_id)
    return ActivoFijoResponse(
        id=str(activo.id),
        categoria_id=str(activo.categoria_id),
        categoria_nombre=cat.nombre if cat else None,
        codigo=activo.codigo,
        nombre=activo.nombre,
        descripcion=activo.descripcion,
        fecha_adquisicion=activo.fecha_adquisicion,
        costo_adquisicion=float(activo.costo_adquisicion),
        valor_residual=float(activo.valor_residual),
        vida_util_anos=activo.vida_util_anos,
        metodo_depreciacion=activo.metodo_depreciacion,
        estado=activo.estado,
        valor_libros=float(activo.valor_libros),
        depreciacion_acumulada=float(activo.depreciacion_acumulada),
        fecha_baja=activo.fecha_baja,
        motivo_baja=activo.motivo_baja,
        ubicacion=activo.ubicacion,
        created_at=activo.created_at,
        updated_at=activo.updated_at,
    )


@router.get("/{activo_id}", response_model=ActivoFijoResponse)
async def obtener_activo(
    activo_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(ActivoFijo).where(
            ActivoFijo.id == activo_id,
            ActivoFijo.empresa_id == current_user.empresa_id,
        )
    )
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Activo no encontrado")

    cat = await db.get(CategoriaActivo, a.categoria_id)
    return ActivoFijoResponse(
        id=str(a.id),
        categoria_id=str(a.categoria_id),
        categoria_nombre=cat.nombre if cat else None,
        codigo=a.codigo,
        nombre=a.nombre,
        descripcion=a.descripcion,
        fecha_adquisicion=a.fecha_adquisicion,
        costo_adquisicion=float(a.costo_adquisicion),
        valor_residual=float(a.valor_residual),
        vida_util_anos=a.vida_util_anos,
        metodo_depreciacion=a.metodo_depreciacion,
        estado=a.estado,
        valor_libros=float(a.valor_libros),
        depreciacion_acumulada=float(a.depreciacion_acumulada),
        fecha_baja=a.fecha_baja,
        motivo_baja=a.motivo_baja,
        ubicacion=a.ubicacion,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


@router.put("/{activo_id}", response_model=ActivoFijoResponse)
async def actualizar_activo(
    activo_id: uuid.UUID,
    data: ActivoFijoUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(ActivoFijo).where(
            ActivoFijo.id == activo_id,
            ActivoFijo.empresa_id == current_user.empresa_id,
        )
    )
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Activo no encontrado")

    update_data = data.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now()
    for key, value in update_data.items():
        setattr(a, key, value)

    await db.commit()
    await db.refresh(a)

    cat = await db.get(CategoriaActivo, a.categoria_id)
    return ActivoFijoResponse(
        id=str(a.id),
        categoria_id=str(a.categoria_id),
        categoria_nombre=cat.nombre if cat else None,
        codigo=a.codigo,
        nombre=a.nombre,
        descripcion=a.descripcion,
        fecha_adquisicion=a.fecha_adquisicion,
        costo_adquisicion=float(a.costo_adquisicion),
        valor_residual=float(a.valor_residual),
        vida_util_anos=a.vida_util_anos,
        metodo_depreciacion=a.metodo_depreciacion,
        estado=a.estado,
        valor_libros=float(a.valor_libros),
        depreciacion_acumulada=float(a.depreciacion_acumulada),
        fecha_baja=a.fecha_baja,
        motivo_baja=a.motivo_baja,
        ubicacion=a.ubicacion,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


@router.delete("/{activo_id}", status_code=204)
async def eliminar_activo(
    activo_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(ActivoFijo).where(
            ActivoFijo.id == activo_id,
            ActivoFijo.empresa_id == current_user.empresa_id,
        )
    )
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Activo no encontrado")

    await db.delete(a)
    await db.commit()


# ----- DEPRECIACION -----

def calcular_depreciacion_linea_recta(costo: float, valor_residual: float, vida_util: int) -> float:
    return round((costo - valor_residual) / vida_util, 2)


def calcular_depreciacion_doble_declinante(costo: float, valor_residual: float, vida_util: int, depreciacion_acumulada: float) -> float:
    tasa = 2.0 / vida_util
    valor_libros = costo - depreciacion_acumulada
    monto = round(valor_libros * tasa, 2)
    max_depreciable = costo - valor_residual
    max_posible = max_depreciable - depreciacion_acumulada
    return min(monto, max_posible, valor_libros - valor_residual)


def calcular_depreciacion_suma_digitos(costo: float, valor_residual: float, vida_util: int, anos_transcurridos: int) -> float:
    max_depreciable = costo - valor_residual
    suma_digitos = vida_util * (vida_util + 1) / 2
    anos_restantes = vida_util - anos_transcurridos
    if anos_restantes <= 0:
        return 0
    return round(max_depreciable * anos_restantes / suma_digitos, 2)


@router.post("/{activo_id}/depreciar")
async def ejecutar_depreciacion(
    activo_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    periodo_id: uuid.UUID = Query(),
):
    svc = ActivoFijoService(db, current_user.empresa_id)
    try:
        result = await svc.ejecutar_depreciacion(activo_id, periodo_id)
        engine = AccountingEngine(db)
        data = {
            'activo_id': str(activo_id),
            'periodo_id': str(periodo_id),
            'monto_depreciacion': result['monto'],
            'depreciacion_acumulada': result['depreciacion_acumulada'],
            'valor_libros': result['valor_libros'],
        }
        asiento_result = await engine.generate_from_event(
            event_type='DEPRECIACION',
            module='activos_fijos',
            data=data,
            company_id=current_user.empresa_id,
            document_id=activo_id,
        )
        if asiento_result:
            result['asiento_id'] = str(asiento_result.get('asiento_id'))
        await db.commit()
        return {"mensaje": "Depreciacion ejecutada", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{activo_id}/depreciaciones", response_model=list[DepreciacionLineaResponse])
async def listar_depreciaciones(
    activo_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(ActivoFijo).where(
            ActivoFijo.id == activo_id,
            ActivoFijo.empresa_id == current_user.empresa_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Activo no encontrado")

    lineas = await db.execute(
        select(DepreciacionLinea).where(
            DepreciacionLinea.activo_id == activo_id
        ).order_by(DepreciacionLinea.fecha_depreciacion)
    )
    return lineas.scalars().all()


# ----- BAJA -----

class BajaActivoRequest(BaseModel):
    fecha_baja: date
    motivo_baja: str


@router.post("/{activo_id}/baja")
async def dar_baja_activo(
    activo_id: uuid.UUID,
    data: BajaActivoRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    svc = ActivoFijoService(db, current_user.empresa_id)
    try:
        result = await svc.dar_baja(activo_id, data.fecha_baja, data.motivo_baja)
        await db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
