# Arquitectura del ERP Contable Empresarial

> ADR-001: Arquitectura General
> Fecha: 2026-06-29
> Estado: Aprobación pendiente

---

## 1. Filosofía Arquitectónica

El dominio contable ha permanecido estable por más de 500 años (partida doble, libro diario, mayor, balance). La tecnología cambia; el dominio no. Por tanto:

- **El dominio es el centro**, no la tecnología
- Los bounded contexts reflejan **departamentos empresariales reales**
- La comunicación entre contextos es **explícita mediante eventos**
- Cada contexto es **independientemente desplegable** y **testeable**
- El motor contable es **el corazón del sistema**: cero dependencias transaccionales
- Toda regla de negocio es **configurable**, nunca hardcodeada

---

## 2. Mapa de Bounded Contexts

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CROSS-CUTTING                               │
│  ┌────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────┐  │
│  │ AUDIT  │  │ NOTIFY   │  │ REPORTING│  │ INTEGRATE│  │  IA   │  │
│  └────▲───┘  └────▲─────┘  └────▲─────┘  └────▲─────┘  └───▲───┘  │
│       │           │              │              │            │      │
├───────┴───────────┴──────────────┴──────────────┴────────────┴──────┤
│                      TRANSACTIONAL                                  │
│  ┌────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ SALES  │  │PURCHASING│  │INVENTORY │  │   CxC    │  │  CxP   │ │
│  └───┬────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│      │            │             │              │             │      │
│      └────────────┴─────────────┴──────────────┴─────────────┘      │
│                                │ Eventos                            │
│  ┌────────┐  ┌──────────┐  ┌───▼────────┐                         │
│  │  BANK   │  │   CASH   │  │JOURNAL ENGINE                    │ │
│  └────────┘  └──────────┘  │ (Motor Contable)                    │ │
│                            │  ┌──────────┐  ┌────────────────┐   │ │
│  ┌────────┐  ┌──────────┐  │  │TEMPLATES │  │  LEDGER        │   │ │
│  │  FIXED  │  │ PAYROLL  │  │  └──────────┘  │  (Mayor General)│   │ │
│  │ ASSETS  │  │          │  │                 └────────────────┘   │ │
│  └────────┘  └──────────┘  └──────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│                      FOUNDATION                                     │
│  ┌────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │IDENTITY│  │ SECURITY │  │CONFIG    │  │ORGANIZAT │  │ CHARTS │ │
│  │ & AUTH │  │ & RBAC   │  │(Param)   │  │ (Company)│  │OF ACCT │ │
│  └────────┘  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Bounded Contexts — Definición Completa

### 3.1 Foundation Layer

---

#### BC-001: Identity & Access (Identidad y Acceso)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Autenticación de usuarios, gestión de sesiones, JWT, MFA |
| **Dependencias** | Ninguna |
| **Publica** | `UserLoggedIn`, `UserLoggedOut`, `UserCreated`, `PasswordChanged`, `MFARegistered` |
| **Consume** | `AccessRevoked` (desde Security) |
| **Entidades** | `User`, `Session`, `LoginAttempt`, `MFAKey` |
| **Servicios** | `AuthenticationService`, `TokenService`, `PasswordService` |

---

#### BC-002: Security & Authorization (Seguridad y RBAC)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Gestión de roles, permisos, segregación de funciones (SoD), políticas de acceso |
| **Dependencias** | BC-001 (Identity) |
| **Publica** | `RoleAssigned`, `RoleRevoked`, `PermissionGranted`, `AccessRevoked`, `SoDViolationDetected` |
| **Consume** | `UserCreated` (para asignar rol por defecto) |
| **Entidades** | `Role`, `Permission`, `Policy`, `SoDRule`, `SoDViolation` |
| **Servicios** | `AuthorizationService`, `SoDValidationService`, `PolicyEvaluationService` |

**Modelo de Permisos**:

```
Permission
├── resource: str (ej: "accounting.journal-entry")
├── action: str (ej: "create", "approve", "reverse", "delete")
├── scope: str (ej: "company", "branch", "own")
└── conditions: JSON (condiciones adicionales: monto < 10000, etc.)
```

**Segregación de Funciones (SoD)**:

```
SoDRule
├── incompatible_actions: [action_a, action_b]  # Misma persona no puede hacer ambas
├── conflict_type: "SAME_USER" | "SAME_ROLE"
├── severity: "WARNING" | "BLOCKING"
└── description: str
```

---

#### BC-003: Configuration (Configuración General)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Parámetros globales y por empresa. Sin constantes hardcodeadas |
| **Dependencias** | BC-004 (Organization) |
| **Publica** | `ParameterCreated`, `ParameterUpdated`, `TaxRateChanged` |
| **Consume** | `CompanyCreated` (para inicializar parámetros default) |
| **Entidades** | `Parameter`, `ParameterGroup`, `Tax`, `TaxRate`, `Withholding`, `WithholdingRate`, `Currency`, `CostingMethod`, `DepreciationMethod` |
| **Servicios** | `ParameterService`, `TaxCalculationService`, `CurrencyConversionService` |

**Catálogo de Parámetros**:

```
Parameter
├── company_id: UUID
├── group: str            (ej: "accounting", "sales", "payroll", "tax")
├── code: str             (ej: "IVA_RATE", "COSTING_METHOD", "DAYS_CREDIT_LIMIT")
├── value: JSON
├── data_type: str         (ej: "decimal", "integer", "string", "json", "boolean")
├── description: str
└── editable: boolean
```

