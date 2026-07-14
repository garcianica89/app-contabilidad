"""Add TipoCuentaBanco, origen col, periodo conciliacion, account link

Revision ID: 0028
Revises: 0027
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0028"
down_revision = "0027"


def upgrade():
    # TipoCuentaBanco
    op.create_table(
        "tipo_cuenta_banco",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(), sa.ForeignKey("empresa.id"), nullable=False),
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_tipo_cuenta_banco_empresa_codigo", "tipo_cuenta_banco", ["empresa_id", "codigo"])

    # CuentaBanco: add tipo_cuenta_banco_id, cuenta_contable_id
    op.add_column("cuenta_banco", sa.Column("tipo_cuenta_banco_id", postgresql.UUID(), sa.ForeignKey("tipo_cuenta_banco.id")))
    op.add_column("cuenta_banco", sa.Column("cuenta_contable_id", postgresql.UUID(), sa.ForeignKey("account.id")))

    # MovimientoBanco: add origen ('LIBRO' or 'BANCO')
    op.add_column("movimiento_banco", sa.Column("origen", sa.String(10), server_default="LIBRO"))
    op.execute("UPDATE movimiento_banco SET origen = 'LIBRO' WHERE asiento_id IS NOT NULL")
    op.execute("UPDATE movimiento_banco SET origen = 'BANCO' WHERE asiento_id IS NULL")

    # ConciliacionBancaria: periodo-based redesign
    op.add_column("conciliacion_bancaria", sa.Column("periodo_id", postgresql.UUID(), sa.ForeignKey("periodo_contable.id")))
    op.add_column("conciliacion_bancaria", sa.Column("saldo_inicial_libro", sa.Numeric(14, 2), server_default="0"))
    op.add_column("conciliacion_bancaria", sa.Column("saldo_inicial_banco", sa.Numeric(14, 2), server_default="0"))
    op.add_column("conciliacion_bancaria", sa.Column("fecha_inicio", sa.Date()))
    op.add_column("conciliacion_bancaria", sa.Column("fecha_fin", sa.Date()))
    op.alter_column("conciliacion_bancaria", "saldo_estado_cuenta", new_column_name="saldo_final_banco")
    op.alter_column("conciliacion_bancaria", "saldo_libros", new_column_name="saldo_final_libro")

    # Update existing conciliaciones: set fecha_inicio/fin from fecha_corte (month)
    op.execute("""
        UPDATE conciliacion_bancaria
        SET fecha_inicio = date_trunc('month', fecha_corte)::date,
            fecha_fin = (date_trunc('month', fecha_corte) + interval '1 month - 1 day')::date
    """)

    # Add unique constraint on cuenta_banco_id + periodo_id
    op.create_unique_constraint("uq_conciliacion_cuenta_periodo", "conciliacion_bancaria", ["cuenta_id", "periodo_id"])

    # Seed tipos de cuenta for existing empresas
    op.execute("""
        INSERT INTO tipo_cuenta_banco (id, empresa_id, codigo, nombre)
        SELECT gen_random_uuid(), id, 'CORRIENTE', 'Cuenta Corriente' FROM empresa
        UNION ALL
        SELECT gen_random_uuid(), id, 'AHORRO', 'Cuenta de Ahorro' FROM empresa
    """)


def downgrade():
    op.drop_constraint("uq_conciliacion_cuenta_periodo", "conciliacion_bancaria")
    op.drop_column("conciliacion_bancaria", "fecha_fin")
    op.drop_column("conciliacion_bancaria", "fecha_inicio")
    op.drop_column("conciliacion_bancaria", "saldo_inicial_banco")
    op.drop_column("conciliacion_bancaria", "saldo_inicial_libro")
    op.drop_column("conciliacion_bancaria", "periodo_id")
    op.alter_column("conciliacion_bancaria", "saldo_final_banco", new_column_name="saldo_estado_cuenta")
    op.alter_column("conciliacion_bancaria", "saldo_final_libro", new_column_name="saldo_libros")
    op.drop_column("movimiento_banco", "origen")
    op.drop_column("cuenta_banco", "cuenta_contable_id")
    op.drop_column("cuenta_banco", "tipo_cuenta_banco_id")
    op.drop_table("tipo_cuenta_banco")
