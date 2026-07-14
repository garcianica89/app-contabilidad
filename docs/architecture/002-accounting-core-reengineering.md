# Reingeniería del Núcleo Contable

> ADR-002: Diseño del Catálogo, Parametrización, Subtipos CxC/CxP y Motor de Plantillas
> Fecha: 2026-06-29
> Estado: Aprobación pendiente
> Rol: Chief ERP Architect

---

## 0. Principios de Diseño

1. **Catálogo vacío al inicio**: El sistema se instala sin cuentas. Solo clasificaciones.
2. **Cero cuentas hardcodeadas**: Ninguna cuenta vive en el código fuente.
3. **Máxima flexibilidad**: Niveles, código, longitud — todo configurable por empresa.
4. **Cada módulo parametriza sus cuentas**: Tablas de configuración, no constantes.
5. **Subtipo de documento = comportamiento completo**: Cuentas, series, plantillas, todo en datos.
6. **Motor de plantillas universal**: Toda generación de asientos pasa por el mismo motor.

---

## 1. Catálogo de Cuentas

### 1.1 Estructura del Catálogo

El catálogo se compone de dos partes:

1. **Definición de estructura**: Cómo se construyen los códigos (niveles, longitud, separador)
2. **Las cuentas**: Cada cuenta con su código, nombre, clasificaciones

### 1.2 Tabla: `company_account_structure`

Define la estructura del código contable para cada empresa.

```sql
CREATE TABLE company_account_structure (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES company(id),
    level INT NOT NULL CHECK (level >= 1 AND level <= 10),
    name VARCHAR(100) NOT NULL,
    -- Ejemplos: "Grupo", "Rubro", "Cuenta", "Subcuenta", "Auxiliar"
    digit_length INT NOT NULL CHECK (digit_length >= 1 AND digit_length <= 10),
    -- Cuántos dígitos tiene este nivel
    separator VARCHAR(5) DEFAULT '-',
    -- Separador entre este nivel y el siguiente (ej: "-", "", "/")
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(company_id, level)
);

-- Ejemplo de configuración para estructura 8 niveles:
-------------------------------------------------------------------------------------
-- level | name          | digit_length | separator
-- 1     | Grupo         | 1            | '-'
-- 2     | Rubro         | 2            | '-'
-- 3     | Cuenta        | 2            | '-'
-- 4     | Subcuenta     | 2            | '-'
-- 5     | Auxiliar      | 2            | '-'
-- 6     | Subauxiliar   | 2            | '-'
-- 7     | Item          | 2            | '-'
-- 8     | Subitem       | 4            | ''
-- Resultado: 1-01-01-01-01-01-01-0001
--
-- Para estructura simple 3 niveles:
-- level | name          | digit_length | separator
-- 1     | Genero        | 1            | '-'
-- 2     | Especie       | 2            | '-'
-- 3     | Individual    | 4            | ''
-- Resultado: 1-01-0001
```

### 1.3 Tabla: `account_type` (Lookup — Clasificación base)

Define la naturaleza contable fundamental. **Esta tabla sí se seedea al instalar** porque
el sistema necesita estas clasificaciones para validar saldos y generar reportes.

```sql
CREATE TABLE account_type (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    nature VARCHAR(10) NOT NULL CHECK (nature IN ('DEUDORA', 'ACREEDORA')),
    -- Naturaleza: DEUDORA (Activo, Costo, Gasto) o ACREEDORA (Pasivo, Patrimonio, Ingreso)
    financial_statement VARCHAR(30),
    -- 'BALANCE' o 'INCOME' o 'ORDER'
    display_order INT DEFAULT 0,
    is_system BOOLEAN DEFAULT FALSE
    -- TRUE = no se puede eliminar
);

-- Seed data (clasificaciones base, NO cuentas):
-- code       | name            | nature    | financial_statement
-- ACTIVO     | Activo          | DEUDORA   | BALANCE
-- PASIVO     | Pasivo          | ACREEDORA | BALANCE
-- PATRIMONIO | Patrimonio      | ACREEDORA | BALANCE
-- INGRESO    | Ingresos        | ACREEDORA | INCOME
-- COSTO      | Costos          | DEUDORA   | INCOME
-- GASTO      | Gastos          | DEUDORA   | INCOME
-- ORDEN_DEUD | Cuentas Orden D | DEUDORA   | ORDER
-- ORDEN_ACRE | Cuentas Orden A | ACREEDORA | ORDER
```

### 1.4 Tabla: `financial_classification` (Lookup — Clasificación financiera)

```sql
CREATE TABLE financial_classification (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('BALANCE', 'INCOME')),
    display_order INT DEFAULT 0
);

-- Seed data:
-- code              | name                    | type
-- CORRIENTE         | Corriente               | BALANCE
-- NO_CORRIENTE      | No Corriente            | BALANCE
-- OTRO_ACTIVO       | Otros Activos           | BALANCE
-- PASIVO_CORRIENTE  | Pasivo Corriente        | BALANCE
-- PASIVO_NO_CORRIENTE | Pasivo No Corriente  | BALANCE
-- CAPITAL           | Capital                 | BALANCE
-- RESERVAS          | Reservas                | BALANCE
-- RESULTADOS        | Resultados              | BALANCE
-- OPERACIONALES     | Operacionales           | INCOME
-- NO_OPERACIONALES  | No Operacionales        | INCOME
-- EXTRAORDINARIOS   | Extraordinarios         | INCOME
```

### 1.5 Tabla: `tax_classification` (Lookup — Clasificación fiscal)

```sql
CREATE TABLE tax_classification (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL
);

-- Seed data:
-- code       | name
-- GRAVADO    | Gravado
-- EXENTO     | Exento
-- EXCLUIDO   | Excluido
-- NO_APLICA  | No Aplica
```

### 1.6 Tabla: `ifrs_classification` (Lookup — Clasificación NIIF)

