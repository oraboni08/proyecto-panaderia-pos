from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import JWT_SECRET, TOKEN_MINUTES
from app.domain.models import User
from app.domain.repositories import PasswordHasher, TokenProvider


ALGORITHM = "HS256"


class BcryptPasswordHasher(PasswordHasher):

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


class JwtTokenProvider(TokenProvider):

    def create_token(self, user: User) -> str:

        payload = {
            "sub": user.usuario,
            "nombre": user.nombre,
            "rol": user.rol,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES),
        }

        return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


class InvalidTokenError(Exception):
    pass


@dataclass
class TokenUser:
    usuario: str
    nombre: str
    rol: str


def decode_token(token: str) -> TokenUser:
    """Verifica la firma y la vigencia del token."""

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise InvalidTokenError("La sesión expiró, inicia sesión de nuevo")
    except jwt.InvalidTokenError:
        raise InvalidTokenError("Token inválido")

    return TokenUser(
        usuario=payload["sub"],
        nombre=payload.get("nombre", payload["sub"]),
        rol=payload["rol"],
    )
