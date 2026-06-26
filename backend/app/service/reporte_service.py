from datetime import date
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import select, and_, func, case, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.asiento import Asiento, AsientoLinea
from app.domain.models.cuenta_contable import CuentaContable


class ReporteService:

    def __init__(self, db: AsyncSession, empresa_id: uuid.UUID):
        self.db = db
        self.empresa_id = empresa_id

    async def balance_comprobacion(
        self,
        fecha_corte: Optional[date] = None,
        periodo_id: Optional[uuid.UUID] = None,
        incluir_ceros: bool = False,
    ):
        query = """
        WITH saldos AS (
            SELECT
                c.id AS cuenta_id,
                c.codigo,
                c.nombre,
                c.tipo,
                c.nivel,
                c.acepta_datos,
                COALESCE(SUM(al.debe_local), 0) AS debe_local,
                COALESCE(SUM(al.haber_local), 0) AS haber_local,
                COALESCE(SUM(al.debe_dolar), 0) AS debe_dolar,
                COALESCE(SUM(al.haber_dolar), 0) AS haber_dolar
            FROM cuenta_contable c
            LEFT JOIN asiento_linea al ON al.cuenta_id = c.id
            LEFT JOIN asiento a ON a.id = al.asiento_id
                AND a.reversado = FALSE
                AND a.empresa_id = :empresa_id
        """

        params = {"empresa_id": self.empresa_id}

        if fecha_corte:
            query += " AND a.fecha <= :fecha_corte"
            params["fecha_corte"] = fecha_corte
        if periodo_id:
            query += " AND a.periodo_id = :periodo_id"
            params["periodo_id"] = periodo_id

        query += """
            WHERE c.empresa_id = :empresa_id
            GROUP BY c.id, c.codigo, c.nombre, c.tipo, c.nivel, c.acepta_datos
        )
        SELECT * FROM saldos
        """

        if not incluir_ceros:
            query += " WHERE (debe_local != 0 OR haber_local != 0)"

        query += " ORDER BY codigo"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        return [
            {
                "cuenta_id": str(r.cuenta_id),
                "codigo": r.codigo,
                "nombre": r.nombre,
                "tipo": r.tipo,
                "nivel": r.nivel,
                "acepta_datos": r.acepta_datos,
                "debe_local": float(r.debe_local),
                "haber_local": float(r.haber_local),
                "debe_dolar": float(r.debe_dolar),
                "haber_dolar": float(r.haber_dolar),
                "saldo_local": float(r.debe_local - r.haber_local),
                "saldo_dolar": float(r.debe_dolar - r.haber_dolar),
            }
            for r in rows
        ]

    async def balance_general(
        self, fecha_corte: date, periodo_id: Optional[uuid.UUID] = None
    ):
        saldos = await self.balance_comprobacion(
            fecha_corte=fecha_corte, periodo_id=periodo_id
        )

        activo = {"corriente": [], "no_corriente": [], "total": 0}
        pasivo = {"corriente": [], "no_corriente": [], "total": 0}
        patrimonio = {"cuentas": [], "total": 0}

        for s in saldos:
            if s["tipo"] == "ACTIVO":
                if s["nivel"] <= 2:
                    continue
                total = s["saldo_local"]
                if total != 0:
                    if self._es_corriente(s["codigo"]):
                        activo["corriente"].append(s)
                    else:
                        activo["no_corriente"].append(s)
                activo["total"] += total

            elif s["tipo"] == "PASIVO":
                if s["nivel"] <= 2:
                    continue
                total = s["saldo_local"]
                if total != 0:
                    if self._es_corriente(s["codigo"]):
                        pasivo["corriente"].append(s)
                    else:
                        pasivo["no_corriente"].append(s)
                pasivo["total"] += total

            elif s["tipo"] == "PATRIMONIO":
                if s["nivel"] <= 2:
                    continue
                total = s["saldo_local"]
                if total != 0:
                    patrimonio["cuentas"].append(s)
                patrimonio["total"] += total

        return {
            "fecha_corte": str(fecha_corte),
            "activo": {
                "corriente": {
                    "cuentas": activo["corriente"],
                    "total": float(activo["total"]),
                },
                "no_corriente": {
                    "cuentas": activo["no_corriente"],
                    "total": float(sum(
                        s["saldo_local"] for s in activo["no_corriente"]
                    )),
                },
                "total_activo": float(activo["total"]),
            },
            "pasivo": {
                "corriente": {
                    "cuentas": pasivo["corriente"],
                    "total": float(pasivo["total"]),
                },
                "no_corriente": {
                    "cuentas": pasivo["no_corriente"],
                    "total": float(sum(
                        s["saldo_local"] for s in pasivo["no_corriente"]
                    )),
                },
                "total_pasivo": float(pasivo["total"]),
            },
            "patrimonio": {
                "cuentas": patrimonio["cuentas"],
                "total": float(patrimonio["total"]),
            },
            "total_pasivo_patrimonio": float(pasivo["total"] + patrimonio["total"]),
        }

    async def estado_resultados(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        periodo_id: Optional[uuid.UUID] = None,
    ):
        query = """
        SELECT
            c.id AS cuenta_id,
            c.codigo,
            c.nombre,
            c.tipo,
            c.nivel,
            COALESCE(SUM(al.haber_local - al.debe_local), 0) AS saldo_local,
            COALESCE(SUM(al.haber_dolar - al.debe_dolar), 0) AS saldo_dolar
        FROM cuenta_contable c
        LEFT JOIN asiento_linea al ON al.cuenta_id = c.id
        LEFT JOIN asiento a ON a.id = al.asiento_id
            AND a.reversado = FALSE
            AND a.empresa_id = :empresa_id
            AND a.fecha BETWEEN :fecha_inicio AND :fecha_fin
        WHERE c.empresa_id = :empresa_id
            AND c.tipo IN ('INGRESO', 'GASTO', 'COSTO')
        GROUP BY c.id, c.codigo, c.nombre, c.tipo, c.nivel
        HAVING COALESCE(SUM(al.haber_local - al.debe_local), 0) != 0
        ORDER BY c.tipo, c.codigo
        """

        result = await self.db.execute(
            text(query),
            {
                "empresa_id": self.empresa_id,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
            },
        )
        rows = result.fetchall()

        ingresos = []
        costos = []
        gastos = []
        total_ingresos = 0
        total_costos = 0
        total_gastos = 0

        for r in rows:
            item = {
                "cuenta_id": str(r.cuenta_id),
                "codigo": r.codigo,
                "nombre": r.nombre,
                "saldo_local": float(abs(r.saldo_local)),
                "saldo_dolar": float(abs(r.saldo_dolar)),
            }
            if r.tipo == "INGRESO":
                ingresos.append(item)
                total_ingresos += float(r.saldo_local)
            elif r.tipo == "COSTO":
                costos.append(item)
                total_costos += float(r.saldo_local)
            elif r.tipo == "GASTO":
                gastos.append(item)
                total_gastos += float(r.saldo_local)

        utilidad_bruta = total_ingresos - total_costos
        utilidad_neta = utilidad_bruta - total_gastos

        return {
            "periodo": f"{fecha_inicio} - {fecha_fin}",
            "ingresos": {
                "cuentas": ingresos,
                "total": float(total_ingresos),
            },
            "costos": {
                "cuentas": costos,
                "total": float(total_costos),
            },
            "utilidad_bruta": float(utilidad_bruta),
            "gastos": {
                "cuentas": gastos,
                "total": float(total_gastos),
            },
            "utilidad_neta": float(utilidad_neta),
        }

    async def mayor_general(
        self,
        cuenta_id: Optional[uuid.UUID] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        periodo_id: Optional[uuid.UUID] = None,
    ):
        query = """
        SELECT
            a.fecha,
            a.numero AS asiento_numero,
            a.tipo AS asiento_tipo,
            a.concepto AS asiento_concepto,
            al.descripcion,
            c.codigo AS cuenta_codigo,
            c.nombre AS cuenta_nombre,
            al.debe_local,
            al.haber_local,
            al.debe_dolar,
            al.haber_dolar,
            cc.codigo AS centro_costo_codigo,
            cc.nombre AS centro_costo_nombre
        FROM asiento_linea al
        JOIN asiento a ON a.id = al.asiento_id AND a.reversado = FALSE
        JOIN cuenta_contable c ON c.id = al.cuenta_id
        LEFT JOIN centro_costo cc ON cc.id = al.centro_costo_id
        WHERE a.empresa_id = :empresa_id
        """

        params = {"empresa_id": self.empresa_id}

        if cuenta_id:
            query += " AND al.cuenta_id = :cuenta_id"
            params["cuenta_id"] = cuenta_id
        if fecha_desde:
            query += " AND a.fecha >= :fecha_desde"
            params["fecha_desde"] = fecha_desde
        if fecha_hasta:
            query += " AND a.fecha <= :fecha_hasta"
            params["fecha_hasta"] = fecha_hasta
        if periodo_id:
            query += " AND a.periodo_id = :periodo_id"
            params["periodo_id"] = periodo_id

        query += " ORDER BY a.fecha, a.numero, al.orden"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        movimientos = []
        saldo_local = 0
        saldo_dolar = 0

        for r in rows:
            dl = float(r.debe_local or 0)
            hl = float(r.haber_local or 0)
            dd = float(r.debe_dolar or 0)
            hd = float(r.haber_dolar or 0)
            saldo_local += dl - hl
            saldo_dolar += dd - hd

            movimientos.append({
                "fecha": str(r.fecha),
                "asiento_numero": r.asiento_numero,
                "asiento_tipo": r.asiento_tipo,
                "asiento_concepto": r.asiento_concepto,
                "descripcion": r.descripcion,
                "cuenta_codigo": r.cuenta_codigo,
                "cuenta_nombre": r.cuenta_nombre,
                "debe_local": dl,
                "haber_local": hl,
                "debe_dolar": dd,
                "haber_dolar": hd,
                "saldo_local": saldo_local,
                "saldo_dolar": saldo_dolar,
                "centro_costo": f"{r.centro_costo_codigo} - {r.centro_costo_nombre}"
                if r.centro_costo_codigo
                else None,
            })

        return movimientos

    async def flujo_efectivo(
        self, fecha_inicio: date, fecha_fin: date
    ):
        cuentas_efectivo = await self.db.execute(
            select(CuentaContable).where(
                CuentaContable.empresa_id == self.empresa_id,
                CuentaContable.tipo == "ACTIVO",
                CuentaContable.codigo.like("1-1-1%"),
                CuentaContable.acepta_datos == True,
            )
        )
        cuentas = cuentas_efectivo.scalars().all()
        cuenta_ids = [c.id for c in cuentas]

        if not cuenta_ids:
            return {
                "periodo": f"{fecha_inicio} - {fecha_fin}",
                "actividades_operacion": {"ingresos": 0, "egresos": 0, "neto": 0, "movimientos": []},
                "actividades_inversion": {"ingresos": 0, "egresos": 0, "neto": 0, "movimientos": []},
                "actividades_financiamiento": {"ingresos": 0, "egresos": 0, "neto": 0, "movimientos": []},
                "variacion_neta": 0,
            }

        stmt = select(
            Asiento.fecha,
            Asiento.numero,
            Asiento.concepto,
            Asiento.tipo,
            AsientoLinea.debe_local,
            AsientoLinea.haber_local,
            AsientoLinea.descripcion,
        ).join(
            Asiento, AsientoLinea.asiento_id == Asiento.id
        ).where(
            Asiento.reversado == False,
            Asiento.empresa_id == self.empresa_id,
            AsientoLinea.cuenta_id.in_(cuenta_ids),
            Asiento.fecha.between(fecha_inicio, fecha_fin),
        ).order_by(Asiento.fecha, Asiento.numero)

        result = await self.db.execute(stmt)
        rows = result.fetchall()

        actividades = {
            "operacion": {"ingresos": 0, "egresos": 0, "movimientos": []},
            "inversion": {"ingresos": 0, "egresos": 0, "movimientos": []},
            "financiamiento": {"ingresos": 0, "egresos": 0, "movimientos": []},
        }

        for r in rows:
            monto = float(r.debe_local or 0) - float(r.haber_local or 0)
            tipo = self._clasificar_flujo(r.tipo, r.concepto)

            item = {
                "fecha": str(r.fecha),
                "numero": r.numero,
                "concepto": r.concepto,
                "descripcion": r.descripcion,
                "monto": abs(monto),
                "tipo_movimiento": "entrada" if monto > 0 else "salida",
            }

            if tipo == "operacion":
                if monto > 0:
                    actividades["operacion"]["ingresos"] += monto
                else:
                    actividades["operacion"]["egresos"] += abs(monto)
                actividades["operacion"]["movimientos"].append(item)
            elif tipo == "inversion":
                if monto > 0:
                    actividades["inversion"]["ingresos"] += monto
                else:
                    actividades["inversion"]["egresos"] += abs(monto)
                actividades["inversion"]["movimientos"].append(item)
            else:
                if monto > 0:
                    actividades["financiamiento"]["ingresos"] += monto
                else:
                    actividades["financiamiento"]["egresos"] += abs(monto)
                actividades["financiamiento"]["movimientos"].append(item)

        resultado = {
            "periodo": f"{fecha_inicio} - {fecha_fin}",
            "actividades_operacion": {
                "ingresos": actividades["operacion"]["ingresos"],
                "egresos": actividades["operacion"]["egresos"],
                "neto": actividades["operacion"]["ingresos"] - actividades["operacion"]["egresos"],
                "movimientos": actividades["operacion"]["movimientos"],
            },
            "actividades_inversion": {
                "ingresos": actividades["inversion"]["ingresos"],
                "egresos": actividades["inversion"]["egresos"],
                "neto": actividades["inversion"]["ingresos"] - actividades["inversion"]["egresos"],
                "movimientos": actividades["inversion"]["movimientos"],
            },
            "actividades_financiamiento": {
                "ingresos": actividades["financiamiento"]["ingresos"],
                "egresos": actividades["financiamiento"]["egresos"],
                "neto": actividades["financiamiento"]["ingresos"] - actividades["financiamiento"]["egresos"],
                "movimientos": actividades["financiamiento"]["movimientos"],
            },
            "variacion_neta": (
                actividades["operacion"]["ingresos"] - actividades["operacion"]["egresos"]
                + actividades["inversion"]["ingresos"] - actividades["inversion"]["egresos"]
                + actividades["financiamiento"]["ingresos"] - actividades["financiamiento"]["egresos"]
            ),
        }

        return resultado

    def _es_corriente(self, codigo: str) -> bool:
        return codigo.startswith("1-1-") or codigo.startswith("2-1-")

    def _clasificar_flujo(self, tipo_asiento: str, concepto: str) -> str:
        tipo = tipo_asiento.upper() if tipo_asiento else ""
        if tipo in ("COMPRA", "VENTA", "CAJA", "COBRO", "PAGO", "DIARIO"):
            return "operacion"
        if tipo in ("INVERSION", "ACTIVO_FIJO"):
            return "inversion"
        if tipo in ("APERTURA", "CIERRE", "CAPITAL"):
            return "financiamiento"
        return "operacion"
