from typing import Annotated
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.domain.models.usuario import Usuario
from app.domain.models.cheque import Cheque, Chequera, ChequeFormato
from app.domain.models.banco import CuentaBanco
from app.service.cheque_print_service import ChequePrintService

router = APIRouter()

# ═══════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════

class ChequeCreate(BaseModel):
    cuenta_bancaria_id: uuid.UUID
    chequera_id: uuid.UUID | None = None
    pagadero_a: str
    monto: float
    fecha: date
    concepto: str | None = None
    proveedor_id: uuid.UUID | None = None
    cliente_id: uuid.UUID | None = None
    numero: str | None = None
    numero_contable: str | None = None


class ChequeResponse(BaseModel):
    id: str
    numero: str
    numero_contable: str | None
    cuenta_bancaria_id: str
    chequera_id: str | None
    pagadero_a: str
    monto: float
    fecha: str
    concepto: str | None
    estado: str
    impreso: bool
    proveedor_id: str | None
    cliente_id: str | None

    class Config:
        from_attributes = True


class ChequeraCreate(BaseModel):
    cuenta_bancaria_id: uuid.UUID
    nombre: str
    numero_inicio: int
    numero_fin: int


class ChequeraResponse(BaseModel):
    id: str
    cuenta_bancaria_id: str
    nombre: str
    numero_inicio: int
    numero_fin: int
    numero_actual: int
    activa: bool

    class Config:
        from_attributes = True


class ChequeConfigUpdate(BaseModel):
    cheque_formato_id: uuid.UUID | None = None
    cheque_ultimo_numero_operativo: int | None = None
    cheque_ultimo_numero_contable: int | None = None
    cheque_prefijo: str | None = None
    cheque_formato_numero: str | None = None


class ChequeConfigResponse(BaseModel):
    cheque_formato_id: str | None
    cheque_ultimo_numero_operativo: int
    cheque_ultimo_numero_contable: int
    cheque_prefijo: str
    cheque_formato_numero: str

    class Config:
        from_attributes = True


class ChequeFormatoCreate(BaseModel):
    nombre: str = 'Default'
    ancho_mm: float = 216.0
    alto_mm: float = 89.0
    campo_fecha_x: float = 130.0
    campo_fecha_y: float = 14.0
    campo_pagadero_x: float = 25.0
    campo_pagadero_y: float = 28.0
    campo_monto_num_x: float = 130.0
    campo_monto_num_y: float = 28.0
    campo_monto_letras_x: float = 25.0
    campo_monto_letras_y: float = 42.0
    campo_concepto_x: float = 25.0
    campo_concepto_y: float = 56.0
    campo_firma_x: float = 25.0
    campo_firma_y: float = 72.0
    fuente_nombre: str = 'Courier New'
    fuente_tamano: int = 11


class ChequeFormatoResponse(BaseModel):
    id: str
    nombre: str
    activo: bool
    ancho_mm: float
    alto_mm: float
    campo_fecha_x: float
    campo_fecha_y: float
    campo_pagadero_x: float
    campo_pagadero_y: float
    campo_monto_num_x: float
    campo_monto_num_y: float
    campo_monto_letras_x: float
    campo_monto_letras_y: float
    campo_concepto_x: float
    campo_concepto_y: float
    campo_firma_x: float
    campo_firma_y: float
    fuente_nombre: str
    fuente_tamano: int

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
# Chequeras
# ═══════════════════════════════════════════════════════════

@router.get("/chequeras", response_model=list[ChequeraResponse])
async def listar_chequeras(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("bancos_ver"))],
    cuenta_id: uuid.UUID | None = None,
):
    q = select(Chequera).where(Chequera.empresa_id == current_user.empresa_id, Chequera.activa == True)
    if cuenta_id:
        q = q.where(Chequera.cuenta_bancaria_id == cuenta_id)
    r = await db.execute(q.order_by(Chequera.nombre))
    return r.scalars().all()


@router.post("/chequeras", response_model=ChequeraResponse, status_code=201)
async def crear_chequera(
    data: ChequeraCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("bancos_crear"))],
):
    ch = Chequera(
        empresa_id=current_user.empresa_id,
        cuenta_bancaria_id=data.cuenta_bancaria_id,
        nombre=data.nombre,
        numero_inicio=data.numero_inicio,
        numero_fin=data.numero_fin,
        numero_actual=data.numero_inicio,
    )
    db.add(ch)
    await db.commit()
    await db.refresh(ch)
    return ch


