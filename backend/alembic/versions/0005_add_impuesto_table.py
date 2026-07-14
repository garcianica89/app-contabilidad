"""Add impuesto table

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-29
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'impuesto',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('empresa_id', postgresql.UUID(), nullable=False),
        sa.Column('codigo', sa.String(20), nullable=False),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('tipo', sa.String(30), nullable=False),
        sa.Column('tasa', sa.Numeric(6, 3), nullable=False),
        sa.Column('cuenta_contable_id', postgresql.UUID(), nullable=True),
        sa.Column('activo', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name='fk_impuesto_empresa'),
        sa.ForeignKeyConstraint(['cuenta_contable_id'], ['cuenta_contable.id'], name='fk_impuesto_cuenta_contable'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('empresa_id', 'codigo', name='uq_impuesto_empresa_codigo'),
    )
    op.create_index('ix_impuesto_empresa_id', 'impuesto', ['empresa_id'])
    op.create_index('ix_impuesto_tipo', 'impuesto', ['tipo'])


def downgrade() -> None:
    op.drop_index('ix_impuesto_tipo')
    op.drop_index('ix_impuesto_empresa_id')
    op.drop_table('impuesto')