```sql
CREATE TABLE ifrs_classification (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    ifrs_standard VARCHAR(20)  -- 'NIIF_COMPLETO', 'NIIF_PYME'
);

-- Seed data (NIIF para PYME):
-- code            | name
-- EFECTIVO        | Efectivo y Equivalentes
-- CLIENTES        | Cuentas por Cobrar
-- INVENTARIOS     | Inventarios
-- PROPIEDADES     | Propiedades, Planta y Equipo
-- INTANGIBLES     | Activos Intangibles
-- PROVEEDORES     | Cuentas por Pagar
-- PASIVOS_FIN     | Pasivos Financieros
-- PATRIMONIO      | Patrimonio
-- INGRESOS_ORD    | Ingresos de Actividades Ordinarias
-- COSTOS_VENTA    | Costo de Ventas
-- GASTOS_ADMIN    | Gastos de Administración
-- GASTOS_VENTA    | Gastos de Venta
-- GASTOS_FIN      | Gastos Financieros
-- IMPUESTO        | Impuesto a la Renta
```

### 1.7 Tabla: `account` (El Catálogo)

```sql
CREATE TABLE account (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES company(id),
    parent_id UUID REFERENCES account(id),
    code VARCHAR(50) NOT NULL,
    -- Código completo: "1-01-001-0001"
    name VARCHAR(200) NOT NULL,
    -- Nombre de la cuenta: "Caja General"
    level INT NOT NULL CHECK (level >= 1),
    -- Nivel en el árbol (1 = raíz)
    account_type_id UUID NOT NULL REFERENCES account_type(id),
    -- ACTIVO, PASIVO, INGRESO, etc.
    accepts_entries BOOLEAN NOT NULL DEFAULT FALSE,
    -- TRUE = cuenta de movimiento (permite asientos)
    -- FALSE = cuenta de agrupación
    is_control_account BOOLEAN DEFAULT FALSE,
    -- TRUE = cuenta de control (agrupa auxiliares)
    is_auxiliary BOOLEAN DEFAULT FALSE,
    -- TRUE = cuenta auxiliar (nivel más detallado)
    currency_id UUID REFERENCES currency(id),
    -- NULL = todas las monedas
    requires_cost_center BOOLEAN DEFAULT FALSE,
    requires_dimension_2 BOOLEAN DEFAULT FALSE,
    requires_dimension_3 BOOLEAN DEFAULT FALSE,
    -- Dimensiones analíticas obligatorias
    financial_classification_id UUID REFERENCES financial_classification(id),
    -- CORRIENTE, NO_CORRIENTE, etc.
    tax_classification_id UUID REFERENCES tax_classification(id),
    -- GRAVADO, EXENTO, etc.
    ifrs_classification_id UUID REFERENCES ifrs_classification(id),
    -- Categoría NIIF
    is_active BOOLEAN DEFAULT TRUE,
    valid_from DATE,
    valid_to DATE,
    observations TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    updated_by UUID REFERENCES usuario(id),

    UNIQUE(company_id, code),
    UNIQUE(company_id, parent_id, name)
);

CREATE INDEX idx_account_company_id ON account(company_id);
CREATE INDEX idx_account_parent_id ON account(parent_id);
CREATE INDEX idx_account_type_id ON account(account_type_id);
CREATE INDEX idx_account_active ON account(company_id, is_active);
```

### 1.8 Reglas de Negocio del Catálogo

```
1. El código completo se genera concatenando códigos de nivel según
   la estructura definida en company_account_structure

2. Si una cuenta tiene accepts_entries = FALSE, no puede aparecer en
   líneas de asientos (validación en el motor contable)

3. Si una cuenta tiene accepts_entries = TRUE pero tiene hijos,
   se genera advertencia (no error - algunas empresas usan cuentas
   de control que también reciben asientos)

4. El árbol se gestiona con parent_id (no con el código)

5. Al desactivar una cuenta (is_active = FALSE), el sistema debe
   verificar que no tenga movimientos en períodos abiertos

6. La moneda de la cuenta es restrictiva: si la cuenta tiene
   currency_id definido, solo acepta transacciones en esa moneda

7. Las clasificaciones (financial, tax, ifrs) son hereditarias:
   si una cuenta no tiene asignada una clasificación, hereda
   de su cuenta padre
```

---

## 2. Parametrización Contable por Módulo

### 2.1 Tabla Única: `module_accounting_config`

En lugar de una tabla por módulo, una sola tabla genérica que
almacena la relación entre conceptos de negocio y cuentas contables.
Cada módulo tiene su propia pantalla de configuración, pero todas
leen de la misma fuente.

```sql
CREATE TABLE module_accounting_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES company(id),
    module VARCHAR(50) NOT NULL,
    -- 'sales', 'purchasing', 'inventory', 'cash', 'bank',
    -- 'fixed_assets', 'payroll', 'budget', 'reconciliation'
    concept_code VARCHAR(100) NOT NULL,
    -- Ej: 'VENTAS_CONTADO', 'IVA_DEBITO', 'COSTO_VENTAS'
    concept_name VARCHAR(200) NOT NULL,
    -- Nombre legible: "Ventas al Contado", "IVA Débito Fiscal"
    account_id UUID NOT NULL REFERENCES account(id),
    -- Cuenta contable asociada
    auxiliary_account_id UUID REFERENCES account(id),
    -- Cuenta auxiliar (opcional, para subdiarios)
    cost_center_id UUID REFERENCES cost_center(id),
    -- Centro de costo por defecto (opcional)
    is_active BOOLEAN DEFAULT TRUE,
    description VARCHAR(500),
    -- Nota o instrucción sobre el uso de este parámetro
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    updated_by UUID REFERENCES usuario(id),

    UNIQUE(company_id, module, concept_code)
);

CREATE INDEX idx_mac_module ON module_accounting_config(company_id, module);
```

### 2.2 Conceptos por Módulo

Cada módulo registra sus conceptos en esta tabla. A continuación,
la lista completa de conceptos que cada módulo debe configurar:

#### Ventas (`module = 'sales'`)

