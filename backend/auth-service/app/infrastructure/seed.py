from sqlalchemy.orm import Session

from app.config import ADMIN_PASSWORD, CAJERO_PASSWORD
from app.domain.models import ROL_ADMIN, ROL_CAJERO
from app.domain.services import UserService
from app.infrastructure.orm_models import UserORM
from app.infrastructure.repositories import SQLAlchemyUserRepository
from app.infrastructure.security import BcryptPasswordHasher


# Cajeros que aparecen en el dataset de ventas (backend/dataset/ventas.csv):
# turno de la mañana (6:00-14:00) y de la tarde (14:00-21:00).
CAJEROS_DATASET = [
    ("Marcela Castillo", "mcastillo"),
    ("Jhonatan Rengifo", "jrengifo"),
    ("Luisa Valencia", "lvalencia"),
    ("Daniela Mosquera", "dmosquera"),
]


def seed_users(session: Session) -> int:
    """Crea los usuarios iniciales (RN21) solo si la tabla está vacía."""

    if session.query(UserORM).first() is not None:
        return 0

    service = UserService(SQLAlchemyUserRepository(session), BcryptPasswordHasher())

    service.create_user("Administrador", "admin", ADMIN_PASSWORD, ROL_ADMIN)
    service.create_user("Cajero de pruebas", "cajero", CAJERO_PASSWORD, ROL_CAJERO)

    for nombre, usuario in CAJEROS_DATASET:
        service.create_user(nombre, usuario, CAJERO_PASSWORD, ROL_CAJERO)

    usuarios = ["admin", "cajero"] + [u for _, u in CAJEROS_DATASET]
    print(f"[auth] Usuarios iniciales creados: {', '.join(usuarios)}")

    return len(usuarios)
