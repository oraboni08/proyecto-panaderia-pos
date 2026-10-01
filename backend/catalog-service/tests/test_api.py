"""Pruebas del servicio completo: HTTP + DTOs + dominio + SQLite.

Usan una base de datos temporal que se llena con el dataset real.
"""

from tests.conftest import make_token

BASE = "/api/v1/catalog"


def test_health(client):
    r = client.get(f"{BASE}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dataset_cargado_con_tipos_de_venta(client, admin_headers):
    r = client.get(f"{BASE}/products", headers=admin_headers)
    assert r.status_code == 200

    productos = {p["id_producto"]: p for p in r.json()}
    assert len(productos) >= 42
    assert productos[27]["nombre"] == "Trenza"
    assert productos[27]["tipo_venta"] == "peso"
    assert productos[38]["nombre"] == "Huevos (docena)"
    assert productos[38]["tipo_venta"] == "unidad"
    assert productos[4]["nombre"] == "Pan"


def test_sin_token_401(client):
    assert client.get(f"{BASE}/products").status_code == 401


def test_token_vencido_401(client):
    headers = {"Authorization": f"Bearer {make_token('admin', 'admin', minutes=-1)}"}
    r = client.get(f"{BASE}/products", headers=headers)
    assert r.status_code == 401


def test_token_falso_401(client):
    r = client.get(f"{BASE}/products", headers={"Authorization": "Bearer abc.def.ghi"})
    assert r.status_code == 401


def test_obtener_producto_y_404(client, cajero_headers):
    assert client.get(f"{BASE}/products/4", headers=cajero_headers).status_code == 200
    assert client.get(f"{BASE}/products/9999", headers=cajero_headers).status_code == 404


def test_cajero_no_puede_crear_ni_ver_historial_rn13(client, cajero_headers):
    r = client.post(
        f"{BASE}/products",
        json={"nombre": "Pan Cajero", "precio": 1, "tipo_venta": "unidad"},
        headers=cajero_headers,
    )
    assert r.status_code == 403
    assert client.get(f"{BASE}/changes", headers=cajero_headers).status_code == 403


def test_crear_producto_201(client, admin_headers):
    r = client.post(
        f"{BASE}/products",
        json={"nombre": "Pan de Bono", "precio": 1.5, "tipo_venta": "unidad"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["id_producto"] > 42
    assert body["activo"] is True


def test_crear_producto_repetido_409(client, admin_headers):
    r = client.post(
        f"{BASE}/products",
        json={"nombre": "baguetina", "precio": 1, "tipo_venta": "unidad"},
        headers=admin_headers,
    )
    assert r.status_code == 409


def test_crear_producto_precio_invalido_400(client, admin_headers):
    r = client.post(
        f"{BASE}/products",
        json={"nombre": "Pan Gratis", "precio": 0, "tipo_venta": "unidad"},
        headers=admin_headers,
    )
    assert r.status_code == 400


def test_crear_producto_dto_invalido_422(client, admin_headers):
    r = client.post(
        f"{BASE}/products",
        json={"nombre": "Pan", "precio": 1, "tipo_venta": "litro"},
        headers=admin_headers,
    )
    assert r.status_code == 422


def test_editar_put_y_historial(client, admin_headers):
    r = client.post(
        f"{BASE}/products",
        json={"nombre": "Pan de Queso", "precio": 2, "tipo_venta": "unidad"},
        headers=admin_headers,
    )
    pid = r.json()["id_producto"]

    r = client.put(
        f"{BASE}/products/{pid}",
        json={"nombre": "Pan de Queso", "precio": 2.5, "tipo_venta": "unidad"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["precio"] == 2.5

    historial = client.get(f"{BASE}/changes?product_id={pid}", headers=admin_headers).json()
    assert [h["accion"] for h in historial] == ["EDITAR", "CREAR"]
    assert historial[0]["producto"] == "Pan de Queso"
    assert historial[0]["valor_anterior"] == "2.00"
    assert historial[0]["valor_nuevo"] == "2.50"
    assert historial[0]["usuario"] == "admin"


def test_put_producto_inexistente_404(client, admin_headers):
    r = client.put(
        f"{BASE}/products/9999",
        json={"nombre": "X", "precio": 1, "tipo_venta": "unidad"},
        headers=admin_headers,
    )
    assert r.status_code == 404


def test_desactivar_con_patch_y_cajero_no_lo_ve_rn11(client, admin_headers, cajero_headers):
    r = client.post(
        f"{BASE}/products",
        json={"nombre": "Pan Temporal", "precio": 1, "tipo_venta": "unidad"},
        headers=admin_headers,
    )
    pid = r.json()["id_producto"]

    r = client.patch(f"{BASE}/products/{pid}", json={"activo": False}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["activo"] is False

    ids_cajero = [p["id_producto"] for p in client.get(f"{BASE}/products", headers=cajero_headers).json()]
    ids_admin = [p["id_producto"] for p in client.get(f"{BASE}/products", headers=admin_headers).json()]
    assert pid not in ids_cajero
    assert pid in ids_admin


def test_no_existe_delete_rn11(client, admin_headers):
    assert client.delete(f"{BASE}/products/4", headers=admin_headers).status_code == 405


def test_historial_no_se_puede_modificar_rn12(client, admin_headers):
    assert client.post(f"{BASE}/changes", json={}, headers=admin_headers).status_code == 405
    assert client.delete(f"{BASE}/changes", headers=admin_headers).status_code == 405
