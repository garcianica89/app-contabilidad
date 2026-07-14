"""Add accounting account FKs to producto and activo_fijo

Revision ID: 0018
Revises: 0017
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # producto: cuenta_compra_id, cuenta_venta_id, cuenta_inventario_id
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='producto' AND column_name='cuenta_compra_id') THEN ALTER TABLE producto ADD COLUMN cuenta_compra_id UUID REFERENCES cuenta_contable(id); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='producto' AND column_name='cuenta_venta_id') THEN ALTER TABLE producto ADD COLUMN cuenta_venta_id UUID REFERENCES cuenta_contable(id); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='producto' AND column_name='cuenta_inventario_id') THEN ALTER TABLE producto ADD COLUMN cuenta_inventario_id UUID REFERENCES cuenta_contable(id); END IF; END $$;")

    # activo_fijo: cuenta_depreciacion_gasto_id, cuenta_depreciacion_acumulada_id, cuenta_baja_id
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='activo_fijo' AND column_name='cuenta_depreciacion_gasto_id') THEN ALTER TABLE activo_fijo ADD COLUMN cuenta_depreciacion_gasto_id UUID REFERENCES cuenta_contable(id); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='activo_fijo' AND column_name='cuenta_depreciacion_acumulada_id') THEN ALTER TABLE activo_fijo ADD COLUMN cuenta_depreciacion_acumulada_id UUID REFERENCES cuenta_contable(id); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='activo_fijo' AND column_name='cuenta_baja_id') THEN ALTER TABLE activo_fijo ADD COLUMN cuenta_baja_id UUID REFERENCES cuenta_contable(id); END IF; END $$;")


def downgrade() -> None:
    op.execute("ALTER TABLE producto DROP COLUMN IF EXISTS cuenta_compra_id")
    op.execute("ALTER TABLE producto DROP COLUMN IF EXISTS cuenta_venta_id")
    op.execute("ALTER TABLE producto DROP COLUMN IF EXISTS cuenta_inventario_id")
    op.execute("ALTER TABLE activo_fijo DROP COLUMN IF EXISTS cuenta_depreciacion_gasto_id")
    op.execute("ALTER TABLE activo_fijo DROP COLUMN IF EXISTS cuenta_depreciacion_acumulada_id")
    op.execute("ALTER TABLE activo_fijo DROP COLUMN IF EXISTS cuenta_baja_id")
