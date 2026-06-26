from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.models.asiento import Asiento, AsientoLinea
from app.domain.models.periodo import PeriodoContable
from app.domain.models.cuenta_contable import CuentaContable
from app.service.auditoria_service import AuditoriaService


class PartidaDobleError(Exception):
    pass


class PeriodoCerradoError(Exception):
    pass


class CuentaNoValidaError(Exception):
    pass


class AsientoService:

    def __init__(self, db: AsyncSession, usuario_id: uuid.UUID, empresa_id: uuid.UUID):
        self.db = db
        self.usuario_id = usuario_id
        self.empresa_id = empresa_id

    async def _validar_periodo(self, periodo_id: uuid.UUID) -> PeriodoContable:
        result = await self.db.execute(
            select(PeriodoContable).where(
                PeriodoContable.id == periodo_id,
                PeriodoContable.empresa_id == self.empresa_id,
            )
        )
        periodo = result.scalar_one_or_none()
        if not periodo:
            raise ValueError("Periodo contable no encontrado")
        if periodo.cerrado:
            raise PeriodoCerradoError(f"El periodo {periodo.codigo} esta cerrado")
        return periodo

    async def _validar_cuenta(self, cuenta_id: uuid.UUID) -> CuentaContable:
        result = await self.db.execute(
            select(CuentaContable).where(
                CuentaContable.id == cuenta_id,
                CuentaContable.empresa_id == self.empresa_id,
                CuentaContable.activa == True,
            )
        )
        cuenta = result.scalar_one_or_none()
        if not cuenta:
            raise CuentaNoValidaError(f"Cuenta contable no encontrada o inactiva")
        if not cuenta.acepta_datos:
            raise CuentaNoValidaError(
                f"La cuenta {cuenta.codigo} - {cuenta.nombre} no acepta datos (es cuenta padre)"
            )
        return cuenta

    async def _validar_partida_doble(self, lineas: list[dict]) -> tuple[Decimal, Decimal]:
        total_debe = sum(Decimal(str(l.get("debe_local", 0))) for l in lineas)
        total_haber = sum(Decimal(str(l.get("haber_local", 0))) for l in lineas)
        if total_debe != total_haber:
            raise PartidaDobleError(
                f"La partida doble no cuadra: Debe={total_debe} vs Haber={total_haber}"
            )
        if total_debe == 0:
            raise PartidaDobleError("El asiento no puede tener montos en cero")
        return total_debe, total_haber

    async def _obtener_siguiente_numero(self, periodo_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.coalesce(func.max(Asiento.numero), 0) + 1).where(
                Asiento.empresa_id == self.empresa_id,
                Asiento.periodo_id == periodo_id,
            )
        )
        return result.scalar()

    async def crear_asiento(
        self,
        fecha: date,
        periodo_id: uuid.UUID,
        tipo: str,
        concepto: str,
        lineas_data: list[dict],
        origen_modulo: Optional[str] = None,
        origen_documento_id: Optional[uuid.UUID] = None,
    ) -> Asiento:
        periodo = await self._validar_periodo(periodo_id)

        if not (periodo.fecha_inicio <= fecha <= periodo.fecha_fin):
            raise ValueError(
                f"La fecha {fecha} no corresponde al periodo {periodo.codigo} "
                f"({periodo.fecha_inicio} - {periodo.fecha_fin})"
            )

        total_debe, total_haber = await self._validar_partida_doble(lineas_data)

        for l in lineas_data:
            await self._validar_cuenta(l["cuenta_id"])

        numero = await self._obtener_siguiente_numero(periodo_id)

        asiento = Asiento(
            empresa_id=self.empresa_id,
            numero=numero,
            fecha=fecha,
            periodo_id=periodo_id,
            tipo=tipo,
            concepto=concepto,
            origen_modulo=origen_modulo,
            origen_documento_id=origen_documento_id,
            creado_por=self.usuario_id,
        )
        self.db.add(asiento)
        await self.db.flush()

        for i, l in enumerate(lineas_data):
            linea = AsientoLinea(
                asiento_id=asiento.id,
                cuenta_id=l["cuenta_id"],
                centro_costo_id=l.get("centro_costo_id"),
                descripcion=l.get("descripcion"),
                debe_local=Decimal(str(l.get("debe_local", 0))),
                haber_local=Decimal(str(l.get("haber_local", 0))),
                debe_dolar=Decimal(str(l.get("debe_dolar", 0))),
                haber_dolar=Decimal(str(l.get("haber_dolar", 0))),
                orden=i + 1,
            )
            self.db.add(linea)

        await self.db.commit()
        await self.db.refresh(asiento)

        audit = AuditoriaService(self.db)
        await audit.log_asiento(
            usuario_id=self.usuario_id,
            empresa_id=self.empresa_id,
            asiento_id=asiento.id,
            asiento_data={
                "numero": asiento.numero,
                "fecha": str(asiento.fecha),
                "tipo": asiento.tipo,
                "concepto": asiento.concepto,
                "total_debe": float(total_debe),
                "total_haber": float(total_haber),
            },
        )

        return asiento

    async def reversar_asiento(self, asiento_id: uuid.UUID, motivo: str) -> Asiento:
        result = await self.db.execute(
            select(Asiento)
            .options(joinedload(Asiento.lineas))
            .where(Asiento.id == asiento_id, Asiento.empresa_id == self.empresa_id)
        )
        asiento_original = result.unique().scalar_one_or_none()
        if not asiento_original:
            raise ValueError("Asiento no encontrado")
        if asiento_original.reversado:
            raise ValueError("El asiento ya fue reversado")

        await self._validar_periodo(asiento_original.periodo_id)

        lineas_reversa = []
        for linea in asiento_original.lineas:
            lineas_reversa.append({
                "cuenta_id": linea.cuenta_id,
                "centro_costo_id": linea.centro_costo_id,
                "descripcion": f"REVERSA: {motivo}",
                "debe_local": linea.haber_local,
                "haber_local": linea.debe_local,
                "debe_dolar": linea.haber_dolar,
                "haber_dolar": linea.debe_dolar,
            })

        asiento_reversa = await self.crear_asiento(
            fecha=datetime.now().date(),
            periodo_id=asiento_original.periodo_id,
            tipo="DIARIO",
            concepto=f"REVERSIÓN: {asiento_original.concepto} - {motivo}",
            lineas_data=lineas_reversa,
        )

        asiento_original.reversado = True
        asiento_original.asiento_reversa_id = asiento_reversa.id
        await self.db.commit()

        audit = AuditoriaService(self.db)
        await audit.log(
            usuario_id=self.usuario_id,
            empresa_id=self.empresa_id,
            tabla="asiento",
            registro_id=asiento_id,
            accion="REVERSAR",
            valor_anterior={"reversado": False},
            valor_nuevo={"reversado": True, "asiento_reversa_id": str(asiento_reversa.id)},
        )

        return asiento_reversa

    async def listar_asientos(
        self, periodo_id: Optional[uuid.UUID] = None, 
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        tipo: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ):
        query = (
            select(Asiento)
            .where(Asiento.empresa_id == self.empresa_id)
            .order_by(Asiento.fecha.desc(), Asiento.numero.desc())
        )

        if periodo_id:
            query = query.where(Asiento.periodo_id == periodo_id)
        if fecha_desde:
            query = query.where(Asiento.fecha >= fecha_desde)
        if fecha_hasta:
            query = query.where(Asiento.fecha <= fecha_hasta)
        if tipo:
            query = query.where(Asiento.tipo == tipo)

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def obtener_asiento(self, asiento_id: uuid.UUID) -> Asiento:
        result = await self.db.execute(
            select(Asiento)
            .options(joinedload(Asiento.lineas))
            .where(Asiento.id == asiento_id, Asiento.empresa_id == self.empresa_id)
        )
        return result.unique().scalar_one_or_none()
