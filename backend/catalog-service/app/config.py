import os
from pathlib import Path


SERVICE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{SERVICE_DIR / 'catalog.db'}",
)

DATASET_DIR = Path(os.getenv("DATASET_DIR", SERVICE_DIR.parent / "dataset"))

JWT_SECRET = os.getenv("JWT_SECRET", "clave-solo-para-desarrollo-cambiar-en-produccion")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
