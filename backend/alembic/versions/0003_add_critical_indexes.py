"""add critical indexes for performance

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-29
"""
from typing import Sequence, Union
from alembic import op


revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE INDEX IF NOT EXISTS idx_asiento_linea_cuenta_id ON asiento_linea (cuenta_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_asiento_linea_asiento_id ON asiento_linea (asiento_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_asiento_periodo_id ON asiento (periodo_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_asiento_fecha ON asiento (fecha)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_asiento_empresa_fecha ON asiento (empresa_id, fecha)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_asiento_tipo ON asiento (tipo)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_factura_venta_estado ON factura_venta (estado)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_factura_venta_cliente_id ON factura_venta (cliente_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_factura_venta_fecha ON factura_venta (fecha)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_factura_compra_estado ON factura_compra (estado)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_factura_compra_proveedor_id ON factura_compra (proveedor_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_factura_compra_fecha ON factura_compra (fecha)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_movimiento_caja_caja_fecha ON movimiento_caja (caja_id, fecha)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_cuenta_contable_codigo ON cuenta_contable (codigo)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_cuenta_contable_empresa_activa ON cuenta_contable (empresa_id, activa)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_cliente_codigo ON cliente (codigo)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_proveedor_codigo ON proveedor (codigo)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_producto_codigo ON producto (codigo)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_periodo_contable_empresa ON periodo_contable (empresa_id, cerrado)')


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS idx_asiento_linea_cuenta_id')
    op.execute('DROP INDEX IF EXISTS idx_asiento_linea_asiento_id')
    op.execute('DROP INDEX IF EXISTS idx_asiento_periodo_id')
    op.execute('DROP INDEX IF EXISTS idx_asiento_fecha')
    op.execute('DROP INDEX IF EXISTS idx_asiento_empresa_fecha')
    op.execute('DROP INDEX IF EXISTS idx_asiento_tipo')
    op.execute('DROP INDEX IF EXISTS idx_factura_venta_estado')
    op.execute('DROP INDEX IF EXISTS idx_factura_venta_cliente_id')
    op.execute('DROP INDEX IF EXISTS idx_factura_venta_fecha')
    op.execute('DROP INDEX IF EXISTS idx_factura_compra_estado')
    op.execute('DROP INDEX IF EXISTS idx_factura_compra_proveedor_id')
    op.execute('DROP INDEX IF EXISTS idx_factura_compra_fecha')
    op.execute('DROP INDEX IF EXISTS idx_movimiento_caja_caja_fecha')
    op.execute('DROP INDEX IF EXISTS idx_cuenta_contable_codigo')
    op.execute('DROP INDEX IF EXISTS idx_cuenta_contable_empresa_activa')
    op.execute('DROP INDEX IF EXISTS idx_cliente_codigo')
    op.execute('DROP INDEX IF EXISTS idx_proveedor_codigo')
    op.execute('DROP INDEX IF EXISTS idx_producto_codigo')
    op.execute('DROP INDEX IF EXISTS idx_periodo_contable_empresa')
