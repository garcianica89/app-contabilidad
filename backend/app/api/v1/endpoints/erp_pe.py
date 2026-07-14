from typing import Annotated
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.cliente import Cliente

router = APIRouter()


class PresupuestoVentaCreate(BaseModel):
    numero: str
    cliente_id: uuid.UUID | None = None
    fecha: date
    fecha_validez: date | None = None
    total: float = 0
    observaciones: str | None = None


class PresupuestoVentaResponse(BaseModel):
    id: str
    empresa_id: str
    numero: str
    cliente_id: str | None
    fecha: str
    fecha_validez: str | None
    total: float
    estado: str
    observaciones: str | None
    created_at: str | None = None


@router.get("/presupuestos")
async def listar_presupuestos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    estado: str | None = None,
):
    query = """
        SELECT pv.id, pv.empresa_id, pv.numero, pv.cliente_id,
               c.nombre AS cliente_nombre,
               pv.fecha, pv.fecha_validez, pv.total, pv.estado,
               pv.observaciones, pv.record_date
        FROM presupuesto_venta pv
        LEFT JOIN cliente c ON c.id = pv.cliente_id
        WHERE pv.empresa_id = :emp_id
    """
    params: dict = {"emp_id": current_user.empresa_id}
    if estado:
        query += " AND pv.estado = :estado"
        params["estado"] = estado
    query += " ORDER BY pv.record_date DESC"

    result = await db.execute(text(query), params)
    rows = result.fetchall()
    return [
        {
            "id": str(r.id),
            "empresa_id": str(r.empresa_id),
            "numero": r.numero,
            "cliente_id": str(r.cliente_id) if r.cliente_id else None,
            "cliente_nombre": r.cliente_nombre,
            "fecha": str(r.fecha),
            "fecha_validez": str(r.fecha_validez) if r.fecha_validez else None,
            "total": float(r.total),
            "estado": r.estado,
            "observaciones": r.observaciones,
            "created_at": str(r.record_date) if r.record_date else None,
        }
        for r in rows
    ]


@router.post("/presupuestos")
async def crear_presupuesto(
    data: PresupuestoVentaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        text("""
            INSERT INTO presupuesto_venta
                (empresa_id, numero, cliente_id, fecha, fecha_validez, total, estado, observaciones,
                 note_exists_flag, record_date, created_by)
            VALUES
                (:emp_id, :numero, :cliente_id, :fecha, :fecha_validez, :total, 'VIGENTE', :observaciones,
                 TRUE, NOW(), :created_by)
            RETURNING id
        """),
        {
            "emp_id": current_user.empresa_id,
            "numero": data.numero,
            "cliente_id": data.cliente_id,
            "fecha": data.fecha,
            "fecha_validez": data.fecha_validez,
            "total": data.total,
            "observaciones": data.observaciones,
            "created_by": str(current_user.id),
        },
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=500, detail="Error al crear presupuesto")
    return {"id": str(row.id), "numero": data.numero, "estado": "VIGENTE"}


@router.get("/presupuestos/{presupuesto_id}")
async def get_presupuesto(
    presupuesto_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        text("""
            SELECT pv.*, c.nombre AS cliente_nombre
            FROM presupuesto_venta pv
            LEFT JOIN cliente c ON c.id = pv.cliente_id
            WHERE pv.id = :id AND pv.empresa_id = :emp_id
        """),
        {"id": presupuesto_id, "emp_id": current_user.empresa_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    return dict(row._mapping)


@router.post("/presupuestos/{presupuesto_id}/aprobar")
async def aprobar_presupuesto(
    presupuesto_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await db.execute(
        text("UPDATE presupuesto_venta SET estado = 'APROBADO' WHERE id = :id AND empresa_id = :emp_id RETURNING id"),
        {"id": presupuesto_id, "emp_id": current_user.empresa_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    await db.commit()
    return {"id": str(row.id), "estado": "APROBADO"}
