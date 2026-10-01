from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


TipoVenta = Literal["unidad", "peso"]


class CreateProductDTO(BaseModel):
    nombre: str
    precio: float
    tipo_venta: TipoVenta


class ReplaceProductDTO(BaseModel):
    nombre: str
    precio: float
    tipo_venta: TipoVenta


class PatchProductDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    precio: float | None = None
    tipo_venta: TipoVenta | None = None
    activo: bool | None = None


class ProductResponseDTO(BaseModel):
    id_producto: int
    nombre: str
    precio: float
    tipo_venta: str
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