**No existen constantes hardcodeadas**. Cada parámetro vive en esta tabla.

---

#### BC-004: Organization Structure (Estructura Organizacional)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Jerarquía empresarial: grupo → empresa → sucursal → departamento |
| **Dependencias** | BC-001 (Identity) |
| **Publica** | `CompanyCreated`, `CompanyUpdated`, `BranchCreated`, `DepartmentCreated` |
| **Consume** | (ninguno) |
| **Entidades** | `Company`, `Branch`, `Department`, `LegalRepresentative`, `CompanyAddress` |
| **Servicios** | `OrganizationService` |

---

### 3.2 Core Accounting Layer

---

#### BC-005: Chart of Accounts (Catálogo de Cuentas)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Catálogo contable, estructura jerárquica, niveles, naturaleza |
| **Dependencias** | BC-003 (Config: monedas), BC-004 (Organization) |
| **Publica** | `AccountCreated`, `AccountUpdated`, `AccountDeactivated`, `AccountMoved` |
| **Consume** | `CompanyCreated` (para crear catálogo default) |
| **Entidades** | `Account`, `AccountGroup`, `AccountType`, `AccountRule`, `AccountBudget` |
| **Servicios** | `AccountCatalogService`, `AccountValidationService`, `AccountHierarchyService` |

**Modelo**:

```
Account
├── company_id: UUID
├── code: str              (estructura: X-XX-XX-XX-XX-XX-XX-XXXX)
├── name: str
├── type: ACCOUNT_TYPE     (ACTIVO, PASIVO, PATRIMONIO, INGRESO, COSTO, GASTO)
├── level: int             (1..8)
├── parent_id: UUID?
├── accepts_entries: boolean
├── currency_id: UUID?     (null = todas)
├── is_active: boolean
├── is_bank_account: boolean
├── is_cash_account: boolean
├── is_receivable: boolean
├── is_payable: boolean
└── allow_manual_entries: boolean
```

---

#### BC-006: Cost Centers & Dimensions (Centros de Costo y Dimensiones)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Dimensiones analíticas para segmentación contable |
| **Dependencias** | BC-004 (Organization) |
| **Publica** | `CostCenterCreated`, `DimensionValueCreated` |
| **Consume** | (ninguno) |
| **Entidades** | `CostCenter`, `CostCenterGroup`, `Dimension`, `DimensionValue` |
| **Servicios** | `CostCenterService` |

Soportar N dimensiones configurables (no solo centro de costo):
- Dimensión 1: Centro de costo (obligatorio)
- Dimensión 2: Proyecto
- Dimensión 3: Línea de negocio
- Dimensión 4..N: Configurable por empresa

---

#### BC-007: Journal Engine (Motor Contable)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | **CORAZÓN DEL ERP**. Creación, validación, reversión de asientos. Cierre/apertura de periodos. Materialización de saldos. |
| **Dependencias** | BC-005 (Chart of Accounts), BC-006 (Cost Centers), BC-003 (Config), BC-004 (Organization) |
| **NO depende de** | Sales, Purchasing, Inventory, CxC, CxP, Cash, Banks, Fixed Assets, Payroll |
| **Publica** | `JournalEntryCreated`, `JournalEntryReversed`, `JournalEntryApproved`, `PeriodClosed`, `PeriodOpened`, `FiscalYearClosed`, `BalanceUpdated` |
| **Consume** | `GenerateJournalEntry` (comando desde cualquier contexto transaccional) |
| **Entidades** | `JournalEntry`, `JournalEntryLine`, `Period`, `FiscalYear`, `AccountBalance`, `AccountBalanceDaily` |
| **Servicios** | `JournalEntryService`, `PeriodService`, `FiscalYearService`, `BalanceMaterializationService`, `JournalTemplateEngine` |

**Independencia**: El Journal Engine expone un servicio/interfaz que cualquier contexto puede llamar:
```
interface JournalEntryPort {
    async create(entries: CreateJournalEntryDTO): JournalEntryResponse
    async reverse(entryId: UUID, reason: string): JournalEntryResponse
    async getBalance(accountId: UUID, periodId: UUID): BalanceDTO
}
```

Los contextos transaccionales NUNCA importan entidades del Journal Engine directamente. Usan el puerto (interfaz).

---

### 3.3 Transactional Layer

---

#### BC-008: Sales (Ventas)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Cotizaciones, pedidos, facturación, notas de crédito |
| **Dependencias** | BC-004 (Organization), BC-013 (Inventory), BC-003 (Config) |
| **Publica** | `SalesOrderCreated`, `SalesOrderConfirmed`, `InvoiceIssued`, `CreditNoteIssued`, `SalesInvoiceCancelled` |
| **Consume** | `InventoryUpdated` (confirmar disponibilidad) |
| **Entidades** | `SalesOrder`, `SalesOrderLine`, `SalesInvoice`, `SalesInvoiceLine`, `CreditNote`, `PriceList`, `DiscountPolicy` |
| **Servicios** | `SalesOrderService`, `PricingService`, `SalesInvoiceService` |

---

#### BC-009: Accounts Receivable (CxC)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Gestión de cartera de clientes, antigüedad de saldos, cobranza |
| **Dependencias** | BC-004 (Organization), BC-003 (Config) |
| **Publica** | `ReceivableCreated`, `PaymentReceived`, `InvoiceAgingCalculated`, `ReceivableWrittenOff` |
| **Consume** | `InvoiceIssued` (crear CxC), `PaymentReceived` (actualizar saldo) |
| **Entidades** | `Customer`, `Receivable`, `ReceivablePayment`, `AgingBucket`, `CollectionAction` |
| **Servicios** | `AgingService`, `CollectionService` |

