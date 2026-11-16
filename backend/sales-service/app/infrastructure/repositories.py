from datetime import date, datetime, time, timedelta

from sqlalchemy import case, func, or_, literal_column
from sqlalchemy.orm import Session, joinedload, selectinload

from app.domain.models import (
    CONSUMIDOR_FINAL_ID,
    Customer,
    CustomerSales,
    GroupSales,
    HourSales,
    MonthSales,
    Order,
    OrderLine,
    ProductSales,
    SalesSummary,
    WeekdaySales,
)
from app.domain.repositories import CustomerRepository, MetricsRepository, OrderRepository
from app.infrastructure.orm_models import CustomerORM, OrderLineORM, OrderORM


CUSTOMER_FIELDS = ("nombre", "tipo_documento", "documento", "telefono", "correo", "direccion", "barrio", "ciudad")


def _to_customer(db_customer: CustomerORM) -> Customer:
    return Customer(
        id=db_customer.id_cliente,
        creado_en=db_customer.creado_en,
        **{campo: getattr(db_customer, campo) for campo in CUSTOMER_FIELDS},
    )


def _to_order(db_order: OrderORM) -> Order:
    return Order(
        id=db_order.id_venta,
        id_cliente=db_order.id_cliente,
        cajero=db_order.cajero,
        fecha=db_order.fecha,
        metodo_pago=db_order.metodo_pago,
        total=db_order.total,
        cliente_nombre=db_order.cliente.nombre,
        lineas=[
            OrderLine(
                id=l.id_linea,
                id_producto=l.id_producto,
                nombre_producto=l.nombre_producto,
                categoria=l.categoria,
                cantidad=l.cantidad,
                precio_unitario=l.precio_unitario,
                subtotal=l.subtotal,
            )
            for l in db_order.lineas
        ],
    )


def _parte_fecha(session, parte: str, columna):
    """Día de la semana, hora o mes de una fecha, en SQLite (local) o PostgreSQL (Docker).

    Ambos devuelven el día de la semana como 0 = domingo ... 6 = sábado.
    """

    if session.get_bind().dialect.name == "postgresql":
        if parte == "mes":
            # Formato como texto literal (no parámetro) para que el SELECT y el GROUP BY
            # sean la misma expresión; si no, PostgreSQL rechaza la consulta.
            return func.to_char(columna, literal_column("'YYYY-MM'"))
        return func.extract("dow" if parte == "dia" else "hour", columna)

    return func.strftime({"dia": "%w", "hora": "%H", "mes": "%Y-%m"}[parte], columna)


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
            creado_en=customer.creado_en,
            **{campo: getattr(customer, campo) for campo in CUSTOMER_FIELDS},
        )

        self.session.add(db_customer)
        self.session.commit()
        self.session.refresh(db_customer)

        return _to_customer(db_customer)

    def update(self, customer: Customer) -> Customer:

        db_customer = self.session.get(CustomerORM, customer.id)

        for campo in CUSTOMER_FIELDS:
            setattr(db_customer, campo, getattr(customer, campo))

        self.session.commit()
        self.session.refresh(db_customer)

        return _to_customer(db_customer)

    def get_by_id(self, customer_id: int) -> Customer | None:

        db_customer = self.session.get(CustomerORM, customer_id)

        return _to_customer(db_customer) if db_customer is not None else None

    def get_by_document(self, documento: str) -> Customer | None:

        db_customer = self.session.query(CustomerORM).filter(CustomerORM.documento == documento).first()

        return _to_customer(db_customer) if db_customer is not None else None

    def _search_query(self, text: str):

        query = self.session.query(CustomerORM)

        if text:
            digits = text.replace(".", "").replace(" ", "")
            condition = CustomerORM.nombre.ilike(f"%{text}%")

            if digits.isdigit():
                condition = or_(
                    condition,
                    CustomerORM.documento.like(f"{digits}%"),
                    CustomerORM.telefono.like(f"%{digits}%"),
                    CustomerORM.id_cliente == int(digits),
                )

            query = query.filter(condition, CustomerORM.id_cliente != CONSUMIDOR_FINAL_ID)

        return query

    def search(self, text: str, limit: int, offset: int = 0) -> list[Customer]:

        query = self._search_query(text)

        # Si buscan un número, el documento o id exacto aparece primero.
        digits = text.replace(".", "").replace(" ", "")
        exact_first = case(
            (or_(CustomerORM.documento == digits, CustomerORM.id_cliente == (int(digits) if digits.isdigit() else -1)), 0),
            else_=1,
        )

        rows = query.order_by(exact_first, CustomerORM.nombre).offset(offset).limit(limit).all()

        return [_to_customer(row) for row in rows]

    def count(self, text: str = "") -> int:
        return self._search_query(text).count()


