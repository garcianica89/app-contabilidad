from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.proveedor import Proveedor
from app.domain.models.cliente import Cliente
from app.domain.models.factura_compra import FacturaCompra
from app.domain.models.factura_venta import FacturaVenta


class ClasificacionSugerida:
    def __init__(
        self,
        movimiento_idx: int,
        modulo: str,
        confianza: float,
        entidad_id: Optional[str] = None,
        entidad_tipo: Optional[str] = None,
        entidad_descripcion: Optional[str] = None,
        regla: Optional[str] = None,
    ):
        self.movimiento_idx = movimiento_idx
        self.modulo = modulo
        self.confianza = confianza
        self.entidad_id = entidad_id
        self.entidad_tipo = entidad_tipo
        self.entidad_descripcion = entidad_descripcion
        self.regla = regla

    def to_dict(self) -> dict:
        return {
            "movimiento_idx": self.movimiento_idx,
            "modulo": self.modulo,
            "confianza": self.confianza,
            "entidad_id": self.entidad_id,
            "entidad_tipo": self.entidad_tipo,
            "entidad_descripcion": self.entidad_descripcion,
            "regla": self.regla,
        }


class ClasificadorService:

    def __init__(self, db: AsyncSession, empresa_id: UUID):
        self.db = db
        self.empresa_id = empresa_id

    async def clasificar(self, movimientos: List[dict]) -> List[ClasificacionSugerida]:
        resultados = []

        for mov in movimientos:
            mejor = await self._mejor_clasificacion(mov)
            resultados.append(mejor)

        return resultados

    async def _mejor_clasificacion(self, mov: dict) -> ClasificacionSugerida:
        idx = mov.get("idx", 0)
        monto = abs(mov.get("monto", 0))
        concepto = (mov.get("concepto", "") or "").upper()
        referencia = (mov.get("referencia", "") or "").upper()
        fecha_str = mov.get("fecha", "")
        mov_fecha = date.fromisoformat(fecha_str) if isinstance(fecha_str, str) else fecha_str

        candidatos = []

        cxp = await self._match_cxp(monto, concepto, referencia, mov_fecha)
        if cxp:
            candidatos.append(cxp)

        cxc = await self._match_cxc(monto, concepto, referencia, mov_fecha)
        if cxc:
            candidatos.append(cxc)

        banco = await self._match_banco(concepto, referencia)
        if banco:
            candidatos.append(banco)

        if not candidatos:
            if monto > 0:
                return ClasificacionSugerida(idx, "CXC", 0.1, regla="INGRESO_SIN_CLASIFICAR")
            else:
                return ClasificacionSugerida(idx, "CXP", 0.1, regla="EGRESO_SIN_CLASIFICAR")

        candidatos.sort(key=lambda c: c.confianza, reverse=True)
        return candidatos[0]

    async def _match_cxp(self, monto: float, concepto: str, referencia: str, fecha: date) -> Optional[ClasificacionSugerida]:
        ventana = timedelta(days=5)
        result = await self.db.execute(
            select(FacturaCompra).where(
                FacturaCompra.empresa_id == self.empresa_id,
                FacturaCompra.estado.notin_(["PAGADA", "ANULADA"]),
                or_(
                    func.abs(FacturaCompra.total - monto) < 0.02,
                    func.abs(FacturaCompra.total - monto) / func.nullif(FacturaCompra.total, 0) < 0.01,
                ),
                func.abs(func.extract('epoch', FacturaCompra.fecha - fecha)) < ventana.days * 86400,
            ).limit(5)
        )
        facturas = result.scalars().all()

        if not facturas:
            result = await self.db.execute(
                select(FacturaCompra).where(
                    FacturaCompra.empresa_id == self.empresa_id,
                    FacturaCompra.estado.notin_(["PAGADA", "ANULADA"]),
                    func.abs(FacturaCompra.total - monto) < 0.02,
                ).limit(5)
            )
            facturas = result.scalars().all()

        facturas = [f for f in facturas if f.total is not None]

        if not facturas:
            if "PAGO" in concepto or "PROVEED" in concepto or "CXP" in concepto:
                return ClasificacionSugerida(0, "CXP", 0.4, regla="KEYWORD_CXP")
            return None

        mejor = min(facturas, key=lambda f: abs(float(f.total) - monto))

        proveedor = await self.db.get(Proveedor, mejor.proveedor_id)
        nombre_prov = proveedor.nombre if proveedor else "Desconocido"

        confianza = 0.9 if abs(float(mejor.total) - monto) < 0.01 else 0.7

        return ClasificacionSugerida(
            movimiento_idx=0,
            modulo="CXP",
            confianza=confianza,
            entidad_id=str(mejor.id),
            entidad_tipo="FacturaCompra",
            entidad_descripcion=f"Pago Factura #{mejor.numero} - {nombre_prov} (${float(mejor.total):.2f})",
            regla="MONTO_FECHA_MATCH" if confianza > 0.8 else "MONTO_MATCH",
        )

    async def _match_cxc(self, monto: float, concepto: str, referencia: str, fecha: date) -> Optional[ClasificacionSugerida]:
        ventana = timedelta(days=5)
        result = await self.db.execute(
            select(FacturaVenta).where(
                FacturaVenta.empresa_id == self.empresa_id,
                FacturaVenta.estado.notin_(["COBRADA", "ANULADA"]),
                or_(
                    func.abs(FacturaVenta.total - monto) < 0.02,
                    func.abs(FacturaVenta.total - monto) / func.nullif(FacturaVenta.total, 0) < 0.01,
                ),
                func.abs(func.extract('epoch', FacturaVenta.fecha - fecha)) < ventana.days * 86400,
            ).limit(5)
        )
        facturas = result.scalars().all()

        if not facturas:
            result = await self.db.execute(
                select(FacturaVenta).where(
                    FacturaVenta.empresa_id == self.empresa_id,
                    FacturaVenta.estado.notin_(["COBRADA", "ANULADA"]),
                    func.abs(FacturaVenta.total - monto) < 0.02,
                ).limit(5)
            )
            facturas = result.scalars().all()

        facturas = [f for f in facturas if f.total is not None]

        if not facturas:
            if "COBRO" in concepto or "CLIENT" in concepto or "CXC" in concepto or "DEPOSITO" in concepto:
                return ClasificacionSugerida(0, "CXC", 0.4, regla="KEYWORD_CXC")
            return None

        mejor = min(facturas, key=lambda f: abs(float(f.total) - monto))

        cliente = await self.db.get(Cliente, mejor.cliente_id)
        nombre_cli = cliente.nombre if cliente else "Desconocido"

        confianza = 0.9 if abs(float(mejor.total) - monto) < 0.01 else 0.7

        return ClasificacionSugerida(
            movimiento_idx=0,
            modulo="CXC",
            confianza=confianza,
            entidad_id=str(mejor.id),
            entidad_tipo="FacturaVenta",
            entidad_descripcion=f"Cobro Factura #{mejor.numero} - {nombre_cli} (${float(mejor.total):.2f})",
            regla="MONTO_FECHA_MATCH" if confianza > 0.8 else "MONTO_MATCH",
        )

    async def _match_banco(self, concepto: str, referencia: str) -> Optional[ClasificacionSugerida]:
        bancos = ["COMISION", "INTERES", "MANTENIMIENTO", "CARGO", "NOTA DEBITO",
                   "NOTA CREDITO", "TRANSFERENCIA", "CHEQUE", "RETIRO", "DEPOSITO"]
        for keyword in bancos:
            if keyword in concepto:
                return ClasificacionSugerida(
                    movimiento_idx=0,
                    modulo="BANCO",
                    confianza=0.5,
                    entidad_tipo="MovimientoBanco",
                    entidad_descripcion=f"Movimiento Bancario: {concepto[:60]}",
                    regla=f"KEYWORD_BANCO_{keyword}",
                )
        return None
