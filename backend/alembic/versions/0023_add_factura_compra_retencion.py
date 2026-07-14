"""Add factura_compra_retencion table for per-invoice withholding overrides

Revision ID: 0023
Revises: 0022
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0023'
down_revision: Union[str, None] = '0022'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='factura_compra_retencion')
            THEN
                CREATE TABLE factura_compra_retencion (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    factura_compra_id UUID NOT NULL REFERENCES factura_compra(id) ON DELETE CASCADE,
                    retencion_id UUID NOT NULL REFERENCES retencion(id) ON DELETE CASCADE,
                    base_imponible NUMERIC(14,2) NOT NULL DEFAULT 0,
                    monto_retenido NUMERIC(14,2) NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                CREATE INDEX idx_fcr_factura ON factura_compra_retencion(factura_compra_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS factura_compra_retencion CASCADE")
