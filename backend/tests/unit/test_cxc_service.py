from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch
import uuid

import pytest

from app.service.cxc_service import CxcService
from app.domain.models.factura_venta import FacturaVenta, FacturaVentaLinea
from app.domain.models.cliente import Cliente
from app.domain.models.producto import Producto


@pytest.fixture
def doc_result():
    m = MagicMock()
    m.success = True
    m.errors = []
    m.document_id = uuid.uuid4()
    return m


class TestCrearFactura:

    @pytest.mark.asyncio
    async def test_crear_factura_contado(
        self, mock_db, empresa_id, usuario_id, doc_result
    ):
        factura_id = doc_result.document_id

        factura_mock = MagicMock(spec=FacturaVenta)
        factura_mock.id = factura_id
        factura_mock.total = Decimal("230.00")
        factura_mock.tipo = "CONTADO"
        factura_mock.subtotal = Decimal("200.00")
        factura_mock.iva = Decimal("30.00")
        factura_mock.numero = "F001"

        fetch_result = MagicMock()
        fetch_result.scalar_one.return_value = factura_mock
        mock_db.execute.return_value = fetch_result

        with patch('app.service.cxc_service.DocumentEngine') as MockDE:
            engine_instance = AsyncMock()
            engine_instance.process.return_value = doc_result
            MockDE.return_value = engine_instance

            service = CxcService(mock_db, usuario_id, empresa_id)

            cliente_id = uuid.uuid4()
            producto_id = uuid.uuid4()
            moneda_id = uuid.uuid4()
            periodo_id = uuid.uuid4()

            factura = await service.crear_factura(
                numero="F001",
                cliente_id=cliente_id,
                fecha=date(2026, 1, 15),
                tipo="CONTADO",
                lineas=[{
                    "producto_id": producto_id,
                    "cantidad": 2,
                    "precio_unitario": 100.00,
                    "descuento": 0,
                }],
                moneda_id=moneda_id,
                periodo_id=periodo_id,
                descuento=0,
                iva=30.00,
            )

            assert factura is not None
            assert factura.total == Decimal("230.00")
            assert factura.tipo == "CONTADO"
            engine_instance.process.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_crear_factura_credito(
        self, mock_db, empresa_id, usuario_id, doc_result
    ):
        factura_id = doc_result.document_id

        factura_mock = MagicMock(spec=FacturaVenta)
        factura_mock.id = factura_id
        factura_mock.total = Decimal("575.00")
        factura_mock.tipo = "CREDITO"
        factura_mock.subtotal = Decimal("500.00")
        factura_mock.iva = Decimal("75.00")
        factura_mock.numero = "F002"

        fetch_result = MagicMock()
        fetch_result.scalar_one.return_value = factura_mock
        mock_db.execute.return_value = fetch_result

        with patch('app.service.cxc_service.DocumentEngine') as MockDE:
            engine_instance = AsyncMock()
            engine_instance.process.return_value = doc_result
            MockDE.return_value = engine_instance

            service = CxcService(mock_db, usuario_id, empresa_id)

            cliente_id = uuid.uuid4()
            producto_id = uuid.uuid4()
            moneda_id = uuid.uuid4()
            periodo_id = uuid.uuid4()

            factura = await service.crear_factura(
                numero="F002",
                cliente_id=cliente_id,
                fecha=date(2026, 1, 15),
                tipo="CREDITO",
                lineas=[{
                    "producto_id": producto_id,
                    "cantidad": 1,
                    "precio_unitario": 500.00,
                    "descuento": 0,
                }],
                moneda_id=moneda_id,
                periodo_id=periodo_id,
                fecha_vencimiento=date(2026, 2, 15),
                descuento=0,
                iva=75.00,
            )

            assert factura is not None
            assert factura.total == Decimal("575.00")
            assert factura.tipo == "CREDITO"
            engine_instance.process.assert_awaited_once()


class TestEstadoCuentaCliente:

    @pytest.mark.asyncio
    async def test_estado_cuenta_cliente(self, mock_db, empresa_id, usuario_id):
        service = CxcService(mock_db, usuario_id, empresa_id)
        cliente_id = uuid.uuid4()

        factura1 = MagicMock(spec=FacturaVenta)
        factura1.numero = "F001"
        factura1.fecha = date(2026, 1, 1)
        factura1.total = Decimal("100.00")
        factura1.estado = "EMITIDA"
        factura1.fecha_vencimiento = date(2026, 1, 31)

        factura2 = MagicMock(spec=FacturaVenta)
        factura2.numero = "F002"
        factura2.fecha = date(2026, 1, 15)
        factura2.total = Decimal("200.00")
        factura2.estado = "COBRADA"
        factura2.fecha_vencimiento = date(2026, 2, 15)

        result = MagicMock()
        result.scalars.return_value.all.return_value = [factura1, factura2]
        mock_db.execute.return_value = result

        estado = await service.estado_cuenta_cliente(cliente_id)

        assert estado["cliente_id"] == str(cliente_id)
        assert estado["saldo_actual"] == 300.0
        assert len(estado["movimientos"]) == 2
