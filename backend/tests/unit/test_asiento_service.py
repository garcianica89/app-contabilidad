from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch
import uuid

import pytest

from app.service.asiento_service import (
    AsientoService,
    PartidaDobleError,
    PeriodoCerradoError,
    CuentaNoValidaError,
)
from app.domain.models.asiento import Asiento, AsientoLinea


def mock_result(**kwargs):
    """Create a MagicMock that mimics SQLAlchemy Result with sync methods."""
    r = MagicMock()
    for k, v in kwargs.items():
        attr = r
        parts = k.split(".")
        for part in parts[:-1]:
            attr = getattr(attr, part)
        setattr(attr, parts[-1], MagicMock(return_value=v))
    return r


class TestValidarPeriodo:

    @pytest.mark.asyncio
    async def test_periodo_abierto_ok(self, mock_db, periodo_abierto):
        service = AsientoService(mock_db, uuid.uuid4(), uuid.uuid4())
        result = MagicMock()
        result.scalar_one_or_none.return_value = periodo_abierto
        mock_db.execute.return_value = result

        periodo = await service._validar_periodo(periodo_abierto.id)
        assert periodo == periodo_abierto
        assert periodo.cerrado is False

    @pytest.mark.asyncio
    async def test_periodo_cerrado_raises(self, mock_db, periodo_cerrado):
        service = AsientoService(mock_db, uuid.uuid4(), uuid.uuid4())
        result = MagicMock()
        result.scalar_one_or_none.return_value = periodo_cerrado
        mock_db.execute.return_value = result

        with pytest.raises(PeriodoCerradoError, match="cerrado"):
            await service._validar_periodo(periodo_cerrado.id)

    @pytest.mark.asyncio
    async def test_periodo_no_encontrado_raises(self, mock_db):
        service = AsientoService(mock_db, uuid.uuid4(), uuid.uuid4())
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        with pytest.raises(ValueError, match="no encontrado"):
            await service._validar_periodo(uuid.uuid4())


class TestValidarCuenta:

    @pytest.mark.asyncio
    async def test_cuenta_valida_ok(self, mock_db, cuenta_valida):
        service = AsientoService(mock_db, uuid.uuid4(), uuid.uuid4())
        result = MagicMock()
        result.scalar_one_or_none.return_value = cuenta_valida
        mock_db.execute.return_value = result

        cuenta = await service._validar_cuenta(cuenta_valida.id)
        assert cuenta == cuenta_valida
        assert cuenta.acepta_datos is True

    @pytest.mark.asyncio
    async def test_cuenta_inactiva_raises(self, mock_db, cuenta_valida):
        service = AsientoService(mock_db, uuid.uuid4(), uuid.uuid4())
        cuenta_valida.activa = False
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        with pytest.raises(CuentaNoValidaError, match="no encontrada o inactiva"):
            await service._validar_cuenta(cuenta_valida.id)

    @pytest.mark.asyncio
    async def test_cuenta_padre_raises(self, mock_db, cuenta_padre):
        service = AsientoService(mock_db, uuid.uuid4(), uuid.uuid4())
        result = MagicMock()
        result.scalar_one_or_none.return_value = cuenta_padre
        mock_db.execute.return_value = result

        with pytest.raises(CuentaNoValidaError, match="no acepta datos"):
            await service._validar_cuenta(cuenta_padre.id)


class TestValidarPartidaDoble:

    @pytest.mark.asyncio
    async def test_partida_doble_cuadra(self, mock_db, lineas_validas):
        service = AsientoService(mock_db, uuid.uuid4(), uuid.uuid4())
        total_debe, total_haber = await service._validar_partida_doble(lineas_validas)
        assert total_debe == Decimal("1000.00")
        assert total_haber == Decimal("1000.00")

    @pytest.mark.asyncio
    async def test_partida_doble_no_cuadra(self, mock_db, lineas_no_cuadran):
        service = AsientoService(mock_db, uuid.uuid4(), uuid.uuid4())
        with pytest.raises(PartidaDobleError, match="no cuadra"):
            await service._validar_partida_doble(lineas_no_cuadran)

    @pytest.mark.asyncio
    async def test_partida_doble_cero(self, mock_db, lineas_cero):
        service = AsientoService(mock_db, uuid.uuid4(), uuid.uuid4())
        with pytest.raises(PartidaDobleError, match="cero"):
            await service._validar_partida_doble(lineas_cero)