---

#### BC-010: Purchasing (Compras)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Órdenes de compra, recepción, facturación de compras |
| **Dependencias** | BC-004 (Organization), BC-013 (Inventory), BC-003 (Config) |
| **Publica** | `PurchaseOrderCreated`, `PurchaseOrderReceived`, `PurchaseInvoiceIssued`, `PurchaseReturns` |
| **Consume** | `InventoryUpdated` (confirmar disponibilidad, actualizar costos) |
| **Entidades** | `PurchaseOrder`, `PurchaseOrderLine`, `PurchaseInvoice`, `PurchaseInvoiceLine`, `Supplier` |
| **Servicios** | `PurchaseOrderService`, `PurchaseInvoiceService`, `CostAverageService` |

---

#### BC-011: Accounts Payable (CxP)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Gestión de cartera de proveedores, programación de pagos |
| **Dependencias** | BC-004 (Organization), BC-003 (Config) |
| **Publica** | `PayableCreated`, `PaymentMade`, `PayableAgingCalculated` |
| **Consume** | `PurchaseInvoiceIssued`, `PaymentMade` |
| **Entidades** | `Supplier`, `Payable`, `PayablePayment` |
| **Servicios** | `AgingService`, `PaymentScheduleService` |

---

#### BC-012: Cash & Bank (Efectivo y Bancos)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Gestión de caja chica, cuentas bancarias, conciliación, flujo de efectivo |
| **Dependencias** | BC-004 (Organization), BC-003 (Config) |
| **Publica** | `CashMovementRecorded`, `BankMovementImported`, `ReconciliationCompleted` |
| **Consume** | `PaymentReceived`, `PaymentMade` (actualizar saldos) |
| **Entidades** | `CashRegister`, `CashMovement`, `BankAccount`, `BankMovement`, `Reconciliation`, `ReconciliationMatch`, `BankStatement` |
| **Servicios** | `CashService`, `BankService`, `ReconciliationService`, `StatementImportService` |

---

#### BC-013: Inventory (Inventario)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Productos, almacenes, valoración de inventario, movimientos |
| **Dependencias** | BC-004 (Organization), BC-003 (Config: costing method) |
| **Publica** | `ProductCreated`, `StockUpdated`, `InventoryValuationCalculated`, `StockTransferCompleted` |
| **Consume** | `SalesInvoiceIssued` (descargar), `PurchaseOrderReceived` (ingresar), `PurchaseReturns` (ajustar) |
| **Entidades** | `Product`, `ProductCategory`, `Warehouse`, `WarehouseLocation`, `StockMovement`, `InventoryValuation`, `SerialNumber`, `LotNumber` |
| **Servicios** | `InventoryService`, `CostingService` (FIFO, LIFO, promedio, identificación específica), `StockValuationService` |

---

### 3.4 Specialized Layer

---

#### BC-014: Fixed Assets (Activos Fijos)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Registro, depreciación, mejora, baja de activos fijos |
| **Dependencias** | BC-004 (Organization), BC-003 (Config: depreciation methods), BC-005 (Chart of Accounts) |
| **Publica** | `AssetAcquired`, `AssetDepreciated`, `AssetDisposed`, `AssetImproved` |
| **Consume** | `PurchaseInvoiceIssued` (capitalizar compra como activo) |
| **Entidades** | `FixedAsset`, `AssetCategory`, `DepreciationSchedule`, `DepreciationEntry`, `AssetDisposal` |
| **Servicios** | `DepreciationService` (straight-line, sum-of-years, double-declining, units-of-production), `AssetLifecycleService` |

---

#### BC-015: Payroll (Nómina)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Gestión de empleados, contratos, cálculo de nómina, deducciones, provisiones |
| **Dependencias** | BC-004 (Organization), BC-003 (Config: INSS, IR parameters), BC-005 (Chart of Accounts) |
| **Publica** | `EmployeeHired`, `PayrollCalculated`, `PayrollPaid`, `EmployeeTerminated` |
| **Consume** | `PaymentMade` (marcar nómina como pagada) |
| **Entidades** | `Employee`, `Contract`, `PayrollHeader`, `PayrollLine`, `PayrollDeduction`, `PayrollProvision`, `Vacation`, `Absence` |
| **Servicios** | `PayrollCalculationService`, `SocialSecurityService`, `IncomeTaxService`, `ProvisionService` |

---

### 3.5 Cross-Cutting Layer

---

#### BC-016: Audit (Auditoría)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Registro inmutable de toda operación significativa |
| **Dependencias** | BC-001 (Identity) |
| **Publica** | (ninguno — es leído) |
| **Consume** | Todos los eventos de dominio |
| **Entidades** | `AuditEvent`, `AuditLog`, `AuditPolicy` |
| **Servicios** | `AuditService`, `AuditQueryService` |

Cada evento de dominio se persiste como un `AuditEvent`:
```
AuditEvent
├── event_id: UUID
├── event_type: str           (ej: "JournalEntryCreated")
├── aggregate_type: str       (ej: "JournalEntry")
├── aggregate_id: UUID
├── version: int
├── occurred_at: timestamp
├── user_id: UUID
├── company_id: UUID
├── ip_address: str?
├── user_agent: str?
├── reason: str?              (obligatorio para reversiones, anulaciones)
├── before: JSON?             (estado anterior)
├── after: JSON?              (estado posterior)
└── metadata: JSON?           (propiedades adicionales)
```

