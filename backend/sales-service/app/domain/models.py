from dataclasses import dataclass, field
from datetime import datetime


TIPO_UNIDAD = "unidad"
TIPO_PESO = "peso"

CONSUMIDOR_FINAL_ID = 0
CONSUMIDOR_FINAL_NOMBRE = "Consumidor final"


@dataclass
class Customer:
    id: int | None
    nombre: str
    creado_en: datetime | None = None


@dataclass
class ProductInfo:
    """Lo que sales necesita saber de un producto. Viene de catalog-service."""

    id: int
    nombre: str
    precio: float
    tipo_venta: str
    activo: bool


@dataclass
class OrderLine:
    id: int | None
    id_producto: int
    nombre_producto: str
    tipo_venta: str
    cantidad: float          # unidades, o kilogramos si el producto es por peso
    precio_unitario: float   # precio por unidad, o por kg
    subtotal: float


@dataclass
class Order:
    id: int | None
    id_cliente: int
    cajero: str | None       # None = venta histórica del dataset
    fecha: datetime
    total: float
    lineas: list[OrderLine] = field(default_factory=list)
    cliente_nombre: str | None = None


@dataclass
class SalesSummary:
    ingresos_totales: float
    numero_ventas: int
    unidades_vendidas: float
    kg_vendidos: float
    clientes_activos: int


@dataclass
class WeekdaySales:
    numero_dia: int          # 1 = lunes ... 7 = domingo
    ventas: int
    ingresos: float


@dataclass
class ProductSales:
    id_producto: int
    nombre: str
    tipo_venta: str
    cantidad: float
    ingresos: float


@dataclass
class CustomerSales:
    id_cliente: int
    nombre: str
    compras: int
    gasto: float
