"""Pruebas unitarias de las reglas de negocio del catálogo.

Usan repositorios falsos en memoria: no hay base de datos ni HTTP.
"""

import pytest

from app.domain.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.domain.models import Product, ProductChange
from app.domain.repositories import ChangeRepository, ProductRepository
from app.domain.services import ProductService


class InMemoryProductRepository(ProductRepository):

    def __init__(self):
        self.products: dict[int, Product] = {}
        self.history: list[ProductChange] = []

    def create(self, product, change):
        product.id = len(self.products) + 1
        self.products[product.id] = Product(**vars(product))
        change.id_producto = product.id
        self.history.append(change)
        return Product(**vars(product))

    def get_by_id(self, product_id):
        p = self.products.get(product_id)
        return Product(**vars(p)) if p else None

    def get_by_name(self, nombre):
        for p in self.products.values():
            if p.nombre.lower() == nombre.lower():
                return Product(**vars(p))
        return None

    def list_all(self, activo=None):
        return [p for p in self.products.values() if activo is None or p.activo == activo]

    def update(self, product, changes):
        self.products[product.id] = Product(**vars(product))
        self.history.extend(changes)
        return Product(**vars(product))


class InMemoryChangeRepository(ChangeRepository):

    def __init__(self, products: InMemoryProductRepository):
        self.products = products

    def list_all(self, product_id=None):
        return [c for c in self.products.history if product_id is None or c.id_producto == product_id]


@pytest.fixture
def repo():
    return InMemoryProductRepository()


@pytest.fixture
def service(repo):
    return ProductService(repo, InMemoryChangeRepository(repo))


def test_crear_producto_limpia_nombre_y_registra_historial(service, repo):
    p = service.create_product("  Pan   de  Maíz ", 1.5, "unidad", "admin")

    assert p.id == 1
    assert p.nombre == "Pan de Maíz"
    assert p.activo is True
    assert len(repo.history) == 1
    assert repo.history[0].accion == "CREAR"
    assert repo.history[0].usuario == "admin"


@pytest.mark.parametrize("nombre", ["", "   "])
def test_nombre_vacio_rn10(service, nombre):
    with pytest.raises(BusinessRuleError):
        service.create_product(nombre, 1.0, "unidad", "admin")


@pytest.mark.parametrize("precio", [0, -2.5])
def test_precio_debe_ser_mayor_que_cero_rn10(service, precio):
    with pytest.raises(BusinessRuleError):
        service.create_product("Pan", precio, "unidad", "admin")


def test_tipo_venta_invalido_rn10(service):
    with pytest.raises(BusinessRuleError):
        service.create_product("Pan", 1.0, "litro", "admin")


def test_nombre_repetido_sin_importar_mayusculas_rn10(service):
    service.create_product("Croissant", 1.0, "unidad", "admin")

    with pytest.raises(ConflictError):
        service.create_product("CROISSANT", 1.2, "unidad", "admin")


def test_producto_inexistente(service):
    with pytest.raises(NotFoundError):
        service.get_product(99)


def test_editar_registra_un_cambio_por_campo_rn12(service, repo):
    p = service.create_product("Pan", 1.80, "unidad", "admin")

    service.replace_product(p.id, "Pan Blanco", 2.00, "unidad", "admin")

    cambios = repo.history[1:]
    assert [(c.campo, c.valor_anterior, c.valor_nuevo) for c in cambios] == [
        ("nombre", "Pan", "Pan Blanco"),
        ("precio", "1.80", "2.00"),
    ]
    assert all(c.accion == "EDITAR" for c in cambios)


def test_editar_sin_cambios_no_registra_nada(service, repo):
    p = service.create_product("Pan", 1.80, "unidad", "admin")

    service.replace_product(p.id, "Pan", 1.8, "unidad", "admin")

    assert len(repo.history) == 1


def test_editar_puede_conservar_su_propio_nombre(service):
    p = service.create_product("Pan", 1.80, "unidad", "admin")

    editado = service.replace_product(p.id, "Pan", 1.90, "unidad", "admin")

    assert editado.precio == 1.90


def test_desactivar_y_reactivar_rn11_rn12(service, repo):
    p = service.create_product("Rulo", 16.0, "peso", "admin")

    inactivo = service.set_active(p.id, False, "admin")
    activo = service.set_active(p.id, True, "admin")

    assert inactivo.activo is False
    assert activo.activo is True
    assert [c.accion for c in repo.history] == ["CREAR", "DESACTIVAR", "REACTIVAR"]
    assert service.get_product(p.id) is not None
