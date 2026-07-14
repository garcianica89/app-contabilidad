from typing import Annotated, List
import uuid
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.models.usuario import Usuario
from app.domain.models.banco import CuentaBanco, MovimientoBanco
from app.domain.models.conciliacion import ConciliacionBancaria, PartidaConciliacion
from app.domain.models.factura_compra import FacturaCompra
from app.domain.models.factura_venta import FacturaVenta
from app.service.cargador_service import CargadorService
from app.service.clasificador_service import ClasificadorService
from app.service.accounting.accounting_engine import AccountingEngine

router = APIRouter()


class PreviewResponse(BaseModel):
    cuenta: dict
    formato: str
    total_movimientos: int
    duplicados: int
    total_ingresos: float
    total_egresos: float
    movimientos: list


class ClasificacionSugeridaResponse(BaseModel):
    movimiento_idx: int
    modulo: str
    confianza: float
    entidad_id: str | None = None
    entidad_tipo: str | None = None
    entidad_descripcion: str | None = None
    regla: str | None = None


class ClasificarPreviewRequest(BaseModel):
    movimientos: list


class ImportarRequest(BaseModel):
    cuenta_banco_id: uuid.UUID
    movimientos: list
    clasificaciones: list | None = None
    auto_match: bool = True
    crear_conciliacion: bool = True
    fecha_corte: date | None = None
    saldo_estado: float | None = None


class ImportarResponse(BaseModel):
    movimientos_creados: int
    conciliacion_id: str | None = None
    conciliacion_estado: str | None = None
    vinculaciones: list = []
    errores: list = []


class AutoMatchRequest(BaseModel):
    conciliacion_id: uuid.UUID


class AutoMatchSugerencia(BaseModel):
    partida_libro_id: str
    partida_libro_concepto: str
    partida_libro_monto: float
    partida_estado_id: str
    partida_estado_concepto: str
    partida_estado_monto: float
    confianza: float
    diferencia: float


class AjusteRequest(BaseModel):
    conciliacion_id: uuid.UUID
    concepto: str
    monto: float
    tipo_ajuste: str = "COMISION"  # COMISION, INTERES, DIFERENCIA_CAMBIARIA, OTRO
    cuenta_contable_id: uuid.UUID | None = None


class PartidaVincularRequest(BaseModel):
    partida_id: uuid.UUID
    entidad_tipo: str  # FacturaCompra or FacturaVenta
    entidad_id: uuid.UUID


