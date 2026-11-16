"""hdfs-exporter: copia las ventas de la panadería al data lake en HDFS.

Cada INTERVALO segundos:
  1. Lee de HDFS el último id de línea que ya exportó (/panaderia/_estado/ultimo_id).
  2. Pide a sales-service las líneas nuevas (GET /api/v1/sales/export/lines?after_id=...).
     No lee la base de datos de ventas: cada servicio es dueño de su base.
  3. Las agrupa por mes y escribe un CSV por mes en /panaderia/ventas/mes=AAAA-MM/.
  4. Guarda en HDFS el nuevo último id. Si el contenedor se reinicia, sigue desde ahí
     sin duplicar líneas.

Se comunica con HDFS por WebHDFS, la API REST que trae Hadoop (puerto 9870 del NameNode).
Debe correr con UNA sola réplica: dos exportadores a la vez copiarían las mismas líneas.
"""

import csv
import io
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import jwt
from prometheus_client import Counter, Gauge, start_http_server


SALES_URL = os.getenv("SALES_URL", "http://sales-service:8003").rstrip("/")
WEBHDFS = os.getenv("WEBHDFS_URL", "http://namenode:9870/webhdfs/v1").rstrip("/")
HDFS_USER = os.getenv("HDFS_USER", "root")
DIR_VENTAS = os.getenv("HDFS_DIR", "/panaderia/ventas")
ARCHIVO_ESTADO = os.getenv("HDFS_ESTADO", "/panaderia/_estado/ultimo_id")
INTERVALO = int(os.getenv("INTERVALO_SEGUNDOS", "60"))
LOTE = int(os.getenv("LOTE", "50000"))

COLUMNAS = [
    "id_linea", "id_venta", "fecha", "id_cliente", "cajero", "metodo_pago",
    "id_producto", "producto", "categoria", "cantidad", "precio_unitario", "subtotal",
]

LINEAS_EXPORTADAS = Counter("panaderia_hdfs_lineas_exportadas_total", "Líneas de venta copiadas a HDFS")
ARCHIVOS_ESCRITOS = Counter("panaderia_hdfs_archivos_escritos_total", "Archivos CSV escritos en HDFS")
ULTIMO_ID = Gauge("panaderia_hdfs_ultimo_id_exportado", "Último id de línea copiado a HDFS")
ERRORES = Counter("panaderia_hdfs_errores_total", "Ciclos de exportación que fallaron")


def _secreto(nombre: str, defecto: str) -> str:
    ruta = os.getenv(f"{nombre}_FILE")
    if ruta and Path(ruta).exists():
        return Path(ruta).read_text(encoding="utf-8").strip()
    return os.getenv(nombre, defecto)


JWT_SECRET = _secreto("JWT_SECRET", "clave-solo-para-desarrollo-cambiar-en-produccion")


def token_de_servicio() -> str:
    """Token JWT del propio exportador, firmado con la misma clave que usa auth-service.
    Tiene rol admin porque el endpoint de exportación solo lo permite a administradores."""

    ahora = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": "hdfs-exporter", "nombre": "Exportador HDFS", "rol": "admin",
         "iat": ahora, "exp": ahora + timedelta(minutes=10)},
        JWT_SECRET,
        algorithm="HS256",
    )


# ---------------- WebHDFS ----------------

def hdfs_leer(http: httpx.Client, ruta: str) -> str | None:
    r = http.get(f"{WEBHDFS}{ruta}", params={"op": "OPEN", "user.name": HDFS_USER}, follow_redirects=True)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.text


def hdfs_escribir(http: httpx.Client, ruta: str, contenido: str) -> None:
    """WebHDFS escribe en dos pasos: el NameNode responde con una redirección (307)
    al DataNode que guardará el bloque, y el archivo se envía a ese DataNode."""

    r = http.put(
        f"{WEBHDFS}{ruta}",
        params={"op": "CREATE", "overwrite": "true", "user.name": HDFS_USER},
        follow_redirects=False,
    )
    if r.status_code != 307:
        r.raise_for_status()
        raise RuntimeError(f"WebHDFS no devolvió la redirección al DataNode ({r.status_code})")

    r = http.put(r.headers["Location"], content=contenido.encode("utf-8"))
    r.raise_for_status()


# ---------------- Exportación ----------------

def a_csv(lineas: list[dict]) -> str:
    salida = io.StringIO()
    escritor = csv.DictWriter(salida, fieldnames=COLUMNAS, lineterminator="\n")
    escritor.writeheader()
    escritor.writerows(lineas)
    return salida.getvalue()


def exportar(http: httpx.Client) -> int:
    """Copia a HDFS todas las líneas nuevas. Devuelve cuántas copió."""

    estado = hdfs_leer(http, ARCHIVO_ESTADO)
    ultimo = int(estado) if estado else 0
    ULTIMO_ID.set(ultimo)
    total = 0

    while True:
        r = http.get(
            f"{SALES_URL}/api/v1/sales/export/lines",
            params={"after_id": ultimo, "limit": LOTE},
            headers={"Authorization": f"Bearer {token_de_servicio()}"},
        )
        r.raise_for_status()
        lineas = r.json()

        if not lineas:
            return total

        por_mes = defaultdict(list)
        for l in lineas:
            por_mes[l["fecha"][:7]].append(l)

        for mes, del_mes in sorted(por_mes.items()):
            ruta = f"{DIR_VENTAS}/mes={mes}/lineas_{del_mes[0]['id_linea']}_{del_mes[-1]['id_linea']}.csv"
            hdfs_escribir(http, ruta, a_csv(del_mes))
            ARCHIVOS_ESCRITOS.inc()
            print(f"[hdfs-exporter] {len(del_mes):>6} líneas -> {ruta}", flush=True)

        # El estado se guarda DESPUÉS de escribir los archivos: si algo falla a la mitad,
        # el siguiente ciclo repite el bloque (sobrescribe los mismos archivos) y no se pierde nada.
        ultimo = lineas[-1]["id_linea"]
        hdfs_escribir(http, ARCHIVO_ESTADO, str(ultimo))
        ULTIMO_ID.set(ultimo)
        LINEAS_EXPORTADAS.inc(len(lineas))
        total += len(lineas)

        if len(lineas) < LOTE:
            return total


def main() -> None:

    start_http_server(int(os.getenv("METRICS_PORT", "8005")))
    print(f"[hdfs-exporter] Copiando ventas de {SALES_URL} a HDFS ({WEBHDFS}) cada {INTERVALO} s", flush=True)

    with httpx.Client(timeout=60) as http:
        while True:
            try:
                copiadas = exportar(http)
                if copiadas:
                    print(f"[hdfs-exporter] Ciclo terminado: {copiadas} líneas nuevas en HDFS", flush=True)
            except Exception as error:  # noqa: BLE001
                # HDFS o sales-service pueden estar arrancando: se reintenta en el siguiente ciclo.
                ERRORES.inc()
                print(f"[hdfs-exporter] No se pudo exportar ({error.__class__.__name__}: {error}); se reintenta", flush=True)
            time.sleep(INTERVALO)


if __name__ == "__main__":
    main()
