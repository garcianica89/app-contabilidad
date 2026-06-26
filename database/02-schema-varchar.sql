-- ============================================================
-- App Contabilidad - Esquema de Base de Datos
-- Version: 1.0
-- Motor: PostgreSQL 16+
-- ============================================================

-- Extensiones
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- TABLAS: Configuracion
-- ============================================================

CREATE TABLE empresa (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(200) NOT NULL,
    nombre_legal VARCHAR(200),
    ruc VARCHAR(20) UNIQUE,
    direccion TEXT,
    telefono VARCHAR(20),
    email VARCHAR(100),
    moneda_local_id UUID,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE TABLE moneda (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo VARCHAR(3) NOT NULL UNIQUE,
    nombre VARCHAR(50) NOT NULL,
    simbolo VARCHAR(5) NOT NULL,
    tasa_cambio DECIMAL(14,6) NOT NULL DEFAULT 1.0,
    es_base BOOLEAN NOT NULL DEFAULT FALSE,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

ALTER TABLE empresa ADD CONSTRAINT fk_empresa_moneda
    FOREIGN KEY (moneda_local_id) REFERENCES moneda(id);

CREATE TABLE usuario (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(200) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    ultimo_acceso TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE TABLE rol (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    nombre VARCHAR(50) NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(empresa_id, nombre)
);

CREATE TABLE usuario_rol (
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    rol_id UUID NOT NULL REFERENCES rol(id) ON DELETE CASCADE,
    PRIMARY KEY (usuario_id, rol_id)
);

CREATE TABLE permiso (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo VARCHAR(100) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    modulo VARCHAR(50) NOT NULL
);

CREATE TABLE rol_permiso (
    rol_id UUID NOT NULL REFERENCES rol(id) ON DELETE CASCADE,
    permiso_id UUID NOT NULL REFERENCES permiso(id) ON DELETE CASCADE,
    PRIMARY KEY (rol_id, permiso_id)
);

CREATE TABLE periodo_contable (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    codigo VARCHAR(10) NOT NULL,
    nombre VARCHAR(100),
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    cerrado BOOLEAN NOT NULL DEFAULT FALSE,
    cerrado_por UUID REFERENCES usuario(id),
    cerrado_en TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(empresa_id, codigo)
);

CREATE TABLE parametro (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    grupo VARCHAR(50) NOT NULL,
    clave VARCHAR(100) NOT NULL,
    valor TEXT,
    tipo_dato VARCHAR(20) DEFAULT 'TEXTO',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(empresa_id, grupo, clave)
);

-- ============================================================
-- TABLAS: Contabilidad
-- ============================================================

CREATE TABLE cuenta_contable (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    codigo VARCHAR(20) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    nivel INTEGER NOT NULL CHECK (nivel BETWEEN 1 AND 8),
    padre_id UUID REFERENCES cuenta_contable(id),
    acepta_datos BOOLEAN NOT NULL DEFAULT FALSE,
    moneda_id UUID REFERENCES moneda(id),
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    indice VARCHAR(10),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(empresa_id, codigo)
);

CREATE INDEX idx_cuenta_padre ON cuenta_contable(padre_id);
CREATE INDEX idx_cuenta_tipo ON cuenta_contable(empresa_id, tipo);

CREATE TABLE centro_costo (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    codigo VARCHAR(20) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    padre_id UUID REFERENCES centro_costo(id),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(empresa_id, codigo)
);

CREATE TABLE asiento (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    numero INTEGER NOT NULL,
    fecha DATE NOT NULL,
    periodo_id UUID NOT NULL REFERENCES periodo_contable(id),
    tipo VARCHAR(20) NOT NULL DEFAULT 'DIARIO',
    concepto TEXT NOT NULL,
    origen_modulo VARCHAR(50),
    origen_documento_id UUID,
    creado_por UUID NOT NULL REFERENCES usuario(id),
    aprobado_por UUID REFERENCES usuario(id),
    reversado BOOLEAN NOT NULL DEFAULT FALSE,
    asiento_reversa_id UUID REFERENCES asiento(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(empresa_id, periodo_id, numero)
);

CREATE INDEX idx_asiento_fecha ON asiento(empresa_id, fecha);
CREATE INDEX idx_asiento_periodo ON asiento(periodo_id);

CREATE TABLE asiento_linea (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asiento_id UUID NOT NULL REFERENCES asiento(id) ON DELETE CASCADE,
    cuenta_id UUID NOT NULL REFERENCES cuenta_contable(id),
    centro_costo_id UUID REFERENCES centro_costo(id),
    descripcion TEXT,
    debe_local DECIMAL(14,2) NOT NULL DEFAULT 0,
    haber_local DECIMAL(14,2) NOT NULL DEFAULT 0,
    debe_dolar DECIMAL(14,2) NOT NULL DEFAULT 0,
    haber_dolar DECIMAL(14,2) NOT NULL DEFAULT 0,
    orden INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_asiento_linea_cuenta ON asiento_linea(cuenta_id);
CREATE INDEX idx_asiento_linea_asiento ON asiento_linea(asiento_id);

-- ============================================================
-- TABLAS: Inventario
-- ============================================================

CREATE TABLE categoria (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    nombre VARCHAR(100) NOT NULL,
    padre_id UUID REFERENCES categoria(id),
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(empresa_id, nombre)
);

CREATE TABLE producto (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    codigo VARCHAR(50),
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    categoria_id UUID REFERENCES categoria(id),
    unidad_medida VARCHAR(20) NOT NULL DEFAULT 'UNIDAD',
    costo_promedio DECIMAL(14,2) NOT NULL DEFAULT 0,
    precio_venta DECIMAL(14,2) NOT NULL DEFAULT 0,
    moneda_id UUID REFERENCES moneda(id),
    stock_actual DECIMAL(14,2) NOT NULL DEFAULT 0,
    stock_minimo DECIMAL(14,2) NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(empresa_id, codigo)
);

CREATE INDEX idx_producto_categoria ON producto(categoria_id);
CREATE INDEX idx_producto_empresa ON producto(empresa_id);

CREATE TABLE kardex_movimiento (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    producto_id UUID NOT NULL REFERENCES producto(id),
    fecha DATE NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    tipo_documento VARCHAR(20),
    documento_id UUID,
    cantidad DECIMAL(14,2) NOT NULL,
    costo_unitario DECIMAL(14,2) NOT NULL DEFAULT 0,
    costo_total DECIMAL(14,2) NOT NULL DEFAULT 0,
    saldo_cantidad DECIMAL(14,2) NOT NULL,
    saldo_costo_promedio DECIMAL(14,2) NOT NULL,
    saldo_total DECIMAL(14,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT kardex_saldo_positivo CHECK (saldo_cantidad >= 0)
);

CREATE INDEX idx_kardex_producto ON kardex_movimiento(producto_id, fecha);
CREATE INDEX idx_kardex_fecha ON kardex_movimiento(empresa_id, fecha);

-- ============================================================
-- TABLAS: Ventas
-- ============================================================

CREATE TABLE cliente (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    codigo VARCHAR(20),
    nombre VARCHAR(200) NOT NULL,
    ruc VARCHAR(20),
    direccion TEXT,
    telefono VARCHAR(20),
    email VARCHAR(100),
    saldo DECIMAL(14,2) NOT NULL DEFAULT 0,
    limite_credito DECIMAL(14,2) NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(empresa_id, codigo)
);

CREATE INDEX idx_cliente_empresa ON cliente(empresa_id);

CREATE TABLE factura_venta (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    numero VARCHAR(20) NOT NULL,
    cliente_id UUID NOT NULL REFERENCES cliente(id),
    fecha DATE NOT NULL,
    fecha_vencimiento DATE,
    tipo VARCHAR(20) NOT NULL DEFAULT 'CONTADO',
    subtotal DECIMAL(14,2) NOT NULL DEFAULT 0,
    descuento DECIMAL(14,2) NOT NULL DEFAULT 0,
    iva DECIMAL(14,2) NOT NULL DEFAULT 0,
    total DECIMAL(14,2) NOT NULL DEFAULT 0,
    moneda_id UUID NOT NULL REFERENCES moneda(id),
    asiento_id UUID REFERENCES asiento(id),
    estado VARCHAR(20) NOT NULL DEFAULT 'EMITIDA',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(empresa_id, numero)
);

CREATE INDEX idx_factura_venta_cliente ON factura_venta(cliente_id);
CREATE INDEX idx_factura_venta_fecha ON factura_venta(empresa_id, fecha);

CREATE TABLE factura_venta_linea (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    factura_id UUID NOT NULL REFERENCES factura_venta(id) ON DELETE CASCADE,
    producto_id UUID NOT NULL REFERENCES producto(id),
    cantidad DECIMAL(14,2) NOT NULL,
    precio_unitario DECIMAL(14,2) NOT NULL,
    descuento DECIMAL(14,2) NOT NULL DEFAULT 0,
    subtotal DECIMAL(14,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE nota_credito_venta (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    numero VARCHAR(20) NOT NULL,
    factura_id UUID NOT NULL REFERENCES factura_venta(id),
    fecha DATE NOT NULL,
    motivo TEXT NOT NULL,
    subtotal DECIMAL(14,2) NOT NULL DEFAULT 0,
    iva DECIMAL(14,2) NOT NULL DEFAULT 0,
    total DECIMAL(14,2) NOT NULL DEFAULT 0,
    asiento_id UUID REFERENCES asiento(id),
    estado VARCHAR(20) NOT NULL DEFAULT 'EMITIDA',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(empresa_id, numero)
);

CREATE TABLE recibo (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    numero VARCHAR(20) NOT NULL,
    cliente_id UUID NOT NULL REFERENCES cliente(id),
    factura_id UUID REFERENCES factura_venta(id),
    fecha DATE NOT NULL,
    monto DECIMAL(14,2) NOT NULL,
    moneda_id UUID NOT NULL REFERENCES moneda(id),
    tipo_pago VARCHAR(50) NOT NULL DEFAULT 'EFECTIVO',
    asiento_id UUID REFERENCES asiento(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(empresa_id, numero)
);

-- ============================================================
-- TABLAS: Compras
-- ============================================================

CREATE TABLE proveedor (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    codigo VARCHAR(20),
    nombre VARCHAR(200) NOT NULL,
    ruc VARCHAR(20),
    direccion TEXT,
    telefono VARCHAR(20),
    email VARCHAR(100),
    saldo DECIMAL(14,2) NOT NULL DEFAULT 0,
    plazo_credito INT NOT NULL DEFAULT 30,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(empresa_id, codigo)
);

CREATE TABLE orden_compra (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    numero VARCHAR(20) NOT NULL,
    proveedor_id UUID NOT NULL REFERENCES proveedor(id),
    fecha DATE NOT NULL,
    fecha_entrega DATE,
    subtotal DECIMAL(14,2) NOT NULL DEFAULT 0,
    iva DECIMAL(14,2) NOT NULL DEFAULT 0,
    total DECIMAL(14,2) NOT NULL DEFAULT 0,
    moneda_id UUID NOT NULL REFERENCES moneda(id),
    estado VARCHAR(20) NOT NULL DEFAULT 'EMITIDA',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(empresa_id, numero)
);

CREATE TABLE orden_compra_linea (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    orden_id UUID NOT NULL REFERENCES orden_compra(id) ON DELETE CASCADE,
    producto_id UUID NOT NULL REFERENCES producto(id),
    cantidad DECIMAL(14,2) NOT NULL,
    precio_unitario DECIMAL(14,2) NOT NULL,
    subtotal DECIMAL(14,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE factura_compra (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    numero VARCHAR(20) NOT NULL,
    proveedor_id UUID NOT NULL REFERENCES proveedor(id),
    orden_id UUID REFERENCES orden_compra(id),
    fecha DATE NOT NULL,
    fecha_vencimiento DATE,
    subtotal DECIMAL(14,2) NOT NULL DEFAULT 0,
    descuento DECIMAL(14,2) NOT NULL DEFAULT 0,
    iva DECIMAL(14,2) NOT NULL DEFAULT 0,
    retencion_ir DECIMAL(14,2) NOT NULL DEFAULT 0,
    total DECIMAL(14,2) NOT NULL DEFAULT 0,
    moneda_id UUID NOT NULL REFERENCES moneda(id),
    asiento_id UUID REFERENCES asiento(id),
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(empresa_id, numero)
);

CREATE INDEX idx_factura_compra_proveedor ON factura_compra(proveedor_id);

CREATE TABLE factura_compra_linea (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    factura_id UUID NOT NULL REFERENCES factura_compra(id) ON DELETE CASCADE,
    producto_id UUID NOT NULL REFERENCES producto(id),
    cantidad DECIMAL(14,2) NOT NULL,
    precio_unitario DECIMAL(14,2) NOT NULL,
    descuento DECIMAL(14,2) NOT NULL DEFAULT 0,
    subtotal DECIMAL(14,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE nota_credito_compra (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    numero VARCHAR(20) NOT NULL,
    factura_id UUID NOT NULL REFERENCES factura_compra(id),
    fecha DATE NOT NULL,
    motivo TEXT NOT NULL,
    subtotal DECIMAL(14,2) NOT NULL DEFAULT 0,
    iva DECIMAL(14,2) NOT NULL DEFAULT 0,
    total DECIMAL(14,2) NOT NULL DEFAULT 0,
    asiento_id UUID REFERENCES asiento(id),
    estado VARCHAR(20) NOT NULL DEFAULT 'EMITIDA',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(empresa_id, numero)
);

-- ============================================================
-- TABLAS: Caja y Bancos
-- ============================================================

CREATE TABLE cuenta_banco (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    banco VARCHAR(100) NOT NULL,
    numero_cuenta VARCHAR(50) NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'CORRIENTE',
    moneda_id UUID NOT NULL REFERENCES moneda(id),
    saldo DECIMAL(14,2) NOT NULL DEFAULT 0,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(empresa_id, numero_cuenta)
);

CREATE TABLE movimiento_banco (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    cuenta_id UUID NOT NULL REFERENCES cuenta_banco(id),
    fecha DATE NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    numero_documento VARCHAR(50),
    concepto TEXT NOT NULL,
    entrada DECIMAL(14,2) NOT NULL DEFAULT 0,
    salida DECIMAL(14,2) NOT NULL DEFAULT 0,
    saldo DECIMAL(14,2) NOT NULL,
    conciliado BOOLEAN NOT NULL DEFAULT FALSE,
    asiento_id UUID REFERENCES asiento(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mov_banco_cuenta ON movimiento_banco(cuenta_id, fecha);

CREATE TABLE caja (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    nombre VARCHAR(100) NOT NULL DEFAULT 'Caja General',
    moneda_id UUID NOT NULL REFERENCES moneda(id),
    saldo_actual DECIMAL(14,2) NOT NULL DEFAULT 0,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE movimiento_caja (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    caja_id UUID NOT NULL REFERENCES caja(id),
    fecha DATE NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    concepto TEXT NOT NULL,
    entrada DECIMAL(14,2) NOT NULL DEFAULT 0,
    salida DECIMAL(14,2) NOT NULL DEFAULT 0,
    saldo DECIMAL(14,2) NOT NULL,
    referencia_id UUID,
    asiento_id UUID REFERENCES asiento(id),
    usuario_id UUID REFERENCES usuario(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mov_caja ON movimiento_caja(caja_id, fecha);

CREATE TABLE arqueo_caja (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    caja_id UUID NOT NULL REFERENCES caja(id),
    fecha DATE NOT NULL,
    saldo_esperado DECIMAL(14,2) NOT NULL,
    saldo_real DECIMAL(14,2) NOT NULL,
    diferencia DECIMAL(14,2) NOT NULL,
    observaciones TEXT,
    realizado_por UUID NOT NULL REFERENCES usuario(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLAS: Auditoria
-- ============================================================

CREATE TABLE auditoria (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuario(id),
    empresa_id UUID REFERENCES empresa(id),
    tabla VARCHAR(50) NOT NULL,
    registro_id UUID NOT NULL,
    accion VARCHAR(10) NOT NULL,
    valor_anterior JSONB,
    valor_nuevo JSONB,
    direccion_ip VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_auditoria_tabla ON auditoria(tabla, registro_id);
CREATE INDEX idx_auditoria_usuario ON auditoria(usuario_id);
CREATE INDEX idx_auditoria_fecha ON auditoria(created_at);

-- ============================================================
-- VISTAS
-- ============================================================

-- Balance de Comprobacion
CREATE VIEW vista_balance_comprobacion AS
SELECT
    c.id AS cuenta_id,
    c.codigo,
    c.nombre,
    c.tipo,
    COALESCE(SUM(al.debe_local), 0) AS total_debe_local,
    COALESCE(SUM(al.haber_local), 0) AS total_haber_local,
    COALESCE(SUM(al.debe_dolar), 0) AS total_debe_dolar,
    COALESCE(SUM(al.haber_dolar), 0) AS total_haber_dolar
FROM cuenta_contable c
LEFT JOIN asiento_linea al ON al.cuenta_id = c.id
LEFT JOIN asiento a ON a.id = al.asiento_id AND a.reversado = FALSE
WHERE c.acepta_datos = TRUE
GROUP BY c.id, c.codigo, c.nombre, c.tipo
ORDER BY c.codigo;

-- Mayor General
CREATE VIEW vista_mayor_general AS
SELECT
    c.id AS cuenta_id,
    c.codigo,
    c.nombre,
    a.fecha,
    a.numero AS asiento_numero,
    a.concepto,
    al.descripcion,
    al.debe_local,
    al.haber_local,
    al.debe_dolar,
    al.haber_dolar,
    SUM(al.debe_local - al.haber_local) OVER (
        PARTITION BY al.cuenta_id ORDER BY a.fecha, a.numero, al.orden
    ) AS saldo_local,
    SUM(al.debe_dolar - al.haber_dolar) OVER (
        PARTITION BY al.cuenta_id ORDER BY a.fecha, a.numero, al.orden
    ) AS saldo_dolar
FROM asiento_linea al
JOIN asiento a ON a.id = al.asiento_id AND a.reversado = FALSE
JOIN cuenta_contable c ON c.id = al.cuenta_id;

-- ============================================================
-- FUNCION: Obtener siguiente numero de asiento
-- ============================================================

CREATE OR REPLACE FUNCTION siguiente_numero_asiento(
    p_empresa_id UUID,
    p_periodo_id UUID
) RETURNS INTEGER AS $$
DECLARE
    v_numero INTEGER;
BEGIN
    SELECT COALESCE(MAX(numero), 0) + 1 INTO v_numero
    FROM asiento
    WHERE empresa_id = p_empresa_id AND periodo_id = p_periodo_id;
    RETURN v_numero;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- FUNCION: Validar partida doble
-- ============================================================

CREATE OR REPLACE FUNCTION validar_partida_doble()
RETURNS TRIGGER AS $$
DECLARE
    v_debe DECIMAL(14,2);
    v_haber DECIMAL(14,2);
BEGIN
    SELECT SUM(debe_local), SUM(haber_local)
    INTO v_debe, v_haber
    FROM asiento_linea
    WHERE asiento_id = NEW.asiento_id;

    IF v_debe IS DISTINCT FROM v_haber THEN
        RAISE EXCEPTION 'La partida doble no cuadra: Debe=% Haber=%', v_debe, v_haber;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- No aplicamos el trigger directamente, se valida en la capa de aplicacion
-- para permitir insercion parcial de lineas.

-- ============================================================
-- DATOS INICIALES
-- ============================================================

-- Monedas
INSERT INTO moneda (codigo, nombre, simbolo, tasa_cambio, es_base) VALUES
    ('NIO', 'Cordoba Nicaragüense', 'C$', 1.0, TRUE),
    ('USD', 'Dolar Estadounidense', 'U$', 36.6243, FALSE);

-- Permisos base
INSERT INTO permiso (codigo, nombre, modulo) VALUES
    ('empresa.listar', 'Listar empresas', 'CONFIG'),
    ('empresa.crear', 'Crear empresa', 'CONFIG'),
    ('empresa.editar', 'Editar empresa', 'CONFIG'),
    ('usuario.listar', 'Listar usuarios', 'CONFIG'),
    ('usuario.crear', 'Crear usuario', 'CONFIG'),
    ('usuario.editar', 'Editar usuario', 'CONFIG'),
    ('rol.listar', 'Listar roles', 'CONFIG'),
    ('rol.crear', 'Crear rol', 'CONFIG'),
    ('rol.editar', 'Editar rol', 'CONFIG'),
    ('cuenta.listar', 'Listar cuentas contables', 'CONTABILIDAD'),
    ('cuenta.crear', 'Crear cuenta contable', 'CONTABILIDAD'),
    ('cuenta.editar', 'Editar cuenta contable', 'CONTABILIDAD'),
    ('asiento.listar', 'Listar asientos', 'CONTABILIDAD'),
    ('asiento.crear', 'Crear asiento', 'CONTABILIDAD'),
    ('asiento.editar', 'Editar asiento', 'CONTABILIDAD'),
    ('asiento.reversar', 'Reversar asiento', 'CONTABILIDAD'),
    ('periodo.cerrar', 'Cerrar periodo', 'CONTABILIDAD'),
    ('producto.listar', 'Listar productos', 'INVENTARIO'),
    ('producto.crear', 'Crear producto', 'INVENTARIO'),
    ('producto.editar', 'Editar producto', 'INVENTARIO'),
    ('kardex.ver', 'Ver kardex', 'INVENTARIO'),
    ('cliente.listar', 'Listar clientes', 'VENTAS'),
    ('cliente.crear', 'Crear cliente', 'VENTAS'),
    ('factura.venta.crear', 'Crear factura de venta', 'VENTAS'),
    ('factura.venta.anular', 'Anular factura de venta', 'VENTAS'),
    ('proveedor.listar', 'Listar proveedores', 'COMPRAS'),
    ('proveedor.crear', 'Crear proveedor', 'COMPRAS'),
    ('factura.compra.crear', 'Crear factura de compra', 'COMPRAS'),
    ('caja.movimiento', 'Registrar movimiento de caja', 'TESORERIA'),
    ('banco.conciliar', 'Conciliar cuentas bancarias', 'TESORERIA'),
    ('reportes.ver', 'Ver reportes', 'REPORTES'),
    ('reportes.exportar', 'Exportar reportes', 'REPORTES');
