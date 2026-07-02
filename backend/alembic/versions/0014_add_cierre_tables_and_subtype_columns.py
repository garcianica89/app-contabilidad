"""Add cierre tables, subtype columns, and invert_in_banking

Revision ID: 0014
Revises: 0013
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── New tables ──────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS cierre_mensual (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            periodo_id UUID NOT NULL REFERENCES periodo_contable(id),
            estado VARCHAR(20) DEFAULT 'ABIERTO',
            cerrado_por UUID REFERENCES usuario(id),
            cerrado_en TIMESTAMP,
            reabierto_por UUID REFERENCES usuario(id),
            reabierto_en TIMESTAMP,
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS cierre_fiscal (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            ejercicio_id UUID NOT NULL REFERENCES ejercicio_fiscal(id),
            estado VARCHAR(20) DEFAULT 'EN_PROCESO',
            resultado_ejercicio NUMERIC(14,2),
            cuenta_resultado_id UUID REFERENCES account(id),
            cuenta_utilidad_id UUID REFERENCES account(id),
            asiento_cierre_id UUID REFERENCES asiento(id),
            asiento_apertura_id UUID REFERENCES asiento(id),
            cerrado_por UUID REFERENCES usuario(id),
            cerrado_en TIMESTAMP,
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # ── New columns on documento_subtipo ─────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE documento_subtipo ADD COLUMN IF NOT EXISTS journal_type_id UUID REFERENCES journal_type(id);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE documento_subtipo ADD COLUMN IF NOT EXISTS journal_template_id UUID REFERENCES journal_template(id);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE documento_subtipo ADD COLUMN IF NOT EXISTS cuenta_retencion_iva_id UUID REFERENCES account(id);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE documento_subtipo ADD COLUMN IF NOT EXISTS cuenta_retencion_ir_id UUID REFERENCES account(id);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE documento_subtipo ADD COLUMN IF NOT EXISTS cuenta_mora_id UUID REFERENCES account(id);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE documento_subtipo ADD COLUMN IF NOT EXISTS cuenta_puente_id UUID REFERENCES account(id);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    # ── New column on journal_template_line ─────────────────────────────
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE journal_template_line ADD COLUMN IF NOT EXISTS invert_in_banking BOOLEAN DEFAULT FALSE;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    # ── asiento_id on nomina_periodo ──────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE nomina_periodo ADD COLUMN IF NOT EXISTS asiento_id UUID REFERENCES asiento(id);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS cierre_fiscal")
    op.execute("DROP TABLE IF EXISTS cierre_mensual")
