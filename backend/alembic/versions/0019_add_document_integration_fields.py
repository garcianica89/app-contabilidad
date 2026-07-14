"""Add document integration fields (IVA per doc, subtipo config)

Revision ID: 0019
Revises: 0018
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0019"
down_revision: Union[str, None] = "0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # factura_compra cabecera: aplica_iva, tasa_iva
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='factura_compra' AND column_name='aplica_iva') THEN ALTER TABLE factura_compra ADD COLUMN aplica_iva BOOLEAN; END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='factura_compra' AND column_name='tasa_iva') THEN ALTER TABLE factura_compra ADD COLUMN tasa_iva NUMERIC(5,2); END IF; END $$;")
    # factura_compra_linea: aplica_iva, tasa_iva
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='factura_compra_linea' AND column_name='aplica_iva') THEN ALTER TABLE factura_compra_linea ADD COLUMN aplica_iva BOOLEAN; END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='factura_compra_linea' AND column_name='tasa_iva') THEN ALTER TABLE factura_compra_linea ADD COLUMN tasa_iva NUMERIC(5,2); END IF; END $$;")

    # factura_venta cabecera: aplica_iva, tasa_iva
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='factura_venta' AND column_name='aplica_iva') THEN ALTER TABLE factura_venta ADD COLUMN aplica_iva BOOLEAN; END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='factura_venta' AND column_name='tasa_iva') THEN ALTER TABLE factura_venta ADD COLUMN tasa_iva NUMERIC(5,2); END IF; END $$;")
    # factura_venta_linea: aplica_iva, tasa_iva
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='factura_venta_linea' AND column_name='aplica_iva') THEN ALTER TABLE factura_venta_linea ADD COLUMN aplica_iva BOOLEAN; END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='factura_venta_linea' AND column_name='tasa_iva') THEN ALTER TABLE factura_venta_linea ADD COLUMN tasa_iva NUMERIC(5,2); END IF; END $$;")

    # documento_subtipo: calcula_iva, aplica_retenciones, genera_costo_venta, requiere_centros_costo
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documento_subtipo' AND column_name='calcula_iva') THEN ALTER TABLE documento_subtipo ADD COLUMN calcula_iva BOOLEAN DEFAULT TRUE NOT NULL; END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documento_subtipo' AND column_name='aplica_retenciones') THEN ALTER TABLE documento_subtipo ADD COLUMN aplica_retenciones BOOLEAN DEFAULT FALSE NOT NULL; END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documento_subtipo' AND column_name='genera_costo_venta') THEN ALTER TABLE documento_subtipo ADD COLUMN genera_costo_venta BOOLEAN DEFAULT FALSE NOT NULL; END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documento_subtipo' AND column_name='requiere_centros_costo') THEN ALTER TABLE documento_subtipo ADD COLUMN requiere_centros_costo BOOLEAN DEFAULT FALSE NOT NULL; END IF; END $$;")

    # documento_subtipo: cuenta_costo_venta_id
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documento_subtipo' AND column_name='cuenta_costo_venta_id') THEN ALTER TABLE documento_subtipo ADD COLUMN cuenta_costo_venta_id UUID REFERENCES account(id); END IF; END $$;")


def downgrade() -> None:
    op.execute("ALTER TABLE factura_compra DROP COLUMN IF EXISTS aplica_iva")
    op.execute("ALTER TABLE factura_compra DROP COLUMN IF EXISTS tasa_iva")
    op.execute("ALTER TABLE factura_compra_linea DROP COLUMN IF EXISTS aplica_iva")
    op.execute("ALTER TABLE factura_compra_linea DROP COLUMN IF EXISTS tasa_iva")
    op.execute("ALTER TABLE factura_venta DROP COLUMN IF EXISTS aplica_iva")
    op.execute("ALTER TABLE factura_venta DROP COLUMN IF EXISTS tasa_iva")
    op.execute("ALTER TABLE factura_venta_linea DROP COLUMN IF EXISTS aplica_iva")
    op.execute("ALTER TABLE factura_venta_linea DROP COLUMN IF EXISTS tasa_iva")
    op.execute("ALTER TABLE documento_subtipo DROP COLUMN IF EXISTS calcula_iva")
    op.execute("ALTER TABLE documento_subtipo DROP COLUMN IF EXISTS aplica_retenciones")
    op.execute("ALTER TABLE documento_subtipo DROP COLUMN IF EXISTS genera_costo_venta")
    op.execute("ALTER TABLE documento_subtipo DROP COLUMN IF EXISTS requiere_centros_costo")
    op.execute("ALTER TABLE documento_subtipo DROP COLUMN IF EXISTS cuenta_costo_venta_id")