---

#### BC-017: Notifications (Notificaciones)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Envío de correos, notificaciones in-app, push, alertas |
| **Dependencias** | Ninguna |
| **Publica** | (ninguno) |
| **Consume** | Cualquier evento que requiera notificación |
| **Entidades** | `Notification`, `NotificationTemplate`, `NotificationChannel` |
| **Servicios** | `NotificationService`, `EmailService`, `PushService` |

---

#### BC-018: Reporting & BI (Reportes)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | Reportes financieros, dashboard, KPIs, exportación |
| **Dependencias** | BC-005 (Accounts), BC-007 (Journal Engine for balances), BC-008..015 (datos transaccionales) |
| **Publica** | `ReportGenerated` |
| **Consume** | `BalanceUpdated` (para mantener reportes actualizados) |
| **Entidades** | `ReportDefinition`, `ReportExecution`, `Dashboard`, `KPI`, `KPIValue` |
| **Servicios** | `ReportService`, `KPIService`, `ExportService` (PDF, Excel, CSV) |

---

#### BC-019: Integration (API / Webhooks / OCR / IA)

| Atributo | Valor |
|---|---|
| **Responsabilidad** | API pública versionada, webhooks, OCR, inteligencia artificial |
| **Dependencias** | Cualquier contexto (vía puertos/interfaces) |
| **Publica** | (ninguno) |
| **Consume** | Eventos de dominio para disparar webhooks |
| **Entidades** | `ApiKey`, `Webhook`, `WebhookDelivery`, `OcrProcessing`, `AiSuggestion`, `AiModel` |
| **Servicios** | `ApiGatewayService`, `WebhookService`, `OcrService`, `AiService`, `ClassificationService`, `AnomalyDetectionService` |

---

## 4. Motor Contable (Journal Engine) — Diseño Detallado

### 4.1 Principios

1. **Cero dependencias transaccionales**: No importa nada de Sales, Purchasing, CxC, CxP, Inventory
2. **Independiente y portable**: Puede vivir en su propio microservicio
3. **Event-driven**: Emite eventos cuando se crean/reversan asientos
4. **Configurable**: Tipos de asiento, plantillas, numeración viven en datos
5. **Inmutable**: Los asientos no se modifican, solo se reversan
6. **Cierre obligatorio**: No se pueden registrar asientos en periodos cerrados
7. **Partida doble validada**: Toda transacción debe cuadrar

### 4.2 Puertos (Interfaces)

```python
# Puertos de entrada (usados por contextos transaccionales)
class JournalEntryPort(ABC):
    @abstractmethod
    async def create(self, dto: CreateJournalEntryDTO) -> JournalEntryResponse: ...
    @abstractmethod
    async def reverse(self, entry_id: UUID, reason: str) -> JournalEntryResponse: ...
    @abstractmethod
    async def get_balance(self, account_id: UUID, period_id: UUID) -> BalanceDTO: ...
    @abstractmethod
    async def get_trial_balance(self, period_id: UUID) -> list[BalanceDTO]: ...

# Puertos de salida (implementados en infraestructura)
class AccountRepository(ABC):
    @abstractmethod
    async def get_by_id(self, account_id: UUID) -> Account: ...
    @abstractmethod
    async def get_by_code(self, company_id: UUID, code: str) -> Account: ...

class PeriodRepository(ABC):
    @abstractmethod
    async def get_open_period(self, company_id: UUID, date: date) -> Period: ...
    @abstractmethod
    async def lock_and_get_next_number(self, period_id: UUID) -> int: ...

class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: DomainEvent): ...
```

### 4.3 Entidades de Dominio (Motor Contable)

```python
class JournalEntry(AggregateRoot):
    id: UUID
    company_id: UUID
    number: int
    date: date
    period_id: UUID
    entry_type: str              # journal_type.code
    concept: str
    lines: list[JournalEntryLine]
    origin_module: str?          # "sales", "purchasing", etc.
    origin_document_id: UUID?
    created_by: UUID
    approved_by: UUID?
    is_reversed: bool
    reversal_entry_id: UUID?
    created_at: datetime
    approved_at: datetime?

    def validate(self):
        """Reglas de dominio: partida doble, cuentas válidas, periodo abierto"""
    def reverse(self, reason: str, user_id: UUID) -> JournalEntry:
        """Crea asiento de reversión"""
    def approve(self, user_id: UUID):
        """Aprueba el asiento"""

class JournalEntryLine(Entity):
    id: UUID
    entry_id: UUID
    account_id: UUID
    cost_center_id: UUID?
    dimension_2_id: UUID?
    dimension_3_id: UUID?
    description: str?
    debit_local: Decimal
    credit_local: Decimal
    debit_foreign: Decimal
    credit_foreign: Decimal
    exchange_rate: Decimal
    foreign_currency_id: UUID?
    order: int

class Period(Entity):
    id: UUID
    company_id: UUID
    fiscal_year_id: UUID
    code: str                    # "2026-01"
    name: str
    start_date: date
    end_date: date
    is_closed: boolean
    closed_by: UUID?
    closed_at: datetime?
    is_adjustment_period: boolean

class FiscalYear(Entity):
    id: UUID
    company_id: UUID
    code: str                    # "2026"
    name: str
    start_date: date
    end_date: date
    is_closed: boolean
    closing_entry_id: UUID?       # Asiento de cierre
    opening_entry_id: UUID?       # Asiento de apertura

class AccountBalance(Entity):
    id: UUID
    company_id: UUID
    account_id: UUID
    period_id: UUID
    opening_balance: Decimal
    total_debit: Decimal
    total_credit: Decimal
    closing_balance: Decimal
    opening_balance_foreign: Decimal
    total_debit_foreign: Decimal
    total_credit_foreign: Decimal
    closing_balance_foreign: Decimal
    version: int                  # Para optimistic locking
```

