"""
Accounting Engine — Servicio central de contabilizacion.

UNICO servicio autorizado para crear asientos.
Ningun modulo de negocio llama a INSERT INTO asiento directamente.

Flujo:
  1. Recibir evento desde DocumentEngine
  2. Buscar accounting_event por event_type + module
  3. Resolver journal_type (DIRECT, SUBTYPE, RULE, PARAM)
  4. Seleccionar plantilla (TemplateEngine)
  5. Validar partida doble
  6. Crear asiento (JournalEngine)
  7. Publicar evento ASIENTO_CONTABILIZADO
"""
import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.accounting.models import (
    AccountingEvent, JournalType, ModuleAccountingConfig,
)
from app.domain.models.asiento import Asiento, AsientoLinea
from app.domain.accounting.models import Account
from app.service.accounting.template_engine import TemplateEngine
from app.service.accounting.expression_evaluator import ExpressionEvaluator
from app.service.document_engine.engine import DocumentContext


class AccountingEngine:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.evaluator = ExpressionEvaluator()

    async def generate_from_document(self, ctx: DocumentContext) -> Optional[dict]:
        """
        Genera asiento contable desde un contexto de documento.

        Returns: { "asiento_id": uuid, "numero_asiento": str }
        """
        company_id = ctx.company_id
        event_data = ctx.data

        # 1. Buscar accounting_event
        event = await self._find_event(ctx.document_type, company_id)
        if not event:
            return None

        # 2. Resolver journal_type
        journal_type = await self._resolve_journal_type(event, ctx)
        if not journal_type:
            return None

        # 3. Crear contexto enriquecido para plantillas
        context = self._build_context(event_data, journal_type, ctx)
        module = event.module

        # 3b. Inyectar cuentas de categoria del tercero al contexto
        await self._inject_categoria_accounts(context, company_id)

        # 4. Ejecutar TemplateEngine
        from app.repository.accounting.repositories import (
            AccountRepository, JournalTypeRepository,
            ModuleAccountingConfigRepository,
        )
        account_repo = AccountRepository(self.db)
        journal_type_repo = JournalTypeRepository(self.db)
        config_repo = ModuleAccountingConfigRepository(self.db)

        # Resolver subtipo desde contexto
        subtype = None
        subtype_code = ctx.data.get('subtype_code', '')
        if subtype_code:
            from app.domain.models.document_type import DocumentoSubtipo
            r = await self.db.execute(
                select(DocumentoSubtipo).where(
                    DocumentoSubtipo.company_id == company_id,
                    DocumentoSubtipo.codigo == subtype_code,
                )
            )
            subtype = r.scalar_one_or_none()

        engine = TemplateEngine(
            account_repo=account_repo,
            journal_type_repo=journal_type_repo,
            config_repo=config_repo,
            evaluator=self.evaluator,
        )

        lines = await engine.generate(
            journal_type_code=journal_type.code,
            context=context,
            company_id=company_id,
            module=module,
            document_subtype=subtype,
        )

        # 5. Validar y crear asiento
        if not lines:
            return None

        return await self._create_entry(
            company_id=company_id,
            journal_type=journal_type,
            lines=lines,
            context=context,
            ctx=ctx,
        )

    async def generate_from_event(
        self,
        event_type: str,
        module: str,
        data: dict,
        company_id: uuid.UUID,
        document_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[dict]:
        """
        Genera asiento directamente desde un evento (uso interno).
        """
        from app.service.document_engine.engine import DocumentContext
        ctx = DocumentContext(
            document_type=event_type,
            subtype_code='',
            action='CREATE',
            data=data,
            user_id=user_id or uuid.uuid4(),
            company_id=company_id,
            document_id=document_id or uuid.uuid4(),
        )
        return await self.generate_from_document(ctx)

    async def _find_event(self, document_type: str, company_id: uuid.UUID) -> Optional[AccountingEvent]:
        q = select(AccountingEvent).where(
            AccountingEvent.company_id == company_id,
            AccountingEvent.code == document_type,
            AccountingEvent.is_active == True,
        )
        r = await self.db.execute(q)
        return r.scalar_one_or_none()

    async def _resolve_journal_type(
        self, event: AccountingEvent, ctx: DocumentContext,
    ) -> Optional[JournalType]:
        resolution = event.journal_type_resolution

        if resolution == 'DIRECT' and event.journal_type_id:
            q = select(JournalType).where(JournalType.id == event.journal_type_id)
            r = await self.db.execute(q)
            return r.scalar_one_or_none()

        if resolution == 'SUBTYPE':
            subtype = ctx.data.get('subtype_code', '')
            q = select(JournalType).where(
                JournalType.company_id == ctx.company_id,
                JournalType.code == f"{ctx.document_type}_{subtype}",
                JournalType.is_active == True,
            )
            r = await self.db.execute(q)
            return r.scalar_one_or_none()

        if resolution == 'RULE' and event.journal_type_rule_id:
            from app.service.rule_engine import RuleEngine
            reng = RuleEngine(self.db)
            rules = await reng._get_active_rules(event.module, ctx.company_id)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("RULE resolution not fully implemented; rules found: %d", len(rules))
            return None

        if resolution == 'PARAM' and event.journal_type_param_key:
            param_val = ctx.data.get(event.journal_type_param_key)
            if param_val:
                q = select(JournalType).where(
                    JournalType.company_id == ctx.company_id,
                    JournalType.code == param_val,
                )
                r = await self.db.execute(q)
                return r.scalar_one_or_none()

        return None

    async def _inject_categoria_accounts(self, context: dict, company_id: uuid.UUID):
        cliente_id = context.get('cliente_id')
        proveedor_id = context.get('proveedor_id')
        tercero_id = cliente_id or proveedor_id
        if not tercero_id:
            return
        from app.domain.models.categoria_cliente import CategoriaCliente
        from app.domain.models.categoria_proveedor import CategoriaProveedor
        if cliente_id:
            from app.domain.models.cliente import Cliente
            row = await self.db.get(Cliente, uuid.UUID(str(cliente_id)))
            if row and row.categoria_id:
                cat = await self.db.get(CategoriaCliente, row.categoria_id)
                if cat:
                    if cat.cuenta_tercero_id:
                        context['cuenta_tercero_id'] = str(cat.cuenta_tercero_id)
                    if cat.cuenta_banco_id:
                        context['cuenta_banco_id'] = str(cat.cuenta_banco_id)
                    if cat.cuenta_caja_id:
                        context['cuenta_caja_id'] = str(cat.cuenta_caja_id)
        elif proveedor_id:
            from app.domain.models.proveedor import Proveedor
            row = await self.db.get(Proveedor, uuid.UUID(str(proveedor_id)))
            if row and row.categoria_id:
                cat = await self.db.get(CategoriaProveedor, row.categoria_id)
                if cat:
                    if cat.cuenta_tercero_id:
                        context['cuenta_tercero_id'] = str(cat.cuenta_tercero_id)
                    if cat.cuenta_banco_id:
                        context['cuenta_banco_id'] = str(cat.cuenta_banco_id)
                    if cat.cuenta_caja_id:
                        context['cuenta_caja_id'] = str(cat.cuenta_caja_id)

    def _build_context(self, data: dict, journal_type: JournalType, ctx: DocumentContext) -> dict:
        return {
            **data,
            'document_type': ctx.document_type,
            'document_id': str(ctx.document_id),
            'numero': ctx.numero or '',
            'journal_type_code': journal_type.code,
            'module': journal_type.module or '',
        }

    async def _create_entry(
        self,
        company_id: uuid.UUID,
        journal_type: JournalType,
        lines: list,
        context: dict,
        ctx: DocumentContext,
    ) -> dict:
        """Crea el asiento contable en BD con numeracion por paquete (JournalType)."""
        periodo = await self._get_periodo_abierto(company_id, context.get('fecha', ''))
        if not periodo:
            raise Exception("No hay periodo contable abierto para la fecha del documento")

        prefijo = journal_type.prefijo or 'CG'
        digitos = journal_type.digitos or 8

        correlativo = journal_type.correlativo_actual + 1
        stmt = (
            update(JournalType)
            .where(
                JournalType.id == journal_type.id,
                JournalType.correlativo_actual == journal_type.correlativo_actual,
            )
            .values(correlativo_actual=correlativo)
        )
        await self.db.execute(stmt)

        numero_asiento = f"{prefijo}{correlativo:0{digitos}d}"

        asiento = Asiento(
            empresa_id=company_id,
            periodo_id=periodo.id,
            numero=numero_asiento,
            fecha=datetime.strptime(context.get('fecha', ''), '%Y-%m-%d') if context.get('fecha') else datetime.now(),
            concepto=context.get('concepto', f"Asiento generado por {ctx.document_type}"),
            journal_type_id=journal_type.id,
            documento_tipo=ctx.document_type,
            documento_id=ctx.document_id,
            estado='CONTABILIZADO',
            creado_por=ctx.user_id,
        )
        self.db.add(asiento)
        await self.db.flush()

        for line in lines:
            al = AsientoLinea(
                asiento_id=asiento.id,
                cuenta_id=line.account_id,
                debe=line.amount if line.nature == 'DEBIT' else Decimal('0'),
                haber=line.amount if line.nature == 'CREDIT' else Decimal('0'),
                descripcion=line.description,
                centro_costo_id=line.cost_center_id,
            )
            self.db.add(al)

        await self.db.flush()

        return {
            'asiento_id': asiento.id,
            'numero_asiento': numero_asiento,
        }

    async def _get_periodo_abierto(self, company_id: uuid.UUID, fecha_str: str):
        from sqlalchemy import select, update
        from app.domain.models.periodo import PeriodoContable
        q = select(PeriodoContable).where(
            PeriodoContable.empresa_id == company_id,
            PeriodoContable.cerrado == False,
            PeriodoContable.fecha_inicio <= datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else True,
            PeriodoContable.fecha_fin >= datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else True,
        ).limit(1)
        r = await self.db.execute(q)
        return r.scalar_one_or_none()
