from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CustomerORM(Base):

    __tablename__ = "clientes"

    id_cliente: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    nombre: Mapped[str] = mapped_column(String, nullable=False, index=True)

    tipo_documento: Mapped[str | None] = mapped_column(String(3), nullable=True)

    # Único cuando existe (el Consumidor final y algunos clientes no tienen documento).
    documento: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)

    telefono: Mapped[str | None] = mapped_column(String(15), nullable=True, index=True)

    correo: Mapped[str | None] = mapped_column(String, nullable=True)

    direccion: Mapped[str | None] = mapped_column(String, nullable=True)

    barrio: Mapped[str | None] = mapped_column(String, nullable=True)

    ciudad: Mapped[str | None] = mapped_column(String, nullable=True)

    creado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class OrderORM(Base):

    __tablename__ = "ventas"

    id_venta: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    id_cliente: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id_cliente"), nullable=False, index=True)

    cajero: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    metodo_pago: Mapped[str] = mapped_column(String(20), nullable=False, default="efectivo")

    # Pesos colombianos, sin decimales.
    total: Mapped[int] = mapped_column(Integer, nullable=False)

    cliente: Mapped[CustomerORM] = relationship()

    lineas: Mapped[list["OrderLineORM"]] = relationship(
        back_populates="venta",
        cascade="all, delete-orphan",
        order_by="OrderLineORM.id_linea",
    )


class OrderLineORM(Base):

    __tablename__ = "lineas_venta"

    id_linea: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    id_venta: Mapped[int] = mapped_column(Integer, ForeignKey("ventas.id_venta"), nullable=False, index=True)

    # Referencia lógica a catalog-service: no puede ser llave foránea porque
    # el producto vive en otra base de datos (decisión D5).
    id_producto: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Copia del nombre, la categoría y el precio en el momento de la venta:
    # si el producto cambia después, la venta histórica no se altera.
    nombre_producto: Mapped[str] = mapped_column(String, nullable=False)

    categoria: Mapped[str] = mapped_column(String, nullable=False)

    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)

    precio_unitario: Mapped[int] = mapped_column(Integer, nullable=False)

    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)

    venta: Mapped[OrderORM] = relationship(back_populates="lineas")
