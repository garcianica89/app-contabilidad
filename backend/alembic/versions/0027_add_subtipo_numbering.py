"""Add subtipo numbering and movimiento_banco subtipo links

Revision ID: 0027
Revises: 0026
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0027"
down_revision = "0026"


def upgrade():
    op.add_column("documento_subtipo", sa.Column("ultimo_numero", sa.Integer(), server_default="0", nullable=False))
    op.add_column("movimiento_banco", sa.Column("subtipo_id", postgresql.UUID(), sa.ForeignKey("documento_subtipo.id"), nullable=True))
    op.add_column("movimiento_banco", sa.Column("numero_subtipo", sa.Integer(), nullable=True))
    op.create_index("ix_movimiento_banco_subtipo_cuenta", "movimiento_banco", ["subtipo_id", "cuenta_id"])


def downgrade():
    op.drop_index("ix_movimiento_banco_subtipo_cuenta", table_name="movimiento_banco")
    op.drop_column("movimiento_banco", "numero_subtipo")
    op.drop_column("movimiento_banco", "subtipo_id")
    op.drop_column("documento_subtipo", "ultimo_numero")
