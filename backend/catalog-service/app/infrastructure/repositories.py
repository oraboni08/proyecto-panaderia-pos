from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.models import Product, ProductChange
from app.domain.repositories import ChangeRepository, ProductRepository
from app.infrastructure.orm_models import ProductChangeORM, ProductORM


def _to_product(db_product: ProductORM) -> Product:
    return Product(
        id=db_product.id_producto,
        nombre=db_product.nombre,
        precio=db_product.precio,
        tipo_venta=db_product.tipo_venta,
        activo=db_product.activo,
    )


def _to_change_orm(change: ProductChange, product_id: int) -> ProductChangeORM:
    return ProductChangeORM(
        id_producto=product_id,
        accion=change.accion,
        campo=change.campo,
        valor_anterior=change.valor_anterior,
        valor_nuevo=change.valor_nuevo,
        usuario=change.usuario,
        fecha=change.fecha,
    )


class SQLAlchemyProductRepository(ProductRepository):

    def __init__(self, session: Session):
        self.session = session

    def create(self, product: Product, change: ProductChange) -> Product:

        db_product = ProductORM(
            nombre=product.nombre,
            precio=product.precio,
            tipo_venta=product.tipo_venta,
            activo=product.activo,
        )

        self.session.add(db_product)
        self.session.flush()

        self.session.add(_to_change_orm(change, db_product.id_producto))

        self.session.commit()
        self.session.refresh(db_product)

        return _to_product(db_product)

    def get_by_id(self, product_id: int) -> Product | None:

        db_product = self.session.get(ProductORM, product_id)

        if db_product is None:
            return None

        return _to_product(db_product)

    def get_by_name(self, nombre: str) -> Product | None:

        db_product = (
            self.session
            .query(ProductORM)
            .filter(func.lower(ProductORM.nombre) == nombre.lower())
            .first()
        )

        if db_product is None:
            return None

        return _to_product(db_product)

    def list_all(self, activo: bool | None = None) -> list[Product]:

        query = self.session.query(ProductORM)

        if activo is not None:
            query = query.filter(ProductORM.activo == activo)

        return [
            _to_product(db_product)
            for db_product in query.order_by(ProductORM.nombre).all()
        ]

    def update(self, product: Product, changes: list[ProductChange]) -> Product:

        db_product = self.session.get(ProductORM, product.id)

        db_product.nombre = product.nombre
        db_product.precio = product.precio
        db_product.tipo_venta = product.tipo_venta
        db_product.activo = product.activo

        for change in changes:
            self.session.add(_to_change_orm(change, product.id))

        self.session.commit()
        self.session.refresh(db_product)

        return _to_product(db_product)


class SQLAlchemyChangeRepository(ChangeRepository):

    def __init__(self, session: Session):
        self.session = session

    def list_all(self, product_id: int | None = None) -> list[ProductChange]:

        query = self.session.query(ProductChangeORM)

        if product_id is not None:
            query = query.filter(ProductChangeORM.id_producto == product_id)

        rows = query.order_by(ProductChangeORM.fecha.desc(), ProductChangeORM.id_cambio.desc()).all()

        return [
            ProductChange(
                id=row.id_cambio,
                id_producto=row.id_producto,
                accion=row.accion,
                campo=row.campo,
                valor_anterior=row.valor_anterior,
                valor_nuevo=row.valor_nuevo,
                usuario=row.usuario,
                fecha=row.fecha,
                producto=row.producto.nombre,
            )
            for row in rows
        ]
