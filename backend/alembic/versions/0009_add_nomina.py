"""add nomina tables
Revision ID: 0009
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("nomina_config",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("empresa_id", sa.Uuid(), sa.ForeignKey("empresa.id"), nullable=False),
        sa.Column("salario_minimo", sa.Numeric(14, 2), default=0),
        sa.Column("inss_patronal_rate", sa.Numeric(5, 4), default=0.225),
        sa.Column("inss_laboral_rate", sa.Numeric(5, 4), default=0.07),
        sa.Column("ir_tramos", sa.JSON()),
        sa.Column("aguinaldo_dias", sa.Integer(), default=30),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_table("nomina_periodo",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("empresa_id", sa.Uuid(), sa.ForeignKey("empresa.id"), nullable=False),
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=False),
        sa.Column("fecha_pago", sa.Date(), nullable=False),
        sa.Column("estado", sa.String(20), default="BORRADOR"),
        sa.Column("total_devengado", sa.Numeric(14, 2), default=0),
        sa.Column("total_deducciones", sa.Numeric(14, 2), default=0),
        sa.Column("total_neto", sa.Numeric(14, 2), default=0),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
    )
    op.create_table("nomina_detalle",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("nomina_periodo_id", sa.Uuid(), sa.ForeignKey("nomina_periodo.id"), nullable=False),
        sa.Column("empleado_id", sa.Uuid(), sa.ForeignKey("empleado.id"), nullable=False),
        sa.Column("dias_trabajados", sa.Integer(), default=30),
        sa.Column("salario_base", sa.Numeric(14, 2), nullable=False),
        sa.Column("horas_extra", sa.Numeric(14, 2), default=0),
        sa.Column("bonos", sa.Numeric(14, 2), default=0),
        sa.Column("comisiones", sa.Numeric(14, 2), default=0),
        sa.Column("total_devengado", sa.Numeric(14, 2), nullable=False),
        sa.Column("inss_laboral", sa.Numeric(14, 2), default=0),
        sa.Column("ir", sa.Numeric(14, 2), default=0),
        sa.Column("otras_deducciones", sa.Numeric(14, 2), default=0),
        sa.Column("total_deducciones", sa.Numeric(14, 2), nullable=False),
        sa.Column("neto", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
    )
    op.create_index("ix_nomina_periodo_empresa", "nomina_periodo", ["empresa_id"])
    op.create_index("ix_nomina_detalle_periodo", "nomina_detalle", ["nomina_periodo_id"])


def downgrade() -> None:
    op.drop_index("ix_nomina_detalle_periodo", table_name="nomina_detalle")
    op.drop_index("ix_nomina_periodo_empresa", table_name="nomina_periodo")
    op.drop_table("nomina_detalle")
    op.drop_table("nomina_periodo")
    op.drop_table("nomina_config")
