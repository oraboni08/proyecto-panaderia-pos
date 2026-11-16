from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_current_user, get_order_service, require_cajero
from app.application.dto import (
    CreateOrderDTO,
    CustomerSummaryDTO,
    OrderLineResponseDTO,
    OrderResponseDTO,
)
from app.domain.models import METODOS_PAGO, Order
from app.domain.services import LineRequest, OrderService
from app.infrastructure.security import TokenUser


router = APIRouter(prefix="/orders", tags=["Ventas"])


def to_response(order: Order) -> OrderResponseDTO:
    return OrderResponseDTO(
        id_venta=order.id,
        fecha=order.fecha,
        cliente=CustomerSummaryDTO(id_cliente=order.id_cliente, nombre=order.cliente_nombre),
        cajero=order.cajero,
        metodo_pago=order.metodo_pago,
        total=order.total,
        lineas=[
            OrderLineResponseDTO(
                id_producto=l.id_producto,
                producto=l.nombre_producto,
                categoria=l.categoria,
                cantidad=l.cantidad,
                precio_unitario=l.precio_unitario,
                subtotal=l.subtotal,
            )
            for l in order.lineas
        ],
    )


@router.get(
    "/payment-methods",
    response_model=dict[str, str],
)
def payment_methods(user: TokenUser = Depends(get_current_user)):
    return METODOS_PAGO


@router.post(
    "",
    response_model=OrderResponseDTO,
    status_code=201,
)
def create_order(
    data: CreateOrderDTO,
    user: TokenUser = Depends(require_cajero),
    service: OrderService = Depends(get_order_service),
):

    order = service.create_order(
        id_cliente=data.id_cliente,
        lineas=[LineRequest(l.id_producto, l.cantidad) for l in data.lineas],
        cajero=user.usuario,
        metodo_pago=data.metodo_pago,
    )

    return to_response(order)


@router.get(
    "",
    response_model=list[OrderResponseDTO],
)
def list_orders(
    desde: date | None = None,
    hasta: date | None = None,
    id_cliente: int | None = None,
    cajero: str | None = Query(default=None, description="Solo para el administrador"),
    metodo_pago: str | None = None,
    limit: int = Query(default=200, ge=1, le=2000),
    user: TokenUser = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):

    # El cajero solo ve las ventas que él registró (RF14); el administrador puede filtrar por cajero.
    if user.rol != "admin":
        cajero = user.usuario

    return [
        to_response(o)
        for o in service.list_orders(desde, hasta, cajero or None, id_cliente, limit, metodo_pago or None)
    ]


@router.get(
    "/{order_id}",
    response_model=OrderResponseDTO,
)
def get_order(
    order_id: int,
    user: TokenUser = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):

    order = service.get_order(order_id)

    if user.rol != "admin" and order.cajero != user.usuario:
        raise HTTPException(status_code=403, detail="Solo puedes ver las ventas que registraste")

    return to_response(order)
