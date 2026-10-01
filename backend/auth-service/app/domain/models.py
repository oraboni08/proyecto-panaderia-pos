from dataclasses import dataclass
from datetime import datetime


ROL_ADMIN = "admin"
ROL_CAJERO = "cajero"
ROLES = (ROL_ADMIN, ROL_CAJERO)

MIN_PASSWORD_LENGTH = 8


@dataclass
class User:
    id: int | None
    nombre: str
    usuario: str
    password_hash: str
    rol: str
    activo: bool = True
    creado_en: datetime | None = None
