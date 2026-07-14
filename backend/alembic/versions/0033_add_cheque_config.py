"""Add cheque configuration fields to cuenta_banco

Adds to cuenta_banco:
- cheque_formato_id (FK → cheque_formato)
- cheque_ultimo_numero_operativo (Integer) — sequential for printed cheque number
- cheque_ultimo_numero_contable (Integer) — sequential for accounting reference
- cheque_prefijo (String) — prefix for cheque numbers (eg "A-")
- cheque_formato_numero (String) — template like "{PREF}{NUM}" or "{NUM}"

Also extends Cheque model:
- numero_contable (String) — accounting reference number

Revision ID: 0033
Revises: 0032
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0033"
down_revision = "0032"


def upgrade():
    op.add_column("cuenta_banco", sa.Column("cheque_formato_id", postgresql.UUID(), sa.ForeignKey("cheque_formato.id"), nullable=True))
    op.add_column("cuenta_banco", sa.Column("cheque_ultimo_numero_operativo", sa.Integer(), server_default=sa.text("0")))
    op.add_column("cuenta_banco", sa.Column("cheque_ultimo_numero_contable", sa.Integer(), server_default=sa.text("0")))
    op.add_column("cuenta_banco", sa.Column("cheque_prefijo", sa.String(10), server_default=""))
    op.add_column("cuenta_banco", sa.Column("cheque_formato_numero", sa.String(30), server_default="{NUM}"))

    op.add_column("cheque", sa.Column("numero_contable", sa.String(30), nullable=True))
    op.create_index("ix_cuenta_banco_cheque_formato", "cuenta_banco", ["cheque_formato_id"])


def downgrade():
    op.drop_index("ix_cuenta_banco_cheque_formato", table_name="cuenta_banco")
    op.drop_column("cheque", "numero_contable")
    op.drop_column("cuenta_banco", "cheque_formato_numero")
    op.drop_column("cuenta_banco", "cheque_prefijo")
    op.drop_column("cuenta_banco", "cheque_ultimo_numero_contable")
    op.drop_column("cuenta_banco", "cheque_ultimo_numero_operativo")
    op.drop_column("cuenta_banco", "cheque_formato_id")
