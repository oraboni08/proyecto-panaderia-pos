from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CustomerORM(Base):

    __tablename__ = "clientes"

    id_cliente: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    nombre: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    creado_en: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )


class OrderORM(Base):

    __tablename__ = "ventas"

    id_venta: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    id_cliente: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clientes.id_cliente"),
        nullable=False,
    )

    cajero: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    fecha: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    total: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    cliente: Mapped[CustomerORM] = relationship()

    lineas: Mapped[list["OrderLineORM"]] = relationship(
        back_populates="venta",
        cascade="all, delete-orphan",
        order_by="OrderLineORM.id_linea",
    )


class OrderLineORM(Base):

    __tablename__ = "lineas_venta"

    id_linea: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    id_venta: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ventas.id_venta"),
        nullable=False,
        index=True,
    )

    # Referencia lógica a catalog-service: no puede ser llave foránea porque
    # el producto vive en otra base de datos (decisión D5).
    id_producto: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    nombre_producto: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    tipo_venta: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    cantidad: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    precio_unitario: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    subtotal: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    venta: Mapped[OrderORM] = relationship(back_populates="lineas")
