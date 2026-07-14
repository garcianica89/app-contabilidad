"""Add IVA fields to proveedor and producto

Revision ID: 0017
Revises: 0016
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='proveedor' AND column_name='aplica_iva') THEN ALTER TABLE proveedor ADD COLUMN aplica_iva BOOLEAN DEFAULT TRUE NOT NULL; END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='proveedor' AND column_name='tasa_iva') THEN ALTER TABLE proveedor ADD COLUMN tasa_iva NUMERIC(5,2) DEFAULT 15.00 NOT NULL; END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='producto' AND column_name='aplica_iva') THEN ALTER TABLE producto ADD COLUMN aplica_iva BOOLEAN DEFAULT TRUE NOT NULL; END IF; END $$;")


def downgrade() -> None:
    op.execute("ALTER TABLE proveedor DROP COLUMN IF EXISTS tasa_iva")
    op.execute("ALTER TABLE proveedor DROP COLUMN IF EXISTS aplica_iva")
    op.execute("ALTER TABLE producto DROP COLUMN IF EXISTS aplica_iva")
