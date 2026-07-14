"""Add categoria_cliente and categoria_proveedor tables with account columns

Revision ID: 0026
Revises: 0025
Create Date: 2026-07-09
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0026'
down_revision: Union[str, None] = '0025'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS categoria_cliente (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            nombre VARCHAR(100) NOT NULL,
            cuenta_tercero_id UUID REFERENCES cuenta_contable(id),
            cuenta_banco_id UUID REFERENCES cuenta_contable(id),
            cuenta_caja_id UUID REFERENCES cuenta_contable(id)
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS categoria_proveedor (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            nombre VARCHAR(100) NOT NULL,
            cuenta_tercero_id UUID REFERENCES cuenta_contable(id),
            cuenta_banco_id UUID REFERENCES cuenta_contable(id),
            cuenta_caja_id UUID REFERENCES cuenta_contable(id)
        )
    """)
    op.execute("ALTER TABLE cliente ADD COLUMN IF NOT EXISTS categoria_id UUID REFERENCES categoria_cliente(id)")
    op.execute("ALTER TABLE proveedor ADD COLUMN IF NOT EXISTS categoria_id UUID REFERENCES categoria_proveedor(id)")


def downgrade() -> None:
    op.execute("ALTER TABLE cliente DROP COLUMN IF EXISTS categoria_id")
    op.execute("ALTER TABLE proveedor DROP COLUMN IF EXISTS categoria_id")
    op.execute("DROP TABLE IF EXISTS categoria_cliente")
    op.execute("DROP TABLE IF EXISTS categoria_proveedor")