### 4.4 Flujo de Creación de Asiento

```
1. Recibir CreateJournalEntryDTO
2. Validar periodo (existente, abierto, rango de fechas)
3. Validar partida doble (total debe == total haber)
4. Validar cada línea: cuenta existe, acepta datos, activa
5. Obtener número secuencial (con FOR UPDATE)
6. Crear entrada y líneas
7. Actualizar saldos materializados (AccountBalance)
8. Publicar evento JournalEntryCreated
9. Retornar JournalEntryResponse
```

### 4.5 Flujo de Reversión

```
1. Recibir ReverseJournalEntryDTO
2. Validar asiento existe y no ha sido reversado
3. Validar periodo abierto (o permitir reversión en periodo siguiente)
4. Crear asiento de reversión (debe <-> haber invertidos)
5. Marcar asiento original como reversado
6. Actualizar saldos (restar original, sumar reversión)
7. Publicar evento JournalEntryReversed
```

---

## 5. Motor de Plantillas (Journal Template Engine)

### 5.1 Modelo de Datos

```sql
CREATE TABLE journal_type (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    code VARCHAR(20) NOT NULL,          -- VENTA_CONT, VENTA_CRED, COMPRA, etc.
    name VARCHAR(100) NOT NULL,
    module VARCHAR(50),                 -- sales, purchasing, cash, payroll, etc.
    nature VARCHAR(20) NOT NULL,        -- AUTOMATIC, MANUAL, RECURRING
    affects_inventory BOOLEAN DEFAULT FALSE,
    affects_receivable BOOLEAN DEFAULT FALSE,
    affects_payable BOOLEAN DEFAULT FALSE,
    affects_cash BOOLEAN DEFAULT FALSE,
    requires_approval BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE journal_template (
    id UUID PRIMARY KEY,
    journal_type_id UUID NOT NULL REFERENCES journal_type(id),
    company_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    priority INT DEFAULT 0,
    condition_expr VARCHAR(500)?,    -- Ej: "{{tipo_pago}} == 'CONTADO'"
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE journal_template_line (
    id UUID PRIMARY KEY,
    template_id UUID NOT NULL REFERENCES journal_template(id),
    line_order INT NOT NULL,
    account_code_expr VARCHAR(200) NOT NULL,  -- Ej: "1-1-1-1-01", o "{{cuenta_cxc}}"
    nature VARCHAR(10) NOT NULL,              -- DEBIT / CREDIT
    amount_expr VARCHAR(500) NOT NULL,        -- Ej: "{{total}}", "{{subtotal - descuento}}"
    description_expr VARCHAR(500),            -- Ej: "Venta contado {{numero}}"
    cost_center_expr VARCHAR(200)?,
    condition_expr VARCHAR(500)?,             -- Ej: "{{iva}} > 0"
    is_mandatory BOOLEAN DEFAULT TRUE
);
```

### 5.2 Variables de Contexto

Cada módulo transaccional envía un `contexto` con variables al solicitar la generación:

```python
# Contexto típico para una venta:
{
    "company_id": "...",
    "document_type": "FACTURA",
    "document_id": "...",
    "number": "F001-000123",
    "date": "2026-06-15",
    "subtotal": 1000.00,
    "descuento": 50.00,
    "iva": 142.50,
    "total": 1092.50,
    "tipo_pago": "CONTADO",
    "cliente_id": "...",
    "cliente_nombre": "Cliente SA",
    "moneda": "NIO",
    "tipo_cambio": 1.0,
    "lineas": [
        {"producto": "P001", "cantidad": 2, "precio": 500, "costo": 350, "cuenta_ingreso": "4-1-1-1-01"},
        ...
    ],
    "costos": [
        {"cuenta": "5-1-1-1-01", "monto": 700},
        {"cuenta": "1-1-3-1-01", "monto": 700},
    ]
}
```

### 5.3 Motor de Evaluación

```python
class TemplateEngine:
    """
    Evalúa plantillas de asiento usando un contexto de variables.
    Sin eval() inseguro: usa un mini-lenguaje con operaciones aritméticas básicas.
    """

    def evaluate(self, template: JournalTemplate, context: dict) -> list[JournalEntryLine]:
        """
        1. Evaluar condition_expr del template: si False, saltar template
        2. Para cada línea:
           a. Evaluar condition_expr: si False, saltar línea
           b. Evaluar account_code_expr → account_id
           c. Evaluar amount_expr → monto
           d. Evaluar description_expr → texto
           e. Evaluar cost_center_expr → cost_center_id
        3. Validar partida doble
        4. Retornar líneas
        """
```

### 5.4 Operaciones Soportadas en Expresiones

