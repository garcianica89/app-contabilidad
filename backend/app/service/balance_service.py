from datetime import date
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.accounting.models import Account, AccountType, CierreMensual
from app.domain.models.asiento import Asiento, AsientoLinea
from app.domain.models.periodo import PeriodoContable


class BalanceService:
    """Service for trial balance (balanza de comprobacion) with cached monthly snapshots."""

    def __init__(self, db: AsyncSession, empresa_id: uuid.UUID):
        self.db = db
        self.empresa_id = empresa_id

    # ── Public API ──

    async def balance_comprobacion(
        self,
        *,
        periodo_id: uuid.UUID | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        cuenta_id: uuid.UUID | None = None,
        nivel_maximo: int = 99,
        centro_costo_id: uuid.UUID | None = None,
        solo_diario: bool = False,
    ) -> list[dict]:
        """Returns hierarchical trial balance rows."""
        # 1. Resolve date range from periodo or params
        fecha_corte, periodo_inicio = await self._resolver_fechas(periodo_id, fecha_desde, fecha_hasta)

        # 2. Get all accounts for this company (up to nivel_maximo)
        cuentas = await self._get_cuentas(nivel_maximo, cuenta_id)

        # 3. Try to use cached balances
        saldo_anterior_map: dict = {}
        debe_haber_map: dict = {}

        if periodo_id and not centro_costo_id and not solo_diario:
            saldo_anterior_map, debe_haber_map = await self._cargar_desde_cache(
                periodo_id, centro_costo_id
            )

        # 4. For accounts without cache, compute from asientos
        cuentas_sin_cache = [
            c for c in cuentas
            if c["id"] not in debe_haber_map
        ]

        if cuentas_sin_cache or not periodo_id:
            debe_haber_directo = await self._sumar_asientos(
                fecha_corte=fecha_corte,
                periodo_inicio=periodo_inicio,
                cuenta_ids=[c["id"] for c in cuentas_sin_cache or cuentas],
                centro_costo_id=centro_costo_id,
                solo_diario=solo_diario,
            )
            for k, v in debe_haber_directo.items():
                debe_haber_map[k] = v

        # 5. Build result rows
        rows = []
        for c in cuentas:
            info = debe_haber_map.get(c["id"], {"debe": Decimal("0"), "haber": Decimal("0")})
            saldo_ant = saldo_anterior_map.get(c["id"], Decimal("0"))
            debe = info["debe"]
            haber = info["haber"]

            saldo_final = self._calcular_saldo_final(c["naturaleza"], saldo_ant, debe, haber)
            saldo_deudor, saldo_acreedor = self._separar_saldo(c["naturaleza"], saldo_final)

            rows.append({
                "cuenta_id": str(c["id"]),
                "codigo": c["codigo"],
                "nombre": c["nombre"],
                "nivel": c["nivel"],
                "naturaleza": c["naturaleza"],
                "tipo": c["tipo"],
                "padre_id": str(c["padre_id"]) if c["padre_id"] else None,
                "saldo_anterior": float(saldo_ant),
                "debe": float(debe),
                "haber": float(haber),
                "saldo_final": float(saldo_final),
                "saldo_deudor": float(saldo_deudor),
                "saldo_acreedor": float(saldo_acreedor),
            })

        return rows

    async def recalcular_saldos(
        self,
        periodo_id: uuid.UUID,
        cuenta_id: uuid.UUID | None = None,
        centro_costo_id: uuid.UUID | None = None,
    ) -> int:
        """Recalculate and cache account balances for a given period."""
        # 1. Get the period
        periodo = await self.db.get(PeriodoContable, periodo_id)
        if not periodo or periodo.empresa_id != self.empresa_id:
            raise ValueError("Periodo no encontrado")

        # 2. Get previous period's balance as saldo_anterior
        periodo_anterior = await self._get_periodo_anterior(periodo)

        # 3. Get accounts
        query = select(
            Account.id,
            Account.code,
            Account.account_type_id,
            AccountType.nature,
            AccountType.code.label("tipo_code"),
        ).join(AccountType, Account.account_type_id == AccountType.id)
        if cuenta_id:
            query = query.where(Account.id == cuenta_id)
        rows = await self.db.execute(
            query.where(
                Account.company_id == self.empresa_id,
                Account.is_active == True,
            )
        )
        cuentas = rows.fetchall()

        # 4. Get saldos from previous period
        saldo_ant_map: dict[uuid.UUID, Decimal] = {}
        if periodo_anterior:
            r = await self.db.execute(
                text("""
                    SELECT cuenta_id, saldo_final
                    FROM cuenta_saldo
                    WHERE empresa_id = :emp_id
                      AND periodo_id = :per_id
                """),
                {"emp_id": self.empresa_id, "per_id": periodo_anterior.id},
            )
            for row in r.fetchall():
                saldo_ant_map[row.cuenta_id] = Decimal(str(row.saldo_final or 0))

        # 5. Sum movements for the period
        count = 0
        for c in cuentas:
            r = await self.db.execute(
                text("""
                    SELECT
                        COALESCE(SUM(al.debe), 0) AS debe,
                        COALESCE(SUM(al.haber), 0) AS haber
                    FROM asiento_linea al
                    JOIN asiento a ON a.id = al.asiento_id
                        AND a.reversado = FALSE
                        AND a.empresa_id = :emp_id
                        AND a.periodo_id = :per_id
                    WHERE al.cuenta_id = :cta_id
                """),
                {"emp_id": self.empresa_id, "per_id": periodo_id, "cta_id": c.id},
            )
            mov = r.fetchone()
            debe = Decimal(str(mov.debe or 0))
            haber = Decimal(str(mov.haber or 0))
            saldo_ant = saldo_ant_map.get(c.id, Decimal("0"))
            saldo_final = self._calcular_saldo_final(c.nature, saldo_ant, debe, haber)

            # Upsert
            await self.db.execute(
                text("""
                    INSERT INTO cuenta_saldo
                        (empresa_id, cuenta_id, periodo_id, centro_costo_id,
                         saldo_anterior, debe, haber, saldo_final, naturaleza, recalculado_en)
                    VALUES
                        (:emp_id, :cta_id, :per_id, :cc_id,
                         :saldo_ant, :debe, :haber, :saldo_final, :naturaleza, now())
                    ON CONFLICT (empresa_id, cuenta_id, periodo_id, centro_costo_id)
                    DO UPDATE SET
                        saldo_anterior = EXCLUDED.saldo_anterior,
                        debe = EXCLUDED.debe,
                        haber = EXCLUDED.haber,
                        saldo_final = EXCLUDED.saldo_final,
                        recalculado_en = now()
                """),
                {
                    "emp_id": self.empresa_id,
                    "cta_id": c.id,
                    "per_id": periodo_id,
                    "cc_id": centro_costo_id,
                    "saldo_ant": float(saldo_ant),
                    "debe": float(debe),
                    "haber": float(haber),
                    "saldo_final": float(saldo_final),
                    "naturaleza": c.nature,
                },
            )
            count += 1

        await self.db.commit()
        return count

    # ── Internal helpers ──

    async def _resolver_fechas(
        self,
        periodo_id: uuid.UUID | None,
        fecha_desde: date | None,
        fecha_hasta: date | None,
    ) -> tuple[date, date | None]:
        if periodo_id:
            periodo = await self.db.get(PeriodoContable, periodo_id)
            if periodo and periodo.empresa_id == self.empresa_id:
                return periodo.fecha_fin, periodo.fecha_inicio
        fecha_corte = fecha_hasta or date.today()
        return fecha_corte, fecha_desde

    async def _get_cuentas(
        self,
        nivel_maximo: int,
        cuenta_id: uuid.UUID | None,
    ) -> list[dict]:
        query = select(
            Account.id,
            Account.code,
            Account.name,
            Account.level,
            Account.parent_id,
            AccountType.nature,
            AccountType.code.label("tipo"),
        ).join(AccountType, Account.account_type_id == AccountType.id).where(
            Account.company_id == self.empresa_id,
            Account.is_active == True,
            Account.level <= nivel_maximo,
        ).order_by(Account.code)

        if cuenta_id:
            # Include the account and all its descendants
            query = query.where(
                Account.id == cuenta_id
            )

        rows = await self.db.execute(query)
        return [
            {
                "id": r.id,
                "codigo": r.code,
                "nombre": r.name,
                "nivel": r.level,
                "padre_id": r.parent_id,
                "naturaleza": r.nature,
                "tipo": r.tipo,
            }
            for r in rows.fetchall()
        ]

    async def _cargar_desde_cache(
        self,
        periodo_id: uuid.UUID,
        centro_costo_id: uuid.UUID | None,
    ) -> tuple[dict, dict]:
        """Load balances from cuenta_saldo cache table."""
        saldo_ant: dict = {}
        debe_haber: dict = {}

        r = await self.db.execute(
            text("""
                SELECT
                    cs.cuenta_id,
                    cs.saldo_anterior,
                    cs.debe,
                    cs.haber,
                    cs.saldo_final
                FROM cuenta_saldo cs
                WHERE cs.empresa_id = :emp_id
                  AND cs.periodo_id = :per_id
                  AND (cs.centro_costo_id IS NULL OR cs.centro_costo_id = :cc_id)
            """),
            {"emp_id": self.empresa_id, "per_id": periodo_id, "cc_id": centro_costo_id},
        )
        for row in r.fetchall():
            cid = row.cuenta_id
            saldo_ant[cid] = Decimal(str(row.saldo_anterior or 0))
            debe_haber[cid] = {
                "debe": Decimal(str(row.debe or 0)),
                "haber": Decimal(str(row.haber or 0)),
            }

        return saldo_ant, debe_haber

    async def _sumar_asientos(
        self,
        fecha_corte: date,
        periodo_inicio: date | None,
        cuenta_ids: list[uuid.UUID],
        centro_costo_id: uuid.UUID | None,
        solo_diario: bool,
    ) -> dict:
        """Sum debe/haber from asiento_linea directly."""
        if not cuenta_ids:
            return {}

        params = {
            "emp_id": self.empresa_id,
            "fecha_corte": fecha_corte,
        }

        where_cc = ""
        if centro_costo_id:
            where_cc = " AND al.centro_costo_id = :cc_id"
            params["cc_id"] = centro_costo_id

        where_diario = ""
        if solo_diario:
            where_diario = " AND a.tipo = 'DIARIO'"

        periodo_filter = ""
        if periodo_inicio:
            periodo_filter = " AND a.fecha >= :fecha_desde"
            params["fecha_desde"] = periodo_inicio

        # Use IN clause for cuenta_ids (up to reasonable count)
        import itertools
        cuenta_ids_str = ",".join(f"'{cid}'" for cid in cuenta_ids)

        r = await self.db.execute(
            text(f"""
                SELECT
                    al.cuenta_id,
                    COALESCE(SUM(al.debe), 0) AS debe,
                    COALESCE(SUM(al.haber), 0) AS haber
                FROM asiento_linea al
                JOIN asiento a ON a.id = al.asiento_id
                    AND a.reversado = FALSE
                    AND a.empresa_id = :emp_id
                    AND a.fecha <= :fecha_corte
                    {periodo_filter}
                    {where_diario}
                WHERE al.cuenta_id IN ({cuenta_ids_str})
                    {where_cc}
                GROUP BY al.cuenta_id
            """),
            params,
        )
        result = {}
        for row in r.fetchall():
            result[row.cuenta_id] = {
                "debe": Decimal(str(row.debe or 0)),
                "haber": Decimal(str(row.haber or 0)),
            }
        return result

    async def _get_periodo_anterior(self, periodo: PeriodoContable) -> PeriodoContable | None:
        """Find the previous accounting period for the same company."""
        r = await self.db.execute(
            select(PeriodoContable).where(
                PeriodoContable.empresa_id == self.empresa_id,
                PeriodoContable.fecha_fin < periodo.fecha_inicio,
            ).order_by(PeriodoContable.fecha_fin.desc()).limit(1)
        )
        return r.scalar_one_or_none()

    def _calcular_saldo_final(
        self,
        naturaleza: str,
        saldo_anterior: Decimal,
        debe: Decimal,
        haber: Decimal,
    ) -> Decimal:
        """Calculate ending balance based on account nature."""
        if naturaleza == "DEUDORA":
            return saldo_anterior + debe - haber
        else:
            return saldo_anterior + haber - debe

    def _separar_saldo(
        self,
        naturaleza: str,
        saldo_final: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """
        Split balance into Deudor/Acreedor columns.
        For DEUDORA accounts:
          - Positive → Saldo Deudor
          - Negative → Saldo Acreedor (abnormal balance)
        For ACREEDORA accounts:
          - Positive → Saldo Acreedor
          - Negative → Saldo Deudor (abnormal balance)
        """
        if saldo_final >= 0:
            if naturaleza == "DEUDORA":
                return saldo_final, Decimal("0")
            else:
                return Decimal("0"), saldo_final
        else:
            # Negative balance — opposite column
            abs_val = abs(saldo_final)
            if naturaleza == "DEUDORA":
                return Decimal("0"), abs_val
            else:
                return abs_val, Decimal("0")
