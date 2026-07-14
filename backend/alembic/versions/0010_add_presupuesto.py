"""add presupuesto tables
Revision ID: 0010
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("presupuesto",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("empresa_id", sa.Uuid(), sa.ForeignKey("empresa.id"), nullable=False),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("version", sa.Integer(), default=1),
        sa.Column("estado", sa.String(20), default="BORRADOR"),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
    )
    op.create_table("presupuesto_partida",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("presupuesto_id", sa.Uuid(), sa.ForeignKey("presupuesto.id"), nullable=False),
        sa.Column("cuenta_contable_id", sa.Uuid(), sa.ForeignKey("cuenta_contable.id"), nullable=False),
        sa.Column("centro_costo_id", sa.Uuid(), sa.ForeignKey("centro_costo.id")),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("monto_presupuestado", sa.Numeric(14, 2), nullable=False),
    )
    op.create_index("ix_presupuesto_empresa", "presupuesto", ["empresa_id"])
    op.create_index("ix_presupuesto_partida_presupuesto", "presupuesto_partida", ["presupuesto_id"])


def downgrade() -> None:
    op.drop_index("ix_presupuesto_partida_presupuesto", table_name="presupuesto_partida")
    op.drop_index("ix_presupuesto_empresa", table_name="presupuesto")
    op.drop_table("presupuesto_partida")
    op.drop_table("presupuesto")
