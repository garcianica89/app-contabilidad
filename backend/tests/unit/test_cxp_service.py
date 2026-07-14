from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch
import uuid

import pytest

from app.service.cxp_service import CxpService
from app.domain.models.factura_compra import FacturaCompra
from app.domain.models.producto import Producto


@pytest.fixture
def doc_result():
    m = MagicMock()
    m.success = True
    m.errors = []
    m.document_id = uuid.uuid4()
    return m


class TestCrearFacturaCompra:

    @pytest.mark.asyncio
    async def test_crear_factura_compra_con_iva_y_retencion(
        self, mock_db, empresa_id, usuario_id, doc_result
    ):
        factura_id = doc_result.document_id

        factura_mock = MagicMock(spec=FacturaCompra)
        factura_mock.id = factura_id
        factura_mock.subtotal = Decimal("1000.00")
        factura_mock.iva = Decimal("150.00")
        factura_mock.retencion_ir = Decimal("20.00")
        factura_mock.total = Decimal("1130.00")
        factura_mock.numero = "FC001"

        fetch_result = MagicMock()
        fetch_result.scalar_one.return_value = factura_mock
        mock_db.execute.return_value = fetch_result

        with patch('app.service.cxp_service.DocumentEngine') as MockDE:
            engine_instance = AsyncMock()
            engine_instance.process.return_value = doc_result
            MockDE.return_value = engine_instance

            service = CxpService(mock_db, usuario_id, empresa_id)

            proveedor_id = uuid.uuid4()
            producto_id = uuid.uuid4()
            moneda_id = uuid.uuid4()
            periodo_id = uuid.uuid4()

            factura = await service.crear_factura_compra(
                numero="FC001",
                proveedor_id=proveedor_id,
                fecha=date(2026, 1, 15),
                lineas=[{
                    "producto_id": producto_id,
                    "cantidad": 10,
                    "precio_unitario": 100.00,
                    "descuento": 0,
                }],
                moneda_id=moneda_id,
                periodo_id=periodo_id,
                descuento=0,
                iva=150.00,
                retencion_ir=20.00,
            )

            assert factura is not None
            assert factura.subtotal == Decimal("1000.00")
            assert factura.iva == Decimal("150.00")
            assert factura.retencion_ir == Decimal("20.00")
            assert factura.total == Decimal("1130.00")
            engine_instance.process.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_crear_factura_compra_costo_promedio(
        self, mock_db, empresa_id, usuario_id, doc_result
    ):
        factura_id = doc_result.document_id

        factura_mock = MagicMock(spec=FacturaCompra)
        factura_mock.id = factura_id
        factura_mock.subtotal = Decimal("1200.00")
        factura_mock.total = Decimal("1200.00")
        factura_mock.numero = "FC002"

        fetch_result = MagicMock()
        fetch_result.scalar_one.return_value = factura_mock
        mock_db.execute.return_value = fetch_result

        with patch('app.service.cxp_service.DocumentEngine') as MockDE:
            engine_instance = AsyncMock()
            engine_instance.process.return_value = doc_result
            MockDE.return_value = engine_instance

            service = CxpService(mock_db, usuario_id, empresa_id)

            proveedor_id = uuid.uuid4()
            producto_id = uuid.uuid4()
            moneda_id = uuid.uuid4()
            periodo_id = uuid.uuid4()

            factura = await service.crear_factura_compra(
                numero="FC002",
                proveedor_id=proveedor_id,
                fecha=date(2026, 2, 1),
                lineas=[{
                    "producto_id": producto_id,
                    "cantidad": 10,
                    "precio_unitario": 120.00,
                    "descuento": 0,
                }],
                moneda_id=moneda_id,
                periodo_id=periodo_id,
            )

            assert factura is not None
            assert factura.subtotal == Decimal("1200.00")
            engine_instance.process.assert_awaited_once()
