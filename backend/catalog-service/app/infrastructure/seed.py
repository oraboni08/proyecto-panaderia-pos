"""Carga inicial del catálogo a partir del dataset (backend/dataset).

    productos.csv          id_producto;nombre;categoria;precio;activo
    cambios_producto.csv   historial: creación, alza de precios 2026 y productos de temporada

Solo se ejecuta si la tabla de productos está vacía. El dataset lo produce
backend/dataset/generar_dataset.py.
"""

import csv
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.infrastructure.orm_models import ProductChangeORM, ProductORM


def _read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def seed_products(session: Session, dataset_dir: Path) -> int:
    """Carga productos.csv (y su historial) solo si la tabla está vacía. Devuelve cuántos cargó."""

    if session.query(ProductORM).first() is not None:
        return 0

    path = dataset_dir / "productos.csv"

    if not path.exists():
        print(f"[catalog] No se encontró {path}; el catálogo inicia vacío")
        return 0

    rows = _read_csv(path)

    session.add_all(
        ProductORM(
            id_producto=int(row["id_producto"]),
            nombre=row["nombre"].strip(),
            categoria=row["categoria"].strip(),
            precio=int(row["precio"]),
            activo=row.get("activo", "true").strip().lower() == "true",
        )
        for row in rows
    )
    session.flush()

    cambios_path = dataset_dir / "cambios_producto.csv"
    cambios = _read_csv(cambios_path) if cambios_path.exists() else []

    session.add_all(
        ProductChangeORM(
            id_producto=int(c["id_producto"]),
            accion=c["accion"],
            campo=c["campo"] or None,
            valor_anterior=c["valor_anterior"] or None,
            valor_nuevo=c["valor_nuevo"],
            usuario=c["usuario"],
            fecha=datetime.strptime(c["fecha"], "%Y-%m-%d %H:%M:%S"),
        )
        for c in cambios
    )

    session.commit()

    print(f"[catalog] {len(rows)} productos y {len(cambios)} cambios cargados desde el dataset")

    return len(rows)