@router.post("/preview", response_model=PreviewResponse)
async def preview_archivo(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    cuenta_banco_id: uuid.UUID = Form(...),
    archivo: UploadFile = File(...),
):
    bytes_archivo = await archivo.read()

    try:
        ruta = await CargadorService.guardar_archivo_subido(bytes_archivo, archivo.filename or "archivo")
        contenido_csv = None
        nombre = archivo.filename or "archivo"

        if nombre.lower().endswith(('.csv', '.txt')):
            contenido_csv = bytes_archivo.decode("utf-8-sig", errors="replace")

        result = await CargadorService.preview_importacion(
            db=db,
            empresa_id=current_user.empresa_id,
            cuenta_banco_id=cuenta_banco_id,
            ruta_archivo=ruta,
            nombre_archivo=nombre,
            contenido_csv=contenido_csv,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(400, f"Error al procesar archivo: {e}")

    return PreviewResponse(**result)


@router.post("/clasificar", response_model=List[ClasificacionSugeridaResponse])
async def clasificar_movimientos(
    data: ClasificarPreviewRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    clasificador = ClasificadorService(db=db, empresa_id=current_user.empresa_id)
    sugerencias = await clasificador.clasificar(data.movimientos)
    return [ClasificacionSugeridaResponse(**s.to_dict()) for s in sugerencias]


@router.post("/importar", response_model=ImportarResponse)
async def importar_movimientos(
    data: ImportarRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    try:
        result = await CargadorService.importar_movimientos(
            db=db,
            empresa_id=current_user.empresa_id,
            cuenta_banco_id=data.cuenta_banco_id,
            movimientos_data=data.movimientos,
            crear_conciliacion=data.crear_conciliacion,
            fecha_corte=data.fecha_corte,
            saldo_estado=data.saldo_estado,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    vinculaciones = []

    if data.clasificaciones and data.auto_match:
        for clasif in data.clasificaciones:
            if clasif.get("modulo") in ("CXP", "CXC") and clasif.get("entidad_id"):
                try:
                    await _vincular_partida(
                        db=db,
                        movimiento_idx=clasif.get("movimiento_idx", 0),
                        entidad_tipo=clasif.get("entidad_tipo", "FacturaCompra" if clasif["modulo"] == "CXP" else "FacturaVenta"),
                        entidad_id=uuid.UUID(clasif["entidad_id"]),
                        conciliacion_id=result.get("conciliacion_id"),
                        empresa_id=current_user.empresa_id,
                    )
                    vinculaciones.append({
                        "idx": clasif.get("movimiento_idx", 0),
                        "entidad_id": clasif["entidad_id"],
                        "entidad_tipo": clasif.get("entidad_tipo"),
                        "estado": "vinculado",
                    })
                except Exception as e:
                    vinculaciones.append({
                        "idx": clasif.get("movimiento_idx", 0),
                        "entidad_id": clasif["entidad_id"],
                        "entidad_tipo": clasif.get("entidad_tipo"),
                        "estado": "error",
                        "error": str(e),
                    })

    await db.commit()

    return ImportarResponse(
        movimientos_creados=result["movimientos_creados"],
        conciliacion_id=result.get("conciliacion_id"),
        conciliacion_estado=result.get("conciliacion_estado"),
        vinculaciones=vinculaciones,
    )


@router.post("/vincular-partida")
async def vincular_partida(
    data: PartidaVincularRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    result = await _vincular_partida(
        db=db,
        partida_id=data.partida_id,
        entidad_tipo=data.entidad_tipo,
        entidad_id=data.entidad_id,
        empresa_id=current_user.empresa_id,
    )
    await db.commit()
    return {"mensaje": "Partida vinculada exitosamente"}


async def _vincular_partida(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    entidad_tipo: str,
    entidad_id: uuid.UUID,
    movimiento_idx: int | None = None,
    partida_id: uuid.UUID | None = None,
    conciliacion_id: str | None = None,
):
    if entidad_tipo == "FacturaCompra":
        factura = await db.get(FacturaCompra, entidad_id)
        if not factura or factura.empresa_id != empresa_id:
            raise HTTPException(404, "Factura de compra no encontrada")
    elif entidad_tipo == "FacturaVenta":
        factura = await db.get(FacturaVenta, entidad_id)
        if not factura or factura.empresa_id != empresa_id:
            raise HTTPException(404, "Factura de venta no encontrada")
    else:
        raise HTTPException(400, f"Tipo de entidad no soportado: {entidad_tipo}")


@router.post("/auto-match", response_model=List[AutoMatchSugerencia])
async def auto_match_conciliacion(
    data: AutoMatchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    conciliacion = await db.get(ConciliacionBancaria, data.conciliacion_id)
    if not conciliacion or conciliacion.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Conciliacion no encontrada")
    if conciliacion.estado in ("CERRADA", "CERRADA_DIF"):
        raise HTTPException(400, "Conciliacion ya esta cerrada")

    result = await db.execute(
        select(PartidaConciliacion).where(
            PartidaConciliacion.conciliacion_id == data.conciliacion_id,
        ).order_by(PartidaConciliacion.fecha)
    )
    partidas = result.scalars().all()

    libros = [p for p in partidas if p.tipo == "LIBRO" and not p.conciliado]
    estados = [p for p in partidas if p.tipo == "ESTADO" and not p.conciliado]

    sugerencias = []

    for libro in libros:
        monto_libro = float(libro.monto)
        for estado in estados:
            monto_estado = float(estado.monto)
            diferencia = round(abs(monto_libro - monto_estado), 2)

            if monto_libro == 0 and monto_estado == 0:
                continue

            if diferencia / max(abs(monto_libro), abs(monto_estado), 0.01) > 0.05:
                continue

            confianza = 0.95 if diferencia == 0 else 0.7

            if libro.fecha and estado.fecha:
                dias_diff = abs((libro.fecha - estado.fecha).days)
                if dias_diff <= 1:
                    confianza = min(1.0, confianza + 0.1)
                elif dias_diff > 5:
                    confianza = max(0.3, confianza - 0.2)

            sugerencias.append(AutoMatchSugerencia(
                partida_libro_id=str(libro.id),
                partida_libro_concepto=libro.concepto,
                partida_libro_monto=monto_libro,
                partida_estado_id=str(estado.id),
                partida_estado_concepto=estado.concepto,
                partida_estado_monto=monto_estado,
                confianza=round(confianza, 2),
                diferencia=diferencia,
            ))

    sugerencias.sort(key=lambda s: s.confianza, reverse=True)
    return sugerencias[:100]


class AplicarAutoMatchRequest(BaseModel):
    conciliacion_id: uuid.UUID
    matches: list


class MatchItem(BaseModel):
    partida_libro_id: uuid.UUID
    partida_estado_id: uuid.UUID


@router.post("/auto-match/aplicar")
async def aplicar_auto_match(
    data: AplicarAutoMatchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    conciliacion = await db.get(ConciliacionBancaria, data.conciliacion_id)
    if not conciliacion or conciliacion.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Conciliacion no encontrada")
    if conciliacion.estado in ("CERRADA", "CERRADA_DIF"):
        raise HTTPException(400, "Conciliacion ya esta cerrada")

    aplicados = 0
    for match in data.matches:
        libro = await db.get(PartidaConciliacion, match.partida_libro_id)
        estado = await db.get(PartidaConciliacion, match.partida_estado_id)

        if not libro or not estado:
            continue
        if libro.conciliacion_id != data.conciliacion_id or estado.conciliacion_id != data.conciliacion_id:
            continue

        libro.conciliado = True
        estado.conciliado = True

        if libro.movimiento_banco_id:
            mov = await db.get(MovimientoBanco, libro.movimiento_banco_id)
            if mov:
                mov.conciliado = True

        aplicados += 1

    await db.commit()
    return {"mensaje": f"{aplicados} pares conciliados automaticamente"}


@router.post("/ajustes", status_code=201)
async def crear_ajuste_conciliacion(
    data: AjusteRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    conciliacion = await db.get(ConciliacionBancaria, data.conciliacion_id)
    if not conciliacion or conciliacion.empresa_id != current_user.empresa_id:
        raise HTTPException(404, "Conciliacion no encontrada")
    if conciliacion.estado in ("CERRADA", "CERRADA_DIF"):
        raise HTTPException(400, "Conciliacion ya esta cerrada")

    engine = AccountingEngine(db)
    entry = await engine.generate_from_event(
        event_type="BANCO",
        module="bancos",
        data={
            "cuenta_id": str(conciliacion.cuenta_id),
            "fecha": conciliacion.fecha_corte.isoformat(),
            "concepto": f"Ajuste Conciliacion: {data.concepto}",
            "entrada": data.monto if data.monto > 0 else 0,
            "salida": abs(data.monto) if data.monto < 0 else 0,
            "tipo": data.tipo_ajuste,
            "numero_documento": f"AJ-{conciliacion.fecha_corte.isoformat()}",
        },
        company_id=current_user.empresa_id,
        document_id=conciliacion.id,
        user_id=current_user.id,
    )

    partida = PartidaConciliacion(
        conciliacion_id=conciliacion.id,
        movimiento_banco_id=None,
        tipo="ESTADO",
        concepto=f"Ajuste: {data.concepto}",
        referencia=f"AS-{entry.get('asiento_numero', '')}" if entry else None,
        fecha=conciliacion.fecha_corte,
        monto=data.monto,
        conciliado=True,
        observacion=f"Ajuste por {data.tipo_ajuste}. Asiento: {entry.get('asiento_id', 'N/A') if entry else 'N/A'}",
    )
    db.add(partida)
    await db.commit()

    return {
        "mensaje": "Ajuste creado exitosamente",
        "partida_id": str(partida.id),
        "asiento_id": entry.get("asiento_id") if entry else None,
        "asiento_numero": entry.get("asiento_numero") if entry else None,
    }


class MovimientoSinClasificar(BaseModel):
    id: str
    cuenta_id: str
    cuenta_nombre: str
    fecha: str
    concepto: str
    monto: float
    tipo: str
    numero_documento: str | None = None
    conciliado: bool
    asiento_id: str | None = None


@router.get("/movimientos-sin-clasificar", response_model=List[MovimientoSinClasificar])
async def listar_movimientos_sin_clasificar(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    cuenta_id: uuid.UUID | None = None,
    dias: int = 90,
):
    query = select(MovimientoBanco).where(
        MovimientoBanco.empresa_id == current_user.empresa_id,
        MovimientoBanco.fecha >= datetime.now().date() - timedelta(days=dias),
    )
    if cuenta_id:
        query = query.where(MovimientoBanco.cuenta_id == cuenta_id)
    query = query.order_by(MovimientoBanco.fecha.desc())

    result = await db.execute(query)
    movs = result.scalars().all()

    response = []
    for m in movs:
        cuenta = await db.get(CuentaBanco, m.cuenta_id)
        response.append(MovimientoSinClasificar(
            id=str(m.id),
            cuenta_id=str(m.cuenta_id),
            cuenta_nombre=f"{cuenta.banco} - {cuenta.numero_cuenta}" if cuenta else "",
            fecha=m.fecha.isoformat() if hasattr(m.fecha, 'isoformat') else str(m.fecha),
            concepto=m.concepto,
            monto=float(m.entrada - m.salida),
            tipo=m.tipo,
            numero_documento=m.numero_documento,
            conciliado=m.conciliado,
            asiento_id=str(m.asiento_id) if m.asiento_id else None,
        ))
    return response
