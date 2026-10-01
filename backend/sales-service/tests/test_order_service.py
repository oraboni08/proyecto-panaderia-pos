"""Pruebas unitarias de las reglas de ventas y clientes.

Usan repositorios y un catálogo falsos en memoria: no hay base de datos ni HTTP.
"""

import pytest

from app.domain.exceptions import BusinessRuleError, NotFoundError
from app.domain.models import Customer, Order
from app.domain.repositories import CustomerRepository, OrderRepository
from app.domain.services import CustomerService, LineRequest, OrderService
from tests.conftest import FakeCatalog


class InMemoryCustomers(CustomerRepository):

    def __init__(self):
        self.customers = {0: Customer(0, "Consumidor final"), 17: Customer(17, "Cliente 17")}

    def create(self, customer):
        customer.id = max(self.customers) + 1
        self.customers[customer.id] = customer
        return customer

    def get_by_id(self, customer_id):
        return self.customers.get(customer_id)

    def search(self, text, limit):
        return [c for c in self.customers.values() if text.lower() in c.nombre.lower()][:limit]


class InMemoryOrders(OrderRepository):

    def __init__(self):
        self.saved: list[Order] = []

    def create(self, order):
        order.id = len(self.saved) + 1
        self.saved.append(order)
        return order

    def get_by_id(self, order_id):
        return next((o for o in self.saved if o.id == order_id), None)

    def list_all(self, desde=None, hasta=None, cajero=None):
        return [o for o in self.saved if cajero is None or o.cajero == cajero]


@pytest.fixture
def orders():
    return InMemoryOrders()


@pytest.fixture
def service(orders):
    return OrderService(orders, InMemoryCustomers(), FakeCatalog())


def test_venta_con_varios_productos_rn16(service):
    order = service.create_order(
        17,
        [LineRequest(16, 2), LineRequest(35, 350)],
        "cajero",
    )

    assert [l.subtotal for l in order.lineas] == [1.20, 2.03]
    assert order.total == 3.23
    assert order.total == round(sum(l.subtotal for l in order.lineas), 2)


def test_producto_por_peso_se_guarda_en_kg_rn04(service):
    order = service.create_order(0, [LineRequest(26, 1239)], "cajero")

    linea = order.lineas[0]
    assert linea.cantidad == 1.239
    assert linea.subtotal == 19.82  # 16.00 €/kg × 1,239 kg


def test_copia_nombre_y_precio_del_producto_rn06(service):
    order = service.create_order(0, [LineRequest(4, 1)], "cajero")

    linea = order.lineas[0]
    assert linea.nombre_producto == "Pan"
    assert linea.precio_unitario == 1.80


def test_guarda_cajero_y_fecha_del_sistema_rn09_rn17(service):
    order = service.create_order(0, [LineRequest(4, 1)], "juan")

    assert order.cajero == "juan"
    assert order.fecha is not None


def test_consumidor_final_rn07(service):
    order = service.create_order(0, [LineRequest(4, 1)], "cajero")
    assert order.cliente_nombre == "Consumidor final"


def test_cliente_inexistente_rn07(service):
    with pytest.raises(NotFoundError):
        service.create_order(999, [LineRequest(4, 1)], "cajero")


def test_venta_sin_productos_rn14(service):
    with pytest.raises(BusinessRuleError):
        service.create_order(0, [], "cajero")


def test_producto_inexistente_rn01(service):
    with pytest.raises(NotFoundError):
        service.create_order(0, [LineRequest(9999, 1)], "cajero")


def test_producto_inactivo_rn01(service):
    with pytest.raises(BusinessRuleError):
        service.create_order(0, [LineRequest(50, 1)], "cajero")


@pytest.mark.parametrize("cantidad", [0, -3])
def test_cantidad_mayor_que_cero_rn02(service, cantidad):
    with pytest.raises(BusinessRuleError):
        service.create_order(0, [LineRequest(4, cantidad)], "cajero")


def test_unidades_enteras_rn03(service):
    with pytest.raises(BusinessRuleError):
        service.create_order(0, [LineRequest(38, 0.5)], "cajero")


def test_dos_docenas_de_huevos_rn03(service):
    order = service.create_order(0, [LineRequest(38, 2)], "cajero")
    assert order.lineas[0].cantidad == 2
    assert order.total == 4.20


def test_todo_o_nada_rn15(service, orders):
    with pytest.raises(BusinessRuleError):
        service.create_order(
            17,
            [LineRequest(4, 1), LineRequest(16, 2), LineRequest(50, 1)],
            "cajero",
        )

    assert orders.saved == []


def test_crear_cliente_solo_con_nombre_rn08():
    customers = CustomerService(InMemoryCustomers())

    c = customers.create_customer("  María   López ")

    assert c.id == 18
    assert c.nombre == "María López"


def test_cliente_sin_nombre_rn08():
    with pytest.raises(BusinessRuleError):
        CustomerService(InMemoryCustomers()).create_customer("   ")
