"""reporting-service: lado de LECTURA (Query) de CQRS.

- La caja escribe las ventas en sales_db (sales-service = lado de escritura / Command).
- El job de Spark lee el histórico desde HDFS, calcula los reportes y los guarda en reports_db.
- Este servicio solo LEE reports_db. Nunca escribe y nunca consulta sales_db: las consultas
  pesadas de análisis no le quitan rendimiento a la caja.
"""

from fastapi import APIRouter, Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, inspect, text

from app.config import CORS_ORIGINS, DATABASE_URL
from app.observabilidad import instrumentar
from app.security import require_admin


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)


def _consultar(sql: str, **parametros) -> list[dict]:
    with engine.connect() as conn:
        return [dict(fila._mapping) for fila in conn.execute(text(sql), parametros)]


def _existe(tabla: str) -> bool:
    return inspect(engine).has_table(tabla)


def _reporte(tabla: str, orden: str, limite: int | None = None) -> list[dict]:
    """Devuelve una tabla de reportes. Si Spark aún no ha corrido, devuelve una lista vacía."""

    if not _existe(tabla):
        return []
    sql = f"SELECT * FROM {tabla} ORDER BY {orden}"
    if limite:
        sql += " LIMIT :limite"
    return _consultar(sql, limite=limite)


app = FastAPI(
    docs_url="/api/v1/reports/docs",
    openapi_url="/api/v1/reports/openapi.json",
    redoc_url=None,
    title="Panadería POS - Reporting Service",
    description="Reportes de ventas calculados por Apache Spark a partir del data lake en HDFS (lado de lectura de CQRS).",
)

app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

# Métricas para Prometheus (/metrics).
instrumentar(app)


api = APIRouter(prefix="/api/v1/reports")


@api.get("/health", tags=["Salud"])
def health():
    return {"status": "ok", "service": "reports"}


@api.get("/ultima-ejecucion", tags=["Spark"])
def ultima_ejecucion(user: dict = Depends(require_admin)):
    """Cuándo corrió Spark por última vez, cuántos datos procesó y en cuántas particiones."""

    if not _existe("spark_ejecuciones"):
        return None
    filas = _consultar("SELECT * FROM spark_ejecuciones ORDER BY id DESC LIMIT 1")
    return filas[0] if filas else None


@api.get("/productos", tags=["Reportes"])
def productos(
    orden: str = Query(default="unidades", pattern="^(unidades|ingresos|ventas)$"),
    limite: int = Query(default=20, ge=1, le=200),
    user: dict = Depends(require_admin),
):
    return _reporte("reporte_productos", f"{orden} DESC, id_producto", limite)


@api.get("/categorias", tags=["Reportes"])
def categorias(user: dict = Depends(require_admin)):
    return _reporte("reporte_categorias", "ingresos DESC")


@api.get("/horas", tags=["Reportes"])
def horas(user: dict = Depends(require_admin)):
    return _reporte("reporte_horas", "hora")


@api.get("/dias", tags=["Reportes"])
def dias(user: dict = Depends(require_admin)):
    return _reporte("reporte_dias", "numero_dia")


@api.get("/meses", tags=["Reportes"])
def meses(user: dict = Depends(require_admin)):
    return _reporte("reporte_meses", "mes")


@api.get("/clientes", tags=["Reportes"])
def clientes(limite: int = Query(default=10, ge=1, le=50), user: dict = Depends(require_admin)):
    return _reporte("reporte_clientes", "compras DESC, gasto DESC, id_cliente", limite)


@api.get("/resumen", tags=["Reportes"])
def resumen(user: dict = Depends(require_admin)):
    """Todo lo que muestra la pantalla de Reportes, en una sola petición."""

    return {
        "ultima_ejecucion": ultima_ejecucion(user),
        "productos": _reporte("reporte_productos", "unidades DESC, id_producto", 10),
        "categorias": _reporte("reporte_categorias", "ingresos DESC"),
        "horas": _reporte("reporte_horas", "hora"),
        "dias": _reporte("reporte_dias", "numero_dia"),
        "meses": _reporte("reporte_meses", "mes"),
        "clientes": _reporte("reporte_clientes", "compras DESC, gasto DESC, id_cliente", 10),
    }


app.include_router(api)
