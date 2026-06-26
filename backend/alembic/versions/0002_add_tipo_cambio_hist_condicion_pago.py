"""add tipo_cambio_hist and condicion_pago

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-26
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tipo_cambio_hist',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('empresa_id', UUID(as_uuid=True), sa.ForeignKey('empresa.id'), nullable=False),
        sa.Column('moneda_id', UUID(as_uuid=True), sa.ForeignKey('moneda.id'), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('tasa_compra', sa.Numeric(14, 6), nullable=False),
        sa.Column('tasa_venta', sa.Numeric(14, 6), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('empresa_id', 'moneda_id', 'fecha', name='uq_tipo_cambio_hist'),
    )
    op.create_table(
        'condicion_pago',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('empresa_id', UUID(as_uuid=True), sa.ForeignKey('empresa.id'), nullable=False),
        sa.Column('codigo', sa.String(10), nullable=False),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('dias_neto', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('descuento_contado', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('activa', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('empresa_id', 'codigo', name='uq_condicion_pago_empresa_codigo'),
    )


def downgrade() -> None:
    op.drop_table('condicion_pago')
    op.drop_table('tipo_cambio_hist')
