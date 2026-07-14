"""Add prefijo, digitos, correlativo_actual to journal_type for asiento numbering

Revision ID: 0015
Revises: 0014
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE journal_type ADD COLUMN IF NOT EXISTS prefijo VARCHAR(10) DEFAULT 'CG';
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE journal_type ADD COLUMN IF NOT EXISTS digitos INTEGER DEFAULT 8;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE journal_type ADD COLUMN IF NOT EXISTS correlativo_actual INTEGER DEFAULT 0;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE journal_type DROP COLUMN IF EXISTS prefijo;
        EXCEPTION WHEN undefined_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE journal_type DROP COLUMN IF EXISTS digitos;
        EXCEPTION WHEN undefined_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE journal_type DROP COLUMN IF EXISTS correlativo_actual;
        EXCEPTION WHEN undefined_column THEN NULL;
        END $$;
    """)
