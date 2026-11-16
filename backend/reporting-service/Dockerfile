# Imagen de reporting-service. Se construye desde la carpeta backend/:
#   docker build -f backend/reporting-service/Dockerfile -t panaderia/reporting-service backend
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=America/Bogota

# Zona horaria de Colombia para que las ventas queden con la hora local.
RUN apt-get update && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

# Primero las dependencias: si solo cambia el código, Docker reutiliza esta capa.
COPY reporting-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY reporting-service/app ./app
# Usuario sin privilegios: el contenedor no corre como root.
RUN useradd --system --uid 1001 panaderia
USER panaderia

EXPOSE 8004

# Swarm reemplaza la réplica si deja de responder.
HEALTHCHECK --interval=15s --timeout=3s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8004/api/v1/reports/health', timeout=2)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
