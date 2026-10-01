from datetime import datetime

from pydantic import BaseModel, Field


class CreateCustomerDTO(BaseModel):
    nombre: str


class CustomerResponseDTO(BaseModel):
    id_cliente: int
    nombre: str


class OrderLineDTO(BaseModel):
    id_producto: int
    cantidad: float = Field(description="Unidades, o gramos si el producto se vende por peso")


class CreateOrderDTO(BaseModel):
    id_cliente: int = Field(default=0, description="0 = Consumidor final")
    lineas: list[OrderLineDTO] = Field(min_length=1)


class OrderLineResponseDTO(BaseModel):
    id_producto: int
    producto: str
    tipo_venta: str
    cantidad: float = Field(description="Unidades, o kilogramos si el producto se vende por peso")
    precio_unitario: float
    subtotal: float


class OrderResponseDTO(BaseModel):
    id_venta: int
    fecha: datetime
    cliente: CustomerResponseDTO
    cajero: str | None
    lineas: list[OrderLineResponseDTO]
    total: float


class SummaryDTO(BaseModel):
    ingresos_totales: float
    numero_ventas: int
    unidades_vendidas: float
    kg_vendidos: float
    ticket_promedio: float
    clientes_activos: int


class WeekdayDTO(BaseModel):
    numero_dia: int
    dia: str
    ventas: int
    ingresos: float


class TopProductDTO(BaseModel):
    id_producto: int
    producto: str
    tipo_venta: str
    cantidad: float
    ingresos: float


class TopCustomerDTO(BaseModel):
    id_cliente: int
    nombre: str
    compras: int
    gasto: float


class ProductWithoutSalesDTO(BaseModel):
    id_producto: int
    nombre: str
    precio: float
    tipo_venta: str
