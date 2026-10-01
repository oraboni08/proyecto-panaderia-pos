"""Pruebas del servicio completo: HTTP + DTOs + dominio + SQLite con el dataset real.

catalog-service se reemplaza por FakeCatalog (ver conftest.py).
"""

BASE = "/api/v1/sales"


def test_health(client):
    assert client.get(f"{BASE}/health").status_code == 200


# ---------- Clientes ----------

def test_dataset_clientes_y_consumidor_final(client, cajero_headers):
    r = client.get(f"{BASE}/customers/17", headers=cajero_headers)
    assert r.status_code == 200
    assert r.json() == {"id_cliente": 17, "nombre": "Cliente 17"}

    r = client.get(f"{BASE}/customers/0", headers=cajero_headers)
    assert r.json()["nombre"] == "Consumidor final"


def test_cliente_inexistente_404(client, cajero_headers):
    assert client.get(f"{BASE}/customers/99999", headers=cajero_headers).status_code == 404


def test_crear_cliente_consecutivo_y_buscar_por_nombre_rf11_rf12(client, cajero_headers):
    r = client.post(f"{BASE}/customers", json={"nombre": "Victoria Herrera"}, headers=cajero_headers)
    assert r.status_code == 201
    nuevo = r.json()
    assert nuevo["id_cliente"] >= 211

    r = client.get(f"{BASE}/customers", params={"search": "victoria"}, headers=cajero_headers)
    assert nuevo in r.json()

    r = client.get(f"{BASE}/customers", params={"search": str(nuevo["id_cliente"])}, headers=cajero_headers)
    assert r.json()[0] == nuevo


def test_buscar_por_numero_pone_primero_el_id_exacto(client, cajero_headers):
    r = client.get(f"{BASE}/customers", params={"search": "17"}, headers=cajero_headers)
    assert r.json()[0]["id_cliente"] == 17


def test_crear_cliente_sin_nombre_400(client, cajero_headers):
    assert client.post(f"{BASE}/customers", json={"nombre": "  "}, headers=cajero_headers).status_code == 400


# ---------- Ventas ----------

def test_registrar_venta_carrito_201(client, cajero_headers):
    r = client.post(
        f"{BASE}/orders",
        json={"id_cliente": 17, "lineas": [{"id_producto": 16, "cantidad": 2}, {"id_producto": 35, "cantidad": 350}]},
        headers=cajero_headers,
    )
    assert r.status_code == 201
    venta = r.json()
    assert venta["id_venta"] >= 1204
    assert venta["cliente"]["nombre"] == "Cliente 17"
    assert venta["cajero"] == "cajero"
    assert venta["total"] == 3.23
    assert venta["lineas"][1]["cantidad"] == 0.35


def test_venta_sin_cliente_es_consumidor_final(client, cajero_headers):
    r = client.post(f"{BASE}/orders", json={"lineas": [{"id_producto": 4, "cantidad": 1}]}, headers=cajero_headers)
    assert r.status_code == 201
    assert r.json()["cliente"]["id_cliente"] == 0


def test_venta_vacia_422_rn14(client, cajero_headers):
    r = client.post(f"{BASE}/orders", json={"id_cliente": 0, "lineas": []}, headers=cajero_headers)
    assert r.status_code == 422


def test_producto_inexistente_404_rn01(client, cajero_headers):
    r = client.post(f"{BASE}/orders", json={"lineas": [{"id_producto": 9999, "cantidad": 1}]}, headers=cajero_headers)
    assert r.status_code == 404


def test_cantidad_negativa_400_rn02(client, cajero_headers):
    r = client.post(f"{BASE}/orders", json={"lineas": [{"id_producto": 4, "cantidad": -5}]}, headers=cajero_headers)
    assert r.status_code == 400


def test_todo_o_nada_no_guarda_nada_rn15(client, cajero_headers):
    antes = len(client.get(f"{BASE}/orders", headers=cajero_headers).json())

    r = client.post(
        f"{BASE}/orders",
        json={"lineas": [{"id_producto": 4, "cantidad": 1}, {"id_producto": 50, "cantidad": 1}]},
        headers=cajero_headers,
    )
    assert r.status_code == 400

    despues = len(client.get(f"{BASE}/orders", headers=cajero_headers).json())
    assert despues == antes


