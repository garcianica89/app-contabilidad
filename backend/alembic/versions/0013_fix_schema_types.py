"""Fix asiento.numero type integer→string, ensure new columns are tracked

Revision ID: 0013
Revises: 0012
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure new columns added via ALTER TABLE are tracked by Alembic
    # These are idempotent — they skip if column already exists

    # asiento: new columns
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE asiento ADD COLUMN IF NOT EXISTS journal_type_id UUID REFERENCES journal_type(id);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE asiento ADD COLUMN IF NOT EXISTS documento_tipo VARCHAR(20);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE asiento ADD COLUMN IF NOT EXISTS documento_id UUID;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE asiento ADD COLUMN IF NOT EXISTS estado VARCHAR(20) DEFAULT 'CONTABILIZADO';
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    # asiento_linea: debe / haber
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE asiento_linea ADD COLUMN IF NOT EXISTS debe NUMERIC(14,2) DEFAULT 0;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE asiento_linea ADD COLUMN IF NOT EXISTS haber NUMERIC(14,2) DEFAULT 0;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    # permiso: module_id, action_type, scope
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE permiso ADD COLUMN IF NOT EXISTS module_id UUID REFERENCES modulo_sistema(id);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE permiso ADD COLUMN IF NOT EXISTS action_type VARCHAR(50);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE permiso ADD COLUMN IF NOT EXISTS scope VARCHAR(20) DEFAULT 'ALL';
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    # numeracion: prefijo, sufijo, digitos, reinicio, numeracion_manual, permite_reserva, sucursal_id
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE numeracion ADD COLUMN IF NOT EXISTS prefijo VARCHAR(20);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE numeracion ADD COLUMN IF NOT EXISTS sufijo VARCHAR(20);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE numeracion ADD COLUMN IF NOT EXISTS digitos INTEGER DEFAULT 6;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE numeracion ADD COLUMN IF NOT EXISTS reinicio VARCHAR(20) DEFAULT 'NUNCA';
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE numeracion ADD COLUMN IF NOT EXISTS numeracion_manual BOOLEAN DEFAULT FALSE;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE numeracion ADD COLUMN IF NOT EXISTS permite_reserva BOOLEAN DEFAULT FALSE;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE numeracion ADD COLUMN IF NOT EXISTS sucursal_id UUID REFERENCES sucursal(id);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    # Change asiento.numero from integer to varchar(30)
    # Only run if column is still integer
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'asiento' AND column_name = 'numero'
                AND data_type = 'integer'
            ) THEN
                ALTER TABLE asiento ALTER COLUMN numero TYPE VARCHAR(30)
                    USING numero::varchar(30);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Revert asiento.numero back to integer
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'asiento' AND column_name = 'numero'
                AND data_type IN ('character varying', 'text')
            ) THEN
                ALTER TABLE asiento ALTER COLUMN numero TYPE INTEGER
                    USING numero::integer;
            END IF;
        END $$;
    """)