| concept_code | concept_name | Descripción |
|---|---|---|
| `VENTAS_CONTADO` | Ventas al Contado | Ingreso por ventas de contado |
| `VENTAS_CREDITO` | Ventas al Crédito | Ingreso por ventas al crédito |
| `VENTAS_EXPORTACION` | Ventas a Exportación | Ingreso por ventas al exterior |
| `IVA_DEBITO_FISCAL` | IVA Débito Fiscal | IVA generado en ventas |
| `DESCUENTOS_VENTA` | Descuentos en Ventas | Descuentos otorgados |
| `DEVOLUCIONES_VENTA` | Devoluciones en Ventas | Devoluciones de clientes |
| `ANTICIPO_CLIENTES` | Anticipos de Clientes | Anticipos recibidos |
| `CXC_CLIENTES_NAC` | Cuentas por Cobrar Clientes Nacionales | CxC clientes nacionales |
| `CXC_CLIENTES_EXT` | Cuentas por Cobrar Clientes Extranjeros | CxC clientes del exterior |
| `CXC_DUDOSO_COBRO` | Estimación Cuentas Incobrables | Provisión de incobrables |

#### Compras (`module = 'purchasing'`)

| concept_code | concept_name | Descripción |
|---|---|---|
| `COMPRAS_NACIONALES` | Compras Nacionales | Costo de compras locales |
| `COMPRAS_IMPORTACION` | Compras de Importación | Costo de compras importadas |
| `IVA_CREDITO_FISCAL` | IVA Crédito Fiscal | IVA pagado en compras |
| `GASTOS_COMPRA` | Gastos de Compra | Fletes, seguros, etc. |
| `RETENCION_IVA` | Retención IVA | IVA retenido al proveedor |
| `RETENCION_IR` | Retención IR | IR retenido al proveedor |
| `ANTICIPO_PROVEEDORES` | Anticipos a Proveedores | Anticipos entregados |
| `CXP_PROVEEDORES_NAC` | Cuentas por Pagar Proveedores Nacionales | CxP proveedores locales |
| `CXP_PROVEEDORES_EXT` | Cuentas por Pagar Proveedores Extranjeros | CxP proveedores del exterior |

#### Inventario (`module = 'inventory'`)

| concept_code | concept_name | Descripción |
|---|---|---|
| `INVENTARIO_MERCANCIAS` | Inventario de Mercancías | Almacén de productos |
| `INVENTARIO_MATERIAS` | Inventario de Materias Primas | Materias primas |
| `INVENTARIO_SUMINISTROS` | Inventario de Suministros | Suministros y empaques |
| `INVENTARIO_PRODUCTOS_PROCESO` | Inventario Productos en Proceso | Producción en curso |
| `INVENTARIO_PT` | Inventario Productos Terminados | Productos terminados |
| `COSTO_VENTAS` | Costo de Ventas | Costo de mercancía vendida |
| `AJUSTE_POSITIVO` | Ajustes Positivos de Inventario | Sobrantes |
| `AJUSTE_NEGATIVO` | Ajustes Negativos de Inventario | Faltantes |
| `DIFERENCIA_INVENTARIO` | Diferencias de Inventario | Ajustes por diferencia |
| `PRODUCCION` | Producción | Costo de producción |
| `CONSUMO_INTERNO` | Consumo Interno | Consumo interno de productos |

#### Caja (`module = 'cash'`)

| concept_code | concept_name | Descripción |
|---|---|---|
| `CAJA_GENERAL` | Caja General | Caja principal |
| `CAJA_CHICA` | Caja Chica | Fondo fijo de caja chica |
| `INGRESOS_VARIOS` | Ingresos Varios de Caja | Ingresos no operativos |
| `EGRESOS_VARIOS` | Egresos Varios de Caja | Egresos no operativos |
| `TRANSFERENCIA_CAJA` | Transferencias entre Cajas | Traslados de efectivo |

#### Bancos (`module = 'bank'`)

| concept_code | concept_name | Descripción |
|---|---|---|
| `BANCO_CUENTA` | Cuenta Bancaria | Banco (se parametriza por cada cuenta bancaria) |
| `COMISIONES_BANCARIAS` | Comisiones Bancarias | Cargos por servicios bancarios |
| `INTERESES_BANCARIOS` | Intereses Bancarios | Intereses ganados o pagados |
| `DIFERENCIA_BANCARIA` | Diferencias de Conciliación | Ajustes por diferencias bancarias |
| `CHEQUES_EMITIDOS` | Cheques Emitidos | Cheques pendientes de cobro |
| `CHEQUES_REVERSADOS` | Cheques Reversados | Cheques anulados |
| `NOTA_DEBITO_BANCARIA` | Notas de Débito Bancarias | Cargos bancarios no esperados |
| `NOTA_CREDITO_BANCARIA` | Notas de Crédito Bancarias | Abonos bancarios no esperados |

#### Activos Fijos (`module = 'fixed_assets'`)

| concept_code | concept_name | Descripción |
|---|---|---|
| `ACTIVO_FIJO` | Activo Fijo | Costo de adquisición |
| `DEPRECIACION_ACUMULADA` | Depreciación Acumulada | Depreciación acumulada del activo |
| `GASTO_DEPRECIACION` | Gasto por Depreciación | Depreciación del período |
| `REVALUACION_ACTIVO` | Revaluación de Activos | Ajuste por revaluación |
| `BAJA_ACTIVO` | Baja de Activos | Eliminación de activos |
| `MEJORA_ACTIVO` | Mejoras de Activos | Capitalización de mejoras |

#### Nómina (`module = 'payroll'`)

| concept_code | concept_name | Descripción |
|---|---|---|
| `SUELDOS` | Sueldos y Salarios | Salario base |
| `HORAS_EXTRAS` | Horas Extras | Tiempo extra |
| `AGUINALDO` | Aguinaldo | Decimotercer mes |
| `VACACIONES` | Vacaciones | Derecho de vacaciones |
| `INSS_PATRONAL` | INSS Patronal | Seguridad social empleador |
| `INSS_LABORAL` | INSS Laboral | Seguridad social empleado |
| `IR_EMPLEADOS` | IR Empleados | Impuesto sobre la renta |
| `PRESTACIONES_LABORALES` | Prestaciones Laborales | Indemnizaciones |
| `APORTES_VOLUNTARIOS` | Aportes Voluntarios | Deducciones voluntarias |
| `PRESTAMOS_EMPLEADOS` | Préstamos Empleados | Préstamos otorgados |
| `ANTICIPO_SUELDO` | Anticipo de Sueldo | Adelantos salariales |

