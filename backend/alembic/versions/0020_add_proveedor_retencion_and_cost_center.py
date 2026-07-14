"""Add proveedor_retencion table, centro_costo_id to retencion

Revision ID: 0020
Revises: 0019
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0020'
down_revision: Union[str, None] = '0019'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # proveedor_retencion association table
    op.execute("""
        CREATE TABLE IF NOT EXISTS proveedor_retencion (
            proveedor_id UUID NOT NULL REFERENCES proveedor(id) ON DELETE CASCADE,
            retencion_id UUID NOT NULL REFERENCES retencion(id) ON DELETE CASCADE,
            PRIMARY KEY (proveedor_id, retencion_id)
        )
    """)
    # centro_costo_id on retencion
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='retencion' AND column_name='centro_costo_id'
            ) THEN
                ALTER TABLE retencion ADD COLUMN centro_costo_id UUID REFERENCES centro_costo(id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS proveedor_retencion")
    op.execute("ALTER TABLE retencion DROP COLUMN IF EXISTS centro_costo_id")
