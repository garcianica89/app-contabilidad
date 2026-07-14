"""Add extra retencion fields and proveedor fiscal config

Revision ID: 0021
Revises: 0020
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0021'
down_revision: Union[str, None] = '0020'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Retencion new columns
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='retencion' AND column_name='cuenta_pagar_id')
            THEN ALTER TABLE retencion ADD COLUMN cuenta_pagar_id UUID REFERENCES account(id); END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='retencion' AND column_name='cuenta_cobrar_id')
            THEN ALTER TABLE retencion ADD COLUMN cuenta_cobrar_id UUID REFERENCES account(id); END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='retencion' AND column_name='base_imponible')
            THEN ALTER TABLE retencion ADD COLUMN base_imponible VARCHAR(20) NOT NULL DEFAULT 'SUBTOTAL'; END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='retencion' AND column_name='prioridad')
            THEN ALTER TABLE retencion ADD COLUMN prioridad INTEGER NOT NULL DEFAULT 10; END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='retencion' AND column_name='redondeo')
            THEN ALTER TABLE retencion ADD COLUMN redondeo INTEGER NOT NULL DEFAULT 2; END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='retencion' AND column_name='naturaleza')
            THEN ALTER TABLE retencion ADD COLUMN naturaleza VARCHAR(10) NOT NULL DEFAULT 'CREDITO'; END IF;
        END $$;
    """)
    # Proveedor new columns
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='proveedor' AND column_name='tipo_fiscal')
            THEN ALTER TABLE proveedor ADD COLUMN tipo_fiscal VARCHAR(20) NOT NULL DEFAULT 'NORMAL'; END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='proveedor' AND column_name='sujeto_retenciones')
            THEN ALTER TABLE proveedor ADD COLUMN sujeto_retenciones BOOLEAN NOT NULL DEFAULT TRUE; END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE retencion DROP COLUMN IF EXISTS cuenta_pagar_id")
    op.execute("ALTER TABLE retencion DROP COLUMN IF EXISTS cuenta_cobrar_id")
    op.execute("ALTER TABLE retencion DROP COLUMN IF EXISTS base_imponible")
    op.execute("ALTER TABLE retencion DROP COLUMN IF EXISTS prioridad")
    op.execute("ALTER TABLE retencion DROP COLUMN IF EXISTS redondeo")
    op.execute("ALTER TABLE retencion DROP COLUMN IF EXISTS naturaleza")
    op.execute("ALTER TABLE proveedor DROP COLUMN IF EXISTS tipo_fiscal")
    op.execute("ALTER TABLE proveedor DROP COLUMN IF EXISTS sujeto_retenciones")
