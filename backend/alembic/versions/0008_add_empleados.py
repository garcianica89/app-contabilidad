"""add empleados, departamentos, cargos
Revision ID: 0008
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("departamento",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("empresa_id", sa.Uuid(), sa.ForeignKey("empresa.id"), nullable=False),
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("activo", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
    )
    op.create_table("cargo",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("empresa_id", sa.Uuid(), sa.ForeignKey("empresa.id"), nullable=False),
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("activo", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
    )
    op.create_table("empleado",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("empresa_id", sa.Uuid(), sa.ForeignKey("empresa.id"), nullable=False),
        sa.Column("departamento_id", sa.Uuid(), sa.ForeignKey("departamento.id")),
        sa.Column("cargo_id", sa.Uuid(), sa.ForeignKey("cargo.id")),
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("cedula", sa.String(20), unique=True),
        sa.Column("fecha_nacimiento", sa.Date()),
        sa.Column("fecha_contratacion", sa.Date(), nullable=False),
        sa.Column("salario_base", sa.Numeric(14, 2), nullable=False),
        sa.Column("tipo_contrato", sa.String(20), default="INDEFINIDO"),
        sa.Column("estado", sa.String(20), default="ACTIVO"),
        sa.Column("direccion", sa.Text()),
        sa.Column("telefono", sa.String(20)),
        sa.Column("email", sa.String(100)),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
    )
    op.create_index("ix_empleado_empresa", "empleado", ["empresa_id"])
    op.create_index("ix_departamento_empresa", "departamento", ["empresa_id"])
    op.create_index("ix_cargo_empresa", "cargo", ["empresa_id"])


def downgrade() -> None:
    op.drop_index("ix_cargo_empresa", table_name="cargo")
    op.drop_index("ix_departamento_empresa", table_name="departamento")
    op.drop_index("ix_empleado_empresa", table_name="empleado")
    op.drop_table("empleado")
    op.drop_table("cargo")
    op.drop_table("departamento")
