"""Pruebas de integración: los tres microservicios funcionando juntos.

Requieren los servicios encendidos (python run_dev.py --no-front) o desplegados.
Las direcciones se pueden cambiar con variables de entorno, por ejemplo para
probar contra el servidor:

    AUTH_URL=http://api.panaderia-pos.test CATALOG_URL=http://api.panaderia-pos.test \
    SALES_URL=http://api.panaderia-pos.test pytest integration_tests -v
"""

import os
import uuid
from datetime import date

import httpx
import pytest


AUTH = os.getenv("AUTH_URL", "http://127.0.0.1:8001").rstrip("/") + "/api/v1/auth"
CATALOG = os.getenv("CATALOG_URL", "http://127.0.0.1:8002").rstrip("/") + "/api/v1/catalog"
SALES = os.getenv("SALES_URL", "http://127.0.0.1:8003").rstrip("/") + "/api/v1/sales"

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin12345")
CAJERO_PASSWORD = os.getenv("CAJERO_PASSWORD", "cajero12345")


def login(usuario: str, password: str) -> dict:
    r = httpx.post(f"{AUTH}/tokens", json={"usuario": usuario, "password": password})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def admin():
    return login("admin", ADMIN_PASSWORD)


@pytest.fixture(scope="module")
def cajero():
    return login("cajero", CAJERO_PASSWORD)


@pytest.fixture
def producto(admin):
    """Crea un producto nuevo para la prueba (nombre único en cada ejecución)."""
    nombre = f"Pan Prueba {uuid.uuid4().hex[:6]}"
    r = httpx.post(
        f"{CATALOG}/products",
        json={"nombre": nombre, "precio": 2.00, "tipo_venta": "unidad"},
        headers=admin,
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_los_tres_servicios_estan_vivos():
    for base in (AUTH, CATALOG, SALES):
        assert httpx.get(f"{base}/health").json()["status"] == "ok"


def test_token_de_auth_es_aceptado_por_catalog_y_sales(admin, cajero):
    assert httpx.get(f"{CATALOG}/products", headers=cajero).status_code == 200
    assert httpx.get(f"{SALES}/customers/0", headers=cajero).status_code == 200
    assert httpx.get(f"{SALES}/metrics/summary", headers=admin).status_code == 200


def test_roles_se_respetan_en_todos_los_servicios(cajero):
    assert httpx.get(f"{AUTH}/users", headers=cajero).status_code == 403
    assert httpx.get(f"{CATALOG}/changes", headers=cajero).status_code == 403
    assert httpx.get(f"{SALES}/metrics/summary", headers=cajero).status_code == 403


def test_flujo_completo_de_venta(admin, cajero, producto):
    """Admin crea producto → cajero registra cliente → venta con carrito → aparece en el dashboard."""

    r = httpx.post(f"{SALES}/customers", json={"nombre": "Cliente Integración"}, headers=cajero)
    assert r.status_code == 201
    cliente = r.json()

    r = httpx.post(
        f"{SALES}/orders",
        json={
            "id_cliente": cliente["id_cliente"],
            "lineas": [
                {"id_producto": producto["id_producto"], "cantidad": 3},
                {"id_producto": 35, "cantidad": 500},  # Magdalenas, por peso: 500 g
            ],
        },
        headers=cajero,
    )
    assert r.status_code == 201, r.text
    venta = r.json()

    # sales consultó a catalog el nombre y el precio de cada producto.
    assert venta["lineas"][0]["producto"] == producto["nombre"]
    assert venta["lineas"][0]["subtotal"] == 6.00
    assert venta["lineas"][1]["producto"] == "Magdalenas"
    assert venta["lineas"][1]["cantidad"] == 0.5
    assert venta["lineas"][1]["subtotal"] == 2.90
    assert venta["total"] == 8.90

    hoy = date.today().isoformat()
    ventas_hoy = httpx.get(f"{SALES}/orders", params={"desde": hoy, "hasta": hoy}, headers=cajero).json()
    assert venta["id_venta"] in [v["id_venta"] for v in ventas_hoy]

    top = httpx.get(f"{SALES}/metrics/top-customers", params={"desde": hoy, "hasta": hoy, "limit": 100}, headers=admin).json()
    assert cliente["id_cliente"] in [c["id_cliente"] for c in top]


def test_cambio_de_precio_no_altera_ventas_anteriores_rn06(admin, cajero, producto):
    pid = producto["id_producto"]

    venta1 = httpx.post(f"{SALES}/orders", json={"lineas": [{"id_producto": pid, "cantidad": 1}]}, headers=cajero).json()

    r = httpx.patch(f"{CATALOG}/products/{pid}", json={"precio": 2.50}, headers=admin)
    assert r.status_code == 200

    venta2 = httpx.post(f"{SALES}/orders", json={"lineas": [{"id_producto": pid, "cantidad": 1}]}, headers=cajero).json()

    assert venta2["total"] == 2.50
    venta1_ahora = httpx.get(f"{SALES}/orders/{venta1['id_venta']}", headers=cajero).json()
    assert venta1_ahora["total"] == 2.00

    historial = httpx.get(f"{CATALOG}/changes", params={"product_id": pid}, headers=admin).json()
    assert historial[0]["campo"] == "precio"
    assert historial[0]["valor_anterior"] == "2.00"
    assert historial[0]["valor_nuevo"] == "2.50"


def test_producto_desactivado_no_se_puede_vender_rn01_rn11(admin, cajero, producto):
    pid = producto["id_producto"]

    httpx.patch(f"{CATALOG}/products/{pid}", json={"activo": False}, headers=admin)

    r = httpx.post(f"{SALES}/orders", json={"lineas": [{"id_producto": pid, "cantidad": 1}]}, headers=cajero)
    assert r.status_code == 400

    activos = [p["id_producto"] for p in httpx.get(f"{CATALOG}/products", headers=cajero).json()]
    assert pid not in activos


def test_producto_nuevo_aparece_sin_ventas_rf05(admin, producto):
    sin_ventas = httpx.get(f"{SALES}/metrics/products-without-sales", headers=admin).json()
    assert producto["id_producto"] in [p["id_producto"] for p in sin_ventas]


def test_usuario_creado_por_admin_puede_vender(admin):
    usuario = f"cajero{uuid.uuid4().hex[:6]}"

    r = httpx.post(
        f"{AUTH}/users",
        json={"nombre": "Cajero Nuevo", "usuario": usuario, "password": "nuevo-12345", "rol": "cajero"},
        headers=admin,
    )
    assert r.status_code == 201

    headers = login(usuario, "nuevo-12345")
    r = httpx.post(f"{SALES}/orders", json={"lineas": [{"id_producto": 4, "cantidad": 1}]}, headers=headers)
    assert r.status_code == 201
    assert r.json()["cajero"] == usuario
