import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.asiento import Asiento, AsientoLinea
from app.domain.models.periodo import PeriodoContable
from app.domain.models.cuenta_contable import CuentaContable
from app.domain.models.empresa import Empresa
from app.domain.models.usuario import Usuario
from app.domain.models.moneda import Moneda


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def empresa_id():
    return uuid.uuid4()


@pytest.fixture
def usuario_id():
    return uuid.uuid4()


@pytest.fixture
def periodo_id():
    return uuid.uuid4()


@pytest.fixture
def cuenta_activo_id():
    return uuid.uuid4()


@pytest.fixture
def cuenta_pasivo_id():
    return uuid.uuid4()


@pytest.fixture
def cuenta_ingreso_id():
    return uuid.uuid4()


@pytest.fixture
def cuenta_gasto_id():
    return uuid.uuid4()


@pytest.fixture
def moneda_nio_id():
    return uuid.uuid4()


@pytest.fixture
def periodo_abierto(periodo_id, empresa_id):
    return PeriodoContable(
        id=periodo_id,
        empresa_id=empresa_id,
        codigo="2026-01",
        nombre="Enero 2026",
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 31),
        cerrado=False,
    )


@pytest.fixture
def periodo_cerrado(periodo_id, empresa_id):
    return PeriodoContable(
        id=periodo_id,
        empresa_id=empresa_id,
        codigo="2025-12",
        nombre="Diciembre 2025",
        fecha_inicio=date(2025, 12, 1),
        fecha_fin=date(2025, 12, 31),
        cerrado=True,
    )


@pytest.fixture
def cuenta_valida(cuenta_activo_id, empresa_id):
    return CuentaContable(
        id=cuenta_activo_id,
        empresa_id=empresa_id,
        codigo="1-1-1-1-01",
        nombre="Caja General",
        tipo="ACTIVO",
        nivel=5,
        acepta_datos=True,
        activa=True,
    )


@pytest.fixture
def cuenta_padre(cuenta_activo_id, empresa_id):
    return CuentaContable(
        id=cuenta_activo_id,
        empresa_id=empresa_id,
        codigo="1-1-1-1-00",
        nombre="Caja (Padre)",
        tipo="ACTIVO",
        nivel=4,
        acepta_datos=False,
        activa=True,
    )


@pytest.fixture
def empresa_valida(empresa_id, moneda_nio_id):
    return Empresa(
        id=empresa_id,
        nombre="Test Company",
        ruc="J123456789",
        moneda_local_id=moneda_nio_id,
        activo=True,
    )


@pytest.fixture
def asiento_ejemplo(periodo_id, empresa_id, usuario_id):
    return Asiento(
        id=uuid.uuid4(),
        empresa_id=empresa_id,
        numero=1,
        fecha=date(2026, 1, 15),
        periodo_id=periodo_id,
        tipo="DIARIO",
        concepto="Test asiento",
        creado_por=usuario_id,
        reversado=False,
    )


@pytest.fixture
def asiento_reversado(periodo_id, empresa_id, usuario_id):
    return Asiento(
        id=uuid.uuid4(),
        empresa_id=empresa_id,
        numero=2,
        fecha=date(2026, 1, 15),
        periodo_id=periodo_id,
        tipo="DIARIO",
        concepto="Asiento ya reversado",
        creado_por=usuario_id,
        reversado=True,
        asiento_reversa_id=uuid.uuid4(),
    )


@pytest.fixture
def lineas_validas(cuenta_activo_id, cuenta_pasivo_id):
    return [
        {
            "cuenta_id": cuenta_activo_id,
            "descripcion": "Debe test",
            "debe_local": 1000.00,
            "haber_local": 0,
        },
        {
            "cuenta_id": cuenta_pasivo_id,
            "descripcion": "Haber test",
            "debe_local": 0,
            "haber_local": 1000.00,
        },
    ]


@pytest.fixture
def lineas_no_cuadran(cuenta_activo_id, cuenta_pasivo_id):
    return [
        {
            "cuenta_id": cuenta_activo_id,
            "descripcion": "Debe test",
            "debe_local": 1000.00,
            "haber_local": 0,
        },
        {
            "cuenta_id": cuenta_pasivo_id,
            "descripcion": "Haber test",
            "debe_local": 0,
            "haber_local": 500.00,
        },
    ]


@pytest.fixture
def lineas_cero(cuenta_activo_id, cuenta_pasivo_id):
    return [
        {
            "cuenta_id": cuenta_activo_id,
            "descripcion": "Debe cero",
            "debe_local": 0,
            "haber_local": 0,
        },
        {
            "cuenta_id": cuenta_pasivo_id,
            "descripcion": "Haber cero",
            "debe_local": 0,
            "haber_local": 0,
        },
    ]
