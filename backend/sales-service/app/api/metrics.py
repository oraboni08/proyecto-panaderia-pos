from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_metrics_service, require_admin
from app.application.dto import (
    ProductWithoutSalesDTO,
    SummaryDTO,
    TopCustomerDTO,
    TopProductDTO,
    WeekdayDTO,
)
from app.domain.services import MetricsService
from app.infrastructure.security import TokenUser


router = APIRouter(prefix="/metrics", tags=["Métricas del dashboard"])

DIAS = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"}


@router.get("/summary", response_model=SummaryDTO)
def summary(
    desde: date | None = None,
    hasta: date | None = None,
    user: TokenUser = Depends(require_admin),
    service: MetricsService = Depends(get_metrics_service),
):

    return SummaryDTO(**vars(service.summary(desde, hasta)))


@router.get("/sales-by-weekday", response_model=list[WeekdayDTO])
def sales_by_weekday(
    desde: date | None = None,
    hasta: date | None = None,
    user: TokenUser = Depends(require_admin),
    service: MetricsService = Depends(get_metrics_service),
):

    return [
        WeekdayDTO(numero_dia=d.numero_dia, dia=DIAS[d.numero_dia], ventas=d.ventas, ingresos=d.ingresos)
        for d in service.sales_by_weekday(desde, hasta)
    ]


@router.get("/top-products", response_model=list[TopProductDTO])
def top_products(
    desde: date | None = None,
    hasta: date | None = None,
    orden: Literal["ingresos", "cantidad"] = "ingresos",
    limit: int = Query(default=10, ge=1, le=100),
    user: TokenUser = Depends(require_admin),
    service: MetricsService = Depends(get_metrics_service),
):

    return [
        TopProductDTO(
            id_producto=p.id_producto,
            producto=p.nombre,
            tipo_venta=p.tipo_venta,
            cantidad=p.cantidad,
            ingresos=p.ingresos,
        )
        for p in service.top_products(desde, hasta, orden, limit)
    ]


@router.get("/top-customers", response_model=list[TopCustomerDTO])
def top_customers(
    desde: date | None = None,
    hasta: date | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    user: TokenUser = Depends(require_admin),
    service: MetricsService = Depends(get_metrics_service),
):

    return [TopCustomerDTO(**vars(c)) for c in service.top_customers(desde, hasta, limit)]


@router.get("/products-without-sales", response_model=list[ProductWithoutSalesDTO])
def products_without_sales(
    desde: date | None = None,
    hasta: date | None = None,
    user: TokenUser = Depends(require_admin),
    service: MetricsService = Depends(get_metrics_service),
):

    return [
        ProductWithoutSalesDTO(id_producto=p.id, nombre=p.nombre, precio=p.precio, tipo_venta=p.tipo_venta)
        for p in service.products_without_sales(desde, hasta)
    ]