#### Presupuestos (`module = 'budget'`)

| concept_code | concept_name | Descripción |
|---|---|---|
| `VARIACION_POSITIVA` | Variación Presupuestaria Positiva | Exceso de ingreso / menor gasto |
| `VARIACION_NEGATIVA` | Variación Presupuestaria Negativa | Menor ingreso / exceso de gasto |
| `AJUSTE_PRESUPUESTO` | Ajustes Presupuestarios | Modificaciones al presupuesto |

#### Conciliación Bancaria (`module = 'reconciliation'`)

| concept_code | concept_name | Descripción |
|---|---|---|
| `AJUSTE_CONCILIACION` | Ajustes de Conciliación | Partidas de ajuste |
| `DIFERENCIA_CONCILIACION` | Diferencias de Conciliación | Diferencias no identificadas |
| `MOVIMIENTO_NO_IDENTIFICADO` | Movimientos No Identificados | Partidas sin contrapartida |
| `PARTIDA_PENDIENTE` | Partidas Pendientes | Movimientos del banco no registrados |

### 2.3 Reglas de Parametrización

```
1. Todo concepto marcado como 'required' en la seed debe tener una cuenta
   asignada antes de que el módulo pueda operar

2. Si un concepto tiene auxiliary_account_id, el sistema genera
   automáticamente un subdiario (auxiliar por cliente/proveedor/etc.)

3. Los cambios en la parametrización afectan SOLO a nuevos documentos,
   no a los ya emitidos

4. Al cambiar una cuenta parametrizada, se registra en auditoría:
   valor anterior, valor nuevo, usuario, fecha, razón
```

---

## 3. Subtipos de Documento CxC

### 3.1 Tabla: `cxc_document_subtype`

```sql
CREATE TABLE cxc_document_subtype (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES company(id),
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(20),
    -- Abreviatura: "FAC", "NCR", "NDB", "REC"

    -- Serie y numeración
    serie VARCHAR(10),
    -- Serie del documento (ej: "A", "B", "F")
    uses_numeracion BOOLEAN DEFAULT TRUE,
    -- TRUE = usa el sistema de numeración configurable
    numeracion_id UUID REFERENCES numeracion(id),
    -- Serie/numeración específica (opcional)

    -- Comportamiento contable
    afecta_saldo BOOLEAN NOT NULL DEFAULT TRUE,
    -- TRUE = este documento modifica el saldo del cliente
    permite_saldo_negativo BOOLEAN DEFAULT FALSE,
    -- TRUE = permite que el saldo del cliente quede negativo
    genera_asiento BOOLEAN DEFAULT TRUE,
    -- TRUE = este documento genera un asiento contable
    journal_type_id UUID REFERENCES journal_type(id),
    -- Tipo de asiento a generar
    journal_template_id UUID REFERENCES journal_template(id),
    -- Plantilla específica (opcional, si se quiere saltar la
    -- resolución normal de plantillas)

    -- Cuentas contables por defecto (sobreescriben parámetros
    -- generales del módulo)
    cuenta_principal_id UUID REFERENCES account(id),
    cuenta_impuestos_id UUID REFERENCES account(id),
    cuenta_descuentos_id UUID REFERENCES account(id),
    cuenta_intereses_id UUID REFERENCES account(id),
    cuenta_mora_id UUID REFERENCES account(id),
    cuenta_puente_id UUID REFERENCES account(id),
    -- Cuenta puente para documentos en tránsito

    -- Centro de costo
    cost_center_default_id UUID REFERENCES cost_center(id),

    -- Control
    requiere_aprobacion BOOLEAN DEFAULT FALSE,
    permite_reversion BOOLEAN DEFAULT TRUE,
    -- TRUE = se puede reversar este documento
    max_dias_reversion INT,
    -- Máximo de días para reversión (NULL = sin límite)
    is_active BOOLEAN DEFAULT TRUE,

    -- Metadata
    observations TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    updated_by UUID REFERENCES usuario(id),

    UNIQUE(company_id, code)
);
```

### 3.2 Subtipos Predefinidos (Seed — NO hardcodeados en código)

La siguiente configuración inicial se inserta como seed,
pero puede modificarse desde la interfaz:

| code | name | Afecta Saldo | Genera Asiento | Permite Reversión |
|---|---|---|---|---|
| `FAC` | Factura | TRUE | TRUE | TRUE |
| `NCR` | Nota de Crédito | TRUE | TRUE | TRUE |
| `NDB` | Nota de Débito | TRUE | TRUE | TRUE |
| `REC` | Recibo de Cobro | TRUE | FALSE | FALSE |
| `ANT` | Anticipo | TRUE | TRUE | TRUE |
| `AJU` | Ajuste | TRUE | TRUE | TRUE |
| `INT` | Interés | TRUE | TRUE | FALSE |
| `CAS` | Castigo | TRUE | TRUE | FALSE |
| `REV` | Reversión | TRUE | TRUE | FALSE |

### 3.3 Reglas de CxC

```
1. Cada documento de CxC (factura, nota crédito, etc.) tiene un subtipo

2. El subtipo determina el comportamiento contable:
   - Si genera_asiento = TRUE → se ejecuta el motor de plantillas
   - El journal_type_id determina qué tipo de asiento se genera
   - Las cuentas del subtipo sobreescriben las del módulo

3. Si afecta_saldo = TRUE, el documento modifica el saldo del cliente

4. Si permite_saldo_negativo = FALSE y el documento dejaría
   el saldo negativo, el sistema bloquea la operación

5. Un documento solo puede reversarse si:
   - permite_reversion = TRUE
   - Está dentro del max_dias_reversion (si aplica)
   - El usuario tiene permiso 'cxc.document.reverse'
```