# ═══════════════════════════════════════════════════════════
# Cheque numbering config per account
# ═══════════════════════════════════════════════════════════

@router.get("/cuentas/{cuenta_id}/cheque-config", response_model=ChequeConfigResponse)
async def obtener_config_cheque(
    cuenta_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("bancos_ver"))],
):
    cuenta = await db.get(CuentaBanco, cuenta_id)
    if not cuenta or cuenta.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Cuenta no encontrada")
    return cuenta


@router.put("/cuentas/{cuenta_id}/cheque-config", response_model=ChequeConfigResponse)
async def actualizar_config_cheque(
    cuenta_id: uuid.UUID,
    data: ChequeConfigUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("bancos_crear"))],
):
    cuenta = await db.get(CuentaBanco, cuenta_id)
    if not cuenta or cuenta.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Cuenta no encontrada")
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(cuenta, key, value)
    await db.commit()
    await db.refresh(cuenta)
    return cuenta


# ═══════════════════════════════════════════════════════════
# Cheques
# ═══════════════════════════════════════════════════════════

@router.get("/cheques", response_model=list[ChequeResponse])
async def listar_cheques(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("bancos_ver"))],
    cuenta_id: uuid.UUID | None = None,
    estado: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
):
    q = select(Cheque).where(Cheque.empresa_id == current_user.empresa_id)
    if cuenta_id:
        q = q.where(Cheque.cuenta_bancaria_id == cuenta_id)
    if estado:
        q = q.where(Cheque.estado == estado)
    if desde:
        q = q.where(Cheque.fecha >= desde)
    if hasta:
        q = q.where(Cheque.fecha <= hasta)
    r = await db.execute(q.order_by(Cheque.fecha.desc(), Cheque.numero.desc()).limit(200))
    return r.scalars().all()


@router.post("/cheques", response_model=ChequeResponse, status_code=201)
async def crear_cheque(
    data: ChequeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("bancos_crear"))],
):
    cuenta = await db.get(CuentaBanco, data.cuenta_bancaria_id)
    if not cuenta or cuenta.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Cuenta bancaria no encontrada")

    # ── Assign operational number (numero) ──
    if data.numero:
        numero = data.numero
    elif data.chequera_id:
        chequera = await db.get(Chequera, data.chequera_id)
        if not chequera or chequera.empresa_id != current_user.empresa_id:
            raise HTTPException(404, "Chequera no encontrada")
        if chequera.numero_actual > chequera.numero_fin:
            raise HTTPException(400, "Chequera agotada")
        numero = str(chequera.numero_actual).zfill(8)
        chequera.numero_actual += 1
    else:
        # Auto from account-level config
        cuenta.cheque_ultimo_numero_operativo += 1
        raw = cuenta.cheque_ultimo_numero_operativo
        template = cuenta.cheque_formato_numero or "{NUM}"
        prefijo = cuenta.cheque_prefijo or ""
        numero = template.replace("{PREF}", prefijo).replace("{NUM}", str(raw).zfill(8))

    # ── Assign accounting sequential (numero_contable) ──
    if data.numero_contable:
        numero_contable = data.numero_contable
    else:
        cuenta.cheque_ultimo_numero_contable += 1
        raw = cuenta.cheque_ultimo_numero_contable
        numero_contable = str(raw).zfill(6)

    cheque = Cheque(
        empresa_id=current_user.empresa_id,
        cuenta_bancaria_id=data.cuenta_bancaria_id,
        chequera_id=data.chequera_id,
        numero=numero,
        numero_contable=numero_contable,
        pagadero_a=data.pagadero_a,
        monto=data.monto,
        fecha=data.fecha,
        concepto=data.concepto,
        proveedor_id=data.proveedor_id,
        cliente_id=data.cliente_id,
        estado='EMITIDO',
    )
    db.add(cheque)
    await db.commit()
    await db.refresh(cheque)
    return cheque


