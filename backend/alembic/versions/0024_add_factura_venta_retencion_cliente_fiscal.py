"""Add factura_venta_retencion table, cliente_retencion pivot, and cliente fiscal fields

Revision ID: 0024
Revises: 0023
"""
from typing import Sequence, Union
from alembic import op


revision: str = '0024'
down_revision: Union[str, None] = '0023'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # factura_venta_retencion table
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='factura_venta_retencion')
            THEN
                CREATE TABLE factura_venta_retencion (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    factura_venta_id UUID NOT NULL REFERENCES factura_venta(id) ON DELETE CASCADE,
                    retencion_id UUID NOT NULL REFERENCES retencion(id) ON DELETE CASCADE,
                    base_imponible NUMERIC(14,2) NOT NULL DEFAULT 0,
                    monto_retenido NUMERIC(14,2) NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                CREATE INDEX idx_fvr_factura ON factura_venta_retencion(factura_venta_id);
            END IF;
        END $$;
    """)

    # cliente_retencion pivot table
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='cliente_retencion')
            THEN
                CREATE TABLE cliente_retencion (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    cliente_id UUID NOT NULL REFERENCES cliente(id) ON DELETE CASCADE,
                    retencion_id UUID NOT NULL REFERENCES retencion(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(cliente_id, retencion_id)
                );
                CREATE INDEX idx_cr_cliente ON cliente_retencion(cliente_id);
            END IF;
        END $$;
    """)

    # Cliente new columns
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cliente' AND column_name='tipo_fiscal')
            THEN ALTER TABLE cliente ADD COLUMN tipo_fiscal VARCHAR(20) NOT NULL DEFAULT 'NORMAL'; END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cliente' AND column_name='sujeto_retenciones')
            THEN ALTER TABLE cliente ADD COLUMN sujeto_retenciones BOOLEAN NOT NULL DEFAULT TRUE; END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cliente' AND column_name='tipo_documento')
            THEN ALTER TABLE cliente ADD COLUMN tipo_documento VARCHAR(20) DEFAULT 'RUC'; END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cliente' AND column_name='plazo_credito')
            THEN ALTER TABLE cliente ADD COLUMN plazo_credito INTEGER DEFAULT 30; END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS factura_venta_retencion CASCADE")
    op.execute("DROP TABLE IF EXISTS cliente_retencion CASCADE")
    op.execute("ALTER TABLE cliente DROP COLUMN IF EXISTS tipo_fiscal")
    op.execute("ALTER TABLE cliente DROP COLUMN IF EXISTS sujeto_retenciones")
    op.execute("ALTER TABLE cliente DROP COLUMN IF EXISTS tipo_documento")
    op.execute("ALTER TABLE cliente DROP COLUMN IF EXISTS plazo_credito")
