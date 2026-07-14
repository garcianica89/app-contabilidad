"""Add conciliacion bancaria tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-29
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conciliacion_bancaria",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("cuenta_id", sa.Uuid(), nullable=False),
        sa.Column("fecha_corte", sa.Date(), nullable=False),
        sa.Column("saldo_estado_cuenta", sa.Numeric(14, 2), nullable=False),
        sa.Column("saldo_libros", sa.Numeric(14, 2), nullable=False),
        sa.Column("diferencia", sa.Numeric(14, 2), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("cerrada_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresa.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cuenta_id"], ["cuenta_banco.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "partida_conciliacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conciliacion_id", sa.Uuid(), nullable=False),
        sa.Column("movimiento_banco_id", sa.Uuid(), nullable=True),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("concepto", sa.Text(), nullable=False),
        sa.Column("referencia", sa.String(50), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("monto", sa.Numeric(14, 2), nullable=False),
        sa.Column("conciliado", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("observacion", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["conciliacion_id"], ["conciliacion_bancaria.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["movimiento_banco_id"], ["movimiento_banco.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_partida_conciliacion_conciliacion_id", "partida_conciliacion", ["conciliacion_id"])
    op.create_index("ix_conciliacion_bancaria_cuenta_id", "conciliacion_bancaria", ["cuenta_id"])


def downgrade() -> None:
    op.drop_index("ix_conciliacion_bancaria_cuenta_id")
    op.drop_index("ix_partida_conciliacion_conciliacion_id")
    op.drop_table("partida_conciliacion")
    op.drop_table("conciliacion_bancaria")
