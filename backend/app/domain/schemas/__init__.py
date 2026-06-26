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


class ProductoResponse(BaseModel):
    id: uuid.UUID
    codigo: Optional[str]
    nombre: str
    costo_promedio: float
    precio_venta: float
    stock_actual: float

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


class ClienteResponse(BaseModel):
    id: uuid.UUID
    codigo: Optional[str]
    nombre: str
    saldo: float

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
    numero: int
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