def test_admin_no_registra_ventas_403(client, admin_headers):
    r = client.post(f"{BASE}/orders", json={"lineas": [{"id_producto": 4, "cantidad": 1}]}, headers=admin_headers)
    assert r.status_code == 403


def test_sin_token_401(client):
    assert client.get(f"{BASE}/orders").status_code == 401


def test_cajero_solo_ve_sus_ventas_rf14(client, cajero_headers, cajero2_headers):
    r = client.post(f"{BASE}/orders", json={"lineas": [{"id_producto": 4, "cantidad": 3}]}, headers=cajero2_headers)
    venta_juan = r.json()["id_venta"]

    ventas_cajero = client.get(f"{BASE}/orders", headers=cajero_headers).json()
    assert all(v["cajero"] == "cajero" for v in ventas_cajero)
    assert venta_juan not in [v["id_venta"] for v in ventas_cajero]

    assert client.get(f"{BASE}/orders/{venta_juan}", headers=cajero_headers).status_code == 403
    assert client.get(f"{BASE}/orders/{venta_juan}", headers=cajero2_headers).status_code == 200


def test_ventas_de_hoy_por_fecha(client, cajero_headers):
    from datetime import date

    hoy = date.today().isoformat()
    ventas = client.get(f"{BASE}/orders", params={"desde": hoy, "hasta": hoy}, headers=cajero_headers).json()
    assert len(ventas) >= 1
    assert all(v["fecha"].startswith(hoy) for v in ventas)


def test_venta_inexistente_404(client, admin_headers):
    assert client.get(f"{BASE}/orders/999999", headers=admin_headers).status_code == 404


# ---------- Métricas (con el dataset: semana del 2 al 7 de marzo de 2020) ----------

SEMANA = {"desde": "2020-03-02", "hasta": "2020-03-07"}


def test_resumen_del_dataset_rf02(client, admin_headers):
    r = client.get(f"{BASE}/metrics/summary", params=SEMANA, headers=admin_headers)
    assert r.status_code == 200
    s = r.json()
    assert s["numero_ventas"] == 1203
    assert abs(s["ingresos_totales"] - 1229.4) < 0.1
    assert s["clientes_activos"] == 203
    assert s["ticket_promedio"] == round(s["ingresos_totales"] / 1203, 2)
    assert s["kg_vendidos"] > 0


def test_ventas_por_dia_rf03(client, admin_headers):
    dias = client.get(f"{BASE}/metrics/sales-by-weekday", params=SEMANA, headers=admin_headers).json()
    assert [d["dia"] for d in dias] == ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    assert [d["ventas"] for d in dias] == [208, 203, 214, 199, 194, 185, 0]


def test_top_productos_rf04(client, admin_headers):
    top = client.get(f"{BASE}/metrics/top-products", params={**SEMANA, "limit": 3}, headers=admin_headers).json()
    assert [p["producto"] for p in top] == ["Puntos", "Pueblo", "Baguetina"]
    assert top[0]["ingresos"] == 354.0


def test_top_clientes_con_nombre_rf06(client, admin_headers):
    top = client.get(f"{BASE}/metrics/top-customers", params={**SEMANA, "limit": 2}, headers=admin_headers).json()
    assert top[0] == {"id_cliente": 17, "nombre": "Cliente 17", "compras": 17, "gasto": top[0]["gasto"]}
    assert top[1]["id_cliente"] == 96


def test_productos_sin_ventas_rf05(client, admin_headers):
    sin_ventas = client.get(f"{BASE}/metrics/products-without-sales", params=SEMANA, headers=admin_headers).json()
    # Del catálogo falso, Rulo (activo) no se vendió esa semana; Pan Viejo está inactivo y no se lista.
    nombres = [p["nombre"] for p in sin_ventas]
    assert "Rulo" in nombres
    assert "Pan Viejo" not in nombres
    assert "Pan" not in nombres


def test_cajero_no_ve_metricas_403(client, cajero_headers):
    assert client.get(f"{BASE}/metrics/summary", headers=cajero_headers).status_code == 403
