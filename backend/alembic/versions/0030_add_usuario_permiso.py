"""Add usuario_permiso table for direct user permissions with entity scope

Adds direct user-to-permission assignments (bypassing roles) with optional
entity_type + entity_id scoping for granular access control.

e.g.:
  - User X has permiso 'cuentas.leer' (global)
  - User X has permiso 'cuentas.leer' scoped to entity_type='cuenta_contable', entity_id='uuid'
  - User X has permiso 'asientos.leer' scoped to entity_type='asiento', entity_id='uuid'

Revision ID: 0030
Revises: 0029
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0030"
down_revision = "0029"


def upgrade():
    op.create_table(
        "usuario_permiso",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(), sa.ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permiso_id", postgresql.UUID(), sa.ForeignKey("permiso.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True, comment="NULL=global, e.g. cuenta_contable, asiento, documento_tipo, documento_subtipo, modulo_sistema, bodega, centro_costo, ..."),
        sa.Column("entity_id", postgresql.UUID(), nullable=True, comment="UUID of the specific entity (NULL if global)"),
        sa.Column("allow", sa.Boolean(), server_default=sa.text("true"), nullable=False, comment="true=grant, false=deny (explicit override)"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("usuario_id", "permiso_id", "entity_type", "entity_id", name="uq_usuario_permiso"),
    )
    op.create_index("ix_usuario_permiso_usuario", "usuario_permiso", ["usuario_id"])
    op.create_index("ix_usuario_permiso_entity", "usuario_permiso", ["entity_type", "entity_id"])

    # Add empresa_id + is_admin to permiso for multi-tenant scope
    op.add_column("permiso", sa.Column("empresa_id", postgresql.UUID(), sa.ForeignKey("empresa.id"), nullable=True))
    op.add_column("permiso", sa.Column("is_system", sa.Boolean(), server_default=sa.text("false")))

    # Populate is_admin=true for the admin role
    op.execute("UPDATE permiso SET is_system = false WHERE is_system IS NULL")


def downgrade():
    op.drop_index("ix_usuario_permiso_entity", table_name="usuario_permiso")
    op.drop_index("ix_usuario_permiso_usuario", table_name="usuario_permiso")
    op.drop_table("usuario_permiso")
    op.drop_column("permiso", "is_system")
    op.drop_column("permiso", "empresa_id")
