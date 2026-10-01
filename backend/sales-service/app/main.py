from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import customers, metrics, orders
from app.api.errors import register_error_handlers
from app.config import CORS_ORIGINS, DATASET_DIR
from app.infrastructure.database import SessionLocal, engine
from app.infrastructure.orm_models import Base
from app.infrastructure.seed import seed_sales


Base.metadata.create_all(
    bind=engine
)

with SessionLocal() as session:
    seed_sales(session, DATASET_DIR)


app = FastAPI(
    docs_url="/api/v1/sales/docs",
    openapi_url="/api/v1/sales/openapi.json",
    redoc_url=None,
    title="Panadería POS - Sales Service",
    description="Clientes, ventas con varios productos y métricas del dashboard.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)


api = APIRouter(prefix="/api/v1/sales")


@api.get("/health", tags=["Salud"])
def health():
    return {"status": "ok", "service": "sales"}


api.include_router(customers.router)
api.include_router(orders.router)
api.include_router(metrics.router)

app.include_router(api)
