import os
from pathlib import Path


SERVICE_DIR = Path(__file__).resolve().parent.parent


def _secreto(nombre: str, defecto: str) -> str:
    """Lee un valor sensible. En Docker Swarm llega como secret (archivo en /run/secrets,
    variable NOMBRE_FILE); en el computador local, como variable de entorno o el valor por defecto."""

    ruta = os.getenv(f"{nombre}_FILE")
    if ruta and Path(ruta).exists():
        return Path(ruta).read_text(encoding="utf-8").strip()
    return os.getenv(nombre, defecto)


def _url_base_datos(archivo_sqlite: str) -> str:
    """PostgreSQL si está definido DB_HOST (Docker Swarm); si no, SQLite local."""

    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]

    host = os.getenv("DB_HOST")
    if host:
        usuario = os.getenv("DB_USER", "panaderia")
        clave = _secreto("DB_PASSWORD", "panaderia")
        nombre = os.getenv("DB_NAME", "reports_db")
        return f"postgresql+psycopg://{usuario}:{clave}@{host}:5432/{nombre}"

    return f"sqlite:///{SERVICE_DIR / archivo_sqlite}"


DATABASE_URL = _url_base_datos("reports.db")

JWT_SECRET = _secreto("JWT_SECRET", "clave-solo-para-desarrollo-cambiar-en-produccion")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
