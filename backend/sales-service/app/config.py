import os
from pathlib import Path


SERVICE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{SERVICE_DIR / 'sales.db'}",
)

DATASET_DIR = Path(os.getenv("DATASET_DIR", SERVICE_DIR.parent / "dataset"))

JWT_SECRET = os.getenv("JWT_SECRET", "clave-solo-para-desarrollo-cambiar-en-produccion")

# Dirección de catalog-service. Sales le consulta los productos por REST.
CATALOG_URL = os.getenv("CATALOG_URL", "http://127.0.0.1:8002").rstrip("/")

CATALOG_TIMEOUT_SECONDS = float(os.getenv("CATALOG_TIMEOUT_SECONDS", "5"))

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
