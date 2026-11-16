from dataclasses import dataclass
from datetime import datetime


# Todos los productos se venden por unidad (en Colombia no se vende pan por peso).
# El precio es en pesos colombianos (COP), sin decimales.
CATEGORIAS = (
    "Panadería de queso",
    "Panes",
    "Hojaldres",
    "Salados",
    "Desayunos",
    "Tortas y postres",
    "Galletas y dulces",
    "Bebidas calientes",
    "Bebidas frías",
    "Lácteos y despensa",
)

PRECIO_MAXIMO = 1_000_000

ACCION_CREAR = "CREAR"
ACCION_EDITAR = "EDITAR"
ACCION_DESACTIVAR = "DESACTIVAR"
ACCION_REACTIVAR = "REACTIVAR"


@dataclass
class Product:
    id: int | None
    nombre: str
    categoria: str
    precio: int
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
