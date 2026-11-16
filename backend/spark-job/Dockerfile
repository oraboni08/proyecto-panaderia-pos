# Imagen del job de Spark (PySpark). Se construye desde la carpeta backend/:
#   docker build -f backend/spark-job/Dockerfile -t panaderia/spark-job backend
FROM apache/spark:3.5.5-python3

USER root

# Driver de PostgreSQL para guardar los reportes en reports_db.
RUN pip install --no-cache-dir "psycopg[binary]>=3.2,<3.3"

COPY spark-job/ventas_analytics.py /opt/panaderia/ventas_analytics.py

# HADOOP_USER_NAME: usuario con el que Spark escribe en HDFS (los permisos están desactivados).
ENV TZ=America/Bogota \
    HADOOP_USER_NAME=root

USER spark

# master local[*]: Spark usa todos los núcleos del contenedor para procesar las particiones
# en paralelo. La interfaz de Spark (puerto 4040) muestra las etapas y tareas mientras corre.
CMD ["/opt/spark/bin/spark-submit", \
     "--master", "local[*]", \
     "--driver-memory", "640m", \
     "--conf", "spark.ui.port=4040", \
     "/opt/panaderia/ventas_analytics.py"]
