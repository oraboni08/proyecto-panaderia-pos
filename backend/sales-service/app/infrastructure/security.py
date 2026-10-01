from dataclasses import dataclass

import jwt

from app.config import JWT_SECRET


ALGORITHM = "HS256"


class InvalidTokenError(Exception):
    pass


@dataclass
class TokenUser:
    usuario: str
    nombre: str
    rol: str
    token: str


def decode_token(token: str) -> TokenUser:
    """Verifica la firma y la vigencia del token emitido por auth-service.

    Se conserva el token original para reenviarlo a catalog-service.
    """

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
        token=token,
    )
