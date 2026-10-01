from abc import ABC, abstractmethod
from datetime import date

from app.domain.models import (
    Customer,
    CustomerSales,
    Order,
    ProductInfo,
    ProductSales,
    SalesSummary,
    WeekdaySales,
)


class CustomerRepository(ABC):

    @abstractmethod
    def create(self, customer: Customer) -> Customer:
        pass

    @abstractmethod
    def get_by_id(self, customer_id: int) -> Customer | None:
        pass

    @abstractmethod
    def search(self, text: str, limit: int) -> list[Customer]:
        pass


class OrderRepository(ABC):
    """Una venta se guarda con todas sus líneas en una sola transacción (RN15)."""

    @abstractmethod
    def create(self, order: Order) -> Order:
        pass

    @abstractmethod
    def get_by_id(self, order_id: int) -> Order | None:
        pass

    @abstractmethod
    def list_all(
        self,
        desde: date | None = None,
        hasta: date | None = None,
        cajero: str | None = None,
    ) -> list[Order]:
        pass


class MetricsRepository(ABC):
    """Consultas agregadas para el dashboard. Todas aceptan rango de fechas."""

    @abstractmethod
    def summary(self, desde: date | None, hasta: date | None) -> SalesSummary:
        pass

    @abstractmethod
    def sales_by_weekday(self, desde: date | None, hasta: date | None) -> list[WeekdaySales]:
        pass

    @abstractmethod
    def product_sales(self, desde: date | None, hasta: date | None) -> list[ProductSales]:
        pass

    @abstractmethod
    def customer_sales(self, desde: date | None, hasta: date | None) -> list[CustomerSales]:
        pass


class ProductCatalog(ABC):
    """Contrato para consultar productos.

    El dominio no sabe que los productos vienen de otro microservicio:
    la implementación real (HttpProductCatalog) los pide por REST a catalog-service.
    """

    @abstractmethod
    def get_product(self, product_id: int) -> ProductInfo | None:
        pass

    @abstractmethod
    def list_products(self) -> list[ProductInfo]:
        pass
