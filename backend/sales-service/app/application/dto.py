from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


MetodoPago = Literal["efectivo", "nequi", "daviplata", "tarjeta_debito", "tarjeta_credito", "transferencia"]


class CreateCustomerDTO(BaseModel):
    nombre: str = Field(description="Nombre completo")
    tipo_documento: str | None = Field(default=None, description="CC, CE, TI, PP o NIT (por defecto CC)")
    documento: str | None = None
    telefono: str | None = Field(default=None, description="Celular (3xx) o fijo con indicativo (60x)")
    correo: str | None = None
    direccion: str | None = None
    barrio: str | None = None
    ciudad: str | None = None


class PatchCustomerDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    tipo_documento: str | None = None
    documento: str | None = None
    telefono: str | None = None
    correo: str | None = None
    direccion: str | None = None
    barrio: str | None = None
    ciudad: str | None = None


class CustomerSummaryDTO(BaseModel):
    """Cliente resumido, como aparece dentro de una venta."""

    id_cliente: int
    nombre: str


class CustomerResponseDTO(BaseModel):
    id_cliente: int
    nombre: str
    tipo_documento: str | None
    documento: str | None
    telefono: str | None
    correo: str | None
    direccion: str | None
    barrio: str | None
    ciudad: str | None
    creado_en: datetime | None


class CustomerPageDTO(BaseModel):
    total: int
    clientes: list[CustomerResponseDTO]


class OrderLineDTO(BaseModel):
    id_producto: int
    cantidad: float = Field(description="Unidades (número entero)")


class CreateOrderDTO(BaseModel):
    id_cliente: int = Field(default=0, description="0 = Consumidor final")
    metodo_pago: MetodoPago = "efectivo"
    lineas: list[OrderLineDTO] = Field(min_length=1)


class OrderLineResponseDTO(BaseModel):
    id_producto: int
    producto: str
    categoria: str
    cantidad: int
    precio_unitario: int
    subtotal: int


class OrderResponseDTO(BaseModel):
    id_venta: int
    fecha: datetime
    cliente: CustomerSummaryDTO
    cajero: str | None
    metodo_pago: str
    lineas: list[OrderLineResponseDTO]
    total: int


class SummaryDTO(BaseModel):
    ingresos_totales: int
    numero_ventas: int
    unidades_vendidas: int
    ticket_promedio: int
    clientes_activos: int


class WeekdayDTO(BaseModel):
    numero_dia: int
    dia: str
    ventas: int
    ingresos: int


class HourDTO(BaseModel):
    hora: int
    etiqueta: str
    ventas: int
    ingresos: int


class MonthDTO(BaseModel):
    mes: str
    ventas: int
    ingresos: int


class CategoryDTO(BaseModel):
    categoria: str
    ventas: int
    unidades: int
    ingresos: int


class PaymentDTO(BaseModel):
    metodo_pago: str
    nombre: str
    ventas: int
    ingresos: int


class TopProductDTO(BaseModel):
    id_producto: int
    producto: str
    categoria: str
    cantidad: int
    ingresos: int


class TopCustomerDTO(BaseModel):
    id_cliente: int
    nombre: str
    compras: int
    gasto: int


class ProductWithoutSalesDTO(BaseModel):
    id_producto: int
    nombre: str
    categoria: str
    precio: int
