from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import tokens, users
from app.api.errors import register_error_handlers
from app.config import CORS_ORIGINS
from app.infrastructure.database import SessionLocal, engine
from app.infrastructure.orm_models import Base
from app.infrastructure.seed import seed_users


Base.metadata.create_all(
    bind=engine
)

with SessionLocal() as session:
    seed_users(session)


app = FastAPI(
    docs_url="/api/v1/auth/docs",
    openapi_url="/api/v1/auth/openapi.json",
    redoc_url=None,
    title="Panadería POS - Auth Service",
    description="Inicio de sesión, tokens JWT y gestión de usuarios.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)


api = APIRouter(prefix="/api/v1/auth")


@api.get("/health", tags=["Salud"])
def health():
    return {"status": "ok", "service": "auth"}


api.include_router(tokens.router)
api.include_router(users.router)

app.include_router(api)
