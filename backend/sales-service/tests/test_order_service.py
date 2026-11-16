"""Pruebas unitarias de las reglas de ventas y clientes.

Usan repositorios y un catálogo falsos en memoria: no hay base de datos ni HTTP.
"""

import pytest

from app.domain.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.domain.models import Customer, Order
from app.domain.repositories import CustomerRepository, OrderRepository
from app.domain.services import CustomerData, CustomerService, LineRequest, OrderService
from tests.conftest import FakeCatalog


class InMemoryCustomers(CustomerRepository):

    def __init__(self):
        self.customers = {
            0: Customer(0, "Consumidor final"),
            17: Customer(17, "Rosa Giraldo Velasco", "CC", "67000190", "3216271957"),
        }

    def create(self, customer):
        customer.id = max(self.customers) + 1
        self.customers[customer.id] = customer
        return customer

    def update(self, customer):
        self.customers[customer.id] = customer
        return customer

    def get_by_id(self, customer_id):
        return self.customers.get(customer_id)

    def get_by_document(self, documento):
        return next((c for c in self.customers.values() if c.documento == documento), None)

    def search(self, text, limit, offset=0):
        return [c for c in self.customers.values() if text.lower() in c.nombre.lower()][offset:offset + limit]

    def count(self, text=""):
        return len(self.search(text, 10_000))


class InMemoryOrders(OrderRepository):

    def __init__(self):
        self.saved: list[Order] = []

    def create(self, order):
        order.id = len(self.saved) + 1
        self.saved.append(order)
        return order

    def get_by_id(self, order_id):
        return next((o for o in self.saved if o.id == order_id), None)

    def list_all(self, desde=None, hasta=None, cajero=None, id_cliente=None, limit=None, metodo_pago=None):
        return [o for o in self.saved if cajero is None or o.cajero == cajero]


@pytest.fixture
def orders():
    return InMemoryOrders()


@pytest.fixture
def service(orders):
    return OrderService(orders, InMemoryCustomers(), FakeCatalog())


@pytest.fixture
def customers():
    return CustomerService(InMemoryCustomers())


# ---------- Ventas ----------

def test_venta_con_varios_productos_rn16(service):
    order = service.create_order(17, [LineRequest(1, 4), LineRequest(68, 2)], "mcastillo")

    assert [l.subtotal for l in order.lineas] == [12800, 6000]
    assert order.total == 18800
    assert isinstance(order.total, int)


def test_copia_nombre_categoria_y_precio_del_producto_rn06(service):
    linea = service.create_order(0, [LineRequest(25, 1)], "mcastillo").lineas[0]

    assert linea.nombre_producto == "Pastel de pollo"
    assert linea.categoria == "Hojaldres"
    assert linea.precio_unitario == 6000


def test_metodo_de_pago_por_defecto_es_efectivo(service):
    assert service.create_order(0, [LineRequest(9, 1)], "mcastillo").metodo_pago == "efectivo"


def test_metodo_de_pago_nequi(service):
    assert service.create_order(0, [LineRequest(9, 1)], "mcastillo", "nequi").metodo_pago == "nequi"


def test_metodo_de_pago_invalido(service):
    with pytest.raises(BusinessRuleError, match="pago"):
        service.create_order(0, [LineRequest(9, 1)], "mcastillo", "bitcoin")


def test_guarda_cajero_y_fecha_del_sistema_rn09_rn17(service):
    order = service.create_order(0, [LineRequest(9, 1)], "lvalencia")

    assert order.cajero == "lvalencia"
    assert order.fecha is not None


def test_consumidor_final_rn07(service):
    assert service.create_order(0, [LineRequest(9, 1)], "cajero").cliente_nombre == "Consumidor final"


def test_cliente_inexistente_rn07(service):
    with pytest.raises(NotFoundError):
        service.create_order(999, [LineRequest(9, 1)], "cajero")


def test_venta_sin_productos_rn14(service):
    with pytest.raises(BusinessRuleError):
        service.create_order(0, [], "cajero")


def test_producto_inexistente_rn01(service):
    with pytest.raises(NotFoundError):
        service.create_order(0, [LineRequest(9999, 1)], "cajero")


def test_producto_inactivo_rn01(service):
    with pytest.raises(BusinessRuleError, match="no está disponible"):
        service.create_order(0, [LineRequest(57, 1)], "cajero")


