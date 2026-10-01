from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import changes, products
from app.api.errors import register_error_handlers
from app.config import CORS_ORIGINS, DATASET_DIR
from app.infrastructure.database import SessionLocal, engine
from app.infrastructure.orm_models import Base
from app.infrastructure.seed import seed_products


Base.metadata.create_all(
    bind=engine
)

with SessionLocal() as session:
    seed_products(session, DATASET_DIR)


app = FastAPI(
    docs_url="/api/v1/catalog/docs",
    openapi_url="/api/v1/catalog/openapi.json",
    redoc_url=None,
    title="Panadería POS - Catalog Service",
    description="Productos, precios, tipo de venta e historial de cambios.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)


api = APIRouter(prefix="/api/v1/catalog")


@api.get("/health", tags=["Salud"])
def health():
    return {"status": "ok", "service": "catalog"}


api.include_router(products.router)
api.include_router(changes.router)

app.include_router(api)