---

## 4. Subtipos de Documento CxP

### 4.1 Tabla: `cxp_document_subtype`

```sql
CREATE TABLE cxp_document_subtype (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES company(id),
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(20),

    -- Serie y numeración
    serie VARCHAR(10),
    uses_numeracion BOOLEAN DEFAULT TRUE,
    numeracion_id UUID REFERENCES numeracion(id),

    -- Comportamiento contable
    afecta_saldo BOOLEAN NOT NULL DEFAULT TRUE,
    permite_saldo_negativo BOOLEAN DEFAULT FALSE,
    genera_asiento BOOLEAN DEFAULT TRUE,
    journal_type_id UUID REFERENCES journal_type(id),
    journal_template_id UUID REFERENCES journal_template(id),

    -- Cuentas contables
    cuenta_principal_id UUID REFERENCES account(id),
    cuenta_impuestos_id UUID REFERENCES account(id),
    cuenta_descuentos_id UUID REFERENCES account(id),
    cuenta_retencion_iva_id UUID REFERENCES account(id),
    cuenta_retencion_ir_id UUID REFERENCES account(id),
    cuenta_puente_id UUID REFERENCES account(id),
    cost_center_default_id UUID REFERENCES cost_center(id),

    -- Control
    requiere_aprobacion BOOLEAN DEFAULT FALSE,
    permite_reversion BOOLEAN DEFAULT TRUE,
    max_dias_reversion INT,
    afecta_inventario BOOLEAN DEFAULT FALSE,
    -- TRUE = la compra ingresa a inventario
    afecta_costo_promedio BOOLEAN DEFAULT FALSE,
    -- TRUE = actualiza el costo promedio del producto
    is_active BOOLEAN DEFAULT TRUE,

    observations TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    updated_by UUID REFERENCES usuario(id),

    UNIQUE(company_id, code)
);
```

### 4.2 Subtipos Predefinidos (Seed)

| code | name | Afecta Saldo | Genera Asiento | Afecta Inventario |
|---|---|---|---|---|
| `FAC` | Factura Proveedor | TRUE | TRUE | TRUE |
| `NCR` | Nota Crédito | TRUE | TRUE | TRUE |
| `NDB` | Nota Débito | TRUE | TRUE | FALSE |
| `PAG` | Pago | TRUE | FALSE | FALSE |
| `ANT` | Anticipo | TRUE | TRUE | FALSE |
| `RET` | Retención | TRUE | TRUE | FALSE |
| `AJU` | Ajuste | TRUE | TRUE | FALSE |

---

## 5. Motor de Tipos de Asiento

### 5.1 Arquitectura del Flujo

```
Documento transaccional
    │
    ├──→ Obtiene subtipo (cxc_document_subtype / cxp_document_subtype)
    │       │
    │       ├──→ Si genera_asiento = FALSE → fin
    │       │
    │       └──→ Si genera_asiento = TRUE →
    │               │
    │               ├──→ journal_type_id (directo) O
    │               └──→ Resolución de journal_type por reglas
    │                       │
    │                       ▼
    │               ┌──────────────────┐
    │               │  Template Engine  │
    │               │                   │
    │               │  1. Buscar        │
    │               │     templates     │
    │               │     activos para  │
    │               │     este          │
    │               │     journal_type  │
    │               │                   │
    │               │  2. Evaluar       │
    │               │     condiciones   │
    │               │     de cada       │
    │               │     template      │
    │               │                   │
    │               │  3. Para el       │
    │               │     template      │
    │               │     ganador:      │
    │               │     evaluar cada  │
    │               │     línea         │
    │               │     (cuenta,      │
    │               │     monto, desc,  │
    │               │     condiciones)  │
    │               │                   │
    │               │  4. Validar       │
    │               │     partida doble │
    │               │                   │
    │               └──────────────────┘
    │                       │
    │                       ▼
    │               ┌──────────────────┐
    │               │  Journal Engine   │
    │               │                   │
    │               │  1. Validar       │
    │               │     periodo       │
    │               │  2. Numerar       │
    │               │  3. Crear asiento │
    │               │  4. Actualizar    │
    │               │     saldos        │
    │               │  5. Publicar      │
    │               │     evento        │
    │               │                   │
    │               └──────────────────┘
```

### 5.2 Tablas del Motor

#### `journal_type`

```sql
CREATE TABLE journal_type (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES company(id),
    code VARCHAR(20) NOT NULL,
    -- 'VENTA_CONT', 'VENTA_CRED', 'COMPRA_NAC', 'COMPRA_IMP'
    name VARCHAR(100) NOT NULL,
    module VARCHAR(50),
    -- 'sales', 'purchasing', 'cash', 'bank', 'payroll', 'fixed_assets'
    nature VARCHAR(20) NOT NULL CHECK (nature IN ('AUTOMATIC', 'MANUAL', 'RECURRING')),
    -- AUTOMATIC = generado por el sistema
    -- MANUAL = creado por el usuario
    -- RECURRING = asiento recurrente (ej: depreciación mensual)

    affects_inventory BOOLEAN DEFAULT FALSE,
    affects_receivable BOOLEAN DEFAULT FALSE,
    affects_payable BOOLEAN DEFAULT FALSE,
    affects_cash BOOLEAN DEFAULT FALSE,
    affects_bank BOOLEAN DEFAULT FALSE,

    requires_approval BOOLEAN DEFAULT FALSE,
    approval_max_amount DECIMAL(14,2),
    -- Si el monto excede, requiere aprobación

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,

    UNIQUE(company_id, code)
);
```

#### `journal_template`

```sql
CREATE TABLE journal_template (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_type_id UUID NOT NULL REFERENCES journal_type(id),
    company_id UUID NOT NULL REFERENCES company(id),
    name VARCHAR(100) NOT NULL,
    -- "Venta Contado Default"
    priority INT DEFAULT 0,
    -- Mayor prioridad = se evalúa primero
    condition_expr TEXT,
    -- Expresión condicional: "{{tipo_pago}} == 'CONTADO'"
    -- Si es NULL, siempre se aplica
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(journal_type_id, company_id, name)
);
```

