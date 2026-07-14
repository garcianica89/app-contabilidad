from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date
import uuid


class EmpresaCreate(BaseModel):
    nombre: str
    nombre_legal: Optional[str] = None
    ruc: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    moneda_local_id: Optional[uuid.UUID] = None


class EmpresaResponse(BaseModel):
    id: uuid.UUID
    nombre: str
    nombre_legal: Optional[str]
    ruc: Optional[str]
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UsuarioCreate(BaseModel):
    empresa_id: uuid.UUID
    username: str
    email: str
    password: str
    nombre_completo: str


class UsuarioResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    nombre_completo: str
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CuentaContableCreate(BaseModel):
    codigo: str
    nombre: str
    tipo: str
    nivel: int
    padre_id: Optional[uuid.UUID] = None
    acepta_datos: bool = False
    moneda_id: Optional[uuid.UUID] = None


class CuentaContableResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    tipo: str
    nivel: int
    padre_id: Optional[uuid.UUID]
    acepta_datos: bool

    class Config:
        from_attributes = True


class ProductoCreate(BaseModel):
    codigo: Optional[str] = None
    nombre: str
    categoria_id: Optional[uuid.UUID] = None
    unidad_medida: str = "UNIDAD"
    precio_venta: float = 0
    stock_minimo: float = 0
    aplica_iva: bool = True
    cuenta_compra_id: Optional[uuid.UUID] = None
    cuenta_venta_id: Optional[uuid.UUID] = None
    cuenta_inventario_id: Optional[uuid.UUID] = None


class ProductoResponse(BaseModel):
    id: uuid.UUID
    codigo: Optional[str]
    nombre: str
    costo_promedio: float
    precio_venta: float
    stock_actual: float
    aplica_iva: bool
    cuenta_compra_id: Optional[uuid.UUID]
    cuenta_venta_id: Optional[uuid.UUID]
    cuenta_inventario_id: Optional[uuid.UUID]

    class Config:
        from_attributes = True


class ClienteCreate(BaseModel):
    codigo: Optional[str] = None
    nombre: str
    ruc: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    limite_credito: float = 0
    categoria_id: Optional[uuid.UUID] = None


class ClienteResponse(BaseModel):
    id: uuid.UUID
    codigo: Optional[str]
    nombre: str
    saldo: float
    categoria_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class AsientoCreate(BaseModel):
    fecha: date
    periodo_id: uuid.UUID
    tipo: str = "DIARIO"
    concepto: str
    lineas: list["AsientoLineaCreate"]


class AsientoLineaCreate(BaseModel):
    cuenta_id: uuid.UUID
    centro_costo_id: Optional[uuid.UUID] = None
    descripcion: Optional[str] = None
    debe_local: float = 0
    haber_local: float = 0
    debe_dolar: float = 0
    haber_dolar: float = 0


class AsientoResponse(BaseModel):
    id: uuid.UUID
    numero: str
    fecha: date
    tipo: str
    concepto: str
    reversado: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MovimientoCajaCreate(BaseModel):
    caja_id: uuid.UUID
    fecha: date
    tipo: str
    concepto: str
    entrada: float = 0
    salida: float = 0


class CondicionPagoCreate(BaseModel):
    codigo: str
    nombre: str
    dias_neto: int = 0
    descuento_contado: float = 0


class CondicionPagoResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    dias_neto: int
    descuento_contado: float
    activa: bool

    class Config:
        from_attributes = True


class TipoCambioHistCreate(BaseModel):
    moneda_id: uuid.UUID
    fecha: date
    tasa_compra: float
    tasa_venta: float


class TipoCambioHistResponse(BaseModel):
    id: uuid.UUID
    moneda_id: uuid.UUID
    fecha: date
    tasa_compra: float
    tasa_venta: float
    created_at: datetime

    class Config:
        from_attributes = True


class CondicionPagoUpdate(CondicionPagoCreate):
    pass


class MonedaCreate(BaseModel):
    codigo: str
    nombre: str
    simbolo: str
    es_local: bool = False
    tasa_cambio: float = 1.0


class MonedaResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    simbolo: str
    es_local: bool
    activa: bool

    class Config:
        from_attributes = True


class MonedaUpdate(BaseModel):
    nombre: Optional[str] = None
    simbolo: Optional[str] = None
    es_local: Optional[bool] = None
    activa: Optional[bool] = None


