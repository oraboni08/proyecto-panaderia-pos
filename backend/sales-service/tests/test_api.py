"""Pruebas del servicio completo: HTTP + DTOs + dominio + SQLite con el dataset real.

catalog-service se reemplaza por FakeCatalog (ver conftest.py). Los valores esperados
de las métricas se calculan aquí leyendo directamente los CSV del dataset.
"""

import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pytest

BASE = "/api/v1/sales"
DATASET = Path(__file__).resolve().parents[2] / "dataset"

# Semana completa (lunes a domingo) para las métricas.
SEMANA = {"desde": "2026-03-02", "hasta": "2026-03-08"}


def _leer(nombre):
    with open(DATASET / nombre, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


@pytest.fixture(scope="module")
def dataset():
    ventas = [v for v in _leer("ventas.csv") if SEMANA["desde"] <= v["fecha"][:10] <= SEMANA["hasta"]]
    ids = {v["id_venta"] for v in ventas}
    lineas = [l for l in _leer("lineas_venta.csv") if l["id_venta"] in ids]
    return {"ventas": ventas, "lineas": lineas, "clientes": _leer("clientes.csv")}


def test_health(client):
    assert client.get(f"{BASE}/health").status_code == 200


# ---------- Clientes ----------

def test_dataset_clientes_con_datos_completos(client, cajero_headers, dataset):
    r = client.get(f"{BASE}/customers/1", headers=cajero_headers)
    assert r.status_code == 200
    c = r.json()
    esperado = dataset["clientes"][0]
    assert c["nombre"] == esperado["nombre"] == "Rosa Giraldo Velasco"
    assert c["documento"] == esperado["documento"]
    assert c["telefono"].startswith("3") and len(c["telefono"]) == 10
    assert c["ciudad"] == "Cali"
    assert c["creado_en"].startswith("2025-08-11")

    assert client.get(f"{BASE}/customers/0", headers=cajero_headers).json()["nombre"] == "Consumidor final"


def test_total_de_clientes(client, cajero_headers, dataset):
    r = client.get(f"{BASE}/customers/page", params={"limit": 5}, headers=cajero_headers)
    assert r.json()["total"] == len(dataset["clientes"]) + 1
    assert len(r.json()["clientes"]) == 5


def test_cliente_inexistente_404(client, cajero_headers):
    assert client.get(f"{BASE}/customers/999999", headers=cajero_headers).status_code == 404


def test_buscar_por_cedula_y_por_telefono(client, cajero_headers, dataset):
    cliente = dataset["clientes"][1]

    r = client.get(f"{BASE}/customers", params={"search": cliente["documento"]}, headers=cajero_headers)
    assert r.json()[0]["id_cliente"] == int(cliente["id_cliente"])

    r = client.get(f"{BASE}/customers", params={"search": cliente["telefono"]}, headers=cajero_headers)
    assert int(cliente["id_cliente"]) in [c["id_cliente"] for c in r.json()]


def test_buscar_por_nombre_sin_consumidor_final(client, cajero_headers):
    r = client.get(f"{BASE}/customers", params={"search": "giraldo"}, headers=cajero_headers)
    assert len(r.json()) > 0
    assert all("giraldo" in c["nombre"].lower() for c in r.json())


def test_crear_editar_y_buscar_cliente_rf11_rf12(client, cajero_headers, dataset):
    r = client.post(
        f"{BASE}/customers",
        json={"nombre": "Victoria Herrera Castro", "documento": "1.144.000.111", "telefono": "3185550000",
              "correo": "victoria@ejemplo.co", "barrio": "San Fernando", "ciudad": "Cali"},
        headers=cajero_headers,
    )
    assert r.status_code == 201
    nuevo = r.json()
    assert nuevo["id_cliente"] > len(dataset["clientes"])
    assert nuevo["documento"] == "1144000111"

    r = client.patch(f"{BASE}/customers/{nuevo['id_cliente']}", json={"telefono": "3005550000"},
                     headers=cajero_headers)
    assert r.status_code == 200
    assert r.json()["telefono"] == "3005550000"

    r = client.get(f"{BASE}/customers", params={"search": "1144000111"}, headers=cajero_headers)
    assert r.json()[0]["nombre"] == "Victoria Herrera Castro"


def test_documento_repetido_409(client, cajero_headers, dataset):
    r = client.post(f"{BASE}/customers", json={"nombre": "Copia", "documento": dataset["clientes"][0]["documento"]},
                    headers=cajero_headers)
    assert r.status_code == 409


def test_crear_cliente_invalido_400(client, cajero_headers):
    assert client.post(f"{BASE}/customers", json={"nombre": "  "}, headers=cajero_headers).status_code == 400
    assert client.post(f"{BASE}/customers", json={"nombre": "Ana Pérez", "telefono": "123"},
                       headers=cajero_headers).status_code == 400


def test_patch_campo_desconocido_422(client, cajero_headers):
    assert client.patch(f"{BASE}/customers/1", json={"edad": 30}, headers=cajero_headers).status_code == 422


# ---------- Ventas ----------

def test_registrar_venta_carrito_201(client, cajero_headers):
    r = client.post(
        f"{BASE}/orders",
        json={"id_cliente": 1, "metodo_pago": "nequi",
              "lineas": [{"id_producto": 1, "cantidad": 4}, {"id_producto": 68, "cantidad": 2}]},
        headers=cajero_headers,
    )
    assert r.status_code == 201
    venta = r.json()
    assert venta["id_venta"] > 94_000
    assert venta["cliente"]["nombre"] == "Rosa Giraldo Velasco"
    assert venta["cajero"] == "cajero"
    assert venta["metodo_pago"] == "nequi"
    assert venta["total"] == 18800
    assert venta["lineas"][0] == {"id_producto": 1, "producto": "Pandebono", "categoria": "Panadería de queso",
                                  "cantidad": 4, "precio_unitario": 3200, "subtotal": 12800}


def test_venta_sin_cliente_es_consumidor_final_y_efectivo(client, cajero_headers):
    r = client.post(f"{BASE}/orders", json={"lineas": [{"id_producto": 9, "cantidad": 1}]}, headers=cajero_headers)
    assert r.status_code == 201
    assert r.json()["cliente"]["id_cliente"] == 0
    assert r.json()["metodo_pago"] == "efectivo"


def test_metodo_pago_invalido_422(client, cajero_headers):
    r = client.post(f"{BASE}/orders", json={"metodo_pago": "bitcoin", "lineas": [{"id_producto": 9, "cantidad": 1}]},
                    headers=cajero_headers)
    assert r.status_code == 422


def test_metodos_de_pago(client, cajero_headers):
    metodos = client.get(f"{BASE}/orders/payment-methods", headers=cajero_headers).json()
    assert metodos["nequi"] == "Nequi" and len(metodos) == 6


def test_venta_vacia_422_rn14(client, cajero_headers):
    assert client.post(f"{BASE}/orders", json={"lineas": []}, headers=cajero_headers).status_code == 422


def test_producto_inexistente_404_rn01(client, cajero_headers):
    r = client.post(f"{BASE}/orders", json={"lineas": [{"id_producto": 9999, "cantidad": 1}]}, headers=cajero_headers)
    assert r.status_code == 404


def test_cantidad_invalida_400_rn02_rn03(client, cajero_headers):
    for cantidad in (-5, 1.5):
        r = client.post(f"{BASE}/orders", json={"lineas": [{"id_producto": 9, "cantidad": cantidad}]},
                        headers=cajero_headers)
        assert r.status_code == 400


def test_todo_o_nada_no_guarda_nada_rn15(client, admin_headers, cajero_headers):
    antes = client.get(f"{BASE}/metrics/summary", headers=admin_headers).json()["numero_ventas"]

    r = client.post(
        f"{BASE}/orders",
        json={"lineas": [{"id_producto": 9, "cantidad": 1}, {"id_producto": 57, "cantidad": 1}]},
        headers=cajero_headers,
    )
    assert r.status_code == 400

    assert client.get(f"{BASE}/metrics/summary", headers=admin_headers).json()["numero_ventas"] == antes


def test_admin_no_registra_ventas_403(client, admin_headers):
    r = client.post(f"{BASE}/orders", json={"lineas": [{"id_producto": 9, "cantidad": 1}]}, headers=admin_headers)
    assert r.status_code == 403


def test_sin_token_401(client):
    assert client.get(f"{BASE}/orders").status_code == 401


def test_cajero_solo_ve_sus_ventas_rf14(client, cajero_headers, cajero2_headers):
    venta_juan = client.post(f"{BASE}/orders", json={"lineas": [{"id_producto": 9, "cantidad": 3}]},
                             headers=cajero2_headers).json()["id_venta"]

    ventas_cajero = client.get(f"{BASE}/orders", headers=cajero_headers).json()
    assert all(v["cajero"] == "cajero" for v in ventas_cajero)
    assert venta_juan not in [v["id_venta"] for v in ventas_cajero]

    assert client.get(f"{BASE}/orders/{venta_juan}", headers=cajero_headers).status_code == 403
    assert client.get(f"{BASE}/orders/{venta_juan}", headers=cajero2_headers).status_code == 200


def test_cajero_del_dataset_ve_su_historial(client):
    from tests.conftest import make_token

    headers = {"Authorization": f"Bearer {make_token('mcastillo', 'cajero')}"}
    ventas = client.get(f"{BASE}/orders", params={"limit": 50}, headers=headers).json()
    assert len(ventas) == 50
    assert all(v["cajero"] == "mcastillo" for v in ventas)
    assert ventas[0]["fecha"] >= ventas[-1]["fecha"]


def test_ventas_de_hoy_por_fecha(client, cajero_headers):
    hoy = date.today().isoformat()
    ventas = client.get(f"{BASE}/orders", params={"desde": hoy, "hasta": hoy}, headers=cajero_headers).json()
    assert len(ventas) >= 1
    assert all(v["fecha"].startswith(hoy) for v in ventas)


def test_admin_filtra_por_cajero_y_metodo_de_pago(client, admin_headers):
    ventas = client.get(f"{BASE}/orders", params={"cajero": "jrengifo", "metodo_pago": "nequi", "limit": 30},
                        headers=admin_headers).json()
    assert len(ventas) == 30
    assert all(v["cajero"] == "jrengifo" and v["metodo_pago"] == "nequi" for v in ventas)


def test_cajero_no_puede_ver_ventas_de_otro_cajero(client, cajero_headers):
    ventas = client.get(f"{BASE}/orders", params={"cajero": "jrengifo"}, headers=cajero_headers).json()
    assert all(v["cajero"] == "cajero" for v in ventas)


def test_historial_de_un_cliente(client, admin_headers, dataset):
    ventas = client.get(f"{BASE}/orders", params={"id_cliente": 1}, headers=admin_headers).json()
    assert len(ventas) > 0
    assert all(v["cliente"]["id_cliente"] == 1 for v in ventas)


def test_venta_inexistente_404(client, admin_headers):
    assert client.get(f"{BASE}/orders/9999999", headers=admin_headers).status_code == 404


# ---------- Métricas (semana del 2 al 8 de marzo de 2026, comparadas con los CSV) ----------

def test_resumen_del_dataset_rf02(client, admin_headers, dataset):
    s = client.get(f"{BASE}/metrics/summary", params=SEMANA, headers=admin_headers).json()

    ventas = dataset["ventas"]
    ingresos = sum(int(v["total"]) for v in ventas)
    assert s["numero_ventas"] == len(ventas)
    assert s["ingresos_totales"] == ingresos
    assert s["unidades_vendidas"] == sum(int(l["cantidad"]) for l in dataset["lineas"])
    assert s["clientes_activos"] == len({v["id_cliente"] for v in ventas if v["id_cliente"] != "0"})
    assert s["ticket_promedio"] == round(ingresos / len(ventas))


def test_ventas_por_dia_rf03(client, admin_headers, dataset):
    dias = client.get(f"{BASE}/metrics/sales-by-weekday", params=SEMANA, headers=admin_headers).json()

    esperado = Counter(date.fromisoformat(v["fecha"][:10]).isoweekday() for v in dataset["ventas"])
    assert [d["dia"] for d in dias] == ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    assert [d["ventas"] for d in dias] == [esperado[i] for i in range(1, 8)]


def test_ventas_por_hora(client, admin_headers, dataset):
    horas = client.get(f"{BASE}/metrics/sales-by-hour", params=SEMANA, headers=admin_headers).json()

    esperado = Counter(int(v["fecha"][11:13]) for v in dataset["ventas"])
    assert {h["hora"]: h["ventas"] for h in horas if h["ventas"]} == dict(esperado)
    assert horas[0]["etiqueta"] == "6 a. m."


def test_ventas_por_mes(client, admin_headers):
    meses = client.get(f"{BASE}/metrics/sales-by-month", params={"desde": "2025-01-01", "hasta": "2025-12-31"},
                       headers=admin_headers).json()
    assert [m["mes"] for m in meses] == [f"2025-{i:02d}" for i in range(1, 13)]
    # Diciembre es el mes más fuerte en una panadería.
    assert max(meses, key=lambda m: m["ingresos"])["mes"] == "2025-12"


def test_ventas_por_categoria(client, admin_headers, dataset):
    cats = client.get(f"{BASE}/metrics/sales-by-category", params=SEMANA, headers=admin_headers).json()

    assert sum(c["ingresos"] for c in cats) == sum(int(l["subtotal"]) for l in dataset["lineas"])
    assert cats == sorted(cats, key=lambda c: c["ingresos"], reverse=True)
    assert "Panadería de queso" in [c["categoria"] for c in cats]


def test_ventas_por_metodo_de_pago(client, admin_headers, dataset):
    pagos = client.get(f"{BASE}/metrics/sales-by-payment", params=SEMANA, headers=admin_headers).json()

    esperado = Counter(v["metodo_pago"] for v in dataset["ventas"])
    assert {p["metodo_pago"]: p["ventas"] for p in pagos} == dict(esperado)
    assert pagos[0]["metodo_pago"] == "efectivo"
    assert pagos[0]["nombre"] == "Efectivo"


def test_top_productos_rf04(client, admin_headers, dataset):
    top = client.get(f"{BASE}/metrics/top-products", params={**SEMANA, "limit": 3}, headers=admin_headers).json()

    ingresos = defaultdict(int)
    for l in dataset["lineas"]:
        ingresos[int(l["id_producto"])] += int(l["subtotal"])
    esperado = sorted(ingresos.items(), key=lambda x: x[1], reverse=True)[:3]

    assert [(p["id_producto"], p["ingresos"]) for p in top] == esperado


def test_top_productos_por_cantidad(client, admin_headers):
    top = client.get(f"{BASE}/metrics/top-products", params={**SEMANA, "orden": "cantidad", "limit": 5},
                     headers=admin_headers).json()
    assert [p["cantidad"] for p in top] == sorted((p["cantidad"] for p in top), reverse=True)


def test_top_clientes_con_nombre_rf06(client, admin_headers, dataset):
    top = client.get(f"{BASE}/metrics/top-customers", params={**SEMANA, "limit": 3}, headers=admin_headers).json()

    compras = Counter(int(v["id_cliente"]) for v in dataset["ventas"] if v["id_cliente"] != "0")
    assert top[0]["compras"] == max(compras.values())
    assert all(c["id_cliente"] != 0 for c in top)
    assert len(top[0]["nombre"].split()) >= 3  # nombre + dos apellidos


def test_productos_sin_ventas_rf05(client, admin_headers):
    sin_ventas = client.get(f"{BASE}/metrics/products-without-sales", params=SEMANA, headers=admin_headers).json()
    nombres = [p["nombre"] for p in sin_ventas]
    # El producto nuevo del catálogo no se ha vendido; la natilla está inactiva y no se lista.
    assert "Pan de bono con guayaba" in nombres
    assert "Natilla (porción)" not in nombres
    assert "Pandebono" not in nombres


def test_cajero_no_ve_metricas_403(client, cajero_headers):
    assert client.get(f"{BASE}/metrics/summary", headers=cajero_headers).status_code == 403