#### `journal_template_line`

```sql
CREATE TABLE journal_template_line (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES journal_template(id),
    line_order INT NOT NULL,
    nature VARCHAR(10) NOT NULL CHECK (nature IN ('DEBIT', 'CREDIT')),
    -- DEBIT o CREDIT

    -- Resolución de cuenta:
    -- Puede ser un código fijo, una variable del contexto,
    -- o un lookup en la tabla de parametrización
    account_source VARCHAR(50) NOT NULL,
    -- 'FIXED' = código fijo en account_code
    -- 'PARAM' = lookup en module_accounting_config por concept_code
    -- 'CONTEXT' = variable del contexto ({{cuenta_ventas}})
    -- 'SUBTYPE' = lookup en cxc/cxp_document_subtype

    account_code VARCHAR(50),
    -- Código de cuenta cuando account_source = 'FIXED'
    account_param_concept VARCHAR(100),
 -- concept_code en module_accounting_config
    account_context_var VARCHAR(100),
    -- Variable del contexto ({{cuenta_ventas}})

    -- Fórmula del monto
    amount_expression TEXT NOT NULL,
    -- "{{total}}", "{{subtotal - descuento}}", "{{iva}}",
    -- "{{sum(costos, 'monto')}}"
    -- Soporta: +, -, *, /, paréntesis, condicional if

    -- Descripción
    description_expression TEXT,
    -- "Venta {{numero}}", "{{cliente_nombre}}"
    -- Puede incluir variables del contexto

    -- Centro de costo
    cost_center_source VARCHAR(50) DEFAULT 'SUBTYPE',
    -- 'FIXED', 'CONTEXT', 'SUBTYPE', 'FROM_TRANSACTION'
    cost_center_id UUID REFERENCES cost_center(id),
    cost_center_context_var VARCHAR(100),

    -- Condición para incluir/excluir esta línea
    condition_expr TEXT,
    -- "{{iva}} > 0" → solo incluir si hay IVA
    -- NULL → siempre incluir

    is_mandatory BOOLEAN DEFAULT TRUE,
    -- Si es mandatory y la condición falla, el template
    -- completo se descarta y se busca el siguiente

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_jtt_template ON journal_template_line(template_id);
CREATE INDEX idx_jt_company ON journal_type(company_id);
CREATE INDEX idx_jtpl_journal ON journal_template(journal_type_id);
```

### 5.3 Fuentes de Resolución de Cuentas

El sistema soporta 4 fuentes para resolver qué cuenta usar en cada línea:

| source | Descripción | Ejemplo |
|---|---|---|
| `FIXED` | Código de cuenta fijo | `account_code = "1-1-1-1-01"` |
| `PARAM` | Lookup en `module_accounting_config` | `account_param_concept = "VENTAS_CONTADO"` |
| `CONTEXT` | Variable del contexto transaccional | `account_context_var = "cuenta_ventas"` |
| `SUBTYPE` | Lookup en el subtipo del documento | El subtipo CxC tiene `cuenta_principal_id` |

**Orden de resolución**:
1. Si `SUBTYPE` está definido y existe un subtipo → usa su cuenta
2. Si no, si `CONTEXT` y la variable existe en el contexto → usa esa
3. Si no, si `PARAM` → busca en `module_accounting_config`
4. Si no, si `FIXED` → usa el código literal
5. Si nada resuelve → error: cuenta no configurada

### 5.4 Motor de Evaluación de Expresiones

```python
class ExpressionEvaluator:
    """
    Evalúa expresiones aritméticas y condicionales SIN usar eval().

    Variables disponibles: {{nombre_variable}}
    Operadores: +, -, *, /, (, )
    Funciones: sum(array, field), if(cond, then, else)

    Ejemplos:
        "{{total}}"
        "{{subtotal - descuento}}"
        "{{total * 0.15}}"
        "{{if(iva > 0, iva, 0)}}"
        "{{sum(lineas, 'subtotal')}}"
    """

    OPERATORS = {'+', '-', '*', '/'}
    FUNCTIONS = {'sum', 'if'}

    def evaluate(self, expression: str, context: dict) -> Decimal:
        # 1. Reemplazar {{variables}} con valores del contexto
        # 2. Parsear expresión con shunting-yard
        # 3. Evaluar AST con Decimal para precisión
        # 4. Retornar resultado
```

### 5.5 Template Engine Completo

```python
class TemplateEngine:
    """
    Motor que orquesta la generación de asientos desde plantillas.
    """

    def __init__(self,
                 journal_type_repo: JournalTypeRepository,
                 template_repo: JournalTemplateRepository,
                 config_repo: ModuleAccountingConfigRepository,
                 subtype_resolver: DocumentSubtypeResolver,
                 evaluator: ExpressionEvaluator):

    async def generate(
        self,
        journal_type_code: str,
        context: dict,
        company_id: UUID,
        document_subtype_id: UUID = None,
    ) -> list[JournalEntryLineDTO]:
        """
        1. Cargar journal_type por código
        2. Cargar templates activos, ordenados por prioridad
        3. Para cada template:
           a. Evaluar condition_expr del template
           b. Si cumple, evaluar cada línea:
              - Resolver cuenta (FIXED / PARAM / CONTEXT / SUBTYPE)
              - Evaluar amount_expression
              - Evaluar description_expression
              - Evaluar condition_expr de la línea
              - Si línea es mandatory y condición FALSE → descartar template
           c. Validar partida doble
           d. Si válido, retornar líneas
        4. Si ningún template produjo líneas → error
        """

    async def _resolve_account(self, line: JournalTemplateLine, context: dict) -> UUID:
        """Resuelve la cuenta según la fuente configurada."""

    async def _evaluate_amount(self, expression: str, context: dict) -> Decimal:
        """Evalúa una expresión de monto."""
```

