-- ============================================================
-- INFRAESTRUCTURA ADICIONAL (inspirado en Softland)
-- Tablas: tipo_cambio_hist, condicion_pago
-- ============================================================

-- TIPO_CAMBIO_HIST: historico de tipos de cambio por fecha
CREATE TABLE tipo_cambio_hist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    moneda_id UUID NOT NULL REFERENCES moneda(id),
    fecha DATE NOT NULL,
    tasa_compra DECIMAL(14,6) NOT NULL,
    tasa_venta DECIMAL(14,6) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(empresa_id, moneda_id, fecha)
);

CREATE INDEX idx_tipo_cambio_hist_fecha ON tipo_cambio_hist(empresa_id, fecha DESC);

COMMENT ON TABLE tipo_cambio_hist IS 'Historico de tipos de cambio por dia';
COMMENT ON COLUMN tipo_cambio_hist.tasa_compra IS 'Tasa de compra (menor)';
COMMENT ON COLUMN tipo_cambio_hist.tasa_venta IS 'Tasa de venta (mayor)';

-- CONDICION_PAGO: plazos de pago para clientes y proveedores
CREATE TABLE condicion_pago (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    codigo VARCHAR(10) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    dias_neto INT NOT NULL DEFAULT 0,
    descuento_contado DECIMAL(5,2) NOT NULL DEFAULT 0,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(empresa_id, codigo)
);

COMMENT ON TABLE condicion_pago IS 'Plazos de pago (CONTADO, 30 DIAS, etc.)';
COMMENT ON COLUMN condicion_pago.dias_neto IS 'Numero de dias para vencimiento';
COMMENT ON COLUMN condicion_pago.descuento_contado IS 'Porcentaje de descuento por pago contado';

-- Insertar condiciones de pago por defecto
INSERT INTO condicion_pago (empresa_id, codigo, nombre, dias_neto, descuento_contado, activa)
SELECT e.id, 'CONTADO', 'Contado', 0, 0, TRUE
FROM empresa e
WHERE NOT EXISTS (SELECT 1 FROM condicion_pago cp WHERE cp.empresa_id = e.id AND cp.codigo = 'CONTADO');

INSERT INTO condicion_pago (empresa_id, codigo, nombre, dias_neto, descuento_contado, activa)
SELECT e.id, '07DIAS', 'Credito a 7 Dias', 7, 0, TRUE
FROM empresa e
WHERE NOT EXISTS (SELECT 1 FROM condicion_pago cp WHERE cp.empresa_id = e.id AND cp.codigo = '07DIAS');

INSERT INTO condicion_pago (empresa_id, codigo, nombre, dias_neto, descuento_contado, activa)
SELECT e.id, '15DIAS', 'Credito a 15 Dias', 15, 0, TRUE
FROM empresa e
WHERE NOT EXISTS (SELECT 1 FROM condicion_pago cp WHERE cp.empresa_id = e.id AND cp.codigo = '15DIAS');

INSERT INTO condicion_pago (empresa_id, codigo, nombre, dias_neto, descuento_contado, activa)
SELECT e.id, '30DIAS', 'Credito a 30 Dias', 30, 0, TRUE
FROM empresa e
WHERE NOT EXISTS (SELECT 1 FROM condicion_pago cp WHERE cp.empresa_id = e.id AND cp.codigo = '30DIAS');
