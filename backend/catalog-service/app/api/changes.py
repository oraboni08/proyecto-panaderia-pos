from fastapi import APIRouter, Depends

from app.api.dependencies import get_product_service, require_admin
from app.application.dto import ChangeResponseDTO
from app.domain.services import ProductService
from app.infrastructure.security import TokenUser


router = APIRouter(prefix="/changes", tags=["Historial de cambios"])


@router.get(
    "",
    response_model=list[ChangeResponseDTO],
)
def list_changes(
    product_id: int | None = None,
    user: TokenUser = Depends(require_admin),
    service: ProductService = Depends(get_product_service),
):

    return [
        ChangeResponseDTO(
            id_cambio=c.id,
            id_producto=c.id_producto,
            producto=c.producto,
            accion=c.accion,
            campo=c.campo,
            valor_anterior=c.valor_anterior,
            valor_nuevo=c.valor_nuevo,
            usuario=c.usuario,
            fecha=c.fecha,
        )
        for c in service.list_changes(product_id)
    ]
