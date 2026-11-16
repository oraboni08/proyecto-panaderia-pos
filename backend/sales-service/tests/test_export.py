"""Pruebas del endpoint que usa hdfs-exporter para copiar las ventas a HDFS."""

URL = "/api/v1/sales/export/lines"


def test_export_requiere_admin(client, cajero_headers):
    assert client.get(URL).status_code == 401
    assert client.get(URL, headers=cajero_headers).status_code == 403


def test_export_devuelve_lineas_en_orden_y_por_bloques(client, admin_headers):

    primeras = client.get(URL, params={"limit": 3}, headers=admin_headers).json()
    assert len(primeras) == 3
    ids = [l["id_linea"] for l in primeras]
    assert ids == sorted(ids)

    # El siguiente bloque empieza después del último id recibido: no se repiten líneas.
    siguientes = client.get(URL, params={"after_id": ids[-1], "limit": 3}, headers=admin_headers).json()
    assert all(l["id_linea"] > ids[-1] for l in siguientes)

    linea = primeras[0]
    for campo in ("id_venta", "fecha", "metodo_pago", "producto", "categoria", "cantidad", "subtotal"):
        assert campo in linea


def test_export_incluye_una_venta_nueva(client, admin_headers, cajero_headers):

    # Recorre todos los bloques (el dataset tiene ~200.000 líneas) hasta el último id.
    ultimo = 0
    while bloque := client.get(URL, params={"after_id": ultimo, "limit": 50000}, headers=admin_headers).json():
        ultimo = bloque[-1]["id_linea"]

    venta = client.post(
        "/api/v1/sales/orders",
        json={"id_cliente": 0, "metodo_pago": "nequi", "lineas": [{"id_producto": 1, "cantidad": 2}]},
        headers=cajero_headers,
    )
    assert venta.status_code == 201

    nuevas = client.get(URL, params={"after_id": ultimo}, headers=admin_headers).json()
    assert len(nuevas) == 1
    assert nuevas[0]["id_venta"] == venta.json()["id_venta"]
    assert nuevas[0]["metodo_pago"] == "nequi"
    assert nuevas[0]["cantidad"] == 2
