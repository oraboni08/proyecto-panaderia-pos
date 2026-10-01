import httpx

from app.config import CATALOG_TIMEOUT_SECONDS, CATALOG_URL
from app.domain.exceptions import ServiceUnavailableError
from app.domain.models import ProductInfo
from app.domain.repositories import ProductCatalog


def _to_product(data: dict) -> ProductInfo:
    return ProductInfo(
        id=data["id_producto"],
        nombre=data["nombre"],
        precio=data["precio"],
        tipo_venta=data["tipo_venta"],
        activo=data["activo"],
    )


class HttpProductCatalog(ProductCatalog):
    """Implementa el contrato ProductCatalog consultando a catalog-service por REST.

    Reenvía el token del usuario que hizo la petición, así catalog-service
    aplica sus propios permisos.
    """

    def __init__(self, token: str, base_url: str = CATALOG_URL):
        self.base_url = f"{base_url}/api/v1/catalog"
        self.headers = {"Authorization": f"Bearer {token}"}

    def _get(self, path: str) -> httpx.Response:
        try:
            response = httpx.get(
                f"{self.base_url}{path}",
                headers=self.headers,
                timeout=CATALOG_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError:
            raise ServiceUnavailableError("El servicio de catálogo no está disponible")

        if response.status_code not in (200, 404):
            raise ServiceUnavailableError(
                f"El servicio de catálogo respondió con un error ({response.status_code})"
            )

        return response

    def get_product(self, product_id: int) -> ProductInfo | None:

        response = self._get(f"/products/{product_id}")

        if response.status_code == 404:
            return None

        return _to_product(response.json())

    def list_products(self) -> list[ProductInfo]:

        response = self._get("/products")

        return [_to_product(p) for p in response.json()]
