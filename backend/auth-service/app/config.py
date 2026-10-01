import os
from pathlib import Path


SERVICE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{SERVICE_DIR / 'auth.db'}",
)

JWT_SECRET = os.getenv("JWT_SECRET", "clave-solo-para-desarrollo-cambiar-en-produccion")

TOKEN_MINUTES = int(os.getenv("TOKEN_MINUTES", "480"))

# Contraseñas de los usuarios iniciales (RN21). En el despliegue se definen por variable de entorno.
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin12345")
CAJERO_PASSWORD = os.getenv("CAJERO_PASSWORD", "cajero12345")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
