# Imagen de hdfs-exporter. Se construye desde la carpeta backend/:
#   docker build -f backend/hdfs-exporter/Dockerfile -t panaderia/hdfs-exporter backend
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv
COPY hdfs-exporter/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY hdfs-exporter/exporter.py .

RUN useradd --system --uid 1001 panaderia
USER panaderia

# Métricas para Prometheus.
EXPOSE 8005

CMD ["python", "exporter.py"]
