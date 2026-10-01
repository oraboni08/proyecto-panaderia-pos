from datetime import datetime
from typing import Literal

from pydantic import BaseModel


Rol = Literal["admin", "cajero"]


class LoginDTO(BaseModel):
    usuario: str
    password: str


class TokenResponseDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: str
    nombre: str
    rol: str


class CreateUserDTO(BaseModel):
    nombre: str
    usuario: str
    password: str
    rol: Rol


class PatchUserDTO(BaseModel):
    activo: bool


class UserResponseDTO(BaseModel):
    id_usuario: int
    nombre: str
    usuario: str
    rol: str
    activo: bool
    creado_en: datetime | None
