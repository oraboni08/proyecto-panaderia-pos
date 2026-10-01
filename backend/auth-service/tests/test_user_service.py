"""Pruebas unitarias de las reglas de usuarios e inicio de sesión.

Usan dobles en memoria: no hay base de datos, ni bcrypt, ni JWT.
"""

import pytest

from app.domain.exceptions import (
    AuthenticationError,
    BusinessRuleError,
    ConflictError,
    NotFoundError,
)
from app.domain.models import User
from app.domain.repositories import PasswordHasher, TokenProvider, UserRepository
from app.domain.services import AuthService, UserService


class InMemoryUserRepository(UserRepository):

    def __init__(self):
        self.users: dict[int, User] = {}

    def create(self, user):
        user.id = len(self.users) + 1
        self.users[user.id] = User(**vars(user))
        return User(**vars(user))

    def get_by_id(self, user_id):
        u = self.users.get(user_id)
        return User(**vars(u)) if u else None

    def get_by_username(self, usuario):
        for u in self.users.values():
            if u.usuario == usuario:
                return User(**vars(u))
        return None

    def list_all(self):
        return list(self.users.values())

    def update(self, user):
        self.users[user.id] = User(**vars(user))
        return User(**vars(user))


class FakeHasher(PasswordHasher):

    def hash(self, password):
        return f"hash::{password}"

    def verify(self, password, password_hash):
        return password_hash == f"hash::{password}"


class FakeTokens(TokenProvider):

    def create_token(self, user):
        return f"token-de-{user.usuario}"


@pytest.fixture
def repo():
    return InMemoryUserRepository()


@pytest.fixture
def users(repo):
    return UserService(repo, FakeHasher())


@pytest.fixture
def auth(repo):
    return AuthService(repo, FakeHasher(), FakeTokens())


def test_crear_usuario_guarda_contrasena_cifrada_rnf05(users, repo):
    u = users.create_user("  Juan   Pérez ", " Juan ", "secreto123", "cajero")

    assert u.nombre == "Juan Pérez"
    assert u.usuario == "juan"
    assert repo.users[u.id].password_hash != "secreto123"


def test_usuario_repetido_rn18(users):
    users.create_user("Juan", "juan", "secreto123", "cajero")

    with pytest.raises(ConflictError):
        users.create_user("Otro Juan", "JUAN", "secreto456", "cajero")


def test_contrasena_corta_rn18(users):
    with pytest.raises(BusinessRuleError):
        users.create_user("Ana", "ana", "1234567", "cajero")


def test_rol_invalido_rn18(users):
    with pytest.raises(BusinessRuleError):
        users.create_user("Ana", "ana", "secreto123", "gerente")


@pytest.mark.parametrize("usuario", ["", "ana maria"])
def test_usuario_vacio_o_con_espacios(users, usuario):
    with pytest.raises(BusinessRuleError):
        users.create_user("Ana", usuario, "secreto123", "cajero")


def test_login_correcto_devuelve_token(users, auth):
    users.create_user("Ana", "ana", "secreto123", "admin")

    token, user = auth.login("ANA", "secreto123")

    assert token == "token-de-ana"
    assert user.rol == "admin"


def test_login_contrasena_incorrecta(users, auth):
    users.create_user("Ana", "ana", "secreto123", "admin")

    with pytest.raises(AuthenticationError):
        auth.login("ana", "otra-cosa")


def test_login_usuario_inexistente(auth):
    with pytest.raises(AuthenticationError):
        auth.login("nadie", "secreto123")


def test_usuario_desactivado_no_inicia_sesion_rn19(users, auth):
    u = users.create_user("Ana", "ana", "secreto123", "cajero")
    users.set_active(u.id, False, "admin")

    with pytest.raises(AuthenticationError):
        auth.login("ana", "secreto123")


def test_reactivar_usuario(users, auth):
    u = users.create_user("Ana", "ana", "secreto123", "cajero")
    users.set_active(u.id, False, "admin")
    users.set_active(u.id, True, "admin")

    token, _ = auth.login("ana", "secreto123")
    assert token


def test_admin_no_puede_desactivarse_a_si_mismo_rn20(users):
    u = users.create_user("Jefe", "jefe", "secreto123", "admin")

    with pytest.raises(BusinessRuleError):
        users.set_active(u.id, False, "jefe")


def test_desactivar_usuario_inexistente(users):
    with pytest.raises(NotFoundError):
        users.set_active(99, False, "admin")