```
{{variable}}                     → valor literal
{{subtotal - descuento}}         → resta
{{total * 0.15}}                 → multiplicación
{{total / 1.15}}                 → división
{{sum(lineas, 'costo')}}         → suma de atributo en array
{{if iva > 0 then iva else 0}}   → condicional
{{cuenta_por_defecto}}           → lookup en tabla de reglas
```

### 5.5 Ejemplo: Plantilla Venta Contado

```
Tipo: VENTA_CONT
Template: "Venta Contado (default)"
Prioridad: 0
Condition: {{tipo_pago}} == "CONTADO"

Línea 1:
  Orden: 1
  Cuenta: 1-1-1-1-01 (Caja General)
  Naturaleza: DEBIT
  Monto: {{total}}
  Descripción: "Venta contado {{numero}}"

Línea 2:
  Orden: 2
  Cuenta: {{cuenta_ventas}}
  Naturaleza: CREDIT
  Monto: {{subtotal - descuento}}
  Descripción: "Venta {{numero}}"
  Condición: {{subtotal - descuento}} > 0

Línea 3:
  Orden: 3
  Cuenta: 2-1-2-1 (IVA por Pagar)
  Naturaleza: CREDIT
  Monto: {{iva}}
  Descripción: "IVA {{numero}}"
  Condición: {{iva}} > 0

Línea 4:
  Orden: 4
  Cuenta: 5-1-1-1-01 (Costo de Ventas)
  Naturaleza: DEBIT
  Monto: {{sum(costos, 'monto')}}
  Condición: {{sum(costos, 'monto')}} > 0

Línea 5:
  Orden: 5
  Cuenta: 1-1-3-1-01 (Inventario)
  Naturaleza: CREDIT
  Monto: {{sum(costos, 'monto')}}
  Condición: {{sum(costos, 'monto')}} > 0
```

---

## 6. Eventos del Dominio

### 6.1 Formato

```python
@dataclass
class DomainEvent:
    event_id: UUID
    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    version: int
    occurred_at: datetime
    user_id: UUID
    company_id: UUID
    data: dict                     # Datos específicos del evento
    metadata: dict                 # IP, user-agent, correlación, etc.
```

### 6.2 Catálogo de Eventos

| Evento | Publicador | Consumidores Potenciales |
|---|---|---|
| `UserCreated` | Identity | Security (asignar rol), Configuration (crear params) |
| `UserLoggedIn` | Identity | Audit |
| `CompanyCreated` | Organization | Charts of Accounts (catálogo default), Configuration (params default) |
| `RoleAssigned` | Security | Audit |
| `SoDViolationDetected` | Security | Notifications (alertar admin) |
| `AccountCreated` | Chart of Accounts | Audit |
| `JournalEntryCreated` | Journal Engine | Audit, Reporting (actualizar reportes), Notifications (si requiere aprobación) |
| `JournalEntryReversed` | Journal Engine | Audit, Reporting |
| `PeriodClosed` | Journal Engine | Audit, Notifications, Reporting |
| `PeriodOpened` | Journal Engine | Audit |
| `BalanceUpdated` | Journal Engine | Reporting (actualizar dashboard) |
| `InvoiceIssued` | Sales | CxC (crear receivable), Inventory (descargar stock), Journal Engine (generar asiento via comando) |
| `InvoiceCancelled` | Sales | CxC, Inventory, Journal Engine |
| `PaymentReceived` | CxC | Cash (registrar movimiento), Journal Engine |
| `PurchaseInvoiceIssued` | Purchasing | CxP (crear payable), Inventory (actualizar costo), Journal Engine |
| `PaymentMade` | CxP | Cash, Journal Engine |
| `CashMovementRecorded` | Cash | Journal Engine |
| `ReconciliationCompleted` | Bank | Journal Engine |
| `StockUpdated` | Inventory | Sales (confirmar disponibilidad), Purchasing (costos) |
| `AssetDepreciated` | Fixed Assets | Journal Engine |
| `PayrollCalculated` | Payroll | Journal Engine |
| `ReportGenerated` | Reporting | Notifications |

### 6.3 Flujo de Comunicación entre Contextos

```
Ejemplo: Emitir Factura de Venta

Sales: InvoiceIssued
    │
    ├──→ CxC: InvoiceIssued → crear Receivable
    ├──→ Inventory: InvoiceIssued → descargar Stock
    │
    └──→ Application Layer (Saga Coordinator)
              │
              ├──→ Journal Engine: comando GenerateJournalEntry(contexto_venta)
              │       │
              │       └──→ Template Engine evalúa VENTA_CONT
              │       └──→ JournalEntryCreated
              │       └──→ BalanceUpdated
              │
              └──→ Cash: si CONTADO, registrar cobro
```

---

## 7. Seguridad (RBAC + SoD)

### 7.1 Modelo de Permisos

Cada endpoint se mapea a un permiso:

```
POST /api/v2/accounting/journal-entries → accounting.journal-entry.create
POST /api/v2/accounting/journal-entries/{id}/reverse → accounting.journal-entry.reverse
POST /api/v2/accounting/periods/{id}/close → accounting.period.close
GET /api/v2/reporting/balance-sheet → reporting.balance-sheet.read
```

### 7.2 Verificación

Middleware/decorador en cada endpoint:

```python
@router.post("/journal-entries")
@require_permission("accounting.journal-entry.create")
async def create_journal_entry(...):
    ...

@require_permission("accounting.journal-entry.approve", conditions={"max_amount": 10000})
async def approve_journal_entry(...):
    ...
```

### 7.3 SoD Matrix (Mínima)

