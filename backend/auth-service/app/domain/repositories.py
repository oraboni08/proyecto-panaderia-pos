from abc import ABC, abstractmethod

from app.domain.models import User


class UserRepository(ABC):
    """Contrato que debe cumplir cualquier almacenamiento de usuarios."""

    @abstractmethod
    def create(self, user: User) -> User:
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> User | None:
        pass

    @abstractmethod
    def get_by_username(self, usuario: str) -> User | None:
        pass

    @abstractmethod
    def list_all(self) -> list[User]:
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        pass


class PasswordHasher(ABC):
    """Contrato para cifrar y verificar contraseñas."""

    @abstractmethod
    def hash(self, password: str) -> str:
        pass

    @abstractmethod
    def verify(self, password: str, password_hash: str) -> bool:
        pass


class TokenProvider(ABC):
    """Contrato para emitir el token de sesión de un usuario."""

    @abstractmethod
    def create_token(self, user: User) -> str:
        pass
