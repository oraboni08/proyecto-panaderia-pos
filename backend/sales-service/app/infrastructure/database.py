"""Conexión a la base de datos del servicio.

En el computador local (run_dev.py y pruebas) se usa SQLite. En Docker Swarm la variable
DATABASE_URL apunta a PostgreSQL, que comparten todas las réplicas del servicio.
"""

import time

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL


ES_SQLITE = DATABASE_URL.startswith("sqlite")


engine = create_engine(
    DATABASE_URL,
    # SQLite no deja usar la conexión desde otro hilo; PostgreSQL no necesita esto.
    connect_args={"check_same_thread": False} if ES_SQLITE else {},
    # Antes de usar una conexión del pool verifica que siga viva (por si PostgreSQL se reinició).
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# Número arbitrario para el candado de PostgreSQL (pg_advisory_lock).
CANDADO_INICIO = 20261117


def _esperar_base(intentos: int = 30, espera: float = 2.0) -> None:
    """En Swarm el servicio puede arrancar antes que PostgreSQL: reintenta la conexión."""

    for intento in range(1, intentos + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as error:  # noqa: BLE001
            print(f"[db] PostgreSQL aún no responde (intento {intento}/{intentos}): {error.__class__.__name__}")
            time.sleep(espera)

    raise RuntimeError("No se pudo conectar a la base de datos")


def _sincronizar_secuencias(conn) -> None:
    """La carga inicial inserta ids explícitos (los del dataset). PostgreSQL no avanza
    solo la secuencia del id en ese caso, así que la ponemos después del id más alto
    para que la siguiente venta, cliente o producto no choque con uno existente."""

    for tabla in inspect(conn).get_table_names():
        for columna in inspect(conn).get_pk_constraint(tabla)["constrained_columns"]:
            secuencia = conn.execute(
                text("SELECT pg_get_serial_sequence(:t, :c)"), {"t": tabla, "c": columna}
            ).scalar()
            if secuencia:
                conn.execute(text(
                    f'SELECT setval(:s, COALESCE((SELECT MAX("{columna}") FROM "{tabla}"), 0) + 1, false)'
                ), {"s": secuencia})


def init_database(metadata, seed) -> None:
    """Crea las tablas y hace la carga inicial.

    Con varias réplicas arrancando a la vez, todas intentarían crear las tablas y cargar el
    dataset al mismo tiempo. En PostgreSQL un candado (advisory lock) hace que solo una lo
    haga; las demás esperan y, al entrar, ven que los datos ya están y no cargan nada.
    """

    if ES_SQLITE:
        metadata.create_all(bind=engine)
        with SessionLocal() as session:
            seed(session)
        return

    _esperar_base()

    with engine.connect() as candado:
        candado.execute(text("SELECT pg_advisory_lock(:k)"), {"k": CANDADO_INICIO})
        try:
            metadata.create_all(bind=engine)
            with SessionLocal() as session:
                seed(session)
            with engine.begin() as conn:
                _sincronizar_secuencias(conn)
        finally:
            candado.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": CANDADO_INICIO})
            candado.commit()