| Acción A | Acción B | Conflicto |
|---|---|---|
| Emitir Factura | Aprobar Factura | Mismo usuario |
| Crear Asiento | Reversar Asiento | Mismo usuario |
| Cerrar Periodo | Reabrir Periodo | Mismo usuario |
| Crear Proveedor | Pagar Proveedor | Mismo usuario |
| Registrar CxC | Aplicar Descuento | Mismo usuario |
| Crear Usuario | Asignar Roles | Mismo usuario |

---

## 8. Módulos Futuros — Contratos Anticipados

### 8.1 Nómina (Payroll)

```python
# Puerto que expondrá Payroll al Journal Engine
class PayrollJournalPort:
    async def generate_payroll_entries(payroll_id: UUID) -> list[JournalEntryDTO]:
        """Genera asientos de nómina (sueldos, INSS, IR)"""

# Eventos que publicará
class PayrollCalculated(DomainEvent):
    payroll_id: UUID
    period_id: UUID
    total_wages: Decimal
    total_deductions: Decimal
    total_employer_cost: Decimal
    lines: list[PayrollLineDTO]
```

### 8.2 Activos Fijos (Fixed Assets)

```python
class AssetJournalPort:
    async def generate_acquisition_entry(asset_id: UUID) -> JournalEntryDTO: ...
    async def generate_depreciation_entry(asset_id: UUID, period_id: UUID) -> JournalEntryDTO: ...
    async def generate_disposal_entry(asset_id: UUID) -> JournalEntryDTO: ...

class AssetDepreciated(DomainEvent):
    asset_id: UUID
    period_id: UUID
    depreciation_amount: Decimal
    accumulated_depreciation: Decimal
```

### 8.3 Conciliación Bancaria

```python
class ReconciliationJournalPort:
    async def generate_reconciliation_entries(reconciliation_id: UUID) -> list[JournalEntryDTO]: ...

class ReconciliationCompleted(DomainEvent):
    reconciliation_id: UUID
    bank_account_id: UUID
    period_id: UUID
    total_differences: Decimal
    matched_count: int
    unmatched_count: int
```

### 8.4 OCR

```python
class OCRPort(ABC):
    async def process_image(image_path: str) -> OCRResult: ...
    async def process_pdf(pdf_path: str) -> OCRResult: ...

class OCRResult:
    vendor_name: str?
    vendor_tax_id: str?
    invoice_number: str?
    date: date?
    subtotal: Decimal?
    tax: Decimal?
    total: Decimal?
    line_items: list[OCRLineItem]
    confidence: float            # 0.0 - 1.0
```

### 8.5 IA (Inteligencia Artificial)

```python
class AIPort(ABC):
    async def suggest_account(description: str, context: dict) -> list[AccountSuggestion]: ...
    async def detect_anomalies(entries: list[JournalEntryDTO]) -> list[Anomaly]: ...
    async def suggest_recurring_entry(company_id: UUID) -> list[JournalEntryDTO]: ...
    async def classify_document(image_path: str) -> DocumentClassification: ...

class AccountSuggestion:
    account_id: UUID
    account_code: str
    account_name: str
    confidence: float
    reason: str

class Anomaly:
    severity: str                # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    description: str
    entry_ids: list[UUID]
    suggested_action: str
```

---

## 9. Roadmap de Construcción

### Fase 2 — Motor Contable Configurable (Semana 1-8)

**Objetivo**: Reemplazar el motor contable actual por el nuevo diseño sin romper nada.

**Pasos**:
1. Crear estructura de carpetas para Journal Engine (no mover nada existente)
2. Implementar entidades de dominio en `domain/` (JournalEntry, Period, AccountBalance)
3. Implementar `TemplateEngine` con evaluación de expresiones segura
4. Crear tablas `journal_type`, `journal_template`, `journal_template_line`
5. Migrar `constants.py` → seed de `journal_type` y `journal_template`
6. Crear `JournalEntryPort` y sus implementaciones
7. Migrar `AsientoService.crear_asiento` a usar el nuevo motor (manteniendo el viejo)
8. Hacer que `CxcService._generar_asiento_venta` llame al nuevo motor
9. Una vez validado, marcar el código viejo como deprecado
10. Tests: 100% cobertura del nuevo motor

**Entregables**:
- `domain/journal_engine/` entidades, value objects
- `application/journal_engine/` use cases
- `infrastructure/persistence/journal_engine/` repositorios SQLAlchemy
- Motor de plantillas funcional
- Seed con tipos de asiento: VENTA_CONT, VENTA_CRED, COMPRA
- Tests unitarios e integración

**Compatibilidad**: El endpoint `POST /api/v1/asientos` sigue funcionando. El código viejo corre en paralelo.

### Fase 3 — Configuración General (Semana 9-12)

**Pasos**:
1. Crear `domain/configuration/` con entidades Parameter, Tax, Currency
2. Migrar parámetros hardcodeados a la tabla `parameter`
3. Crear endpoints de configuración (GET/PUT)
4. Crear UI de administración de parámetros
5. Servicio de conversión de moneda con tipo de cambio histórico

### Fase 4 — Tipos de Asiento + Plantillas UI (Semana 13-16)

**Pasos**:
1. UI para CRUD de tipos de asiento
2. UI para diseñar plantillas (arrastrar y soltar líneas)
3. UI para previsualizar asiento antes de generar
4. Migrar todas las constantes de cuenta a parámetros

### Fase 5 — RBAC Completo (Semana 17-20)

