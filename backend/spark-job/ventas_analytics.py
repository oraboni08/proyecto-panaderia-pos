"""Job de Spark: reportes de ventas de la panadería a partir del data lake en HDFS.

Procesamiento paralelo:
  - Lee todos los CSV de hdfs://namenode:9000/panaderia/ventas (un archivo por mes y bloque).
  - Spark divide los datos en PARTICIONES (al menos una por bloque de HDFS) y las procesa
    al mismo tiempo, una por núcleo del procesador (master local[*] = todos los núcleos).
  - Cada agregación (groupBy) hace un "shuffle": junta en la misma partición las filas con
    la misma clave (producto, hora, día...) y suma. Es la misma idea de map -> reduce.

Resultados:
  - PostgreSQL (reports_db): las tablas que lee reporting-service, el lado de LECTURA de
    CQRS. La caja escribe en sales_db; los reportes se consultan en otra base.
  - HDFS (/panaderia/reportes/<nombre>): copia en formato Parquet.
"""

import os
import time
from datetime import datetime
from pathlib import Path

import psycopg
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, StringType, StructField, StructType


HDFS = os.getenv("HDFS_URL", "hdfs://namenode:9000")
ENTRADA = f"{HDFS}/panaderia/ventas"
SALIDA = f"{HDFS}/panaderia/reportes"

ESQUEMA = StructType([
    StructField("id_linea", IntegerType()),
    StructField("id_venta", IntegerType()),
    StructField("fecha", StringType()),
    StructField("id_cliente", IntegerType()),
    StructField("cajero", StringType()),
    StructField("metodo_pago", StringType()),
    StructField("id_producto", IntegerType()),
    StructField("producto", StringType()),
    StructField("categoria", StringType()),
    StructField("cantidad", IntegerType()),
    StructField("precio_unitario", IntegerType()),
    StructField("subtotal", IntegerType()),
])

DIAS = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"}

CONSUMIDOR_FINAL = 0


def conexion_postgres() -> psycopg.Connection:
    ruta = os.getenv("DB_PASSWORD_FILE")
    clave = Path(ruta).read_text(encoding="utf-8").strip() if ruta else os.getenv("DB_PASSWORD", "panaderia")
    return psycopg.connect(
        host=os.getenv("DB_HOST", "postgres"),
        dbname=os.getenv("DB_NAME", "reports_db"),
        user=os.getenv("DB_USER", "panaderia"),
        password=clave,
    )


# Tablas del modelo de lectura. Se reemplazan completas en cada ejecución.
TABLAS = {
    "reporte_productos": "id_producto INT PRIMARY KEY, producto TEXT, categoria TEXT, ventas INT, unidades INT, ingresos BIGINT",
    "reporte_horas": "hora INT PRIMARY KEY, ventas INT, ingresos BIGINT",
    "reporte_dias": "numero_dia INT PRIMARY KEY, dia TEXT, ventas INT, ingresos BIGINT",
    "reporte_categorias": "categoria TEXT PRIMARY KEY, ventas INT, unidades INT, ingresos BIGINT",
    "reporte_meses": "mes TEXT PRIMARY KEY, ventas INT, ingresos BIGINT",
    "reporte_clientes": "id_cliente INT PRIMARY KEY, compras INT, gasto BIGINT",
}


