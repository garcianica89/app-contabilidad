"""Add bodega_id, condicion_pago_id, descuento, retencion_ir to orden_compra; add descuento, aplica_iva, tasa_iva to orden_compra_linea

Revision ID: 0022
Revises: 0021
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0022'
down_revision: Union[str, None] = '0021'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # OrdenCompra new columns
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orden_compra' AND column_name='bodega_id')
            THEN ALTER TABLE orden_compra ADD COLUMN bodega_id UUID REFERENCES bodega(id); END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orden_compra' AND column_name='condicion_pago_id')
            THEN ALTER TABLE orden_compra ADD COLUMN condicion_pago_id UUID REFERENCES condicion_pago(id); END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orden_compra' AND column_name='descuento')
            THEN ALTER TABLE orden_compra ADD COLUMN descuento NUMERIC(14,2) NOT NULL DEFAULT 0; END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orden_compra' AND column_name='retencion_ir')
            THEN ALTER TABLE orden_compra ADD COLUMN retencion_ir NUMERIC(14,2) NOT NULL DEFAULT 0; END IF;
        END $$;
    """)
    # OrdenCompraLinea new columns
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orden_compra_linea' AND column_name='descuento')
            THEN ALTER TABLE orden_compra_linea ADD COLUMN descuento NUMERIC(14,2) NOT NULL DEFAULT 0; END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orden_compra_linea' AND column_name='aplica_iva')
            THEN ALTER TABLE orden_compra_linea ADD COLUMN aplica_iva BOOLEAN; END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orden_compra_linea' AND column_name='tasa_iva')
            THEN ALTER TABLE orden_compra_linea ADD COLUMN tasa_iva NUMERIC(5,2); END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE orden_compra DROP COLUMN IF EXISTS bodega_id")
    op.execute("ALTER TABLE orden_compra DROP COLUMN IF EXISTS condicion_pago_id")
    op.execute("ALTER TABLE orden_compra DROP COLUMN IF EXISTS descuento")
    op.execute("ALTER TABLE orden_compra DROP COLUMN IF EXISTS retencion_ir")
    op.execute("ALTER TABLE orden_compra_linea DROP COLUMN IF EXISTS descuento")
    op.execute("ALTER TABLE orden_compra_linea DROP COLUMN IF EXISTS aplica_iva")
    op.execute("ALTER TABLE orden_compra_linea DROP COLUMN IF EXISTS tasa_iva")
