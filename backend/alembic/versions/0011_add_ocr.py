"""add documento_ocr table
Revision ID: 0011
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("documento_ocr",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("empresa_id", sa.Uuid(), sa.ForeignKey("empresa.id"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100)),
        sa.Column("file_size", sa.Integer()),
        sa.Column("estado", sa.String(20), default="PENDIENTE"),
        sa.Column("texto_extraido", sa.Text()),
        sa.Column("datos_procesados", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
    )
    op.create_index("ix_documento_ocr_empresa", "documento_ocr", ["empresa_id"])


def downgrade() -> None:
    op.drop_index("ix_documento_ocr_empresa", table_name="documento_ocr")
    op.drop_table("documento_ocr")