### 5.6 Ejemplo Completo: Venta Contado

**Contexto enviado por el módulo de Ventas**:
```json
{
    "company_id": "uuid",
    "document_id": "uuid",
    "document_type": "FAC",
    "document_subtype_id": "uuid",
    "number": "F001-000123",
    "date": "2026-06-15",
    "subtotal": 1000.00,
    "descuento": 50.00,
    "iva": 142.50,
    "total": 1092.50,
    "tipo_pago": "CONTADO",
    "cliente_id": "uuid",
    "cliente_nombre": "Cliente SA",
    "moneda": "NIO",
    "tipo_cambio": 1.0,
    "costos": [{"cuenta_param": "COSTO_VENTAS", "monto": 300.00},
               {"cuenta_param": "INVENTARIO_MERCANCIAS", "monto": 300.00}]
}
```

**Tipo de Asiento**: `VENTA_CONT`

**Template evaluado** (prioridad más alta que cumple `{{tipo_pago}} == 'CONTADO'`):

| # | Nature | Account Source | Cuenta | Monto | Descripción | Condición |
|---|---|---|---|---|---|---|
| 1 | DEBIT | PARAM | `CAJA_GENERAL` | `{{total}}` | `Venta contado {{number}}` | — |
| 2 | CREDIT | PARAM | `VENTAS_CONTADO` | `{{subtotal - descuento}}` | `Venta {{number}}` | `{{subtotal - descuento}} > 0` |
| 3 | CREDIT | PARAM | `IVA_DEBITO_FISCAL` | `{{iva}}` | `IVA {{number}}` | `{{iva}} > 0` |
| 4 | DEBIT | PARAM | `COSTO_VENTAS` | `{{sum(costos, 'monto')}}` | `Costo {{number}}` | `{{sum(costos, 'monto')}} > 0` |
| 5 | CREDIT | PARAM | `INVENTARIO_MERCANCIAS` | `{{sum(costos, 'monto')}}` | `Descargo {{number}}` | `{{sum(costos, 'monto')}} > 0` |

**Resultado**: Asiento de 5 líneas, partida doble validada, $1,092.50 debe = $1,092.50 haber.

---

## 6. Importador de Catálogo (Excel/CSV)

### 6.1 Formato Esperado

El archivo debe contener las siguientes columnas (orden flexible, detectado por encabezado):

| Columna | Requerido | Descripción |
|---|---|---|
| `CODIGO` | Sí | Código completo: `1-01-001-0001` |
| `NOMBRE` | Sí | Nombre de la cuenta |
| `NIVEL` | Sí | Nivel en el árbol (1, 2, 3...) |
| `TIPO` | Sí | Código de account_type: `ACTIVO`, `PASIVO`, etc. |
| `ACEPTA_DATOS` | No | `SI`/`NO` (default: `NO`) |
| `ES_CONTROL` | No | `SI`/`NO` |
| `ES_AUXILIAR` | No | `SI`/`NO` |
| `MONEDA` | No | Código de moneda (`NIO`, `USD`) |
| `REQ_CCOSTO` | No | `SI`/`NO` |
| `CLASIF_FINANCIERA` | No | `CORRIENTE`, `NO_CORRIENTE`, etc. |
| `CLASIF_FISCAL` | No | `GRAVADO`, `EXENTO`, etc. |
| `CLASIF_NIIF` | No | Código NIIF |
| `ACTIVA` | No | `SI`/`NO` (default: `SI`) |
| `OBSERVACIONES` | No | Texto libre |

### 6.2 Pipeline de Importación

```
Upload archivo
    │
    ▼
Parseo (pandas/openpyxl)
    │
    ▼
Validación (lote completo, no fila por fila):
    ├── Encabezados obligatorios presentes
    ├── Códigos sin duplicados
    ├── Niveles consistentes (no saltos: 1, 2, 3... no 1, 3)
    ├── Jerarquía válida (códigos padre existen)
    ├── Tipos contables existen en account_type
    ├── Monedas existen (si se especifican)
    ├── Clasificaciones existen
    └── ACEPTA_DATOS consistente con nivel hoja
    │
    ├── Errores → mostrar vista previa con errores → detener
    └── OK → mostrar vista previa con resumen
            │
            ▼
    Confirmación del usuario
            │
            ▼
    Importación (una transacción):
        └── Rollback si falla
```

### 6.3 Componentes

```python
class CatalogImporter:
    """
    Importa catálogo de cuentas desde Excel/CSV.
    Reutilizable para cualquier empresa.
    """

    REQUIRED_COLUMNS = ['CODIGO', 'NOMBRE', 'NIVEL', 'TIPO']

    async def preview(self, file_path: str) -> ImportPreview:
        """Analiza el archivo y retorna vista previa + errores."""

    async def validate(self, rows: list[dict]) -> ValidationResult:
        """Valida todas las filas antes de importar."""

    async def import_catalog(self, file_path: str, company_id: UUID) -> ImportResult:
        """Ejecuta la importación en una transacción."""

    async def _validate_hierarchy(self, rows: list[dict]) -> list[str]:
        """Valida que la jerarquía del árbol sea correcta."""

    async def _validate_codes(self, rows: list[dict]) -> list[str]:
        """Valida códigos únicos y formato."""

    async def _build_tree(self, rows: list[dict]) -> list[Account]:
        """Construye el árbol de cuentas con relaciones parent_id."""
```

---

## 7. Plan de Migración (No Destructivo)

### 7.1 Estado Actual

```
constants.py           → 10 códigos de cuenta hardcodeados
cuenta_contable.py     → Modelo SQLAlchemy con estructura fija (8 niveles, código 20 chars)
cxc_service.py         → Raw SQL para buscar cuentas por código
cxp_service.py         → Raw SQL para buscar cuentas por código
asiento_service.py     → Lógica de validación de cuentas
seed.py                → 32 cuentas insertadas al inicio
```

### 7.2 Fase 1: Crear Nuevas Tablas (Sin Impacto)

