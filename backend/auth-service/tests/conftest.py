import os
import tempfile

import pytest


# La base de datos de pruebas es un archivo temporal: nunca se toca auth.db.
_tmp_dir = tempfile.mkdtemp(prefix="auth-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp_dir, 'test.db')}"
os.environ["JWT_SECRET"] = "clave-de-pruebas-panaderia-pos-2026"
os.environ["ADMIN_PASSWORD"] = "admin-pruebas-123"
os.environ["CAJERO_PASSWORD"] = "cajero-pruebas-123"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        yield c


def login(client, usuario, password):
    r = client.post("/api/v1/auth/tokens", json={"usuario": usuario, "password": password})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin_headers(client):
    return login(client, "admin", "admin-pruebas-123")


@pytest.fixture
def cajero_headers(client):
    return login(client, "cajero", "cajero-pruebas-123")
