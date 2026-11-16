"""Carga inicial de clientes y ventas a partir del dataset (backend/dataset).

    clientes.csv       clientes registrados con cédula, teléfono, correo y dirección
    ventas.csv         encabezado de cada venta (fecha y hora, cliente, cajero, método de pago)
    lineas_venta.csv   productos de cada venta con el precio que tenían ese día
    productos.csv      solo para copiar el nombre y la categoría en cada línea

Para copiar nombre y categoría se lee productos.csv del dataset, no la base de datos de
catalog-service, que no le pertenece a este servicio. Se usan inserciones en bloque:
son ~95.000 ventas y ~200.000 líneas y así cargan en pocos segundos.
"""

import csv
from datetime import datetime
from pathlib import Path

from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.domain.models import CONSUMIDOR_FINAL_ID, CONSUMIDOR_FINAL_NOMBRE
from app.infrastructure.orm_models import CustomerORM, OrderLineORM, OrderORM


LOTE = 20_000
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


def _read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _insert_en_lotes(session: Session, tabla, filas: list[dict]) -> None:
    for i in range(0, len(filas), LOTE):
        session.execute(insert(tabla), filas[i:i + LOTE])


def seed_sales(session: Session, dataset_dir: Path) -> None:

    if session.query(CustomerORM).first() is None:
        _seed_customers(session, dataset_dir)

    if session.query(OrderORM).first() is None:
        _seed_orders(session, dataset_dir)


def _seed_customers(session: Session, dataset_dir: Path) -> None:

    session.add(CustomerORM(id_cliente=CONSUMIDOR_FINAL_ID, nombre=CONSUMIDOR_FINAL_NOMBRE))
    session.flush()

    path = dataset_dir / "clientes.csv"
    rows = _read_csv(path) if path.exists() else []

    _insert_en_lotes(session, CustomerORM, [
        {
            "id_cliente": int(r["id_cliente"]),
            "nombre": r["nombre"],
            "tipo_documento": r["tipo_documento"] or None,
            "documento": r["documento"] or None,
            "telefono": r["telefono"] or None,
            "correo": r["correo"] or None,
            "direccion": r["direccion"] or None,
            "barrio": r["barrio"] or None,
            "ciudad": r["ciudad"] or None,
            "creado_en": datetime.strptime(r["fecha_registro"], FORMATO_FECHA) if r["fecha_registro"] else None,
        }
        for r in rows
    ])

    session.commit()

    print(f"[sales] {len(rows)} clientes cargados + Consumidor final")


def _seed_orders(session: Session, dataset_dir: Path) -> None:

    ventas_path = dataset_dir / "ventas.csv"
    lineas_path = dataset_dir / "lineas_venta.csv"
    prod_path = dataset_dir / "productos.csv"

    if not (ventas_path.exists() and lineas_path.exists() and prod_path.exists()):
        print("[sales] No se encontró el dataset; las ventas inician vacías")
        return

    productos = {int(p["id_producto"]): (p["nombre"], p["categoria"]) for p in _read_csv(prod_path)}

    ventas = _read_csv(ventas_path)

    _insert_en_lotes(session, OrderORM, [
        {
            "id_venta": int(v["id_venta"]),
            "id_cliente": int(v["id_cliente"]),
            "cajero": v["cajero"] or None,
            "fecha": datetime.strptime(v["fecha"], FORMATO_FECHA),
            "metodo_pago": v["metodo_pago"],
            "total": int(v["total"]),
        }
        for v in ventas
    ])

    lineas = _read_csv(lineas_path)

    _insert_en_lotes(session, OrderLineORM, [
        {
            "id_venta": int(l["id_venta"]),
            "id_producto": int(l["id_producto"]),
            "nombre_producto": productos[int(l["id_producto"])][0],
            "categoria": productos[int(l["id_producto"])][1],
            "cantidad": int(l["cantidad"]),
            "precio_unitario": int(l["precio_unitario"]),
            "subtotal": int(l["subtotal"]),
        }
        for l in lineas
    ])

    session.commit()

    print(f"[sales] {len(ventas)} ventas históricas y {len(lineas)} líneas cargadas")
