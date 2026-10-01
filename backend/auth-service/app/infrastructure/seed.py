from sqlalchemy.orm import Session

from app.config import ADMIN_PASSWORD, CAJERO_PASSWORD
from app.domain.models import ROL_ADMIN, ROL_CAJERO
from app.domain.services import UserService
from app.infrastructure.orm_models import UserORM
from app.infrastructure.repositories import SQLAlchemyUserRepository
from app.infrastructure.security import BcryptPasswordHasher


def seed_users(session: Session) -> int:
    """Crea los usuarios iniciales (RN21) solo si la tabla está vacía."""

    if session.query(UserORM).first() is not None:
        return 0

    service = UserService(SQLAlchemyUserRepository(session), BcryptPasswordHasher())

    service.create_user("Administrador", "admin", ADMIN_PASSWORD, ROL_ADMIN)
    service.create_user("Cajero", "cajero", CAJERO_PASSWORD, ROL_CAJERO)

    print("[auth] Usuarios iniciales creados: admin, cajero")

    return 2
