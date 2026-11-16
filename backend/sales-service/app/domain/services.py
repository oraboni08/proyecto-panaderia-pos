import re
from dataclasses import dataclass
from datetime import date, datetime

from app.domain.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.domain.models import (
    CANTIDAD_MAXIMA_POR_LINEA,
    CONSUMIDOR_FINAL_ID,
    METODOS_PAGO,
    TIPOS_DOCUMENTO,
    Customer,
    CustomerSales,
    GroupSales,
    HourSales,
    MonthSales,
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


CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")


@dataclass
class LineRequest:
    id_producto: int
    cantidad: float          # unidades (debe ser entero)


@dataclass
class CustomerData:
    """Datos que llegan para crear o editar un cliente. None = no se envió."""

    nombre: str | None = None
    tipo_documento: str | None = None
    documento: str | None = None
    telefono: str | None = None
    correo: str | None = None
    direccion: str | None = None
    barrio: str | None = None
    ciudad: str | None = None


def _clean(texto: str | None) -> str | None:
    if texto is None:
        return None
    texto = " ".join(texto.split())
    return texto or None


class CustomerService:

    def __init__(self, customers: CustomerRepository):
        self.customers = customers

    def get_customer(self, customer_id: int) -> Customer:

        customer = self.customers.get_by_id(customer_id)

        if customer is None:
            raise NotFoundError("Cliente no encontrado")

        return customer

    def search_customers(self, text: str = "", limit: int = 20, offset: int = 0) -> list[Customer]:
        return self.customers.search(text.strip(), limit, offset)

    def count_customers(self, text: str = "") -> int:
        return self.customers.count(text.strip())

    def create_customer(self, data: CustomerData) -> Customer:

        customer = self._validate(Customer(id=None, nombre=data.nombre or ""), data)
        customer.creado_en = datetime.now().replace(microsecond=0)

        return self.customers.create(customer)

    def update_customer(self, customer_id: int, data: CustomerData) -> Customer:

        if customer_id == CONSUMIDOR_FINAL_ID:
            raise BusinessRuleError("El Consumidor final no se puede modificar")

        customer = self.get_customer(customer_id)

        return self.customers.update(self._validate(customer, data))

    def _validate(self, customer: Customer, data: CustomerData) -> Customer:
        """Aplica los campos enviados sobre el cliente y valida el resultado (RN05)."""

        for campo in ("nombre", "tipo_documento", "documento", "telefono", "correo", "direccion", "barrio", "ciudad"):
            valor = getattr(data, campo)
            if valor is not None:
                setattr(customer, campo, _clean(valor))

        if not customer.nombre or len(customer.nombre) < 3:
            raise BusinessRuleError("El nombre del cliente debe tener al menos 3 caracteres")

        if customer.nombre.lower() == "consumidor final":
            raise BusinessRuleError("Ese nombre está reservado")

        customer.nombre = customer.nombre.title() if customer.nombre.isupper() or customer.nombre.islower() else customer.nombre

        if customer.documento:
            customer.documento = customer.documento.replace(".", "").replace(" ", "")
            customer.tipo_documento = (customer.tipo_documento or "CC").upper()

            if customer.tipo_documento not in TIPOS_DOCUMENTO:
                raise BusinessRuleError(f"Tipo de documento inválido. Opciones: {', '.join(TIPOS_DOCUMENTO)}")

            if customer.tipo_documento == "PP":
                valido = re.fullmatch(r"[A-Za-z0-9]{5,15}", customer.documento)
            else:
                valido = re.fullmatch(r"\d{5,11}(-\d)?", customer.documento)

            if not valido:
                raise BusinessRuleError("El documento no es válido: usa solo números (entre 5 y 11 dígitos)")

            existente = self.customers.get_by_document(customer.documento)

            if existente is not None and existente.id != customer.id:
                raise ConflictError(f"Ya existe un cliente con el documento {customer.documento}: {existente.nombre}")
        else:
            customer.tipo_documento = None

        if customer.telefono:
            customer.telefono = re.sub(r"[\s\-()+]", "", customer.telefono)
            if customer.telefono.startswith("57") and len(customer.telefono) == 12:
                customer.telefono = customer.telefono[2:]

            # Celular colombiano (3xx xxx xxxx) o fijo con indicativo (60x xxx xxxx).
            if not re.fullmatch(r"(3\d{9}|60\d{8})", customer.telefono):
                raise BusinessRuleError("El teléfono debe ser un celular de 10 dígitos (3xx) o un fijo con indicativo (60x)")

        if customer.correo:
            customer.correo = customer.correo.lower()
            if not CORREO.match(customer.correo):
                raise BusinessRuleError("El correo electrónico no es válido")

        return customer


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
        metodo_pago: str = "efectivo",
    ) -> Order:

        if not lineas:
            raise BusinessRuleError("La venta debe tener al menos un producto")

        if metodo_pago not in METODOS_PAGO:
            raise BusinessRuleError(f"Método de pago inválido. Opciones: {', '.join(METODOS_PAGO)}")

        if len({l.id_producto for l in lineas}) != len(lineas):
            raise BusinessRuleError("Un producto aparece repetido: agrúpalo en una sola línea")

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
            metodo_pago=metodo_pago,
            total=sum(l.subtotal for l in order_lines),
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
        id_cliente: int | None = None,
        limit: int | None = None,
        metodo_pago: str | None = None,
    ) -> list[Order]:
        return self.orders.list_all(desde, hasta, cajero, id_cliente, limit, metodo_pago)

    def _build_line(self, linea: LineRequest) -> OrderLine:

        product = self.catalog.get_product(linea.id_producto)

        if product is None:
            raise NotFoundError(f"El producto {linea.id_producto} no existe")

        if not product.activo:
            raise BusinessRuleError(f"El producto '{product.nombre}' no está disponible para la venta")

        if linea.cantidad <= 0:
            raise BusinessRuleError(f"La cantidad de '{product.nombre}' debe ser mayor que 0")

        # Todo se vende por unidad (RN03).
        if linea.cantidad != int(linea.cantidad):
            raise BusinessRuleError(f"La cantidad de '{product.nombre}' debe ser un número entero de unidades")

        cantidad = int(linea.cantidad)

        if cantidad > CANTIDAD_MAXIMA_POR_LINEA:
            raise BusinessRuleError(
                f"La cantidad de '{product.nombre}' no puede superar {CANTIDAD_MAXIMA_POR_LINEA} unidades"
            )

        precio = int(product.precio)

        return OrderLine(
            id=None,
            id_producto=product.id,
            nombre_producto=product.nombre,
            categoria=product.categoria,
            cantidad=cantidad,
            precio_unitario=precio,
            subtotal=precio * cantidad,
        )


