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
            4: ProductInfo(4, "Pan", 1.80, "unidad", True),
            16: ProductInfo(16, "Baguetina", 0.60, "unidad", True),
            35: ProductInfo(35, "Magdalenas", 5.80, "peso", True),
            38: ProductInfo(38, "Huevos (docena)", 2.10, "unidad", True),
            26: ProductInfo(26, "Rulo", 16.00, "peso", True),
            50: ProductInfo(50, "Pan Viejo", 1.00, "unidad", False),
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
