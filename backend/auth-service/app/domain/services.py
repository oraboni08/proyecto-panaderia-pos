from datetime import datetime

from app.domain.exceptions import (
    AuthenticationError,
    BusinessRuleError,
    ConflictError,
    NotFoundError,
)
from app.domain.models import MIN_PASSWORD_LENGTH, ROLES, User
from app.domain.repositories import PasswordHasher, TokenProvider, UserRepository


class AuthService:

    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenProvider,
    ):
        self.users = users
        self.hasher = hasher
        self.tokens = tokens

    def login(self, usuario: str, password: str) -> tuple[str, User]:

        user = self.users.get_by_username(usuario.strip().lower())

        # El mismo mensaje para usuario inexistente o contraseña incorrecta:
        # no se le da pistas a un atacante sobre qué usuarios existen.
        if user is None or not self.hasher.verify(password, user.password_hash):
            raise AuthenticationError("Usuario o contraseña incorrectos")

        if not user.activo:
            raise AuthenticationError("El usuario está desactivado")

        return self.tokens.create_token(user), user


class UserService:

    def __init__(self, users: UserRepository, hasher: PasswordHasher):
        self.users = users
        self.hasher = hasher

    def list_users(self) -> list[User]:
        return self.users.list_all()

    def get_user(self, user_id: int) -> User:

        user = self.users.get_by_id(user_id)

        if user is None:
            raise NotFoundError("Usuario no encontrado")

        return user

    def get_by_username(self, usuario: str) -> User:

        user = self.users.get_by_username(usuario)

        if user is None:
            raise NotFoundError("Usuario no encontrado")

        return user

    def create_user(
        self,
        nombre: str,
        usuario: str,
        password: str,
        rol: str,
    ) -> User:

        nombre = " ".join(nombre.split())
        usuario = usuario.strip().lower()

        if not nombre:
            raise BusinessRuleError("El nombre no puede estar vacío")

        if not usuario or " " in usuario:
            raise BusinessRuleError("El usuario no puede estar vacío ni tener espacios")

        if len(password) < MIN_PASSWORD_LENGTH:
            raise BusinessRuleError(
                f"La contraseña debe tener mínimo {MIN_PASSWORD_LENGTH} caracteres"
            )

        if rol not in ROLES:
            raise BusinessRuleError("El rol debe ser 'admin' o 'cajero'")

        if self.users.get_by_username(usuario) is not None:
            raise ConflictError(f"El usuario '{usuario}' ya existe")

        user = User(
            id=None,
            nombre=nombre,
            usuario=usuario,
            password_hash=self.hasher.hash(password),
            rol=rol,
            activo=True,
            creado_en=datetime.now(),
        )

        return self.users.create(user)

    def set_active(self, user_id: int, activo: bool, usuario_actual: str) -> User:

        user = self.get_user(user_id)

        if not activo and user.usuario == usuario_actual:
            raise BusinessRuleError("No puedes desactivar tu propio usuario")

        if user.activo == activo:
            return user

        user.activo = activo

        return self.users.update(user)
