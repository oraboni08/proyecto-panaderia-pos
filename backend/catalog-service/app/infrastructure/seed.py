import csv
from pathlib import Path

from sqlalchemy.orm import Session

from app.domain.models import TIPO_PESO, TIPO_UNIDAD
from app.infrastructure.orm_models import ProductORM


# Productos que se venden por peso (precio por kg). Ver Fase 1, sección 2.4.
PRODUCTOS_POR_PESO = {26, 27, 28, 29, 32, 35, 42}

NOMBRES_AJUSTADOS = {
    "Huevos": "Huevos (docena)",
}


def seed_products(session: Session, dataset_dir: Path) -> int:
    """Carga producto.csv solo si la tabla está vacía. Devuelve cuántos cargó."""

    if session.query(ProductORM).first() is not None:
        return 0

    path = dataset_dir / "producto.csv"

    if not path.exists():
        print(f"[catalog] No se encontró {path}; el catálogo inicia vacío")
        return 0

    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    for row in rows:

        id_producto = int(row["id_producto"])
        nombre = " ".join(row["nombre_producto"].split())

        session.add(
            ProductORM(
                id_producto=id_producto,
                nombre=NOMBRES_AJUSTADOS.get(nombre, nombre),
                precio=float(row["precio_unidad"]),
                tipo_venta=TIPO_PESO if id_producto in PRODUCTOS_POR_PESO else TIPO_UNIDAD,
                activo=True,
            )
        )

    session.commit()

    print(f"[catalog] {len(rows)} productos cargados desde {path.name}")

    return len(rows)
