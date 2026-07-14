"""Create ERP module tables (32 new tables for CG, CI, FA, CO, CC, AF, CB, RH, PE)

Revision ID: 0016
Revises: 0015
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid_pk():
    return "UUID DEFAULT gen_random_uuid() PRIMARY KEY"


def _uuid_fk(ref: str):
    return f"UUID REFERENCES {ref}(id)"


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # ── 1. Tables without foreign keys to other ERP tables ──────
    op.execute("""
        CREATE TABLE IF NOT EXISTS paquete (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            codigo VARCHAR(10) NOT NULL UNIQUE,
            descripcion VARCHAR(100) NOT NULL,
            ultimo_asiento INTEGER DEFAULT 0 NOT NULL,
            usa_doble_moneda BOOLEAN DEFAULT TRUE NOT NULL,
            prefijo VARCHAR(10) DEFAULT '' NOT NULL,
            digitos INTEGER DEFAULT 8 NOT NULL,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_paquete_empresa ON paquete(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS tipo_activo (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            codigo VARCHAR(20) NOT NULL,
            nombre VARCHAR(100) NOT NULL,
            tasa_depreciacion_fiscal NUMERIC(5,2) DEFAULT 0 NOT NULL,
            tasa_depreciacion_contable NUMERIC(5,2) DEFAULT 0 NOT NULL,
            metodo_depreciacion VARCHAR(20) DEFAULT 'LINEA_RECTA' NOT NULL,
            activa BOOLEAN DEFAULT TRUE NOT NULL,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tipo_activo_empresa ON tipo_activo(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS cuenta_bancaria (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            codigo VARCHAR(20) NOT NULL,
            banco VARCHAR(100) NOT NULL,
            numero_cuenta VARCHAR(50) NOT NULL,
            tipo VARCHAR(20) DEFAULT 'CORRIENTE' NOT NULL,
            moneda_id UUID,
            saldo_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            saldo_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            activa BOOLEAN DEFAULT TRUE NOT NULL,
            cuenta_contable_id UUID,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_cuenta_bancaria_empresa ON cuenta_bancaria(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS global_config (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            modulo VARCHAR(10) NOT NULL,
            nombre VARCHAR(100) NOT NULL,
            tipo VARCHAR(5) DEFAULT 'C' NOT NULL,
            valor VARCHAR(500),
            texto TEXT,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL,
            UNIQUE (modulo, nombre)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_global_config_empresa ON global_config(empresa_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_global_config_modulo ON global_config(modulo)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS nomina (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            codigo VARCHAR(20) NOT NULL,
            descripcion VARCHAR(100) NOT NULL,
            periodicidad VARCHAR(20) DEFAULT 'MENSUAL' NOT NULL,
            activa BOOLEAN DEFAULT TRUE NOT NULL,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_nomina_empresa ON nomina(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS nomina_concepto (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            codigo VARCHAR(20) NOT NULL,
            nombre VARCHAR(100) NOT NULL,
            tipo VARCHAR(20) NOT NULL,
            formula VARCHAR(200),
            cuenta_contable_id UUID,
            activo BOOLEAN DEFAULT TRUE NOT NULL,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_nomina_concepto_empresa ON nomina_concepto(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS puesto (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            codigo VARCHAR(20) NOT NULL,
            nombre VARCHAR(100) NOT NULL,
            salario_minimo NUMERIC(18,2) DEFAULT 0 NOT NULL,
            salario_maximo NUMERIC(18,2) DEFAULT 0 NOT NULL,
            activo BOOLEAN DEFAULT TRUE NOT NULL,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_puesto_empresa ON puesto(empresa_id)")

    # ── 2. Tables with FK to level 1 or existing app tables ────
    op.execute("""
        CREATE TABLE IF NOT EXISTS articulo (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            codigo VARCHAR(50) NOT NULL,
            descripcion VARCHAR(200) NOT NULL,
            descripcion_adicional VARCHAR(200),
            unidad_medida VARCHAR(10) DEFAULT 'UNIDAD' NOT NULL,
            tipo_costo VARCHAR(20) DEFAULT 'PROMEDIO' NOT NULL,
            cuenta_contable_id UUID REFERENCES cuenta_contable(id),
            costo_prom_local NUMERIC(18,4) DEFAULT 0 NOT NULL,
            costo_prom_usd NUMERIC(18,4) DEFAULT 0 NOT NULL,
            costo_ult_local NUMERIC(18,4) DEFAULT 0 NOT NULL,
            costo_ult_usd NUMERIC(18,4) DEFAULT 0 NOT NULL,
            costo_std_local NUMERIC(18,4) DEFAULT 0 NOT NULL,
            costo_std_usd NUMERIC(18,4) DEFAULT 0 NOT NULL,
            costo_prom_comparativo_local NUMERIC(18,4) DEFAULT 0 NOT NULL,
            costo_prom_comparativo_usd NUMERIC(18,4) DEFAULT 0 NOT NULL,
            costo_prom_ultimo_local NUMERIC(18,4) DEFAULT 0 NOT NULL,
            costo_prom_ultimo_usd NUMERIC(18,4) DEFAULT 0 NOT NULL,
            activo BOOLEAN DEFAULT TRUE NOT NULL,
            categoria_id UUID,
            impuesto_id UUID,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_articulo_codigo ON articulo(codigo)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_articulo_empresa ON articulo(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS cheque (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            numero VARCHAR(30) NOT NULL,
            cuenta_bancaria_id UUID NOT NULL REFERENCES cuenta_bancaria(id),
            pagadero_a VARCHAR(200) NOT NULL,
            monto NUMERIC(18,2) NOT NULL,
            monto_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            monto_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            tipo VARCHAR(20) DEFAULT 'CHEQUE' NOT NULL,
            metodo_pago VARCHAR(30),
            referencia VARCHAR(50),
            concepto VARCHAR(200),
            fecha DATE NOT NULL,
            estado VARCHAR(20) DEFAULT 'EMITIDO' NOT NULL,
            proveedor_id UUID REFERENCES proveedor(id),
            asiento_id UUID,
            tipo_cambio NUMERIC(10,4) DEFAULT 1 NOT NULL,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_cheque_numero ON cheque(numero)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cheque_cuenta ON cheque(cuenta_bancaria_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cheque_empresa ON cheque(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS pedido (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            numero VARCHAR(30) NOT NULL,
            cliente_id UUID NOT NULL REFERENCES cliente(id),
            fecha_pedido DATE NOT NULL,
            fecha_entrega DATE,
            total_mercaderia NUMERIC(18,2) DEFAULT 0 NOT NULL,
            estado VARCHAR(20) DEFAULT 'PENDIENTE' NOT NULL,
            vendedor_id UUID,
            cobrador_id UUID,
            ruta VARCHAR(30),
            zona VARCHAR(30),
            bodega_id UUID REFERENCES bodega(id),
            condicion_pago_id UUID,
            moneda_id UUID,
            tipo_cambio NUMERIC(10,4) DEFAULT 1 NOT NULL,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_pedido_numero ON pedido(numero)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_pedido_cliente ON pedido(cliente_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_pedido_empresa ON pedido(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS presupuesto_venta (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            numero VARCHAR(30) NOT NULL,
            cliente_id UUID REFERENCES cliente(id),
            fecha DATE NOT NULL,
            fecha_validez DATE,
            total NUMERIC(18,2) DEFAULT 0 NOT NULL,
            estado VARCHAR(20) DEFAULT 'VIGENTE' NOT NULL,
            observaciones TEXT,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_presupuesto_venta_numero ON presupuesto_venta(numero)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_presupuesto_venta_empresa ON presupuesto_venta(empresa_id)")

    # ── 3. Tables with FK to level 2 ──────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS existencia_bodega (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            articulo_id UUID NOT NULL REFERENCES articulo(id),
            bodega_id UUID NOT NULL REFERENCES bodega(id),
            cantidad_disponible NUMERIC(18,4) DEFAULT 0 NOT NULL,
            cantidad_reservada NUMERIC(18,4) DEFAULT 0 NOT NULL,
            costo_unt_promedio_local NUMERIC(18,4) DEFAULT 0 NOT NULL,
            costo_unt_promedio_usd NUMERIC(18,4) DEFAULT 0 NOT NULL,
            costo_unt_estandar_local NUMERIC(18,4) DEFAULT 0 NOT NULL,
            costo_unt_estandar_usd NUMERIC(18,4) DEFAULT 0 NOT NULL,
            costo_prom_comparativo_local NUMERIC(18,4) DEFAULT 0 NOT NULL,
            costo_prom_comparativo_usd NUMERIC(18,4) DEFAULT 0 NOT NULL,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL,
            UNIQUE (articulo_id, bodega_id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_existencia_bodega_articulo ON existencia_bodega(articulo_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_existencia_bodega_empresa ON existencia_bodega(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS transaccion_inv (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            consecutivo INTEGER NOT NULL,
            articulo_id UUID NOT NULL REFERENCES articulo(id),
            bodega_id UUID NOT NULL REFERENCES bodega(id),
            cantidad NUMERIC(18,4) NOT NULL,
            costo_tot_fiscal_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            costo_tot_fiscal_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            costo_tot_comp_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            costo_tot_comp_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            precio_total_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            precio_total_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            tipo VARCHAR(20) NOT NULL,
            subtipo VARCHAR(20),
            subsubtipo VARCHAR(20),
            fecha DATE NOT NULL,
            asiento_cardex_id UUID,
            nit VARCHAR(30),
            centro_costo_id UUID,
            cuenta_contable_id UUID REFERENCES cuenta_contable(id),
            doc_fiscal VARCHAR(50),
            tipo_cambio NUMERIC(10,4) DEFAULT 1 NOT NULL,
            referencia VARCHAR(200),
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_transaccion_inv_articulo ON transaccion_inv(articulo_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_transaccion_inv_fecha ON transaccion_inv(fecha)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_transaccion_inv_consecutivo ON transaccion_inv(consecutivo)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_transaccion_inv_empresa ON transaccion_inv(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS factura (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            numero VARCHAR(30) NOT NULL,
            tipo_documento VARCHAR(5) NOT NULL,
            cliente_id UUID NOT NULL REFERENCES cliente(id),
            fecha DATE NOT NULL,
            fecha_vence DATE,
            total_mercaderia NUMERIC(18,2) DEFAULT 0 NOT NULL,
            total_impuestos NUMERIC(18,2) DEFAULT 0 NOT NULL,
            total_factura NUMERIC(18,2) DEFAULT 0 NOT NULL,
            monto_cobrado NUMERIC(18,2) DEFAULT 0 NOT NULL,
            saldo NUMERIC(18,2) DEFAULT 0 NOT NULL,
            moneda_id UUID,
            tipo_cambio NUMERIC(10,4) DEFAULT 1 NOT NULL,
            consecutivo_fiscal VARCHAR(50),
            tipo_factura VARCHAR(20),
            bodega_id UUID,
            vendedor_id UUID,
            asiento_id UUID,
            anulada BOOLEAN DEFAULT FALSE NOT NULL,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_factura_numero ON factura(numero)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_factura_cliente ON factura(cliente_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_factura_empresa ON factura(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS factura_linea (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            factura_id UUID NOT NULL REFERENCES factura(id),
            linea INTEGER NOT NULL,
            articulo_id UUID NOT NULL REFERENCES articulo(id),
            cantidad NUMERIC(18,4) NOT NULL,
            precio_unitario NUMERIC(18,4) DEFAULT 0 NOT NULL,
            precio_total NUMERIC(18,2) DEFAULT 0 NOT NULL,
            costo_total_fiscal_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            costo_total_fiscal_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            costo_total_comp_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            costo_total_comp_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            descuento NUMERIC(18,2) DEFAULT 0 NOT NULL,
            bodega_id UUID NOT NULL REFERENCES bodega(id),
            impuesto_id UUID,
            tarifa_impuesto NUMERIC(5,2) DEFAULT 0 NOT NULL,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_factura_linea_factura ON factura_linea(factura_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_factura_linea_empresa ON factura_linea(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS pedido_linea (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            pedido_id UUID NOT NULL REFERENCES pedido(id),
            linea INTEGER NOT NULL,
            articulo_id UUID NOT NULL REFERENCES articulo(id),
            cantidad NUMERIC(18,4) NOT NULL,
            cantidad_despachada NUMERIC(18,4) DEFAULT 0 NOT NULL,
            precio_unitario NUMERIC(18,4) DEFAULT 0 NOT NULL,
            precio_total NUMERIC(18,2) DEFAULT 0 NOT NULL,
            descuento NUMERIC(18,2) DEFAULT 0 NOT NULL,
            bodega_id UUID REFERENCES bodega(id),
            estado VARCHAR(20) DEFAULT 'PENDIENTE' NOT NULL,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_pedido_linea_pedido ON pedido_linea(pedido_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_pedido_linea_empresa ON pedido_linea(empresa_id)")

    # ── 4. Document tables (CC/CP) ────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS documento_cc (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            cliente_id UUID NOT NULL REFERENCES cliente(id),
            numero VARCHAR(30) NOT NULL,
            tipo VARCHAR(5) NOT NULL,
            fecha_documento DATE NOT NULL,
            fecha_vence DATE,
            monto NUMERIC(18,2) DEFAULT 0 NOT NULL,
            saldo NUMERIC(18,2) DEFAULT 0 NOT NULL,
            monto_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            saldo_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            monto_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            saldo_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            tipo_cambio NUMERIC(10,4) DEFAULT 1 NOT NULL,
            asiento_id UUID,
            factura_id UUID REFERENCES factura(id),
            vendedor_id UUID,
            cobrador_id UUID,
            anulado BOOLEAN DEFAULT FALSE NOT NULL,
            aprobado BOOLEAN DEFAULT TRUE NOT NULL,
            condicion_pago_id UUID,
            moneda_id UUID,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL,
            UNIQUE (cliente_id, numero, tipo)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_documento_cc_cliente ON documento_cc(cliente_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_documento_cc_empresa ON documento_cc(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS documento_cp (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            proveedor_id UUID NOT NULL REFERENCES proveedor(id),
            numero VARCHAR(30) NOT NULL,
            tipo VARCHAR(5) NOT NULL,
            fecha_documento DATE NOT NULL,
            fecha_vence DATE,
            monto NUMERIC(18,2) DEFAULT 0 NOT NULL,
            saldo NUMERIC(18,2) DEFAULT 0 NOT NULL,
            monto_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            saldo_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            monto_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            saldo_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            tipo_cambio NUMERIC(10,4) DEFAULT 1 NOT NULL,
            asiento_id UUID,
            anulado BOOLEAN DEFAULT FALSE NOT NULL,
            condicion_pago_id UUID,
            moneda_id UUID,
            orden_compra_id UUID REFERENCES orden_compra(id),
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL,
            UNIQUE (proveedor_id, numero, tipo)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_documento_cp_proveedor ON documento_cp(proveedor_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_documento_cp_empresa ON documento_cp(empresa_id)")

    # ── 5. Auxiliary tables ───────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS auxiliar_cc (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            documento_cc_id UUID NOT NULL REFERENCES documento_cc(id),
            fecha DATE NOT NULL,
            tipo_movimiento VARCHAR(20) NOT NULL,
            monto_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            monto_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            referencia VARCHAR(200),
            asiento_id UUID,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_auxiliar_cc_documento ON auxiliar_cc(documento_cc_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_auxiliar_cc_empresa ON auxiliar_cc(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS auxiliar_cp (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            documento_cp_id UUID NOT NULL REFERENCES documento_cp(id),
            fecha DATE NOT NULL,
            tipo_movimiento VARCHAR(20) NOT NULL,
            monto_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            monto_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            referencia VARCHAR(200),
            asiento_id UUID,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_auxiliar_cp_documento ON auxiliar_cp(documento_cp_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_auxiliar_cp_empresa ON auxiliar_cp(empresa_id)")

    # ── 6. Asiento / Mayor / Cheque / MovBanco ────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS asiento_de_diario (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            numero VARCHAR(30) NOT NULL,
            paquete_id UUID NOT NULL REFERENCES paquete(id),
            tipo_asiento VARCHAR(20) NOT NULL,
            fecha DATE NOT NULL,
            periodo_id UUID NOT NULL REFERENCES periodo_contable(id),
            total_debito_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            total_credito_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            total_debito_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            total_credito_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            marcado BOOLEAN DEFAULT FALSE NOT NULL,
            notas TEXT,
            origen VARCHAR(50),
            dependencia_id UUID REFERENCES asiento_de_diario(id),
            documento_global_id VARCHAR(50),
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_asiento_de_diario_numero ON asiento_de_diario(numero)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_asiento_de_diario_empresa ON asiento_de_diario(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS mov_banco (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            cuenta_bancaria_id UUID NOT NULL REFERENCES cuenta_bancaria(id),
            tipo_documento VARCHAR(10) NOT NULL,
            numero VARCHAR(30) NOT NULL,
            fecha DATE NOT NULL,
            monto NUMERIC(18,2) NOT NULL,
            monto_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            monto_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            tipo_cambio NUMERIC(10,4) DEFAULT 1 NOT NULL,
            concepto VARCHAR(200),
            asiento_id UUID,
            conciliacion_id UUID,
            anulado BOOLEAN DEFAULT FALSE NOT NULL,
            origen VARCHAR(30),
            cheque_id UUID REFERENCES cheque(id),
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL,
            UNIQUE (cuenta_bancaria_id, tipo_documento, numero)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_mov_banco_cuenta ON mov_banco(cuenta_bancaria_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mov_banco_empresa ON mov_banco(empresa_id)")

    # ── 7. Diario / Mayor detail tables ───────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS diario (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            asiento_id UUID NOT NULL REFERENCES asiento_de_diario(id),
            consecutivo INTEGER NOT NULL,
            nit VARCHAR(30),
            centro_costo_id UUID,
            cuenta_contable_id UUID NOT NULL REFERENCES cuenta_contable(id),
            debito_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            debito_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            credito_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            credito_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            tipo_cambio NUMERIC(10,4) DEFAULT 1 NOT NULL,
            referencia VARCHAR(200),
            fuente VARCHAR(30),
            base_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            base_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            proyecto_id UUID,
            fase VARCHAR(30),
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_diario_asiento ON diario(asiento_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_diario_cuenta ON diario(cuenta_contable_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_diario_empresa ON diario(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS mayor (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            asiento_id UUID NOT NULL REFERENCES asiento_de_diario(id),
            consecutivo INTEGER NOT NULL,
            cuenta_contable_id UUID NOT NULL REFERENCES cuenta_contable(id),
            fecha DATE NOT NULL,
            debito_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            credito_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            debito_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            credito_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            periodo_id UUID NOT NULL REFERENCES periodo_contable(id),
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_mayor_asiento ON mayor(asiento_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mayor_cuenta ON mayor(cuenta_contable_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mayor_periodo ON mayor(periodo_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mayor_empresa ON mayor(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS asiento_distribuido (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            asiento_id UUID NOT NULL REFERENCES asiento_de_diario(id),
            cuenta_origen_id UUID NOT NULL REFERENCES cuenta_contable(id),
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_asiento_distribuido_asiento ON asiento_distribuido(asiento_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_asiento_distribuido_empresa ON asiento_distribuido(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS asiento_dist_linea (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            distribuido_id UUID NOT NULL REFERENCES asiento_distribuido(id),
            cuenta_destino_id UUID NOT NULL REFERENCES cuenta_contable(id),
            centro_costo_id UUID,
            porcentaje NUMERIC(5,2) DEFAULT 0 NOT NULL,
            monto_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            monto_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_asiento_dist_linea_distribuido ON asiento_dist_linea(distribuido_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_asiento_dist_linea_empresa ON asiento_dist_linea(empresa_id)")

    # ── 8. Activo Fijo child tables ───────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS activo_accion (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            activo_fijo_id UUID NOT NULL REFERENCES activo_fijo(id),
            tipo_accion VARCHAR(30) NOT NULL,
            fecha DATE NOT NULL,
            estado_activo VARCHAR(20),
            estado_accion VARCHAR(20) DEFAULT 'PENDIENTE' NOT NULL,
            responsable VARCHAR(50),
            fecha_aplicacion DATE,
            fecha_aprobacion DATE,
            rubro1 NUMERIC(18,2),
            rubro2 NUMERIC(18,2),
            rubro3 NUMERIC(18,2),
            rubro4 NUMERIC(18,2),
            rubro5 NUMERIC(18,2),
            observaciones TEXT,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_activo_accion_activo ON activo_accion(activo_fijo_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_activo_accion_empresa ON activo_accion(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS hist_depreciacion (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            activo_fijo_id UUID NOT NULL REFERENCES activo_fijo(id),
            fecha DATE NOT NULL,
            periodo_id UUID,
            metodo VARCHAR(20) DEFAULT 'LINEA_RECTA' NOT NULL,
            depr_local NUMERIC(18,2) DEFAULT 0 NOT NULL,
            depr_usd NUMERIC(18,2) DEFAULT 0 NOT NULL,
            asiento_id UUID,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_hist_depreciacion_activo ON hist_depreciacion(activo_fijo_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_hist_depreciacion_empresa ON hist_depreciacion(empresa_id)")

    # ── 9. RH child tables ────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS empleado_conc_nomina (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            empleado_id UUID NOT NULL REFERENCES empleado(id),
            concepto_id UUID NOT NULL REFERENCES nomina_concepto(id),
            monto NUMERIC(18,2) DEFAULT 0 NOT NULL,
            activo BOOLEAN DEFAULT TRUE NOT NULL,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_empl_conc_nomina_empleado ON empleado_conc_nomina(empleado_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_empl_conc_nomina_empresa ON empleado_conc_nomina(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS empleado_contrato (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            empleado_id UUID NOT NULL REFERENCES empleado(id),
            tipo_contrato VARCHAR(30) NOT NULL,
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE,
            salario NUMERIC(18,2) DEFAULT 0 NOT NULL,
            activo BOOLEAN DEFAULT TRUE NOT NULL,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_empleado_contrato_empleado ON empleado_contrato(empleado_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_empleado_contrato_empresa ON empleado_contrato(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS empleado_vacacion (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            empleado_id UUID NOT NULL REFERENCES empleado(id),
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE NOT NULL,
            dias INTEGER DEFAULT 0 NOT NULL,
            estado VARCHAR(20) DEFAULT 'APROBADA' NOT NULL,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_empleado_vacacion_empleado ON empleado_vacacion(empleado_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_empleado_vacacion_empresa ON empleado_vacacion(empresa_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS periodo_nomina (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            empresa_id UUID NOT NULL REFERENCES empresa(id),
            codigo VARCHAR(20) NOT NULL,
            nomina_id UUID NOT NULL REFERENCES nomina(id),
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE NOT NULL,
            fecha_pago DATE,
            estado VARCHAR(20) DEFAULT 'ABIERTO' NOT NULL,
            asiento_id UUID,
            note_exists_flag BOOLEAN DEFAULT TRUE NOT NULL,
            record_date TIMESTAMP DEFAULT NOW() NOT NULL,
            row_pointer UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            create_date TIMESTAMP DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_periodo_nomina_empresa ON periodo_nomina(empresa_id)")


def downgrade() -> None:
    tables = [
        "periodo_nomina",
        "empleado_vacacion",
        "empleado_contrato",
        "empleado_conc_nomina",
        "hist_depreciacion",
        "activo_accion",
        "asiento_dist_linea",
        "asiento_distribuido",
        "mayor",
        "diario",
        "mov_banco",
        "asiento_de_diario",
        "auxiliar_cp",
        "auxiliar_cc",
        "documento_cp",
        "documento_cc",
        "pedido_linea",
        "factura_linea",
        "factura",
        "transaccion_inv",
        "existencia_bodega",
        "presupuesto_venta",
        "pedido",
        "cheque",
        "articulo",
        "puesto",
        "nomina_concepto",
        "nomina",
        "global_config",
        "cuenta_bancaria",
        "tipo_activo",
        "paquete",
    ]
    for tbl in tables:
        op.execute(f"DROP TABLE IF EXISTS {tbl} CASCADE")
