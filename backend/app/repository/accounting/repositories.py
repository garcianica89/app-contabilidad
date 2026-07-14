import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.accounting.models import (
    Account,
    AccountType,
    JournalType,
    JournalTemplate,
    JournalTemplateLine,
    ModuleAccountingConfig,
    CxcDocumentSubtype,
    CxpDocumentSubtype,
)


class AccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, account_id: uuid.UUID) -> Optional[Account]:
        result = await self.db.execute(select(Account).where(Account.id == account_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, company_id: uuid.UUID, code: str) -> Optional[Account]:
        result = await self.db.execute(
            select(Account).where(
                Account.company_id == company_id,
                Account.code == code,
                Account.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_accounts(self, company_id: uuid.UUID) -> dict[str, uuid.UUID]:
        result = await self.db.execute(
            select(Account).where(
                Account.company_id == company_id,
                Account.is_active == True,
                Account.accepts_entries == True,
            )
        )
        return {r.code: r.id for r in result.scalars().all()}


class JournalTypeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_code(self, company_id: uuid.UUID, code: str) -> Optional[JournalType]:
        result = await self.db.execute(
            select(JournalType).where(
                JournalType.company_id == company_id,
                JournalType.code == code,
                JournalType.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_templates(self, journal_type_id: uuid.UUID) -> list[JournalTemplate]:
        result = await self.db.execute(
            select(JournalTemplate)
            .where(
                JournalTemplate.journal_type_id == journal_type_id,
                JournalTemplate.is_active == True,
            )
            .order_by(JournalTemplate.priority.desc())
        )
        return list(result.scalars().all())

    async def get_template_lines(self, template_id: uuid.UUID) -> list[JournalTemplateLine]:
        result = await self.db.execute(
            select(JournalTemplateLine)
            .where(JournalTemplateLine.template_id == template_id)
            .order_by(JournalTemplateLine.line_order)
        )
        return list(result.scalars().all())


class ModuleAccountingConfigRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_concept(self, company_id: uuid.UUID, module: str, concept_code: str) -> Optional[ModuleAccountingConfig]:
        result = await self.db.execute(
            select(ModuleAccountingConfig).where(
                ModuleAccountingConfig.company_id == company_id,
                ModuleAccountingConfig.module == module,
                ModuleAccountingConfig.concept_code == concept_code,
                ModuleAccountingConfig.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_account_by_concept(self, company_id: uuid.UUID, module: str, concept_code: str) -> Optional[uuid.UUID]:
        config = await self.get_by_concept(company_id, module, concept_code)
        if config:
            return config.account_id
        return None

    async def get_all_by_module(self, company_id: uuid.UUID, module: str) -> list[ModuleAccountingConfig]:
        result = await self.db.execute(
            select(ModuleAccountingConfig).where(
                ModuleAccountingConfig.company_id == company_id,
                ModuleAccountingConfig.module == module,
                ModuleAccountingConfig.is_active == True,
            )
        )
        return list(result.scalars().all())


class CxcSubtypeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, subtype_id: uuid.UUID) -> Optional[CxcDocumentSubtype]:
        result = await self.db.execute(select(CxcDocumentSubtype).where(CxcDocumentSubtype.id == subtype_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, company_id: uuid.UUID, code: str) -> Optional[CxcDocumentSubtype]:
        result = await self.db.execute(
            select(CxcDocumentSubtype).where(
                CxcDocumentSubtype.company_id == company_id,
                CxcDocumentSubtype.code == code,
                CxcDocumentSubtype.is_active == True,
            )
        )
        return result.scalar_one_or_none()


class CxpSubtypeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, subtype_id: uuid.UUID) -> Optional[CxpDocumentSubtype]:
        result = await self.db.execute(select(CxpDocumentSubtype).where(CxpDocumentSubtype.id == subtype_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, company_id: uuid.UUID, code: str) -> Optional[CxpDocumentSubtype]:
        result = await self.db.execute(
            select(CxpDocumentSubtype).where(
                CxpDocumentSubtype.company_id == company_id,
                CxpDocumentSubtype.code == code,
                CxpDocumentSubtype.is_active == True,
            )
        )
        return result.scalar_one_or_none()
