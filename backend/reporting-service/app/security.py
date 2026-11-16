"""Validación del token JWT emitido por auth-service (misma clave compartida por Docker secret)."""

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import JWT_SECRET


bearer = HTTPBearer(auto_error=False)


def require_admin(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    """Los reportes solo los ve el administrador."""

    if credentials is None:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión", headers={"WWW-Authenticate": "Bearer"})

    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="La sesión expiró, inicia sesión de nuevo")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

    if payload.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Solo el administrador puede ver los reportes")

    return payload