**Pasos**:
1. Implementar middleware de permisos
2. Anotar todos los endpoints con `@require_permission`
3. UI de gestión de roles y permisos
4. Implementar SoD básico
5. Tests de seguridad

### Fase 6 — Conciliación Bancaria (Semana 21-24)

**Pasos**:
1. Implementar importación de estados de cuenta (Excel, CSV, OFX)
2. Motor de matching automático (monto + fecha + referencia)
3. UI de conciliación (drag & drop, match sugerido)
4. Generación de asientos de diferencias
5. Reporte de conciliación

### Fase 7 — Activos Fijos (Semana 25-28)

**Pasos**:
1. CRUD de activos fijos
2. Configuración de métodos de depreciación
3. Cálculo de depreciación mensual (job programado)
4. Generación automática de asientos
5. Reporte de activos fijos

### Fase 8 — Empleados (Semana 29-30)

**Pasos**:
1. CRUD de empleados (separado de usuarios del sistema)
2. Contratos, historial salarial
3. Vacaciones, ausencias
4. Preparación de datos para nómina

### Fase 9 — Nómina (Semana 31-36)

**Pasos**:
1. Configuración de INSS, IR, otras deducciones
2. Cálculo de nómina mensual
3. Generación de asientos de nómina
4. Provisiones (aguinaldo, indemnización, vacaciones)
5. Reportes de nómina (planilla, INSS, IR)

### Fase 10 — Presupuestos (Semana 37-40)

**Pasos**:
1. CRUD de presupuestos por cuenta + centro de costo
2. Reporte real vs presupuesto
3. Alertas de exceso presupuestario
4. Aprobación de presupuestos

### Fase 11 — OCR (Semana 41-44)

**Pasos**:
1. Integración con Tesseract / Google Vision / AWS Textract
2. Pipeline de extracción de campos
3. Matching contra proveedores y clientes
4. Sugerencia de registro automático

### Fase 12 — IA (Semana 45-48)

**Pasos**:
1. Clasificación contable inteligente
2. Detección de anomalías
3. Asientos sugeridos basados en patrones
4. Copilot contable en lenguaje natural

---

## 10. ADRs Vinculados

| ADR | Título | Estado |
|---|---|---|
| ADR-001 | Arquitectura general del ERP | Pendiente |
| ADR-002 | Motor Contable independiente | Pendiente |
| ADR-003 | Motor de Plantillas configurable | Pendiente |
| ADR-004 | Eventos del dominio vs llamadas directas | Pendiente |
| ADR-005 | Materialización de saldos | Pendiente |
| ADR-006 | RBAC granular con SoD | Pendiente |
| ADR-007 | Estrategia de migración no destructiva | Pendiente |

---

## 11. Estrategia de Migración (No Destructiva)

### Principio
>Cada cambio debe mantener el sistema actual 100% funcional. El código nuevo y viejo coexisten hasta que el nuevo está validado.

### Técnica: Strangler Fig Pattern

1. **Añadir, no reemplazar**: El nuevo código se escribe en carpetas nuevas (`domain/`, `application/`, `infrastructure/`)
2. **Puertos**: El código viejo se abstrae detrás de un puerto
3. **Feature Flag**: Un flag `USE_NEW_ENGINE` controla qué implementación se usa
4. **Doble escritura** (opcional): Durante la migración, ambos motores ejecutan pero solo el viejo persiste
5. **Comparación**: Los resultados del nuevo motor se comparan con el viejo en tests
6. **Corte**: Cuando la comparación muestra 100% coincidencia por N días, se elimina el código viejo

### Ejemplo: Migración del Motor Contable

```
Semana 1: Crear carpetas, entidades, puertos (cero impacto)
Semana 2: Implementar TemplateEngine, tests
Semana 3: Crear implementación del puerto usando el nuevo motor
Semana 4: Feature flag en endpoints
Semana 5: Doble escritura en CXC (viejo + nuevo asiento)
Semana 6: Validación, corte, eliminación de código viejo
```

---

## 12. Preguntas para el Negocio

Antes de aprobar este diseño, necesito resolver:

1. **Número de desarrolladores**: ¿1 persona o equipo? (impacta velocidad del roadmap)
2. **Fecha límite**: ¿Hay algún hito inamovible?
3. **Datos reales en producción**: ¿El sistema actual tiene datos contables reales?
4. **Módulo más crítico hoy**: ¿Cuál necesita estabilidad inmediata?
5. **Presupuesto de infraestructura**: ¿Podemos agregar Redis, colas, almacenamiento?
6. **Usuarios activos**: ¿Cuantos y en qué horario? (impacta ventanas de mantenimiento)
7. **Regulación**: ¿NIIF completo o solo PYME? ¿Facturación electrónica DAE ya implementada?

---

## Resumen para Aprobación

| Aspecto | Decisión |
|---|---|
| **Arquitectura** | Bounded Contexts + Event-Driven + Hexagonal |
| **Motor Contable** | Independiente, cero dependencias transaccionales |
| **Plantillas** | Configurables vía datos, no código |
| **Eventos** | Comunicación asíncrona entre contextos |
| **RBAC** | Granular por permiso, con SoD |
| **Auditoría** | Inmutable, basada en eventos de dominio |
| **Migración** | Strangler Fig, 100% backward compatible |
| **Roadmap** | 12 fases, ~48 semanas estimadas |

**Próximo paso**: Tu aprobación para iniciar Fase 2 (Motor Contable) siguiendo este diseño.
