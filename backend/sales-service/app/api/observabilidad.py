"""Métricas para Prometheus.

Un middleware mide cada petición HTTP y el endpoint /metrics las publica en el formato
que lee Prometheus. /metrics queda fuera de /api/v1, así que el API Gateway no lo expone:
solo Prometheus lo consulta, por la red interna de Docker Swarm.
"""

import time

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest


PETICIONES = Counter(
    "http_requests_total",
    "Peticiones HTTP atendidas",
    ["method", "handler", "status"],
)

LATENCIA = Histogram(
    "http_request_duration_seconds",
    "Tiempo de respuesta de las peticiones HTTP",
    ["method", "handler"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)


def instrumentar(app: FastAPI) -> None:

    @app.middleware("http")
    async def medir(request: Request, call_next):

        ruta = request.url.path
        if ruta == "/metrics" or ruta.endswith("/health"):
            return await call_next(request)

        inicio = time.perf_counter()
        codigo = 500
        try:
            respuesta = await call_next(request)
            codigo = respuesta.status_code
            return respuesta
        finally:
            # Se usa la plantilla de la ruta (/orders/{id_venta}) y no la URL real,
            # para no crear una serie de datos distinta por cada venta.
            endpoint = getattr(request.scope.get("route"), "path", None) or "sin_ruta"
            PETICIONES.labels(request.method, endpoint, f"{codigo // 100}xx").inc()
            LATENCIA.labels(request.method, endpoint).observe(time.perf_counter() - inicio)

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
