"""Pruebas unitarias de las reglas de negocio del catálogo.

Usan repositorios falsos en memoria: no hay base de datos ni HTTP.
"""

import pytest

from app.domain.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.domain.models import CATEGORIAS, Product, ProductChange
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

    def list_all(self, activo=None, categoria=None):
        return [
            p for p in self.products.values()
            if (activo is None or p.activo == activo) and (categoria is None or p.categoria == categoria)
        ]

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
    p = service.create_product("  Pan   de  Maíz ", "Panes", 2400, "admin")

    assert p.id == 1
    assert p.nombre == "Pan de Maíz"
    assert p.categoria == "Panes"
    assert p.precio == 2400 and isinstance(p.precio, int)
    assert p.activo is True
    assert len(repo.history) == 1
    assert repo.history[0].accion == "CREAR"
    assert repo.history[0].valor_nuevo == "Pan de Maíz | Panes | 2400"
    assert repo.history[0].usuario == "admin"


@pytest.mark.parametrize("nombre", ["", "   "])
def test_nombre_vacio_rn10(service, nombre):
    with pytest.raises(BusinessRuleError):
        service.create_product(nombre, "Panes", 1000, "admin")


@pytest.mark.parametrize("precio", [0, -2500])
def test_precio_debe_ser_mayor_que_cero_rn10(service, precio):
    with pytest.raises(BusinessRuleError):
        service.create_product("Pan", "Panes", precio, "admin")


def test_precio_en_pesos_sin_centavos(service):
    with pytest.raises(BusinessRuleError, match="entero"):
        service.create_product("Pan", "Panes", 1800.5, "admin")


def test_precio_con_decimales_cero_se_acepta_como_entero(service):
    p = service.create_product("Pan", "Panes", 1800.0, "admin")
    assert p.precio == 1800 and isinstance(p.precio, int)


def test_precio_maximo(service):
    with pytest.raises(BusinessRuleError):
        service.create_product("Torta gigante", "Tortas y postres", 1_000_001, "admin")


def test_categoria_invalida_rn10(service):
    with pytest.raises(BusinessRuleError, match="categoría"):
        service.create_product("Pan", "Carnes frías", 1000, "admin")


def test_categoria_sin_importar_mayusculas_se_guarda_con_nombre_oficial(service):
    p = service.create_product("Tinto doble", "  bebidas   CALIENTES ", 2500, "admin")
    assert p.categoria == "Bebidas calientes"


def test_lista_de_categorias(service):
    assert service.list_categories() == list(CATEGORIAS)
    assert "Panadería de queso" in CATEGORIAS


def test_nombre_repetido_sin_importar_mayusculas_rn10(service):
    service.create_product("Croissant", "Hojaldres", 4000, "admin")

    with pytest.raises(ConflictError):
        service.create_product("CROISSANT", "Hojaldres", 4200, "admin")


def test_producto_inexistente(service):
    with pytest.raises(NotFoundError):
        service.get_product(99)


def test_editar_registra_un_cambio_por_campo_rn12(service, repo):
    p = service.create_product("Pan", "Panes", 1800, "admin")

    service.replace_product(p.id, "Pan aliñado", "Panes", 2000, "admin")

    cambios = repo.history[1:]
    assert [(c.campo, c.valor_anterior, c.valor_nuevo) for c in cambios] == [
        ("nombre", "Pan", "Pan aliñado"),
        ("precio", "1800", "2000"),
    ]
    assert all(c.accion == "EDITAR" for c in cambios)


def test_cambiar_categoria_queda_en_historial(service, repo):
    p = service.create_product("Mantecada", "Panes", 2500, "admin")

    service.update_product(p.id, "admin", categoria="Galletas y dulces")

    assert (repo.history[-1].campo, repo.history[-1].valor_anterior, repo.history[-1].valor_nuevo) == (
        "categoria", "Panes", "Galletas y dulces",
    )


def test_editar_sin_cambios_no_registra_nada(service, repo):
    p = service.create_product("Pan", "Panes", 1800, "admin")

    service.replace_product(p.id, "Pan", "panes", 1800.0, "admin")

    assert len(repo.history) == 1


def test_editar_puede_conservar_su_propio_nombre(service):
    p = service.create_product("Pan", "Panes", 1800, "admin")

    editado = service.replace_product(p.id, "Pan", "Panes", 1900, "admin")

    assert editado.precio == 1900


def test_listar_por_categoria(service):
    service.create_product("Tinto", "Bebidas calientes", 1500, "admin")
    service.create_product("Pandebono", "Panadería de queso", 3200, "admin")

    assert [p.nombre for p in service.list_products(categoria="Bebidas calientes")] == ["Tinto"]


def test_desactivar_y_reactivar_rn11_rn12(service, repo):
    p = service.create_product("Natilla (porción)", "Tortas y postres", 3500, "admin")

    inactivo = service.set_active(p.id, False, "admin")
    activo = service.set_active(p.id, True, "admin")

    assert inactivo.activo is False
    assert activo.activo is True
    assert [c.accion for c in repo.history] == ["CREAR", "DESACTIVAR", "REACTIVAR"]
    assert service.get_product(p.id) is not None
