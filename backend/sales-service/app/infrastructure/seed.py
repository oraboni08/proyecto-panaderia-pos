"""Carga inicial de clientes y ventas a partir del dataset (Fase 2, sección 3.4).

Para copiar nombre, tipo y precio de cada producto en las ventas históricas se lee
producto.csv del dataset (no la base de datos de catalog-service, que no le pertenece).
"""

import csv
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.domain.models import CONSUMIDOR_FINAL_ID, CONSUMIDOR_FINAL_NOMBRE, TIPO_PESO, TIPO_UNIDAD
from app.infrastructure.orm_models import CustomerORM, OrderLineORM, OrderORM


# Deben coincidir con catalog-service (Fase 1, sección 2.4).
PRODUCTOS_POR_PESO = {26, 27, 28, 29, 32, 35, 42}
NOMBRES_AJUSTADOS = {"Huevos": "Huevos (docena)"}


def _read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def seed_sales(session: Session, dataset_dir: Path) -> None:

    if session.query(CustomerORM).first() is None:
        _seed_customers(session, dataset_dir)

    if session.query(OrderORM).first() is None:
        _seed_orders(session, dataset_dir)


def _seed_customers(session: Session, dataset_dir: Path) -> None:

    session.add(CustomerORM(id_cliente=CONSUMIDOR_FINAL_ID, nombre=CONSUMIDOR_FINAL_NOMBRE))

    path = dataset_dir / "cliente.csv"
    rows = _read_csv(path) if path.exists() else []

    for row in rows:
        id_cliente = int(row["id_cliente"])
        session.add(CustomerORM(id_cliente=id_cliente, nombre=f"Cliente {id_cliente}"))

    session.commit()

    print(f"[sales] {len(rows)} clientes cargados + Consumidor final")


def _seed_orders(session: Session, dataset_dir: Path) -> None:

    op_path = dataset_dir / "operacion.csv"
    prod_path = dataset_dir / "producto.csv"

    if not (op_path.exists() and prod_path.exists()):
        print("[sales] No se encontró el dataset; las ventas inician vacías")
        return

    productos = {}

    for row in _read_csv(prod_path):
        pid = int(row["id_producto"])
        nombre = " ".join(row["nombre_producto"].split())
        productos[pid] = (
            NOMBRES_AJUSTADOS.get(nombre, nombre),
            TIPO_PESO if pid in PRODUCTOS_POR_PESO else TIPO_UNIDAD,
            float(row["precio_unidad"]),
        )

    operaciones = _read_csv(op_path)

    for row in operaciones:

        pid = int(row["id_producto"])
        nombre, tipo, precio = productos[pid]
        cantidad = float(row["cantidad_producto"])
        subtotal = round(precio * cantidad, 2)

        session.add(
            OrderORM(
                id_venta=int(row["id_operacion"]),
                id_cliente=int(row["id_cliente"]),
                cajero=None,
                fecha=datetime.strptime(row["fecha_operacion"], "%Y-%m-%d"),
                total=subtotal,
                lineas=[
                    OrderLineORM(
                        id_producto=pid,
                        nombre_producto=nombre,
                        tipo_venta=tipo,
                        cantidad=cantidad,
                        precio_unitario=precio,
                        subtotal=subtotal,
                    )
                ],
            )
        )

    session.commit()

    print(f"[sales] {len(operaciones)} ventas históricas cargadas")