@router.post("/cheques/{cheque_id}/anular")
async def anular_cheque(
    cheque_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("bancos_crear"))],
):
    cheque = await db.get(Cheque, cheque_id)
    if not cheque or cheque.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Cheque no encontrado")
    if cheque.estado != 'EMITIDO':
        raise HTTPException(400, f"No se puede anular un cheque en estado {cheque.estado}")
    cheque.estado = 'ANULADO'
    await db.commit()
    return {"mensaje": "Cheque anulado"}


# ═══════════════════════════════════════════════════════════
# Impresion (HTML / PDF / Texto matricial)
# ═══════════════════════════════════════════════════════════

@router.get("/cheques/{cheque_id}/imprimir")
async def imprimir_cheque(
    cheque_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("bancos_ver"))],
    formato: str = Query("pdf", pattern="^(html|pdf|texto)$"),
):
    """
    Genera el cheque listo para imprimir.
    - formato=pdf: PDF con posicionamiento exacto (recomendado)
    - formato=html: HTML con posicionamiento CSS para vista previa
    - formato=texto: texto plano con posiciones por columnas (matricial)
    """
    cheque = await db.get(Cheque, cheque_id)
    if not cheque or cheque.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Cheque no encontrado")

    svc = ChequePrintService()

    if formato == 'pdf':
        content = await svc.generar_pdf(db, cheque_id)
        await svc.marcar_impreso(db, cheque_id)
        return Response(content=content, media_type="application/pdf", headers={
            "Content-Disposition": f'inline; filename="cheque_{cheque.numero}.pdf"'
        })
    elif formato == 'texto':
        content = await svc.generar_texto_matricial(db, cheque_id)
        await svc.marcar_impreso(db, cheque_id)
        return Response(content=content, media_type="text/plain")
    else:
        html = await svc.generar_html_impresion(db, cheque_id)
        await svc.marcar_impreso(db, cheque_id)
        return Response(content=html, media_type="text/html")


@router.get("/cheques/{cheque_id}/vista-previa")
async def vista_previa_cheque(
    cheque_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("bancos_ver"))],
    formato: str = Query("html", pattern="^(html|pdf)$"),
):
    """Vista previa sin marcar como impreso."""
    cheque = await db.get(Cheque, cheque_id)
    if not cheque or cheque.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Cheque no encontrado")
    svc = ChequePrintService()
    if formato == 'pdf':
        content = await svc.generar_pdf(db, cheque_id)
        return Response(content=content, media_type="application/pdf", headers={
            "Content-Disposition": f'inline; filename="cheque_{cheque.numero}_preview.pdf"'
        })
    html = await svc.generar_html_impresion(db, cheque_id)
    return Response(content=html, media_type="text/html")


# ═══════════════════════════════════════════════════════════
# Formatos de impresion
# ═══════════════════════════════════════════════════════════

@router.get("/formatos", response_model=list[ChequeFormatoResponse])
async def listar_formatos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("bancos_ver"))],
):
    r = await db.execute(
        select(ChequeFormato).where(ChequeFormato.empresa_id == current_user.empresa_id)
    )
    return r.scalars().all()


@router.post("/formatos", response_model=ChequeFormatoResponse, status_code=201)
async def crear_formato(
    data: ChequeFormatoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("bancos_crear"))],
):
    formato = ChequeFormato(empresa_id=current_user.empresa_id, **data.model_dump())
    db.add(formato)
    await db.commit()
    await db.refresh(formato)
    return formato


@router.put("/formatos/{formato_id}", response_model=ChequeFormatoResponse)
async def actualizar_formato(
    formato_id: uuid.UUID,
    data: ChequeFormatoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("bancos_crear"))],
):
    formato = await db.get(ChequeFormato, formato_id)
    if not formato or formato.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Formato no encontrado")
    for key, value in data.model_dump().items():
        setattr(formato, key, value)
    await db.commit()
    await db.refresh(formato)
    return formato


@router.post("/formatos/{formato_id}/activar")
async def activar_formato(
    formato_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(require_permission("bancos_crear"))],
):
    await db.execute(
        ChequeFormato.__table__.update()
        .where(ChequeFormato.empresa_id == current_user.empresa_id)
        .values(activo=False)
    )
    formato = await db.get(ChequeFormato, formato_id)
    if not formato or formato.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Formato no encontrado")
    formato.activo = True
    await db.commit()
    return {"mensaje": f"Formato '{formato.nombre}' activado"}