class TestCrearAsiento:

    @pytest.mark.asyncio
    async def test_crear_asiento_exitoso(
        self, mock_db, empresa_id, usuario_id, periodo_abierto,
        cuenta_valida, lineas_validas
    ):
        service = AsientoService(mock_db, usuario_id, empresa_id)

        periodo_result = MagicMock()
        periodo_result.scalar_one_or_none.return_value = periodo_abierto

        cuenta_result = MagicMock()
        cuenta_result.scalar_one_or_none.return_value = cuenta_valida

        numero_result = MagicMock()
        numero_result.scalar.return_value = 1

        mock_db.execute.side_effect = [
            periodo_result,
            cuenta_result,
            cuenta_result,
            numero_result,
        ]

        asiento = await service.crear_asiento(
            fecha=date(2026, 1, 15),
            periodo_id=periodo_abierto.id,
            tipo="DIARIO",
            concepto="Test asiento exitoso",
            lineas_data=lineas_validas,
            origen_modulo="TEST",
            origen_documento_id=uuid.uuid4(),
        )

        assert asiento is not None
        assert asiento.empresa_id == empresa_id
        assert asiento.numero == 1
        assert asiento.tipo == "DIARIO"
        assert asiento.concepto == "Test asiento exitoso"
        assert mock_db.add.called
        assert mock_db.flush.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_crear_asiento_periodo_cerrado(
        self, mock_db, usuario_id, empresa_id, periodo_cerrado, lineas_validas
    ):
        service = AsientoService(mock_db, usuario_id, empresa_id)

        periodo_result = MagicMock()
        periodo_result.scalar_one_or_none.return_value = periodo_cerrado
        mock_db.execute.return_value = periodo_result

        with pytest.raises(PeriodoCerradoError):
            await service.crear_asiento(
                fecha=date(2025, 12, 15),
                periodo_id=periodo_cerrado.id,
                tipo="DIARIO",
                concepto="No debe crear",
                lineas_data=lineas_validas,
            )

        assert not mock_db.add.called
        assert not mock_db.commit.called

    @pytest.mark.asyncio
    async def test_crear_asiento_fuera_de_periodo(
        self, mock_db, usuario_id, empresa_id, periodo_abierto, lineas_validas
    ):
        service = AsientoService(mock_db, usuario_id, empresa_id)

        periodo_result = MagicMock()
        periodo_result.scalar_one_or_none.return_value = periodo_abierto
        mock_db.execute.return_value = periodo_result

        with pytest.raises(ValueError, match="no corresponde"):
            await service.crear_asiento(
                fecha=date(2026, 6, 15),
                periodo_id=periodo_abierto.id,
                tipo="DIARIO",
                concepto="Fecha incorrecta",
                lineas_data=lineas_validas,
            )

        assert not mock_db.add.called
        assert not mock_db.commit.called

    @pytest.mark.asyncio
    async def test_crear_asiento_cuenta_invalida(
        self, mock_db, usuario_id, empresa_id, periodo_abierto,
        cuenta_padre, lineas_validas
    ):
        service = AsientoService(mock_db, usuario_id, empresa_id)

        p_result = MagicMock()
        p_result.scalar_one_or_none.return_value = periodo_abierto

        c_result = MagicMock()
        c_result.scalar_one_or_none.return_value = cuenta_padre

        mock_db.execute.side_effect = [
            p_result,
            c_result,
        ]

        with pytest.raises(CuentaNoValidaError, match="no acepta datos"):
            await service.crear_asiento(
                fecha=date(2026, 1, 15),
                periodo_id=periodo_abierto.id,
                tipo="DIARIO",
                concepto="Cuenta padre",
                lineas_data=lineas_validas,
            )


