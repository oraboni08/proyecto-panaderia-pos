from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateProductDTO(BaseModel):
    nombre: str
    categoria: str
    precio: float = Field(description="Precio por unidad en pesos colombianos (entero)")


class ReplaceProductDTO(BaseModel):
    nombre: str
    categoria: str
    precio: float = Field(description="Precio por unidad en pesos colombianos (entero)")


class PatchProductDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    categoria: str | None = None
    precio: float | None = None
    activo: bool | None = None


class ProductResponseDTO(BaseModel):
    id_producto: int
    nombre: str
    categoria: str
    precio: int
    activo: bool


class ChangeResponseDTO(BaseModel):
    id_cambio: int
    id_producto: int
    producto: str
    accion: str
    campo: str | None
    valor_anterior: str | None
    valor_nuevo: str
    usuario: str
    fecha: datetime
