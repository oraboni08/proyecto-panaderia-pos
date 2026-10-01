from datetime import date, datetime, time, timedelta

from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload, selectinload

from app.domain.models import (
    TIPO_PESO,
    TIPO_UNIDAD,
    Customer,
    CustomerSales,
    Order,
    OrderLine,
    ProductSales,
    SalesSummary,
    WeekdaySales,
)
from app.domain.repositories import CustomerRepository, MetricsRepository, OrderRepository
from app.infrastructure.orm_models import CustomerORM, OrderLineORM, OrderORM


def _to_customer(db_customer: CustomerORM) -> Customer:
    return Customer(
        id=db_customer.id_cliente,
        nombre=db_customer.nombre,
        creado_en=db_customer.creado_en,
    )


def _to_order(db_order: OrderORM) -> Order:
    return Order(
        id=db_order.id_venta,
        id_cliente=db_order.id_cliente,
        cajero=db_order.cajero,
        fecha=db_order.fecha,
        total=db_order.total,
        cliente_nombre=db_order.cliente.nombre,
        lineas=[
            OrderLine(
                id=l.id_linea,
                id_producto=l.id_producto,
                nombre_producto=l.nombre_producto,
                tipo_venta=l.tipo_venta,
                cantidad=l.cantidad,
                precio_unitario=l.precio_unitario,
                subtotal=l.subtotal,
            )
            for l in db_order.lineas
        ],
    )


def _date_filter(query, desde: date | None, hasta: date | None):
    """Filtra ventas entre dos fechas, ambas incluidas."""

    if desde is not None:
        query = query.filter(OrderORM.fecha >= datetime.combine(desde, time.min))

    if hasta is not None:
        query = query.filter(OrderORM.fecha < datetime.combine(hasta + timedelta(days=1), time.min))

    return query


class SQLAlchemyCustomerRepository(CustomerRepository):

    def __init__(self, session: Session):
        self.session = session

    def create(self, customer: Customer) -> Customer:

        db_customer = CustomerORM(
            nombre=customer.nombre,
            creado_en=customer.creado_en,
        )

        self.session.add(db_customer)
        self.session.commit()
        self.session.refresh(db_customer)

        return _to_customer(db_customer)

    def get_by_id(self, customer_id: int) -> Customer | None:

        db_customer = self.session.get(CustomerORM, customer_id)

        if db_customer is None:
            return None

        return _to_customer(db_customer)

    def search(self, text: str, limit: int) -> list[Customer]:

        query = self.session.query(CustomerORM)

        if text:
            condition = CustomerORM.nombre.ilike(f"%{text}%")

            if text.isdigit():
                condition = condition | (CustomerORM.id_cliente == int(text))

            query = query.filter(condition)

        # Si buscan un número, el cliente con ese id exacto aparece primero.
        exact_first = case((CustomerORM.id_cliente == (int(text) if text.isdigit() else -1), 0), else_=1)

        rows = query.order_by(exact_first, CustomerORM.id_cliente).limit(limit).all()

        return [_to_customer(row) for row in rows]


class SQLAlchemyOrderRepository(OrderRepository):

    def __init__(self, session: Session):
        self.session = session

    def create(self, order: Order) -> Order:

        db_order = OrderORM(
            id_cliente=order.id_cliente,
            cajero=order.cajero,
            fecha=order.fecha,
            total=order.total,
            lineas=[
                OrderLineORM(
                    id_producto=l.id_producto,
                    nombre_producto=l.nombre_producto,
                    tipo_venta=l.tipo_venta,
                    cantidad=l.cantidad,
                    precio_unitario=l.precio_unitario,
                    subtotal=l.subtotal,
                )
                for l in order.lineas
            ],
        )

        # La venta y todas sus líneas se guardan en un solo commit (RN15).
        try:
            self.session.add(db_order)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        self.session.refresh(db_order)

        return _to_order(db_order)

    def get_by_id(self, order_id: int) -> Order | None:

        db_order = (
            self.session
            .query(OrderORM)
            .options(joinedload(OrderORM.cliente), selectinload(OrderORM.lineas))
            .filter(OrderORM.id_venta == order_id)
            .first()
        )

        if db_order is None:
            return None

        return _to_order(db_order)

    def list_all(
        self,
        desde: date | None = None,
        hasta: date | None = None,
        cajero: str | None = None,
    ) -> list[Order]:

        query = (
            self.session
            .query(OrderORM)
            .options(joinedload(OrderORM.cliente), selectinload(OrderORM.lineas))
        )

        query = _date_filter(query, desde, hasta)

        if cajero is not None:
            query = query.filter(OrderORM.cajero == cajero)

        return [_to_order(o) for o in query.order_by(OrderORM.fecha.desc(), OrderORM.id_venta.desc()).all()]


