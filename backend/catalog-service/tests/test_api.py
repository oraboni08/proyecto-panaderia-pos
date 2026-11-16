"""Pruebas del servicio completo: HTTP + DTOs + dominio + SQLite.

Usan una base de datos temporal que se llena con el dataset real (backend/dataset).
"""

from tests.conftest import make_token

BASE = "/api/v1/catalog"


def nuevo(nombre, categoria="Panes", precio=2000):
    return {"nombre": nombre, "categoria": categoria, "precio": precio}


def test_health(client):
    r = client.get(f"{BASE}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dataset_cargado_con_productos_colombianos(client, admin_headers):
    r = client.get(f"{BASE}/products", headers=admin_headers)
    assert r.status_code == 200

    productos = {p["id_producto"]: p for p in r.json()}
    assert len(productos) >= 90
    assert productos[1] == {
        "id_producto": 1, "nombre": "Pandebono", "categoria": "Panadería de queso", "precio": 3200, "activo": True,
    }
    assert productos[25]["nombre"] == "Pastel de pollo"
    assert productos[68]["categoria"] == "Bebidas calientes"
    assert "tipo_venta" not in productos[1]
    # Productos de temporada (diciembre) inician desactivados
    assert productos[57]["nombre"] == "Natilla (porción)"
    assert productos[57]["activo"] is False


def test_historial_del_dataset_tiene_alza_de_2026(client, admin_headers):
    historial = client.get(f"{BASE}/changes?product_id=1", headers=admin_headers).json()
    assert [h["accion"] for h in historial] == ["EDITAR", "CREAR"]
    assert (historial[0]["campo"], historial[0]["valor_anterior"], historial[0]["valor_nuevo"]) == ("precio", "3000", "3200")


def test_categorias(client, cajero_headers):
    r = client.get(f"{BASE}/products/categories", headers=cajero_headers)
    assert r.status_code == 200
    assert len(r.json()) == 10
    assert r.json()[0] == "Panadería de queso"


def test_filtrar_por_categoria(client, cajero_headers):
    r = client.get(f"{BASE}/products", params={"categoria": "bebidas calientes"}, headers=cajero_headers)
    assert r.status_code == 200
    nombres = {p["nombre"] for p in r.json()}
    assert {"Tinto", "Café con leche"} <= nombres
    assert all(p["categoria"] == "Bebidas calientes" for p in r.json())


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
    assert client.get(f"{BASE}/products/9", headers=cajero_headers).status_code == 200
    assert client.get(f"{BASE}/products/9999", headers=cajero_headers).status_code == 404


def test_cajero_no_ve_productos_inactivos_rn11(client, cajero_headers):
    ids = {p["id_producto"] for p in client.get(f"{BASE}/products", headers=cajero_headers).json()}
    assert 57 not in ids and 1 in ids


def test_cajero_no_puede_crear_ni_ver_historial_rn13(client, cajero_headers):
    r = client.post(f"{BASE}/products", json=nuevo("Pan Cajero"), headers=cajero_headers)
    assert r.status_code == 403
    assert client.get(f"{BASE}/changes", headers=cajero_headers).status_code == 403


def test_crear_producto_201(client, admin_headers):
    r = client.post(f"{BASE}/products", json=nuevo("Pan de bono con guayaba", "Panadería de queso", 3900),
                    headers=admin_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["id_producto"] > 90
    assert body["precio"] == 3900
    assert body["activo"] is True


def test_crear_producto_repetido_409(client, admin_headers):
    r = client.post(f"{BASE}/products", json=nuevo("PANDEBONO", "Panadería de queso"), headers=admin_headers)
    assert r.status_code == 409


def test_crear_producto_precio_invalido_400(client, admin_headers):
    assert client.post(f"{BASE}/products", json=nuevo("Pan Gratis", precio=0), headers=admin_headers).status_code == 400
    assert client.post(f"{BASE}/products", json=nuevo("Pan Centavos", precio=1800.5), headers=admin_headers).status_code == 400


def test_crear_producto_categoria_invalida_400(client, admin_headers):
    r = client.post(f"{BASE}/products", json=nuevo("Salchichón", "Carnes frías"), headers=admin_headers)
    assert r.status_code == 400
    assert "categoría" in r.json()["detail"]


def test_crear_producto_dto_invalido_422(client, admin_headers):
    r = client.post(f"{BASE}/products", json={"nombre": "Pan", "precio": 1000}, headers=admin_headers)
    assert r.status_code == 422


def test_editar_put_y_historial(client, admin_headers):
    pid = client.post(f"{BASE}/products", json=nuevo("Pan de queso costeño", precio=2000),
                      headers=admin_headers).json()["id_producto"]

    r = client.put(f"{BASE}/products/{pid}", json=nuevo("Pan de queso costeño", precio=2500), headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["precio"] == 2500

    historial = client.get(f"{BASE}/changes?product_id={pid}", headers=admin_headers).json()
    assert [h["accion"] for h in historial] == ["EDITAR", "CREAR"]
    assert historial[0]["producto"] == "Pan de queso costeño"
    assert historial[0]["valor_anterior"] == "2000"
    assert historial[0]["valor_nuevo"] == "2500"
    assert historial[0]["usuario"] == "admin"


def test_put_producto_inexistente_404(client, admin_headers):
    assert client.put(f"{BASE}/products/9999", json=nuevo("X"), headers=admin_headers).status_code == 404


def test_desactivar_con_patch_y_cajero_no_lo_ve_rn11(client, admin_headers, cajero_headers):
    pid = client.post(f"{BASE}/products", json=nuevo("Pan Temporal"), headers=admin_headers).json()["id_producto"]

    r = client.patch(f"{BASE}/products/{pid}", json={"activo": False}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["activo"] is False

    ids_cajero = [p["id_producto"] for p in client.get(f"{BASE}/products", headers=cajero_headers).json()]
    ids_admin = [p["id_producto"] for p in client.get(f"{BASE}/products", headers=admin_headers).json()]
    assert pid not in ids_cajero
    assert pid in ids_admin


def test_patch_no_acepta_tipo_venta(client, admin_headers):
    r = client.patch(f"{BASE}/products/9", json={"tipo_venta": "peso"}, headers=admin_headers)
    assert r.status_code == 422


def test_no_existe_delete_rn11(client, admin_headers):
    assert client.delete(f"{BASE}/products/9", headers=admin_headers).status_code == 405


def test_historial_no_se_puede_modificar_rn12(client, admin_headers):
    assert client.post(f"{BASE}/changes", json={}, headers=admin_headers).status_code == 405
    assert client.delete(f"{BASE}/changes", headers=admin_headers).status_code == 405
