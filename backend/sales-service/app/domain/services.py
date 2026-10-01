from dataclasses import dataclass
from datetime import date, datetime

from app.domain.exceptions import BusinessRuleError, NotFoundError
from app.domain.models import (
    CONSUMIDOR_FINAL_ID,
    TIPO_PESO,
    Customer,
    CustomerSales,
    Order,
    OrderLine,
    ProductInfo,
    ProductSales,
    SalesSummary,
    WeekdaySales,
)
from app.domain.repositories import (
    CustomerRepository,
    MetricsRepository,
    OrderRepository,
    ProductCatalog,
)


@dataclass
class LineRequest:
    id_producto: int
    cantidad: float          # unidades, o gramos si el producto es por peso


class CustomerService:

    def __init__(self, customers: CustomerRepository):
        self.customers = customers

    def get_customer(self, customer_id: int) -> Customer:

        customer = self.customers.get_by_id(customer_id)

        if customer is None:
            raise NotFoundError("Cliente no encontrado")

        return customer

    def search_customers(self, text: str = "", limit: int = 20) -> list[Customer]:
        return self.customers.search(text.strip(), limit)

    def create_customer(self, nombre: str) -> Customer:

        nombre = " ".join(nombre.split())

        if not nombre:
            raise BusinessRuleError("El nombre del cliente no puede estar vacío")

        return self.customers.create(
            Customer(id=None, nombre=nombre, creado_en=datetime.now())
        )


class OrderService:

    def __init__(
        self,
        orders: OrderRepository,
        customers: CustomerRepository,
        catalog: ProductCatalog,
    ):
        self.orders = orders
        self.customers = customers
        self.catalog = catalog

    def create_order(
        self,
        id_cliente: int,
        lineas: list[LineRequest],
        cajero: str,
    ) -> Order:

        if not lineas:
            raise BusinessRuleError("La venta debe tener al menos un producto")

        customer = self.customers.get_by_id(id_cliente)

        if customer is None:
            raise NotFoundError("Cliente no encontrado")

        # Se validan TODAS las líneas antes de guardar: si una falla, no se guarda nada (RN15).
        order_lines = [self._build_line(linea) for linea in lineas]

        order = Order(
            id=None,
            id_cliente=customer.id,
            cajero=cajero,
            fecha=datetime.now().replace(microsecond=0),
            total=round(sum(l.subtotal for l in order_lines), 2),
            lineas=order_lines,
            cliente_nombre=customer.nombre,
        )

        return self.orders.create(order)

    def get_order(self, order_id: int) -> Order:

        order = self.orders.get_by_id(order_id)

        if order is None:
            raise NotFoundError("Venta no encontrada")

        return order

    def list_orders(
        self,
        desde: date | None = None,
        hasta: date | None = None,
        cajero: str | None = None,
    ) -> list[Order]:
        return self.orders.list_all(desde, hasta, cajero)

    def _build_line(self, linea: LineRequest) -> OrderLine:

        product = self.catalog.get_product(linea.id_producto)

        if product is None:
            raise NotFoundError(f"El producto {linea.id_producto} no existe")

        if not product.activo:
            raise BusinessRuleError(f"El producto '{product.nombre}' no está disponible para la venta")

        if linea.cantidad <= 0:
            raise BusinessRuleError(f"La cantidad de '{product.nombre}' debe ser mayor que 0")

        if product.tipo_venta == TIPO_PESO:
            # El cajero ingresa gramos; se guarda en kg, igual que el dataset (RN04).
            cantidad = round(linea.cantidad / 1000, 3)
            if cantidad <= 0:
                raise BusinessRuleError(f"El peso de '{product.nombre}' debe ser de al menos 1 gramo")
        else:
            if linea.cantidad != int(linea.cantidad):
                raise BusinessRuleError(
                    f"'{product.nombre}' se vende por unidad: la cantidad debe ser un número entero"
                )
            cantidad = int(linea.cantidad)

        return OrderLine(
            id=None,
            id_producto=product.id,
            nombre_producto=product.nombre,
            tipo_venta=product.tipo_venta,
            cantidad=cantidad,
            precio_unitario=product.precio,
            subtotal=round(product.precio * cantidad, 2),
        )


@dataclass
class DashboardSummary:
    ingresos_totales: float
    numero_ventas: int
    unidades_vendidas: float
    kg_vendidos: float
    ticket_promedio: float
    clientes_activos: int


class MetricsService:

    def __init__(self, metrics: MetricsRepository, catalog: ProductCatalog | None = None):
        self.metrics = metrics
        self.catalog = catalog

    def summary(self, desde: date | None = None, hasta: date | None = None) -> DashboardSummary:

        s: SalesSummary = self.metrics.summary(desde, hasta)

        ticket = round(s.ingresos_totales / s.numero_ventas, 2) if s.numero_ventas else 0.0

        return DashboardSummary(
            ingresos_totales=round(s.ingresos_totales, 2),
            numero_ventas=s.numero_ventas,
            unidades_vendidas=s.unidades_vendidas,
            kg_vendidos=round(s.kg_vendidos, 3),
            ticket_promedio=ticket,
            clientes_activos=s.clientes_activos,
        )

    def sales_by_weekday(self, desde: date | None = None, hasta: date | None = None) -> list[WeekdaySales]:

        por_dia = {d.numero_dia: d for d in self.metrics.sales_by_weekday(desde, hasta)}

        return [
            por_dia.get(dia, WeekdaySales(numero_dia=dia, ventas=0, ingresos=0.0))
            for dia in range(1, 8)
        ]

    def top_products(
        self,
        desde: date | None = None,
        hasta: date | None = None,
        orden: str = "ingresos",
        limit: int = 10,
    ) -> list[ProductSales]:

        productos = self.metrics.product_sales(desde, hasta)
        productos.sort(key=lambda p: getattr(p, orden), reverse=True)

        return productos[:limit]

    def top_customers(
        self,
        desde: date | None = None,
        hasta: date | None = None,
        limit: int = 10,
    ) -> list[CustomerSales]:

        clientes = [
            c for c in self.metrics.customer_sales(desde, hasta)
            if c.id_cliente != CONSUMIDOR_FINAL_ID
        ]
        clientes.sort(key=lambda c: (c.compras, c.gasto), reverse=True)

        return clientes[:limit]

    def products_without_sales(
        self,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> list[ProductInfo]:

        vendidos = {p.id_producto for p in self.metrics.product_sales(desde, hasta)}

        return [
            p for p in self.catalog.list_products()
            if p.activo and p.id not in vendidos
        ]
