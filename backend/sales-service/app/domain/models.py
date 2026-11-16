from dataclasses import dataclass, field
from datetime import datetime


CONSUMIDOR_FINAL_ID = 0
CONSUMIDOR_FINAL_NOMBRE = "Consumidor final"

# Todos los productos se venden por unidad; los precios son pesos colombianos sin decimales.
CANTIDAD_MAXIMA_POR_LINEA = 500

METODOS_PAGO = {
    "efectivo": "Efectivo",
    "nequi": "Nequi",
    "daviplata": "Daviplata",
    "tarjeta_debito": "Tarjeta débito",
    "tarjeta_credito": "Tarjeta crédito",
    "transferencia": "Transferencia",
}

TIPOS_DOCUMENTO = {
    "CC": "Cédula de ciudadanía",
    "CE": "Cédula de extranjería",
    "TI": "Tarjeta de identidad",
    "PP": "Pasaporte",
    "NIT": "NIT",
}


@dataclass
class Customer:
    id: int | None
    nombre: str
    tipo_documento: str | None = None
    documento: str | None = None
    telefono: str | None = None
    correo: str | None = None
    direccion: str | None = None
    barrio: str | None = None
    ciudad: str | None = None
    creado_en: datetime | None = None


@dataclass
class ProductInfo:
    """Lo que sales necesita saber de un producto. Viene de catalog-service."""

    id: int
    nombre: str
    categoria: str
    precio: int
    activo: bool


@dataclass
class OrderLine:
    id: int | None
    id_producto: int
    nombre_producto: str
    categoria: str
    cantidad: int            # unidades
    precio_unitario: int     # precio del producto en el momento de la venta
    subtotal: int


@dataclass
class Order:
    id: int | None
    id_cliente: int
    cajero: str | None
    fecha: datetime
    metodo_pago: str
    total: int
    lineas: list[OrderLine] = field(default_factory=list)
    cliente_nombre: str | None = None


@dataclass
class SalesSummary:
    ingresos_totales: int
    numero_ventas: int
    unidades_vendidas: int
    clientes_activos: int


@dataclass
class WeekdaySales:
    numero_dia: int          # 1 = lunes ... 7 = domingo
    ventas: int
    ingresos: int


@dataclass
class HourSales:
    hora: int                # 0 ... 23
    ventas: int
    ingresos: int


@dataclass
class MonthSales:
    mes: str                 # "AAAA-MM"
    ventas: int
    ingresos: int


@dataclass
class GroupSales:
    """Ventas agrupadas por una etiqueta (categoría o método de pago)."""

    clave: str
    ventas: int
    unidades: int
    ingresos: int


@dataclass
class ProductSales:
    id_producto: int
    nombre: str
    categoria: str
    cantidad: int
    ingresos: int


@dataclass
class CustomerSales:
    id_cliente: int
    nombre: str
    compras: int
    gasto: int
