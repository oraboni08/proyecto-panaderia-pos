"""Levanta los tres microservicios (y el front-end) en el computador local para desarrollo.

Uso (desde la carpeta backend, con el entorno virtual activado):

    python run_dev.py            # servicios + front-end
    python run_dev.py --no-front # solo los servicios

    auth-service     http://127.0.0.1:8001/api/v1/auth/docs
    catalog-service  http://127.0.0.1:8002/api/v1/catalog/docs
    sales-service    http://127.0.0.1:8003/api/v1/sales/docs
    front-end        http://127.0.0.1:8080

Ctrl + C detiene todo.
"""

import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"

SERVICES = [
    ("auth-service", 8001),
    ("catalog-service", 8002),
    ("sales-service", 8003),
]

ENV = {
    **os.environ,
    "JWT_SECRET": os.getenv("JWT_SECRET", "clave-solo-para-desarrollo-cambiar-en-produccion"),
    "CATALOG_URL": "http://127.0.0.1:8002",
    "PYTHONIOENCODING": "utf-8",
}


# Señal de que la base local ya tiene el modelo de datos actual (dataset colombiano, sin venta por peso).
# Si una base creada con una versión anterior no la cumple, se aparta como respaldo y el servicio
# crea una nueva desde backend/dataset al arrancar.
VERIFICACION_ESQUEMA = {
    "auth-service": ("auth.db", "SELECT 1 FROM usuarios WHERE usuario = 'mcastillo'"),
    "catalog-service": ("catalog.db", "SELECT categoria FROM productos LIMIT 1"),
    "sales-service": ("sales.db", "SELECT metodo_pago, (SELECT categoria FROM lineas_venta LIMIT 1) FROM ventas LIMIT 1"),
}


def apartar_bases_viejas() -> None:

    for servicio, (archivo, consulta) in VERIFICACION_ESQUEMA.items():
        db = BACKEND_DIR / servicio / archivo
        if not db.exists():
            continue
        try:
            with sqlite3.connect(db) as con:
                vigente = con.execute(consulta).fetchone() is not None
        except sqlite3.Error:
            vigente = False
        if not vigente:
            respaldo = db.with_name(f"{db.stem}_version_anterior_{time.strftime('%Y%m%d_%H%M%S')}.db")
            db.rename(respaldo)
            print(f"  {servicio}: la base local era de una versión anterior; se guardó como {respaldo.name} y se crea una nueva.")


def main() -> None:

    apartar_bases_viejas()
    processes = []

    for name, port in SERVICES:
        processes.append(
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)],
                cwd=BACKEND_DIR / name,
                env=ENV,
            )
        )
        print(f"  {name:<16} http://127.0.0.1:{port}/api/v1/{name.split('-')[0]}/docs")

    if "--no-front" not in sys.argv and FRONTEND_DIR.exists():
        processes.append(
            subprocess.Popen(
                [sys.executable, "-m", "http.server", "8080", "--bind", "127.0.0.1"],
                cwd=FRONTEND_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        )
        print("  front-end        http://127.0.0.1:8080")

    print("\nCtrl + C para detener.\n")

    try:
        while all(p.poll() is None for p in processes):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for p in processes:
            if p.poll() is None:
                p.terminate()
        for p in processes:
            p.wait()


if __name__ == "__main__":
    main()