def guardar_en_postgres(resultados: dict, ejecucion: dict) -> None:
    with conexion_postgres() as conn, conn.cursor() as cur:
        for tabla, columnas in TABLAS.items():
            cur.execute(f"CREATE TABLE IF NOT EXISTS {tabla} ({columnas})")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS spark_ejecuciones (
                id SERIAL PRIMARY KEY, inicio TIMESTAMP, fin TIMESTAMP, segundos REAL,
                lineas INT, ventas INT, archivos INT, particiones INT, nucleos INT
            )
        """)

        # Todo en una transacción: quien consulte los reportes ve los anteriores
        # o los nuevos completos, nunca una mezcla.
        for tabla, filas in resultados.items():
            cur.execute(f"DELETE FROM {tabla}")
            if filas:
                columnas = list(filas[0].keys())
                marcas = ", ".join(["%s"] * len(columnas))
                cur.executemany(
                    f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES ({marcas})",
                    [tuple(f[c] for c in columnas) for f in filas],
                )

        cur.execute(
            """INSERT INTO spark_ejecuciones (inicio, fin, segundos, lineas, ventas, archivos, particiones, nucleos)
               VALUES (%(inicio)s, %(fin)s, %(segundos)s, %(lineas)s, %(ventas)s, %(archivos)s, %(particiones)s, %(nucleos)s)""",
            ejecucion,
        )


def main() -> None:

    inicio = datetime.now()
    t0 = time.perf_counter()

    spark = (
        SparkSession.builder
        .appName("panaderia-reportes-ventas")
        .config("spark.sql.session.timeZone", "America/Bogota")
        # Pocas particiones después de cada agregación: los resultados son pequeños.
        .config("spark.sql.shuffle.partitions", "8")
        # En Docker Swarm el NameNode ve al DataNode con la IP del balanceador interno
        # (NAT de la red overlay), no con su IP real. Conectarse por NOMBRE ("datanode")
        # hace que el DNS de Swarm lo resuelva bien.
        .config("spark.hadoop.dfs.client.use.datanode.hostname", "true")
        # Partición de máximo 4 MB = tamaño de bloque de HDFS: cada bloque se procesa
        # como una tarea aparte (por defecto Spark junta archivos pequeños hasta 128 MB).
        .config("spark.sql.files.maxPartitionBytes", str(4 * 1024 * 1024))
        .config("spark.sql.files.openCostInBytes", str(512 * 1024))
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    nucleos = spark.sparkContext.defaultParallelism

    # ---------- 1. Leer el data lake ----------
    crudo = spark.read.option("header", "true").schema(ESQUEMA).csv(ENTRADA)  # todas las carpetas mes=AAAA-MM
    archivos = len(crudo.inputFiles())

    lineas = (
        crudo
        .withColumn("fecha", F.to_timestamp("fecha", "yyyy-MM-dd HH:mm:ss"))
        .cache()               # se usa en varias agregaciones: se lee de HDFS una sola vez
    )

    particiones = lineas.rdd.getNumPartitions()
    total_lineas = lineas.count()
    total_ventas = lineas.select("id_venta").distinct().count()

    print(f"[spark] Leídas {total_lineas} líneas ({total_ventas} ventas) de {archivos} archivos en HDFS")
    print(f"[spark] {particiones} particiones procesadas en paralelo con {nucleos} núcleos")

    # ---------- 2. Agregaciones (en paralelo por partición) ----------
    ventas = F.countDistinct("id_venta").alias("ventas")
    unidades = F.sum("cantidad").alias("unidades")
    ingresos = F.sum("subtotal").alias("ingresos")

    por_producto = (
        lineas.groupBy("id_producto")
        .agg(
            # Nombre y categoría de la venta más reciente (por si el producto cambió de nombre).
            F.max_by("producto", "id_linea").alias("producto"),
            F.max_by("categoria", "id_linea").alias("categoria"),
            ventas, unidades, ingresos,
        )
    )

    por_hora = lineas.groupBy(F.hour("fecha").alias("hora")).agg(ventas, ingresos)

    # dayofweek: 1 = domingo ... 7 = sábado -> se pasa a 1 = lunes ... 7 = domingo.
    por_dia = (
        lineas.withColumn("numero_dia", ((F.dayofweek("fecha") + 5) % 7) + 1)
        .groupBy("numero_dia").agg(ventas, ingresos)
    )

    por_categoria = lineas.groupBy("categoria").agg(ventas, unidades, ingresos)

    por_mes = lineas.groupBy(F.date_format("fecha", "yyyy-MM").alias("mes")).agg(ventas, ingresos)

    por_cliente = (
        lineas.where(F.col("id_cliente") != CONSUMIDOR_FINAL)
        .groupBy("id_cliente")
        .agg(F.countDistinct("id_venta").alias("compras"), F.sum("subtotal").alias("gasto"))
        .orderBy(F.desc("compras"), F.desc("gasto"))  # mismo criterio que el dashboard de sales
        .limit(50)
    )

    reportes = {
        "reporte_productos": por_producto,
        "reporte_horas": por_hora,
        "reporte_dias": por_dia,
        "reporte_categorias": por_categoria,
        "reporte_meses": por_mes,
        "reporte_clientes": por_cliente,
    }

    # ---------- 3. Guardar copia en HDFS (Parquet) ----------
    for nombre, df in reportes.items():
        df.coalesce(1).write.mode("overwrite").parquet(f"{SALIDA}/{nombre.replace('reporte_', '')}")

    # ---------- 4. Guardar en PostgreSQL (modelo de lectura de CQRS) ----------
    # Los resultados son pequeños (decenas de filas): se traen al driver y se insertan.
    resultados = {nombre: [fila.asDict() for fila in df.collect()] for nombre, df in reportes.items()}
    for fila in resultados["reporte_dias"]:
        fila["dia"] = DIAS[fila["numero_dia"]]

    segundos = round(time.perf_counter() - t0, 1)
    guardar_en_postgres(resultados, {
        "inicio": inicio, "fin": datetime.now(), "segundos": segundos,
        "lineas": total_lineas, "ventas": total_ventas,
        "archivos": archivos, "particiones": particiones, "nucleos": nucleos,
    })

    top = sorted(resultados["reporte_productos"], key=lambda p: p["unidades"], reverse=True)[:3]
    print("[spark] Más vendidos: " + ", ".join(f"{p['producto']} ({p['unidades']} und.)" for p in top))
    print(f"[spark] TERMINADO en {segundos} s. Reportes guardados en reports_db y en {SALIDA}")

    spark.stop()


if __name__ == "__main__":
    main()
