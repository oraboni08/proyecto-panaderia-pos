import os
import tempfile
from datetime import datetime, timedelta, timezone

import jwt
import pytest


# La base de datos de pruebas es un archivo temporal: nunca se toca sales.db.
_tmp_dir = tempfile.mkdtemp(prefix="sales-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp_dir, 'test.db')}"
os.environ["JWT_SECRET"] = "clave-de-pruebas-panaderia-pos-2026"


from app.domain.models import ProductInfo  # noqa: E402
from app.domain.repositories import ProductCatalog  # noqa: E402


def make_token(usuario: str, rol: str) -> str:
    payload = {
        "sub": usuario,
        "nombre": usuario.title(),
        "rol": rol,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return jwt.encode(payload, "clave-de-pruebas-panaderia-pos-2026", algorithm="HS256")


class FakeCatalog(ProductCatalog):
    """Catálogo en memoria que reemplaza a catalog-service en las pruebas."""

    def __init__(self):
        self.products = {
            1: ProductInfo(1, "Pandebono", "Panadería de queso", 3200, True),
            9: ProductInfo(9, "Pan aliñado", "Panes", 1800, True),
            25: ProductInfo(25, "Pastel de pollo", "Hojaldres", 6000, True),
            68: ProductInfo(68, "Café con leche", "Bebidas calientes", 3000, True),
            86: ProductInfo(86, "Huevo AA (unidad)", "Lácteos y despensa", 650, True),
            57: ProductInfo(57, "Natilla (porción)", "Tortas y postres", 3500, False),
            # Producto recién creado en el catálogo: todavía no tiene ventas.
            91: ProductInfo(91, "Pan de bono con guayaba", "Panadería de queso", 3900, True),
        }

    def get_product(self, product_id):
        return self.products.get(product_id)

    def list_products(self):
        return list(self.products.values())


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from app.api.dependencies import get_product_catalog
    from app.main import app

    app.dependency_overrides[get_product_catalog] = FakeCatalog

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers():
    return {"Authorization": f"Bearer {make_token('admin', 'admin')}"}


@pytest.fixture
def cajero_headers():
    return {"Authorization": f"Bearer {make_token('cajero', 'cajero')}"}


@pytest.fixture
def cajero2_headers():
    return {"Authorization": f"Bearer {make_token('juan', 'cajero')}"}