class ImpuestoCreate(BaseModel):
    codigo: str
    nombre: str
    porcentaje: float
    tipo: str = "IVA"


class ImpuestoUpdate(BaseModel):
    nombre: Optional[str] = None
    porcentaje: Optional[float] = None
    activo: Optional[bool] = None


class ImpuestoResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    porcentaje: float
    tipo: str
    activo: bool

    class Config:
        from_attributes = True


class ParametroCreate(BaseModel):
    codigo: str
    nombre: str
    valor_defecto: Optional[str] = None
    tipo_dato: str = "TEXTO"
    modulo: Optional[str] = None


class ParametroUpdate(BaseModel):
    valor_defecto: Optional[str] = None
    descripcion: Optional[str] = None


class ParametroResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    valor_defecto: Optional[str]
    tipo_dato: str
    modulo: Optional[str]

    class Config:
        from_attributes = True


class NumeracionCreate(BaseModel):
    serie: str
    nombre: str
    tipo_documento: str
    mascara: Optional[str] = '{SERIE}-{NUMERO}'
    correlativo_inicial: int = 1
    prefijo: Optional[str] = None
    sufijo: Optional[str] = None
    digitos: int = 6
    reinicio: str = 'NUNCA'
    numeracion_manual: bool = False


class NumeracionUpdate(BaseModel):
    nombre: Optional[str] = None
    mascara: Optional[str] = None
    correlativo_actual: Optional[int] = None
    activa: Optional[bool] = None


class NumeracionResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    serie: str
    nombre: str
    tipo_documento: str
    mascara: str
    correlativo_actual: int
    prefijo: Optional[str]
    sufijo: Optional[str]
    digitos: int
    reinicio: str
    activa: bool

    class Config:
        from_attributes = True


class TipoAsientoCreate(BaseModel):
    codigo: str
    nombre: str
    modulo: str = 'CONTABILIDAD'
    naturaleza: str = 'AMBOS'


class TipoAsientoResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    modulo: str
    naturaleza: str
    activo: bool

    class Config:
        from_attributes = True


class PlantillaLineaCreate(BaseModel):
    orden: int = 0
    cuenta_id: uuid.UUID
    debe: bool = True
    formula: Optional[str] = None
    porcentaje: Optional[float] = None


class PlantillaCreate(BaseModel):
    codigo: str
    nombre: str
    tipo_asiento_id: uuid.UUID
    lineas: list[PlantillaLineaCreate] = []


class PlantillaResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    tipo_asiento_id: uuid.UUID

    class Config:
        from_attributes = True


class JournalTemplateCreate(BaseModel):
    codigo: str
    nombre: str
    tipo_asiento_id: uuid.UUID
    es_defecto: bool = False


class JournalTemplateUpdate(BaseModel):
    nombre: Optional[str] = None
    es_defecto: Optional[bool] = None


class JournalTypeCreate(BaseModel):
    codigo: str
    nombre: str
    modulo: str = 'CONTABILIDAD'
    naturaleza: str = 'AMBOS'
    prefijo: str = 'CG'
    digitos: int = 8


class JournalTypeUpdate(BaseModel):
    nombre: Optional[str] = None
    modulo: Optional[str] = None
    naturaleza: Optional[str] = None
    activo: Optional[bool] = None
    prefijo: Optional[str] = None
    digitos: Optional[int] = None


class JournalTypeResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    modulo: str
    naturaleza: str
    activo: bool
    prefijo: str
    digitos: int

    class Config:
        from_attributes = True


class JournalTemplateLineCreate(BaseModel):
    orden: int = 0
    cuenta_id: uuid.UUID
    debe: bool = True
    formula: Optional[str] = None
    porcentaje: Optional[float] = None


class JournalTemplateResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    tipo_asiento_id: uuid.UUID
    es_defecto: bool
    activo: bool

    class Config:
        from_attributes = True


class JournalTemplateLineResponse(BaseModel):
    id: uuid.UUID
    orden: int
    cuenta_id: uuid.UUID
    debe: bool
    formula: Optional[str]
    porcentaje: Optional[float]

    class Config:
        from_attributes = True


class CentroCostoCreate(BaseModel):
    codigo: str
    nombre: str
    padre_id: Optional[uuid.UUID] = None


class CentroCostoResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    padre_id: Optional[uuid.UUID]
    activo: bool

    class Config:
        from_attributes = True
