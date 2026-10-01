import os
import tempfile
from datetime import datetime, timedelta, timezone

import jwt
import pytest


# La base de datos de pruebas es un archivo temporal: nunca se toca catalog.db.
_tmp_dir = tempfile.mkdtemp(prefix="catalog-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp_dir, 'test.db')}"
os.environ["JWT_SECRET"] = "clave-de-pruebas-panaderia-pos-2026"


def make_token(usuario: str, rol: str, minutes: int = 30) -> str:
    payload = {
        "sub": usuario,
        "nombre": usuario.title(),
        "rol": rol,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, "clave-de-pruebas-panaderia-pos-2026", algorithm="HS256")


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_headers():
    return {"Authorization": f"Bearer {make_token('admin', 'admin')}"}


@pytest.fixture
def cajero_headers():
    return {"Authorization": f"Bearer {make_token('cajero', 'cajero')}"}
