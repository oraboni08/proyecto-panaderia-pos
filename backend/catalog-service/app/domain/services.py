from datetime import datetime

from app.domain.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.domain.models import (
    ACCION_CREAR,
    ACCION_DESACTIVAR,
    ACCION_EDITAR,
    ACCION_REACTIVAR,
    TIPOS_VENTA,
    Product,
    ProductChange,
)
from app.domain.repositories import ChangeRepository, ProductRepository


def _format(campo: str, valor) -> str:
    if campo == "precio":
        return f"{valor:.2f}"
    if campo == "activo":
        return "activo" if valor else "inactivo"
    return str(valor)


class ProductService:

    def __init__(self, products: ProductRepository, changes: ChangeRepository):
        self.products = products
        self.changes = changes

    def list_products(self, activo: bool | None = None) -> list[Product]:
        return self.products.list_all(activo)

    def get_product(self, product_id: int) -> Product:

        product = self.products.get_by_id(product_id)

        if product is None:
            raise NotFoundError("Producto no encontrado")

        return product

    def create_product(
        self,
        nombre: str,
        precio: float,
        tipo_venta: str,
        usuario: str,
    ) -> Product:

        nombre, precio, tipo_venta = self._validate(nombre, precio, tipo_venta)

        product = Product(
            id=None,
            nombre=nombre,
            precio=precio,
            tipo_venta=tipo_venta,
            activo=True,
        )

        change = ProductChange(
            id=None,
            id_producto=None,
            accion=ACCION_CREAR,
            campo=None,
            valor_anterior=None,
            valor_nuevo=f"{nombre} | {precio:.2f} | {tipo_venta}",
            usuario=usuario,
            fecha=datetime.now(),
        )

        return self.products.create(product, change)

    def replace_product(
        self,
        product_id: int,
        nombre: str,
        precio: float,
        tipo_venta: str,
        usuario: str,
    ) -> Product:

        return self.update_product(
            product_id,
            usuario,
            nombre=nombre,
            precio=precio,
            tipo_venta=tipo_venta,
        )

    def update_product(
        self,
        product_id: int,
        usuario: str,
        nombre: str | None = None,
        precio: float | None = None,
        tipo_venta: str | None = None,
        activo: bool | None = None,
    ) -> Product:

        product = self.get_product(product_id)

        nombre, precio, tipo_venta = self._validate(
            nombre if nombre is not None else product.nombre,
            precio if precio is not None else product.precio,
            tipo_venta if tipo_venta is not None else product.tipo_venta,
            exclude_id=product.id,
        )

        nuevos = {
            "nombre": nombre,
            "precio": precio,
            "tipo_venta": tipo_venta,
            "activo": activo if activo is not None else product.activo,
        }

        changes = []
        ahora = datetime.now()

        for campo, valor_nuevo in nuevos.items():

            valor_anterior = getattr(product, campo)

            if valor_nuevo == valor_anterior:
                continue

            if campo == "activo":
                accion = ACCION_REACTIVAR if valor_nuevo else ACCION_DESACTIVAR
            else:
                accion = ACCION_EDITAR

            changes.append(
                ProductChange(
                    id=None,
                    id_producto=product.id,
                    accion=accion,
                    campo=campo,
                    valor_anterior=_format(campo, valor_anterior),
                    valor_nuevo=_format(campo, valor_nuevo),
                    usuario=usuario,
                    fecha=ahora,
                )
            )

            setattr(product, campo, valor_nuevo)

        if not changes:
            return product

        return self.products.update(product, changes)

    def set_active(self, product_id: int, activo: bool, usuario: str) -> Product:
        return self.update_product(product_id, usuario, activo=activo)

    def list_changes(self, product_id: int | None = None) -> list[ProductChange]:
        return self.changes.list_all(product_id)

    def _validate(
        self,
        nombre: str,
        precio: float,
        tipo_venta: str,
        exclude_id: int | None = None,
    ) -> tuple[str, float, str]:

        nombre = " ".join(nombre.split())

        if not nombre:
            raise BusinessRuleError("El nombre del producto no puede estar vacío")

        if precio <= 0:
            raise BusinessRuleError("El precio debe ser mayor que 0")

        tipo_venta = tipo_venta.strip().lower()

        if tipo_venta not in TIPOS_VENTA:
            raise BusinessRuleError("El tipo de venta debe ser 'unidad' o 'peso'")

        existente = self.products.get_by_name(nombre)

        if existente is not None and existente.id != exclude_id:
            raise ConflictError(f"Ya existe un producto llamado '{nombre}'")

        return nombre, round(precio, 2), tipo_venta
