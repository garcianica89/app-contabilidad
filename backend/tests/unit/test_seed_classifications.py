from unittest.mock import AsyncMock, MagicMock
import pytest

from app.domain.accounting.seed_classifications import (
    seed_classifications,
    ACCOUNT_TYPES,
    FINANCIAL_CLASSIFICATIONS,
    TAX_CLASSIFICATIONS,
    IFRS_CLASSIFICATIONS,
)


@pytest.mark.asyncio
async def test_seed_classifications_adds_all_types():
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result_mock)

    await seed_classifications(db)

    total = (
        len(ACCOUNT_TYPES)
        + len(FINANCIAL_CLASSIFICATIONS)
        + len(TAX_CLASSIFICATIONS)
        + len(IFRS_CLASSIFICATIONS)
    )
    assert db.add.call_count == total
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_seed_classifications_skips_existing():
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = MagicMock()
    db.execute = AsyncMock(return_value=result_mock)

    await seed_classifications(db)

    db.add.assert_not_called()


def test_seed_account_types_have_correct_nature():
    for at in ACCOUNT_TYPES:
        assert at["nature"] in ("DEUDORA", "ACREEDORA")


def test_seed_financial_classifications_have_correct_type():
    for fc in FINANCIAL_CLASSIFICATIONS:
        assert fc["type"] in ("BALANCE", "INCOME")
