from dataclasses import dataclass
from datetime import datetime


TIPO_UNIDAD = "unidad"
TIPO_PESO = "peso"
TIPOS_VENTA = (TIPO_UNIDAD, TIPO_PESO)

ACCION_CREAR = "CREAR"
ACCION_EDITAR = "EDITAR"
ACCION_DESACTIVAR = "DESACTIVAR"
ACCION_REACTIVAR = "REACTIVAR"


@dataclass
class Product:
    id: int | None
    nombre: str
    precio: float
    tipo_venta: str
    activo: bool = True


@dataclass
class ProductChange:
    id: int | None
    id_producto: int | None
    accion: str
    campo: str | None
    valor_anterior: str | None
    valor_nuevo: str
    usuario: str
    fecha: datetime
    producto: str | None = None