class SQLAlchemyOrderRepository(OrderRepository):

    def __init__(self, session: Session):
        self.session = session

    def create(self, order: Order) -> Order:

        db_order = OrderORM(
            id_cliente=order.id_cliente,
            cajero=order.cajero,
            fecha=order.fecha,
            metodo_pago=order.metodo_pago,
            total=order.total,
            lineas=[
                OrderLineORM(
                    id_producto=l.id_producto,
                    nombre_producto=l.nombre_producto,
                    categoria=l.categoria,
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

        return _to_order(db_order) if db_order is not None else None

    def list_all(
        self,
        desde: date | None = None,
        hasta: date | None = None,
        cajero: str | None = None,
        id_cliente: int | None = None,
        limit: int | None = None,
        metodo_pago: str | None = None,
    ) -> list[Order]:

        query = (
            self.session
            .query(OrderORM)
            .options(joinedload(OrderORM.cliente), selectinload(OrderORM.lineas))
        )

        query = _date_filter(query, desde, hasta)

        if cajero is not None:
            query = query.filter(OrderORM.cajero == cajero)

        if id_cliente is not None:
            query = query.filter(OrderORM.id_cliente == id_cliente)

        if metodo_pago is not None:
            query = query.filter(OrderORM.metodo_pago == metodo_pago)

        query = query.order_by(OrderORM.fecha.desc(), OrderORM.id_venta.desc())

        if limit is not None:
            query = query.limit(limit)

        return [_to_order(o) for o in query.all()]


class SQLAlchemyMetricsRepository(MetricsRepository):

    def __init__(self, session: Session):
        self.session = session

    def _lines(self, *columns):
        return self.session.query(*columns).join(OrderORM, OrderLineORM.id_venta == OrderORM.id_venta)

    def summary(self, desde: date | None, hasta: date | None) -> SalesSummary:

        ventas = _date_filter(
            self.session.query(
                func.count(OrderORM.id_venta),
                func.coalesce(func.sum(OrderORM.total), 0),
                func.count(func.distinct(case((OrderORM.id_cliente != CONSUMIDOR_FINAL_ID, OrderORM.id_cliente)))),
            ),
            desde,
            hasta,
        ).one()

        unidades = _date_filter(self._lines(func.coalesce(func.sum(OrderLineORM.cantidad), 0)), desde, hasta).scalar()

        return SalesSummary(
            numero_ventas=ventas[0],
            ingresos_totales=int(ventas[1]),
            clientes_activos=ventas[2],
            unidades_vendidas=int(unidades),
        )

    def sales_by_weekday(self, desde: date | None, hasta: date | None) -> list[WeekdaySales]:

        dia = _parte_fecha(self.session, "dia", OrderORM.fecha)

        rows = _date_filter(
            self.session.query(dia, func.count(OrderORM.id_venta), func.sum(OrderORM.total)),
            desde,
            hasta,
        ).group_by(dia).all()

        return [
            WeekdaySales(numero_dia=7 if int(d) == 0 else int(d), ventas=ventas, ingresos=int(ingresos))
            for d, ventas, ingresos in rows
        ]

    def sales_by_hour(self, desde: date | None, hasta: date | None) -> list[HourSales]:

        hora = _parte_fecha(self.session, "hora", OrderORM.fecha)

        rows = _date_filter(
            self.session.query(hora, func.count(OrderORM.id_venta), func.sum(OrderORM.total)),
            desde,
            hasta,
        ).group_by(hora).all()

        return [HourSales(hora=int(h), ventas=ventas, ingresos=int(ingresos)) for h, ventas, ingresos in rows]

    def sales_by_month(self, desde: date | None, hasta: date | None) -> list[MonthSales]:

        mes = _parte_fecha(self.session, "mes", OrderORM.fecha)

        rows = _date_filter(
            self.session.query(mes, func.count(OrderORM.id_venta), func.sum(OrderORM.total)),
            desde,
            hasta,
        ).group_by(mes).order_by(mes).all()

        return [MonthSales(mes=m, ventas=ventas, ingresos=int(ingresos)) for m, ventas, ingresos in rows]

    def sales_by_category(self, desde: date | None, hasta: date | None) -> list[GroupSales]:

        rows = _date_filter(
            self._lines(
                OrderLineORM.categoria,
                func.count(func.distinct(OrderLineORM.id_venta)),
                func.sum(OrderLineORM.cantidad),
                func.sum(OrderLineORM.subtotal),
            ),
            desde,
            hasta,
        ).group_by(OrderLineORM.categoria).all()

        return [GroupSales(clave=c, ventas=v, unidades=int(u), ingresos=int(i)) for c, v, u, i in rows]

    def sales_by_payment(self, desde: date | None, hasta: date | None) -> list[GroupSales]:

        rows = _date_filter(
            self.session.query(OrderORM.metodo_pago, func.count(OrderORM.id_venta), func.sum(OrderORM.total)),
            desde,
            hasta,
        ).group_by(OrderORM.metodo_pago).all()

        return [GroupSales(clave=m, ventas=v, unidades=0, ingresos=int(i)) for m, v, i in rows]

    def product_sales(self, desde: date | None, hasta: date | None) -> list[ProductSales]:

        columnas = (
            OrderLineORM.id_producto,
            func.sum(OrderLineORM.cantidad),
            func.sum(OrderLineORM.subtotal),
            func.max(OrderLineORM.id_linea),
        )

        if desde is None and hasta is None:
            # Sin rango de fechas no hace falta unir con ventas. En SQLite, "+ 0" evita que
            # recorra el índice de id_producto (más lento que leer la tabla completa).
            # PostgreSQL no acepta ese truco (exige agrupar por la misma columna del SELECT).
            es_sqlite = self.session.get_bind().dialect.name == "sqlite"
            agrupar = OrderLineORM.id_producto + 0 if es_sqlite else OrderLineORM.id_producto
            query = self.session.query(*columnas).group_by(agrupar)
        else:
            query = _date_filter(self._lines(*columnas), desde, hasta).group_by(OrderLineORM.id_producto)

        rows = query.all()

        # Nombre y categoría tal como aparecen en la línea más reciente de cada producto.
        ultimas = {
            l.id_linea: l
            for l in self.session.query(OrderLineORM).filter(OrderLineORM.id_linea.in_([r[3] for r in rows]))
        }

        return [
            ProductSales(
                id_producto=pid,
                nombre=ultimas[ultima].nombre_producto,
                categoria=ultimas[ultima].categoria,
                cantidad=int(cantidad),
                ingresos=int(ingresos),
            )
            for pid, cantidad, ingresos, ultima in rows
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
            CustomerSales(id_cliente=cid, nombre=nombre, compras=compras, gasto=int(gasto))
            for cid, nombre, compras, gasto in rows
        ]
