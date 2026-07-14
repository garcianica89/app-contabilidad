"""Add CHECK constraints for double-entry accounting, non-zero lines

Revision ID: 0029
Revises: 0028
Create Date: 2026-07-11
"""
from alembic import op

revision = "0029"
down_revision = "0028"


def upgrade():
    # Ensure each line has either debit or credit (not both zero, not both non-zero)
    op.execute("""
        ALTER TABLE asiento_linea
        ADD CONSTRAINT chk_asiento_linea_debe_haber
        CHECK (
            (debe > 0 AND haber = 0) OR
            (haber > 0 AND debe = 0) OR
            (debe = 0 AND haber = 0)
        )
    """)
    # Ensure debit and credit are non-negative
    op.execute("""
        ALTER TABLE asiento_linea
        ADD CONSTRAINT chk_asiento_linea_non_negative
        CHECK (debe >= 0 AND haber >= 0)
    """)


def downgrade():
    op.execute("ALTER TABLE asiento_linea DROP CONSTRAINT IF EXISTS chk_asiento_linea_debe_haber")
    op.execute("ALTER TABLE asiento_linea DROP CONSTRAINT IF EXISTS chk_asiento_linea_non_negative")
