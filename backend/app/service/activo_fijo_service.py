from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.activo_fijo import ActivoFijo, DepreciacionLinea
from app.domain.models.periodo import PeriodoContable


def calcular_linea_recta(costo: float, valor_residual: float, vida_util: int) -> float:
    return round((costo - valor_residual) / vida_util, 2)


def calcular_doble_declinante(costo: float, valor_residual: float, vida_util: int, depreciacion_acumulada: float) -> float:
    tasa = 2.0 / vida_util
    valor_libros = costo - depreciacion_acumulada
    monto = round(valor_libros * tasa, 2)
    max_depreciable = costo - valor_residual
    max_posible = max_depreciable - depreciacion_acumulada
    return min(monto, max_posible, valor_libros - valor_residual)


def calcular_suma_digitos(costo: float, valor_residual: float, vida_util: int, anos_transcurridos: int) -> float:
    max_depreciable = costo - valor_residual
    suma_digitos = vida_util * (vida_util + 1) / 2
    anos_restantes = vida_util - anos_transcurridos
    if anos_restantes <= 0:
        return 0
    return round(max_depreciable * anos_restantes / suma_digitos, 2)


class ActivoFijoService:

    def __init__(self, db: AsyncSession, empresa_id: uuid.UUID):
        self.db = db
        self.empresa_id = empresa_id

    async def ejecutar_depreciacion(self, activo_id: uuid.UUID, periodo_id: uuid.UUID) -> dict:
        result = await self.db.execute(
            select(ActivoFijo).where(
                ActivoFijo.id == activo_id,
                ActivoFijo.empresa_id == self.empresa_id,
            )
        )
        activo = result.scalar_one_or_none()
        if not activo:
            raise ValueError("Activo no encontrado")
        if activo.estado != "ACTIVO":
            raise ValueError(f"Activo en estado {activo.estado}. No se puede depreciar")

        periodo = await self.db.get(PeriodoContable, periodo_id)
        if not periodo or periodo.empresa_id != self.empresa_id:
            raise ValueError("Periodo no encontrado")
        if periodo.cerrado:
            raise ValueError("Periodo cerrado")

        existing = await self.db.execute(
            select(DepreciacionLinea).where(
                DepreciacionLinea.activo_id == activo_id,
                DepreciacionLinea.periodo_id == periodo_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Ya existe depreciacion para este activo en el periodo")

        monto = await self._calcular_monto(activo)

        if monto <= 0:
            raise ValueError("El activo ya esta completamente depreciado")

        nueva_acumulada = float(activo.depreciacion_acumulada) + monto
        nuevo_valor_libros = float(activo.costo_adquisicion) - nueva_acumulada

        linea = DepreciacionLinea(
            activo_id=activo.id,
            periodo_id=periodo.id,
            fecha_depreciacion=periodo.fecha_fin,
            monto_depreciacion=monto,
            depreciacion_acumulada=nueva_acumulada,
            valor_libros_despues=nuevo_valor_libros,
        )
        self.db.add(linea)

        activo.depreciacion_acumulada = nueva_acumulada
        activo.valor_libros = nuevo_valor_libros
        if nuevo_valor_libros <= float(activo.valor_residual):
            activo.estado = "DEPRECIADO_TOTAL"

        return {
            "monto": monto,
            "depreciacion_acumulada": nueva_acumulada,
            "valor_libros": nuevo_valor_libros,
            "estado_activo": activo.estado,
        }

    async def _calcular_monto(self, activo: ActivoFijo) -> float:
        costo = float(activo.costo_adquisicion)
        valor_residual = float(activo.valor_residual)
        vida_util = activo.vida_util_anos

        if activo.metodo_depreciacion == "LINEA_RECTA":
            return calcular_linea_recta(costo, valor_residual, vida_util)
        elif activo.metodo_depreciacion == "DOBLE_DECLINANTE":
            return calcular_doble_declinante(
                costo, valor_residual, vida_util, float(activo.depreciacion_acumulada)
            )
        elif activo.metodo_depreciacion == "SUMA_DIGITOS":
            result = await self.db.execute(
                select(func.count(DepreciacionLinea.id)).where(DepreciacionLinea.activo_id == activo.id)
            )
            anos_transcurridos = result.scalar() or 0
            return calcular_suma_digitos(costo, valor_residual, vida_util, anos_transcurridos)
        else:
            raise ValueError(f"Metodo de depreciacion no soportado: {activo.metodo_depreciacion}")

    async def dar_baja(self, activo_id: uuid.UUID, fecha_baja: date, motivo_baja: str) -> dict:
        result = await self.db.execute(
            select(ActivoFijo).where(
                ActivoFijo.id == activo_id,
                ActivoFijo.empresa_id == self.empresa_id,
            )
        )
        activo = result.scalar_one_or_none()
        if not activo:
            raise ValueError("Activo no encontrado")
        if activo.estado == "BAJA":
            raise ValueError("Activo ya esta dado de baja")

        activo.estado = "BAJA"
        activo.fecha_baja = fecha_baja
        activo.motivo_baja = motivo_baja
        activo.updated_at = datetime.now()

        return {"mensaje": "Activo dado de baja exitosamente", "estado": "BAJA"}
