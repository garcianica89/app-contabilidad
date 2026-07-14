"""Add fixed asset tables

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-29
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categoria_activo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("vida_util_default", sa.Numeric(3, 0), nullable=True),
        sa.Column("metodo_depreciacion_default", sa.String(20), nullable=True),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresa.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "activo_fijo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("categoria_id", sa.Uuid(), nullable=False),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("fecha_adquisicion", sa.Date(), nullable=False),
        sa.Column("costo_adquisicion", sa.Numeric(14, 2), nullable=False),
        sa.Column("valor_residual", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("vida_util_anos", sa.Numeric(3, 0), nullable=False),
        sa.Column("metodo_depreciacion", sa.String(20), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="ACTIVO"),
        sa.Column("valor_libros", sa.Numeric(14, 2), nullable=False),
        sa.Column("depreciacion_acumulada", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("fecha_baja", sa.Date(), nullable=True),
        sa.Column("motivo_baja", sa.Text(), nullable=True),
        sa.Column("cuenta_contable_id", sa.Uuid(), nullable=True),
        sa.Column("ubicacion", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresa.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["categoria_id"], ["categoria_activo.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cuenta_contable_id"], ["cuenta_contable.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "depreciacion_linea",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("activo_id", sa.Uuid(), nullable=False),
        sa.Column("periodo_id", sa.Uuid(), nullable=False),
        sa.Column("fecha_depreciacion", sa.Date(), nullable=False),
        sa.Column("monto_depreciacion", sa.Numeric(14, 2), nullable=False),
        sa.Column("depreciacion_acumulada", sa.Numeric(14, 2), nullable=False),
        sa.Column("valor_libros_despues", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["activo_id"], ["activo_fijo.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["periodo_id"], ["periodo_contable.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_activo_fijo_empresa", "activo_fijo", ["empresa_id"])
    op.create_index("ix_activo_fijo_categoria", "activo_fijo", ["categoria_id"])
    op.create_index("ix_activo_fijo_estado", "activo_fijo", ["estado"])
    op.create_index("ix_depreciacion_linea_activo", "depreciacion_linea", ["activo_id"])
    op.create_index("ix_depreciacion_linea_periodo", "depreciacion_linea", ["periodo_id"])


def downgrade() -> None:
    op.drop_index("ix_depreciacion_linea_periodo")
    op.drop_index("ix_depreciacion_linea_activo")
    op.drop_index("ix_activo_fijo_estado")
    op.drop_index("ix_activo_fijo_categoria")
    op.drop_index("ix_activo_fijo_empresa")
    op.drop_table("depreciacion_linea")
    op.drop_table("activo_fijo")
    op.drop_table("categoria_activo")
