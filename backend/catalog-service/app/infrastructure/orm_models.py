from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ProductORM(Base):

    __tablename__ = "productos"

    id_producto: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    nombre: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
    )

    precio: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    tipo_venta: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class ProductChangeORM(Base):

    __tablename__ = "cambios_producto"

    id_cambio: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    id_producto: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("productos.id_producto"),
        nullable=False,
    )

    accion: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    campo: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    valor_anterior: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    valor_nuevo: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    usuario: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    fecha: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    producto: Mapped[ProductORM] = relationship()
