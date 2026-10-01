from abc import ABC, abstractmethod

from app.domain.models import Product, ProductChange


class ProductRepository(ABC):
    """Contrato que debe cumplir cualquier almacenamiento de productos.

    Un producto se guarda siempre junto con los registros de historial que
    explican el cambio, en una sola operación (RN12).
    """

    @abstractmethod
    def create(self, product: Product, change: ProductChange) -> Product:
        pass

    @abstractmethod
    def get_by_id(self, product_id: int) -> Product | None:
        pass

    @abstractmethod
    def get_by_name(self, nombre: str) -> Product | None:
        pass

    @abstractmethod
    def list_all(self, activo: bool | None = None) -> list[Product]:
        pass

    @abstractmethod
    def update(self, product: Product, changes: list[ProductChange]) -> Product:
        pass


class ChangeRepository(ABC):
    """Contrato de solo lectura para el historial de cambios."""

    @abstractmethod
    def list_all(self, product_id: int | None = None) -> list[ProductChange]:
        pass