class SQLAlchemyMetricsRepository(MetricsRepository):

    def __init__(self, session: Session):
        self.session = session

    def summary(self, desde: date | None, hasta: date | None) -> SalesSummary:

        ventas = _date_filter(
            self.session.query(
                func.count(OrderORM.id_venta),
                func.coalesce(func.sum(OrderORM.total), 0),
                func.count(func.distinct(case((OrderORM.id_cliente != 0, OrderORM.id_cliente)))),
            ),
            desde,
            hasta,
        ).one()

        cantidades = _date_filter(
            self.session.query(
                func.coalesce(func.sum(case((OrderLineORM.tipo_venta == TIPO_UNIDAD, OrderLineORM.cantidad), else_=0)), 0),
                func.coalesce(func.sum(case((OrderLineORM.tipo_venta == TIPO_PESO, OrderLineORM.cantidad), else_=0)), 0),
            ).join(OrderORM, OrderLineORM.id_venta == OrderORM.id_venta),
            desde,
            hasta,
        ).one()

        return SalesSummary(
            numero_ventas=ventas[0],
            ingresos_totales=float(ventas[1]),
            clientes_activos=ventas[2],
            unidades_vendidas=float(cantidades[0]),
            kg_vendidos=float(cantidades[1]),
        )

    def sales_by_weekday(self, desde: date | None, hasta: date | None) -> list[WeekdaySales]:

        # En SQLite, strftime('%w') devuelve 0 = domingo ... 6 = sábado.
        dia = func.strftime("%w", OrderORM.fecha)

        rows = _date_filter(
            self.session.query(dia, func.count(OrderORM.id_venta), func.sum(OrderORM.total)),
            desde,
            hasta,
        ).group_by(dia).all()

        return [
            WeekdaySales(
                numero_dia=7 if int(d) == 0 else int(d),
                ventas=ventas,
                ingresos=round(float(ingresos), 2),
            )
            for d, ventas, ingresos in rows
        ]

    def product_sales(self, desde: date | None, hasta: date | None) -> list[ProductSales]:

        rows = _date_filter(
            self.session.query(
                OrderLineORM.id_producto,
                func.max(OrderLineORM.nombre_producto),
                func.max(OrderLineORM.tipo_venta),
                func.sum(OrderLineORM.cantidad),
                func.sum(OrderLineORM.subtotal),
            ).join(OrderORM, OrderLineORM.id_venta == OrderORM.id_venta),
            desde,
            hasta,
        ).group_by(OrderLineORM.id_producto).all()

        return [
            ProductSales(
                id_producto=pid,
                nombre=nombre,
                tipo_venta=tipo,
                cantidad=round(float(cantidad), 3),
                ingresos=round(float(ingresos), 2),
            )
            for pid, nombre, tipo, cantidad, ingresos in rows
        ]

    def customer_sales(self, desde: date | None, hasta: date | None) -> list[CustomerSales]:

        rows = _date_filter(
            self.session.query(
                CustomerORM.id_cliente,
                CustomerORM.nombre,
                func.count(OrderORM.id_venta),
                func.sum(OrderORM.total),
            ).join(OrderORM, OrderORM.id_cliente == CustomerORM.id_cliente),
            desde,
            hasta,
        ).group_by(CustomerORM.id_cliente, CustomerORM.nombre).all()

        return [
            CustomerSales(
                id_cliente=cid,
                nombre=nombre,
                compras=compras,
                gasto=round(float(gasto), 2),
            )
            for cid, nombre, compras, gasto in rows
        ]
