from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.accounting.models import Numeracion
from app.domain.schemas import NumeracionCreate, NumeracionUpdate, NumeracionResponse
from app.service.numeracion_service import NumeracionService

router = APIRouter()


@router.get("/", response_model=list[NumeracionResponse])
async def list_numeraciones(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(get_current_user)],
    tipo_documento: str | None = None,
):
    query = select(Numeracion).where(Numeracion.company_id == user.empresa_id)
    if tipo_documento:
        query = query.where(Numeracion.tipo_documento == tipo_documento)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=NumeracionResponse, status_code=status.HTTP_201_CREATED)
async def create_numeracion(
    data: NumeracionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(get_current_user)],
):
    numeracion = Numeracion(
        company_id=user.empresa_id,
        serie=data.serie,
        nombre=data.nombre,
        tipo_documento=data.tipo_documento,
        mascara=data.mascara or '{SERIE}-{NUMERO}',
        correlativo_actual=data.correlativo_inicial or 0,
        prefijo=getattr(data, 'prefijo', None),
        sufijo=getattr(data, 'sufijo', None),
        digitos=getattr(data, 'digitos', 6),
        reinicio=getattr(data, 'reinicio', 'NUNCA'),
        numeracion_manual=getattr(data, 'numeracion_manual', False),
    )
    db.add(numeracion)
    await db.commit()
    await db.refresh(numeracion)
    return numeracion


@router.put("/{numeracion_id}", response_model=NumeracionResponse)
async def update_numeracion(
    numeracion_id: str,
    data: NumeracionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        select(Numeracion).where(
            Numeracion.id == numeracion_id,
            Numeracion.company_id == user.empresa_id,
        )
    )
    numeracion = result.scalar_one_or_none()
    if not numeracion:
        raise HTTPException(status_code=404, detail="Numeracion no encontrada")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(numeracion, field, value)
    await db.commit()
    await db.refresh(numeracion)
    return numeracion


@router.post("/{numeracion_id}/next", response_model=dict)
async def next_correlativo(
    numeracion_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Usuario, Depends(get_current_user)],
):
    service = NumeracionService(db)
    result = await service.get_next(
        company_id=user.empresa_id,
        document_type='',
        serie=None,
    )
    # Fallback to direct approach
    if not result:
        numeracion_q = await db.execute(
            select(Numeracion).where(
                Numeracion.id == numeracion_id,
                Numeracion.company_id == user.empresa_id,
            )
        )
        numeracion = numeracion_q.scalar_one_or_none()
        if not numeracion:
            raise HTTPException(status_code=404, detail="Numeracion no encontrada")
        numeracion.correlativo_actual += 1
        await db.commit()
        numero = numeracion.mascara.replace("{SERIE}", numeracion.serie).replace("{NUMERO}", str(numeracion.correlativo_actual).zfill(numeracion.digitos or 6))
        return {"numero": numero, "correlativo": numeracion.correlativo_actual}
    return result
