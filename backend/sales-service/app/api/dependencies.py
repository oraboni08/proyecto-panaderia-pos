from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.domain.repositories import ProductCatalog
from app.domain.services import CustomerService, MetricsService, OrderService
from app.infrastructure.catalog_client import HttpProductCatalog
from app.infrastructure.database import SessionLocal
from app.infrastructure.repositories import (
    SQLAlchemyCustomerRepository,
    SQLAlchemyMetricsRepository,
    SQLAlchemyOrderRepository,
)
from app.infrastructure.security import InvalidTokenError, TokenUser, decode_token


bearer = HTTPBearer(auto_error=False)


def get_db():

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> TokenUser:

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Debes iniciar sesión",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return decode_token(credentials.credentials)
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_admin(
    user: TokenUser = Depends(get_current_user),
) -> TokenUser:

    if user.rol != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador puede realizar esta acción",
        )

    return user


def require_cajero(
    user: TokenUser = Depends(get_current_user),
) -> TokenUser:

    if user.rol != "cajero":
        raise HTTPException(
            status_code=403,
            detail="Solo un cajero puede registrar ventas",
        )

    return user


def get_product_catalog(
    user: TokenUser = Depends(get_current_user),
) -> ProductCatalog:

    return HttpProductCatalog(user.token)


def get_customer_service(
    db: Session = Depends(get_db),
) -> CustomerService:

    return CustomerService(SQLAlchemyCustomerRepository(db))


def get_order_service(
    db: Session = Depends(get_db),
    catalog: ProductCatalog = Depends(get_product_catalog),
) -> OrderService:

    return OrderService(
        SQLAlchemyOrderRepository(db),
        SQLAlchemyCustomerRepository(db),
        catalog,
    )


def get_metrics_service(
    db: Session = Depends(get_db),
    catalog: ProductCatalog = Depends(get_product_catalog),
) -> MetricsService:

    return MetricsService(SQLAlchemyMetricsRepository(db), catalog)