@pytest.mark.parametrize("cantidad", [0, -3])
def test_cantidad_mayor_que_cero_rn02(service, cantidad):
    with pytest.raises(BusinessRuleError):
        service.create_order(0, [LineRequest(9, cantidad)], "cajero")


def test_todo_se_vende_por_unidad_rn03(service):
    with pytest.raises(BusinessRuleError, match="entero"):
        service.create_order(0, [LineRequest(1, 1.5)], "cajero")


def test_cantidad_maxima_por_linea(service):
    with pytest.raises(BusinessRuleError):
        service.create_order(0, [LineRequest(86, 501)], "cajero")


def test_treinta_huevos(service):
    order = service.create_order(0, [LineRequest(86, 30)], "cajero")
    assert order.lineas[0].cantidad == 30
    assert order.total == 19500


def test_producto_repetido_en_dos_lineas(service):
    with pytest.raises(BusinessRuleError, match="repetido"):
        service.create_order(0, [LineRequest(1, 2), LineRequest(1, 3)], "cajero")


def test_todo_o_nada_rn15(service, orders):
    with pytest.raises(BusinessRuleError):
        service.create_order(17, [LineRequest(1, 1), LineRequest(68, 2), LineRequest(57, 1)], "cajero")

    assert orders.saved == []


# ---------- Clientes ----------

def test_crear_cliente_completo(customers):
    c = customers.create_customer(CustomerData(
        nombre="  victoria   herrera castro ",
        documento="1.144.123.456",
        telefono="+57 318 555 1234",
        correo="Victoria@Correo.COM",
        direccion="Calle 5 # 38-20",
        barrio="San Fernando",
        ciudad="Cali",
    ))

    assert c.id == 18
    assert c.nombre == "Victoria Herrera Castro"
    assert c.tipo_documento == "CC"
    assert c.documento == "1144123456"
    assert c.telefono == "3185551234"
    assert c.correo == "victoria@correo.com"
    assert c.creado_en is not None


def test_crear_cliente_solo_con_nombre_rn08(customers):
    c = customers.create_customer(CustomerData(nombre="María López"))

    assert c.nombre == "María López"
    assert c.documento is None and c.tipo_documento is None


@pytest.mark.parametrize("nombre", ["   ", "Al", "Consumidor Final"])
def test_nombre_invalido_rn08(customers, nombre):
    with pytest.raises(BusinessRuleError):
        customers.create_customer(CustomerData(nombre=nombre))


def test_documento_repetido_409(customers):
    with pytest.raises(ConflictError, match="Rosa Giraldo"):
        customers.create_customer(CustomerData(nombre="Otra Persona", documento="67.000.190"))


@pytest.mark.parametrize("documento", ["12ab45", "123", "123456789012"])
def test_documento_invalido(customers, documento):
    with pytest.raises(BusinessRuleError):
        customers.create_customer(CustomerData(nombre="Ana Pérez", documento=documento))


def test_tipo_documento_invalido(customers):
    with pytest.raises(BusinessRuleError):
        customers.create_customer(CustomerData(nombre="Ana Pérez", tipo_documento="XX", documento="1234567"))


@pytest.mark.parametrize("telefono", ["12345", "2125551234", "31855512345"])
def test_telefono_invalido(customers, telefono):
    with pytest.raises(BusinessRuleError):
        customers.create_customer(CustomerData(nombre="Ana Pérez", telefono=telefono))


def test_telefono_fijo_con_indicativo(customers):
    assert customers.create_customer(CustomerData(nombre="Ana Pérez", telefono="602 555 1234")).telefono == "6025551234"


def test_correo_invalido(customers):
    with pytest.raises(BusinessRuleError):
        customers.create_customer(CustomerData(nombre="Ana Pérez", correo="ana.perez@"))


def test_editar_cliente_conserva_su_documento(customers):
    c = customers.update_customer(17, CustomerData(telefono="3001112233", documento="67000190"))

    assert c.telefono == "3001112233"
    assert c.nombre == "Rosa Giraldo Velasco"


def test_consumidor_final_no_se_edita(customers):
    with pytest.raises(BusinessRuleError):
        customers.update_customer(0, CustomerData(nombre="Otro"))