class TestReversarAsiento:

    @pytest.mark.asyncio
    async def test_reversar_asiento_ok(
        self, mock_db, usuario_id, empresa_id, periodo_abierto,
        cuenta_valida
    ):
        service = AsientoService(mock_db, usuario_id, empresa_id)

        asiento_id = uuid.uuid4()
        asiento_mock = MagicMock(spec=Asiento)
        asiento_mock.id = asiento_id
        asiento_mock.reversado = False
        asiento_mock.empresa_id = empresa_id
        asiento_mock.periodo_id = periodo_abierto.id
        asiento_mock.concepto = "Asiento original"

        linea_debe = MagicMock(spec=AsientoLinea)
        linea_debe.cuenta_id = cuenta_valida.id
        linea_debe.centro_costo_id = None
        linea_debe.debe_local = 1000.00
        linea_debe.haber_local = 0
        linea_debe.debe_dolar = 0
        linea_debe.haber_dolar = 0
        linea_debe.descripcion = "Debe original"

        linea_haber = MagicMock(spec=AsientoLinea)
        linea_haber.cuenta_id = cuenta_valida.id
        linea_haber.centro_costo_id = None
        linea_haber.debe_local = 0
        linea_haber.haber_local = 1000.00
        linea_haber.debe_dolar = 0
        linea_haber.haber_dolar = 0
        linea_haber.descripcion = "Haber original"

        asiento_mock.lineas = [linea_debe, linea_haber]

        search_result = MagicMock()
        search_result.unique.return_value.scalar_one_or_none.return_value = asiento_mock

        periodo_result = MagicMock()
        periodo_result.scalar_one_or_none.return_value = periodo_abierto

        cuenta_result = MagicMock()
        cuenta_result.scalar_one_or_none.return_value = cuenta_valida

        numero_result = MagicMock()
        numero_result.scalar.return_value = 2

        mock_db.execute.side_effect = [
            search_result,
            periodo_result,
        ]

        reversa_id = uuid.uuid4()
        asiento_reversa_mock = MagicMock(spec=Asiento)
        asiento_reversa_mock.id = reversa_id
        mock_crear = AsyncMock(return_value=asiento_reversa_mock)
        service.crear_asiento = mock_crear

        with patch("app.service.asiento_service.datetime") as mock_datetime:
            mock_datetime.now.return_value.date.return_value = date(2026, 1, 16)
            result = await service.reversar_asiento(
                asiento_id, "Error contable"
            )

        assert result is not None
        assert result.id == reversa_id
        assert asiento_mock.reversado is True
        assert asiento_mock.asiento_reversa_id == reversa_id

    @pytest.mark.asyncio
    async def test_reversar_asiento_ya_reversado(
        self, mock_db, usuario_id, empresa_id, asiento_reversado
    ):
        service = AsientoService(mock_db, usuario_id, empresa_id)

        asiento_result = MagicMock()
        asiento_result.unique.return_value.scalar_one_or_none.return_value = asiento_reversado
        mock_db.execute.return_value = asiento_result

        with pytest.raises(ValueError, match="ya fue reversado"):
            await service.reversar_asiento(asiento_reversado.id, "Doble reversa")

    @pytest.mark.asyncio
    async def test_reversar_asiento_no_encontrado(
        self, mock_db, usuario_id, empresa_id
    ):
        service = AsientoService(mock_db, usuario_id, empresa_id)

        asiento_result = MagicMock()
        asiento_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = asiento_result

        with pytest.raises(ValueError, match="no encontrado"):
            await service.reversar_asiento(uuid.uuid4(), "No existe")


class TestObtenerSiguienteNumero:

    @pytest.mark.asyncio
    async def test_primer_numero(self, mock_db, empresa_id, periodo_id):
        service = AsientoService(mock_db, uuid.uuid4(), empresa_id)

        result = MagicMock()
        result.scalar.return_value = 1
        mock_db.execute.return_value = result

        numero = await service._obtener_siguiente_numero(periodo_id)
        assert numero == 1

    @pytest.mark.asyncio
    async def test_numero_concurrente(self, mock_db, empresa_id, periodo_id):
        service = AsientoService(mock_db, uuid.uuid4(), empresa_id)

        result = MagicMock()
        result.scalar.return_value = 42
        mock_db.execute.return_value = result

        numero = await service._obtener_siguiente_numero(periodo_id)
        assert numero == 42
