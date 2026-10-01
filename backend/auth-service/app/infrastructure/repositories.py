from sqlalchemy.orm import Session

from app.domain.models import User
from app.domain.repositories import UserRepository
from app.infrastructure.orm_models import UserORM


def _to_user(db_user: UserORM) -> User:
    return User(
        id=db_user.id_usuario,
        nombre=db_user.nombre,
        usuario=db_user.usuario,
        password_hash=db_user.password_hash,
        rol=db_user.rol,
        activo=db_user.activo,
        creado_en=db_user.creado_en,
    )


class SQLAlchemyUserRepository(UserRepository):

    def __init__(self, session: Session):
        self.session = session

    def create(self, user: User) -> User:

        db_user = UserORM(
            nombre=user.nombre,
            usuario=user.usuario,
            password_hash=user.password_hash,
            rol=user.rol,
            activo=user.activo,
            creado_en=user.creado_en,
        )

        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)

        return _to_user(db_user)

    def get_by_id(self, user_id: int) -> User | None:

        db_user = self.session.get(UserORM, user_id)

        if db_user is None:
            return None

        return _to_user(db_user)

    def get_by_username(self, usuario: str) -> User | None:

        db_user = (
            self.session
            .query(UserORM)
            .filter(UserORM.usuario == usuario)
            .first()
        )

        if db_user is None:
            return None

        return _to_user(db_user)

    def list_all(self) -> list[User]:

        return [
            _to_user(db_user)
            for db_user in self.session.query(UserORM).order_by(UserORM.id_usuario).all()
        ]

    def update(self, user: User) -> User:

        db_user = self.session.get(UserORM, user.id)

        db_user.nombre = user.nombre
        db_user.rol = user.rol
        db_user.activo = user.activo

        self.session.commit()
        self.session.refresh(db_user)

        return _to_user(db_user)
