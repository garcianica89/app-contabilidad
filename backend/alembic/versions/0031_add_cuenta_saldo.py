"""Create cuenta_saldo table for cached monthly account balances

Enables fast trial balance queries by caching period-end balances.
Supports incremental recalculation: saldo_final from previous period
+ debe/haber movements from current period.

Revision ID: 0031
Revises: 0030
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0031"
down_revision = "0030"


def upgrade():
    op.create_table(
        "cuenta_saldo",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(), sa.ForeignKey("empresa.id"), nullable=False),
        sa.Column("cuenta_id", postgresql.UUID(), sa.ForeignKey("account.id"), nullable=False),
        sa.Column("periodo_id", postgresql.UUID(), sa.ForeignKey("periodo_contable.id"), nullable=False),
        sa.Column("centro_costo_id", postgresql.UUID(), sa.ForeignKey("centro_costo.id"), nullable=True),
        sa.Column("saldo_anterior", sa.Numeric(14, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("debe", sa.Numeric(14, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("haber", sa.Numeric(14, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("saldo_final", sa.Numeric(14, 2), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "naturaleza", sa.String(10), nullable=False,
            comment="DEUDORA or ACREEDORA — copied from account_type.nature at calculation time",
        ),
        sa.Column("recalculado_en", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "empresa_id", "cuenta_id", "periodo_id", "centro_costo_id",
            name="uq_cuenta_saldo_periodo",
        ),
    )
    op.create_index("ix_cuenta_saldo_periodo", "cuenta_saldo", ["empresa_id", "periodo_id"])
    op.create_index("ix_cuenta_saldo_cuenta", "cuenta_saldo", ["cuenta_id"])


def downgrade():
    op.drop_index("ix_cuenta_saldo_cuenta", table_name="cuenta_saldo")
    op.drop_index("ix_cuenta_saldo_periodo", table_name="cuenta_saldo")
    op.drop_table("cuenta_saldo")
