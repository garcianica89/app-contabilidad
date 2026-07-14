"""add analisis_ia table
Revision ID: 0012
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("analisis_ia",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("empresa_id", sa.Uuid(), sa.ForeignKey("empresa.id"), nullable=False),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("modulo", sa.String(50)),
        sa.Column("titulo", sa.String(200)),
        sa.Column("descripcion", sa.Text()),
        sa.Column("datos_entrada", sa.JSON()),
        sa.Column("resultado", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("analisis_ia")