**Qué**: Crear todas las tablas nuevas del diseño (account, account_type, journal_type, etc.)
**Impacto**: Cero. Las tablas nuevas coexisten con las existentes.
**Backward compat**: 100%.

### 7.3 Fase 2: Migrar Cuentas Existentes

**Qué**: 
1. Migrar las 32 cuentas actuales de `cuenta_contable` a `account`
2. Crear registros en `company_account_structure` para mantener compatibilidad
3. Crear registros en `module_accounting_config` con los valores actuales de `constants.py`

**Compatibilidad**: 
- `cuenta_contable` sigue existiendo y funcionando
- Se crea un trigger/servicio que sincroniza `cuenta_contable` ↔ `account`
- O mejor: se modifica el modelo `CuentaContable` para leer desde `account` (vista)

**Riesgo**: Bajo. Solo se agregan datos.

### 7.4 Fase 3: Adaptar Servicios (Puerto/Adaptador)

**Qué**: 
1. Crear `JournalEntryPort` con implementación usando las nuevas tablas
2. El `TemplateEngine` se implementa como nuevo servicio
3. `cxc_service.py` y `cxp_service.py` se modifican para usar el puerto

**Estrategia**:
```python
# Temporarily: both old and new coexist
class CxcService:
    def __init__(self, use_new_engine: bool = False):
        self.use_new_engine = use_new_engine

    async def crear_factura(self, ...):
        # Old way
        asiento_old = await self.asiento_svc.crear_asiento(...)

        if self.use_new_engine:
            # New way (double-write for validation)
            asiento_new = await self.template_engine.generate(...)
            # Compare asiento_old vs asiento_new
            # Log differences for audit
```

**Compatibilidad**: 100% con flag `use_new_engine = False`.

### 7.5 Fase 4: Feature Flag + Validación

**Qué**: 
1. Agregar flag `NEW_ACCOUNTING_ENGINE` en tabla `parameter`
2. Cuando está en `VALIDATION`, ambos motores corren, se comparan resultados
3. Cuando está en `ACTIVE`, solo el nuevo motor corre
4. Cuando está en `INACTIVE`, solo el viejo motor corre

**Flujo**:
```
INACTIVE → VALIDATION → ACTIVE
  (viejo)   (ambos)     (nuevo)
```

### 7.6 Fase 5: Eliminar Código Viejo

**Qué**: 
1. Eliminar `constants.py`
2. Eliminar `cuenta_contable.py` (o mantener como wrapper de `account`)
3. Refactorizar `asiento_service.py` para que use el nuevo motor
4. Cambiar flag a `ACTIVE` por defecto

**Impacto**: Eliminación de código muerto. Sistema totalmente migrado.

---

## 8. Tablas Existentes vs Nuevas

| Tabla Actual | Tabla Nueva | Relación |
|---|---|---|
| `cuenta_contable` | `account` | Migrar datos, luego deprecar |
| *(no existe)* | `account_type` | Nueva — clasificaciones base |
| *(no existe)* | `financial_classification` | Nueva — lookup |
| *(no existe)* | `tax_classification` | Nueva — lookup |
| *(no existe)* | `ifrs_classification` | Nueva — lookup |
| *(no existe)* | `company_account_structure` | Nueva — configuración de código |
| *(no existe)* | `module_accounting_config` | Nueva — reemplaza `constants.py` |
| *(no existe)* | `cxc_document_subtype` | Nueva — CxC configurable |
| *(no existe)* | `cxp_document_subtype` | Nueva — CxP configurable |
| *(no existe)* | `journal_type` | Nueva — tipos de asiento |
| *(no existe)* | `journal_template` | Nueva — plantillas |
| *(no existe)* | `journal_template_line` | Nueva — líneas de plantilla |
| `asiento` | *(usar existente)* | El motor escribe en la misma tabla |
| `asiento_linea` | *(usar existente)* | El motor escribe en la misma tabla |

---

## 9. Resumen de Cambios vs Código Actual

| Aspecto | Actual | Nuevo |
|---|---|---|
| Cuentas | Hardcodeadas en `constants.py` | `module_accounting_config` configurable |
| Catálogo | 32 cuentas semilla, estructura fija | Vacío al inicio, estructura configurable |
| CxC | `if tipo == "CONTADO"` en servicio | Subtipo de documento → template |
| CxP | `if iva > 0` en servicio | Subtipo de documento → template |
| Asientos | `AsientoService.crear_asiento()` con reglas en código | `TemplateEngine.generate()` con reglas en datos |
| IVA/Retenciones | Hardcodeado en constantes | `module_accounting_config` |
| Numeración | `SELECT max(numero) + 1` (race condition) | `numeracion` con `FOR UPDATE` |
| Validaciones | En `asiento_service.py` | En `TemplateEngine` + `JournalEngine` |

---

## 10. Pendiente de Aprobación

Para proceder con la implementación, necesito tu confirmación en los siguientes puntos:

1. **¿Apruebas este diseño general del catálogo, parametrización, subtipos y motor?**
2. **¿Apruebas la estrategia de migración no destructiva (Strangler Fig)?**
3. **¿Confirmas que el catálogo debe ir vacío al inicio y solo con clasificaciones base?**
4. **¿Prefieres un solo `module_accounting_config` o tablas separadas por módulo?**
5. **Para el motor de expresiones: ¿aceptas el mini-lenguaje con `{{}}` y funciones `sum/if`?**
6. **¿Quieres que prepare un archivo de ejemplo del catálogo en Excel/CSV para validar el importador?**
7. **¿Orden de implementación: primero tablas + migración de datos, luego motor, luego refactor de servicios?**

Una vez aprobado, procedo con:

1. Migración Alembic con todas las tablas nuevas
2. Seed de clasificaciones base (account_type, financial_classification, etc.)
3. Seed de subtipos CxC/CxP
4. Seed de tipos de asiento básicos (VENTA_CONT, VENTA_CRED, COMPRA)
5. Implementación del `TemplateEngine`
6. Adaptación de `cxc_service.py` con feature flag
7. Adaptación de `cxp_service.py` con feature flag
