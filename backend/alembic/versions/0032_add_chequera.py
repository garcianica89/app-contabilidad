"""Create chequera table, add cheque fields to movimiento_banco, create cheque_formato

Adds:
- chequera (checkbook with number ranges per bank account)
- cheque column enhancements (chequera_id, impreso, veces_impreso, movimiento_banco_id, cliente_id)
- cheque_formato (configurable print layout with X/Y coordinates)
- cheque_id FK on movimiento_banco

Revision ID: 0032
Revises: 0031
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0032"
down_revision = "0031"


def upgrade():
    # ── Chequera (checkbook) ──
    op.create_table(
        "chequera",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(), sa.ForeignKey("empresa.id"), nullable=False),
        sa.Column("cuenta_bancaria_id", postgresql.UUID(), sa.ForeignKey("cuenta_banco.id"), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("numero_inicio", sa.Integer(), nullable=False),
        sa.Column("numero_fin", sa.Integer(), nullable=False),
        sa.Column("numero_actual", sa.Integer(), nullable=False),
        sa.Column("activa", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_chequera_cuenta", "chequera", ["cuenta_bancaria_id"])

    # ── Cheque columns added ──
    op.add_column("cheque", sa.Column("chequera_id", postgresql.UUID(), sa.ForeignKey("chequera.id"), nullable=True))
    op.add_column("cheque", sa.Column("cliente_id", postgresql.UUID(), sa.ForeignKey("cliente.id"), nullable=True))
    op.add_column("cheque", sa.Column("movimiento_banco_id", postgresql.UUID(), sa.ForeignKey("movimiento_banco.id"), nullable=True))
    op.add_column("cheque", sa.Column("impreso", sa.Boolean(), server_default=sa.text("false")))
    op.add_column("cheque", sa.Column("veces_impreso", sa.Integer(), server_default=sa.text("0")))

    # Fix nullable columns that should not be NOT NULL
    op.alter_column("cheque", "monto_local", nullable=True, server_default=sa.text("0"))
    op.alter_column("cheque", "monto_usd", nullable=True, server_default=sa.text("0"))
    op.alter_column("cheque", "tipo", nullable=True, server_default=sa.text("'CHEQUE'"))
    op.alter_column("cheque", "estado", nullable=True, server_default=sa.text("'EMITIDO'"))

    # ── Cheque Formato (print template) ──
    op.create_table(
        "cheque_formato",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(), sa.ForeignKey("empresa.id"), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False, server_default="Default"),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true")),

        sa.Column("ancho_mm", sa.Numeric(6, 1), server_default=sa.text("216.0")),
        sa.Column("alto_mm", sa.Numeric(6, 1), server_default=sa.text("89.0")),

        sa.Column("campo_fecha_x", sa.Numeric(6, 1), server_default=sa.text("130.0")),
        sa.Column("campo_fecha_y", sa.Numeric(6, 1), server_default=sa.text("14.0")),
        sa.Column("campo_fecha_formato", sa.String(20), server_default="DD/MM/YYYY"),

        sa.Column("campo_pagadero_x", sa.Numeric(6, 1), server_default=sa.text("25.0")),
        sa.Column("campo_pagadero_y", sa.Numeric(6, 1), server_default=sa.text("28.0")),

        sa.Column("campo_monto_num_x", sa.Numeric(6, 1), server_default=sa.text("130.0")),
        sa.Column("campo_monto_num_y", sa.Numeric(6, 1), server_default=sa.text("28.0")),

        sa.Column("campo_monto_letras_x", sa.Numeric(6, 1), server_default=sa.text("25.0")),
        sa.Column("campo_monto_letras_y", sa.Numeric(6, 1), server_default=sa.text("42.0")),

        sa.Column("campo_concepto_x", sa.Numeric(6, 1), server_default=sa.text("25.0")),
        sa.Column("campo_concepto_y", sa.Numeric(6, 1), server_default=sa.text("56.0")),

        sa.Column("campo_firma_x", sa.Numeric(6, 1), server_default=sa.text("25.0")),
        sa.Column("campo_firma_y", sa.Numeric(6, 1), server_default=sa.text("72.0")),

        sa.Column("fuente_nombre", sa.String(50), server_default="Courier New"),
        sa.Column("fuente_tamano", sa.Integer(), server_default=sa.text("11")),

        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # ── Add cheque_id FK to movimiento_banco ──
    op.add_column("movimiento_banco", sa.Column("cheque_id", postgresql.UUID(), sa.ForeignKey("cheque.id"), nullable=True))
    op.create_index("ix_movimiento_banco_cheque", "movimiento_banco", ["cheque_id"])

    # ── Create index on cheque.chequera_id ──
    op.execute("CREATE INDEX IF NOT EXISTS ix_cheque_chequera ON cheque(chequera_id)")


def downgrade():
    op.drop_index("ix_movimiento_banco_cheque", table_name="movimiento_banco")
    op.drop_column("movimiento_banco", "cheque_id")

    op.drop_table("cheque_formato")

    op.drop_column("cheque", "veces_impreso")
    op.drop_column("cheque", "impreso")
    op.drop_column("cheque", "movimiento_banco_id")
    op.drop_column("cheque", "cliente_id")
    op.drop_column("cheque", "chequera_id")

    op.drop_index("ix_chequera_cuenta", table_name="chequera")
    op.drop_table("chequera")
