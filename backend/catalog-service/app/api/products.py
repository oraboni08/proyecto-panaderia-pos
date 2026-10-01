from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_product_service, require_admin
from app.application.dto import (
    CreateProductDTO,
    PatchProductDTO,
    ProductResponseDTO,
    ReplaceProductDTO,
)
from app.domain.models import Product
from app.domain.services import ProductService
from app.infrastructure.security import TokenUser


router = APIRouter(prefix="/products", tags=["Productos"])


def to_response(product: Product) -> ProductResponseDTO:
    return ProductResponseDTO(
        id_producto=product.id,
        nombre=product.nombre,
        precio=product.precio,
        tipo_venta=product.tipo_venta,
        activo=product.activo,
    )


@router.get(
    "",
    response_model=list[ProductResponseDTO],
)
def list_products(
    activo: bool | None = None,
    user: TokenUser = Depends(get_current_user),
    service: ProductService = Depends(get_product_service),
):

    # El cajero solo puede ver los productos activos (RN01, RN11).
    if user.rol != "admin":
        activo = True

    return [to_response(p) for p in service.list_products(activo)]


@router.get(
    "/{product_id}",
    response_model=ProductResponseDTO,
)
def get_product(
    product_id: int,
    user: TokenUser = Depends(get_current_user),
    service: ProductService = Depends(get_product_service),
):

    return to_response(service.get_product(product_id))


@router.post(
    "",
    response_model=ProductResponseDTO,
    status_code=201,
)
def create_product(
    data: CreateProductDTO,
    user: TokenUser = Depends(require_admin),
    service: ProductService = Depends(get_product_service),
):

    product = service.create_product(
        nombre=data.nombre,
        precio=data.precio,
        tipo_venta=data.tipo_venta,
        usuario=user.usuario,
    )

    return to_response(product)


@router.put(
    "/{product_id}",
    response_model=ProductResponseDTO,
)
def replace_product(
    product_id: int,
    data: ReplaceProductDTO,
    user: TokenUser = Depends(require_admin),
    service: ProductService = Depends(get_product_service),
):

    product = service.replace_product(
        product_id=product_id,
        nombre=data.nombre,
        precio=data.precio,
        tipo_venta=data.tipo_venta,
        usuario=user.usuario,
    )

    return to_response(product)


@router.patch(
    "/{product_id}",
    response_model=ProductResponseDTO,
)
def update_product(
    product_id: int,
    data: PatchProductDTO,
    user: TokenUser = Depends(require_admin),
    service: ProductService = Depends(get_product_service),
):

    product = service.update_product(
        product_id,
        user.usuario,
        **data.model_dump(exclude_none=True),
    )

    return to_response(product)
