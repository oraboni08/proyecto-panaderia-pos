"""Exportación de las líneas de venta para el data lake (HDFS).

La usa hdfs-exporter: pide las líneas cuyo id es mayor que el último que ya copió, en
bloques. Así el exportador no lee la base de datos de ventas directamente (cada servicio
es dueño de su base: patrón database per service), sino que las pide por la API.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_admin
from app.infrastructure.orm_models import OrderLineORM, OrderORM
from app.infrastructure.security import TokenUser


router = APIRouter(prefix="/export", tags=["Exportación al data lake"])


class ExportLineDTO(BaseModel):
    id_linea: int
    id_venta: int
    fecha: str
    id_cliente: int
    cajero: str | None
    metodo_pago: str
    id_producto: int
    producto: str
    categoria: str
    cantidad: int
    precio_unitario: int
    subtotal: int


@router.get("/lines", response_model=list[ExportLineDTO])
def export_lines(
    after_id: int = Query(default=0, ge=0, description="Devuelve las líneas con id_linea mayor a este"),
    limit: int = Query(default=5000, ge=1, le=50000),
    user: TokenUser = Depends(require_admin),
    db: Session = Depends(get_db),
):

    rows = (
        db.query(OrderLineORM, OrderORM)
        .join(OrderORM, OrderORM.id_venta == OrderLineORM.id_venta)
        .filter(OrderLineORM.id_linea > after_id)
        .order_by(OrderLineORM.id_linea)
        .limit(limit)
        .all()
    )

    return [
        ExportLineDTO(
            id_linea=l.id_linea,
            id_venta=v.id_venta,
            fecha=v.fecha.strftime("%Y-%m-%d %H:%M:%S"),
            id_cliente=v.id_cliente,
            cajero=v.cajero,
            metodo_pago=v.metodo_pago,
            id_producto=l.id_producto,
            producto=l.nombre_producto,
            categoria=l.categoria,
            cantidad=l.cantidad,
            precio_unitario=l.precio_unitario,
            subtotal=l.subtotal,
        )
        for l, v in rows
    ]
