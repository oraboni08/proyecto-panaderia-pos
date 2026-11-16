"""Pruebas de reporting-service con una base SQLite temporal que imita lo que deja Spark."""

import os
import tempfile
from datetime import datetime, timedelta, timezone

import jwt
import pytest


_tmp = tempfile.mkdtemp(prefix="reports-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp, 'reports.db')}"
os.environ["JWT_SECRET"] = "clave-de-pruebas-panaderia-pos-2026"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.main import app, engine  # noqa: E402


def _headers(rol: str) -> dict:
    token = jwt.encode(
        {"sub": rol, "rol": rol, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "clave-de-pruebas-panaderia-pos-2026",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


ADMIN = _headers("admin")
CAJERO = _headers("cajero")
client = TestClient(app)


def _cargar_resultados_de_spark():
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE reporte_productos (id_producto INT PRIMARY KEY, producto TEXT, categoria TEXT, ventas INT, unidades INT, ingresos BIGINT)"))
        conn.execute(text("INSERT INTO reporte_productos VALUES (1, 'Pandebono', 'Panadería de queso', 900, 2000, 6400000), (66, 'Tinto', 'Bebidas calientes', 1500, 1600, 2400000), (3, 'Almojábana', 'Panadería de queso', 500, 700, 2310000)"))
        conn.execute(text("CREATE TABLE reporte_horas (hora INT PRIMARY KEY, ventas INT, ingresos BIGINT)"))
        conn.execute(text("INSERT INTO reporte_horas VALUES (14, 30, 400000), (7, 50, 600000)"))
        conn.execute(text("CREATE TABLE spark_ejecuciones (id INTEGER PRIMARY KEY, inicio TIMESTAMP, fin TIMESTAMP, segundos REAL, lineas INT, ventas INT, archivos INT, particiones INT, nucleos INT)"))
        conn.execute(text("INSERT INTO spark_ejecuciones (segundos, lineas, ventas, archivos, particiones, nucleos) VALUES (40.5, 1000, 400, 27, 27, 8), (35.2, 1200, 450, 28, 28, 8)"))


def test_health_sin_token():
    assert client.get("/api/v1/reports/health").json()["status"] == "ok"


def test_solo_el_admin_ve_los_reportes():
    assert client.get("/api/v1/reports/productos").status_code == 401
    assert client.get("/api/v1/reports/productos", headers=CAJERO).status_code == 403


def test_antes_de_correr_spark_devuelve_vacio():
    r = client.get("/api/v1/reports/resumen", headers=ADMIN)
    assert r.status_code == 200
    assert r.json()["ultima_ejecucion"] is None
    assert r.json()["productos"] == []


def test_reportes_despues_de_spark():
    _cargar_resultados_de_spark()

    productos = client.get("/api/v1/reports/productos", headers=ADMIN).json()
    assert [p["producto"] for p in productos] == ["Pandebono", "Tinto", "Almojábana"]

    por_ingresos = client.get("/api/v1/reports/productos", params={"orden": "ingresos", "limite": 1}, headers=ADMIN).json()
    assert por_ingresos[0]["producto"] == "Pandebono" and len(por_ingresos) == 1

    horas = client.get("/api/v1/reports/horas", headers=ADMIN).json()
    assert [h["hora"] for h in horas] == [7, 14]

    ultima = client.get("/api/v1/reports/ultima-ejecucion", headers=ADMIN).json()
    assert ultima["lineas"] == 1200 and ultima["particiones"] == 28

    # Una tabla que Spark todavía no ha creado no rompe el resumen.
    assert client.get("/api/v1/reports/resumen", headers=ADMIN).json()["clientes"] == []


def test_orden_invalido_se_rechaza():
    # El orden se valida con un patrón: no se puede inyectar SQL por ese parámetro.
    r = client.get("/api/v1/reports/productos", params={"orden": "ingresos; DROP TABLE x"}, headers=ADMIN)
    assert r.status_code == 422


def test_metrics_para_prometheus():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "http_requests_total" in r.text
