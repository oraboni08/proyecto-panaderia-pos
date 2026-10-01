from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserORM(Base):

    __tablename__ = "usuarios"

    id_usuario: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    nombre: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    usuario: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    rol: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    creado_en: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