@dataclass
class DashboardSummary:
    ingresos_totales: int
    numero_ventas: int
    unidades_vendidas: int
    ticket_promedio: int
    clientes_activos: int


class MetricsService:

    def __init__(self, metrics: MetricsRepository, catalog: ProductCatalog | None = None):
        self.metrics = metrics
        self.catalog = catalog

    def summary(self, desde: date | None = None, hasta: date | None = None) -> DashboardSummary:

        s: SalesSummary = self.metrics.summary(desde, hasta)

        ticket = round(s.ingresos_totales / s.numero_ventas) if s.numero_ventas else 0

        return DashboardSummary(
            ingresos_totales=s.ingresos_totales,
            numero_ventas=s.numero_ventas,
            unidades_vendidas=s.unidades_vendidas,
            ticket_promedio=ticket,
            clientes_activos=s.clientes_activos,
        )

    def sales_by_weekday(self, desde: date | None = None, hasta: date | None = None) -> list[WeekdaySales]:

        por_dia = {d.numero_dia: d for d in self.metrics.sales_by_weekday(desde, hasta)}

        return [
            por_dia.get(dia, WeekdaySales(numero_dia=dia, ventas=0, ingresos=0))
            for dia in range(1, 8)
        ]

    def sales_by_hour(self, desde: date | None = None, hasta: date | None = None) -> list[HourSales]:

        por_hora = {h.hora: h for h in self.metrics.sales_by_hour(desde, hasta)}

        # Horario de la panadería: 6:00 a 21:00 (se incluye cualquier hora con ventas).
        horas = sorted(set(range(6, 21)) | set(por_hora))

        return [por_hora.get(h, HourSales(hora=h, ventas=0, ingresos=0)) for h in horas]

    def sales_by_month(self, desde: date | None = None, hasta: date | None = None) -> list[MonthSales]:
        return self.metrics.sales_by_month(desde, hasta)

    def sales_by_category(self, desde: date | None = None, hasta: date | None = None) -> list[GroupSales]:
        return sorted(self.metrics.sales_by_category(desde, hasta), key=lambda g: g.ingresos, reverse=True)

    def sales_by_payment(self, desde: date | None = None, hasta: date | None = None) -> list[GroupSales]:
        return sorted(self.metrics.sales_by_payment(desde, hasta), key=lambda g: g.ventas, reverse=True)

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
