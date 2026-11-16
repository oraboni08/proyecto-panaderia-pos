# Retos de la entrega final y cómo se resolvieron

Bitácora de lo que no salió bien a la primera mientras migrábamos la Panadería POS a
Docker Swarm. Cada reto tiene: qué pasó, por qué pasó y cómo se resolvió.

---

## Paso 1 · Docker, Swarm y PostgreSQL

### 1. Poca memoria RAM para todo el sistema
- **Qué pasó:** el computador de la demo tiene 7,4 GB de RAM y, con las aplicaciones de uso diario abiertas, solo quedaban 1,6 GB libres. Windows ya estaba comprimiendo memoria.
- **Por qué:** Swarm, PostgreSQL, HDFS, Spark, Prometheus y Grafana juntos piden mucha memoria, y Hadoop y Spark corren sobre Java.
- **Solución:**
  - cerrar las aplicaciones que no se usan;
  - limitar la memoria de Docker/WSL con `.wslconfig` (5 GB + 6 GB de swap);
  - poner un límite de memoria a cada servicio en `docker-stack.yml`;
  - usar un Swarm de un solo nodo;
  - encender Spark solo cuando corre el job.

### 2. SQLite no sirve con varias réplicas
- **Qué pasó:** en el Proyecto 1 cada servicio guardaba sus datos en un archivo SQLite.
- **Por qué:** con 2 réplicas, cada contenedor tendría su propio archivo. Una venta registrada en la réplica 1 no aparecería en la réplica 2.
- **Solución:** pasar a **PostgreSQL**, un servidor que comparten todas las réplicas, con una base separada por servicio (patrón *database per service*). En local y en las pruebas se sigue usando SQLite, porque el servicio elige el motor según la variable `DB_HOST`.

### 3. Los servicios arrancaban antes que PostgreSQL
- **Qué pasó:** al desplegar, los servicios fallaban con `OperationalError` porque PostgreSQL aún no aceptaba conexiones.
- **Por qué:** Docker Swarm no respeta `depends_on`, así que arranca todos los servicios a la vez.
- **Solución:** al iniciar, cada servicio **reintenta la conexión** hasta 30 veces, cada 2 segundos (`_esperar_base` en `database.py`). Además, Swarm reinicia el contenedor si de todas formas falla.

### 4. Dos réplicas cargando el dataset al mismo tiempo
- **Qué pasó:** las 2 réplicas de cada servicio arrancan juntas y las dos ven la base vacía.
- **Por qué:** es una *condición de carrera*. Las dos intentarían crear las tablas y cargar las 94.758 ventas, lo que duplica datos o genera errores de llave repetida.
- **Solución:** un **candado de PostgreSQL** (`pg_advisory_lock`). La primera réplica toma el candado y carga los datos; la segunda espera y, cuando entra, ve que ya están. En los logs se comprueba que cada dataset lo cargó una sola réplica.

### 5. La primera venta nueva chocaba con el id de una venta del dataset
- **Qué pasó:** el dataset se carga con sus ids originales (1 a 94.758).
- **Por qué:** cuando se inserta un id a mano, PostgreSQL no avanza el contador automático (la *secuencia*). La siguiente venta habría intentado usar el id 1, que ya existe.
- **Solución:** después de la carga, el servicio ajusta cada secuencia al id más alto + 1 (`setval`). La venta de prueba quedó con el id 94.759.

### 6. Consultas que solo funcionaban en SQLite
- **Qué pasó:** las métricas del dashboard (ventas por día, hora y mes) usaban `strftime`, que no existe en PostgreSQL. En las pruebas por el gateway, además, el reporte de **productos más vendidos respondía error 500**.
- **Por qué:**
  - Cada motor tiene sus propias funciones de fecha.
  - Para el mes, la consulta enviaba el formato `'YYYY-MM'` como parámetro, una vez en el SELECT y otra en el GROUP BY. PostgreSQL los toma como expresiones distintas y rechaza la consulta.
  - El top de productos usaba un truco de optimización de SQLite (`GROUP BY id_producto + 0`) que PostgreSQL no acepta.
- **Solución:**
  - una función `_parte_fecha` que usa `EXTRACT` / `to_char` en PostgreSQL y `strftime` en SQLite;
  - el formato del mes pasa a texto literal;
  - el truco del `+ 0` solo se aplica en SQLite.
  - El arreglo se desplegó con un **rolling update** (`docker service update`): Swarm cambió una réplica a la vez y el servicio nunca dejó de responder.

### 7. Falló la descarga de la imagen de PostgreSQL
- **Qué pasó:** la primera vez Swarm marcó la tarea de PostgreSQL como `Rejected` con el error `failed to copy: httpReadSeeker`.
- **Por qué:** un corte de red durante la descarga de la imagen desde Docker Hub.
- **Solución:** Swarm reintentó solo la tarea, y se descargó la imagen a mano con `docker pull postgres:16-alpine`. Lección para la demo: **descargar todas las imágenes antes** de presentar.

### 8. La hora de las ventas
- **Qué pasó:** la imagen `python:3.12-slim` no trae zonas horarias, así que las ventas nuevas habrían quedado con la hora UTC (5 horas adelante).
- **Solución:** instalar `tzdata` en la imagen y definir `TZ=America/Bogota` (también en PostgreSQL).

### 9. Contraseñas escritas en el código
- **Qué pasó:** las claves de la base de datos, del JWT y de los usuarios iniciales estaban como valores por defecto o variables de entorno visibles.
- **Solución:** **Docker secrets**. Swarm entrega cada clave como un archivo en `/run/secrets/`, y el servicio la lee mediante la variable `NOMBRE_FILE`. Los archivos de `deploy/secrets/` no se suben a GitHub.

### 10. El front-end apuntaba a una dirección fija
- **Qué pasó:** `config.js` tenía escrita la dirección `api.panaderia-pos.test` del despliegue con Vagrant.
- **Solución:** en Swarm, la interfaz y la API llegan por el mismo API Gateway, así que se usan rutas relativas (`/api/v1/...`).

### 11. El gateway se caía si un servicio no había arrancado
- **Qué pasó:** Nginx resuelve los nombres de los servicios al iniciar. Si `sales-service` aún no existe, Nginx no arranca.
- **Solución:** usar el DNS interno de Docker (`resolver 127.0.0.11`) con variables en `proxy_pass`. Así Nginx resuelve el nombre en cada petición y responde 502 mientras el servicio arranca, en vez de caerse. Además, `proxy_next_upstream` reintenta la petición en otra réplica si una falla.

---

## Paso 2 · Monitoreo con Prometheus y Grafana

### 12. La librería de métricas no era compatible con nuestra versión de FastAPI
- **Qué pasó:** al agregar `prometheus-fastapi-instrumentator`, 65 de las 144 pruebas fallaron con `AttributeError: '_IncludedRouter' object has no attribute 'path'`.
- **Por qué:** la librería no se ha actualizado para FastAPI 0.142, que cambió cómo guarda las rutas internamente.
- **Solución:** en vez de bajar la versión de FastAPI, se escribió un **middleware propio** (`app/api/observabilidad.py`, unas 30 líneas) con la librería oficial `prometheus_client`. Mide cada petición (contador por ruta y código, e histograma de tiempos) y publica `/metrics`. Se etiqueta con la *plantilla* de la ruta (`/orders/{id_venta}`) y no con la URL real, para no crear una serie de datos por cada venta.

### 13. Swarm avisa que las imágenes no están en un registro
- **Qué pasó:** al desplegar, `docker stack deploy` muestra: *"image panaderia/sales-service:latest could not be accessed on a registry to record its digest"*.
- **Por qué:** las imágenes se construyen en el mismo computador y no se suben a Docker Hub. Con un solo nodo funciona, pero en un clúster de varios nodos cada nodo tendría que tener la imagen o podría correr versiones distintas.
- **Solución:** para la demo (un nodo) no hay problema. Si se agregan más nodos, hay que publicar las imágenes en un registro (Docker Hub o un `registry` propio dentro del Swarm). Además, al actualizar un servicio con la misma etiqueta `latest` hay que forzarlo: `docker service update --force --image panaderia/sales-service:latest panaderia_sales-service`.

---

## Pruebas que salieron bien (evidencia para la presentación)

- **Alta disponibilidad (2026-11-16):** con peticiones continuas al API se borró a la fuerza una réplica de `sales-service` (`docker rm -f`). **60 de 60 peticiones respondieron 200** y Swarm volvió a tener 2/2 réplicas en **11 segundos** (en `docker service ps` se ve `Failed … exit (137)` y luego la réplica nueva en `Running`).
- **Rolling update:** el arreglo del top de productos se desplegó con `docker service update` sin cortar el servicio.
- **Carga inicial con candado:** en los logs cada dataset lo carga una sola réplica (6 usuarios, 90 productos, 3.201 clientes, 94.758 ventas, 203.696 líneas).

---

## Paso 3 · HDFS y exportador de ventas

### 14. Muchos archivos pequeños en HDFS
- **Qué pasó:** la primera idea era un archivo CSV por día de ventas.
- **Por qué es un problema:** el NameNode guarda en memoria la información de cada archivo y cada bloque. Con miles de archivos pequeños se llena su memoria y Spark tiene que abrir miles de archivos (el clásico *small files problem* de Hadoop). Solo el histórico habría generado unos 700 archivos.
- **Solución:** agrupar por **mes** (`/panaderia/ventas/mes=AAAA-MM/`). El histórico queda en pocas decenas de archivos y, dentro de cada mes, cada ciclo del exportador agrega un archivo nuevo con las ventas del último minuto.

### 15. No duplicar ni perder ventas si el exportador se reinicia
- **Qué pasó:** si el contenedor del exportador se reinicia, no puede volver a copiar todo ni saltarse ventas.
- **Solución:** el último id exportado se guarda **en el mismo HDFS** (`/panaderia/_estado/ultimo_id`), y se guarda *después* de escribir los archivos. Si falla a mitad de camino, el siguiente ciclo repite el bloque sobrescribiendo los mismos archivos (mismo nombre), así que no se duplica nada. Por la misma razón el exportador corre con **una sola réplica**.

### 16. El exportador no debe leer la base de datos de ventas
- **Qué pasó:** lo más rápido habría sido conectarse directo a `sales_db`.
- **Por qué no:** rompe el patrón *database per service*, porque la base es solo de `sales-service`.
- **Solución:** un endpoint nuevo, `GET /api/v1/sales/export/lines?after_id=…`, que devuelve las líneas por bloques. El exportador se autentica con un **token JWT de servicio** firmado con el mismo Docker secret.

### 17. Los configs de Swarm no se pueden modificar
- **Qué pasó:** al agregar el exportador a `prometheus.yml`, Swarm no deja actualizar un config que ya existe (los configs y secrets son inmutables).
- **Solución:** versionar el nombre (`prometheus_conf` → `prometheus_conf_v2`). Así Swarm crea el config nuevo y actualiza el servicio con un rolling update.

### 18. Swarm seguía corriendo la versión vieja de sales-service
- **Qué pasó:** después de agregar el endpoint de exportación y reconstruir la imagen, el exportador recibía **404** en `/api/v1/sales/export/lines`.
- **Por qué:** la imagen nueva tenía la misma etiqueta (`panaderia/sales-service:latest`). Para `docker stack deploy` el servicio "no cambió", así que no reemplazó las réplicas (ver reto 13).
- **Solución:** forzar el rolling update con `docker service update --force --image panaderia/sales-service:latest panaderia_sales-service`. Mejora futura: etiquetar cada versión (`:v2`, `:v3`) en vez de usar `latest`.


### Evidencias del paso 3 (2026-11-16)
- **Carga del histórico a HDFS:** el exportador copió 203.706 líneas en 23 carpetas de mes (27 archivos, 19,3 MB). `hdfs fsck /panaderia/ventas` → `Status: HEALTHY`.
- **De la caja a HDFS:** la venta 94765 (Daviplata) apareció en `/panaderia/ventas/mes=2026-11/lineas_203707_203708.csv` **36 segundos** después de registrarse.
- **Reinicio sin duplicados:** se borró a la fuerza el contenedor del exportador. Swarm lo recreó en 11 s, retomó desde el id 203708 guardado en HDFS y no volvió a copiar nada (28 archivos en total).

---

## Paso 4 · Spark, reporting-service (CQRS) y pantalla de Reportes

### 19. Spark no podía leer los bloques de HDFS dentro de Swarm
- **Qué pasó:** el job fallaba con `java.net.ConnectException: Connection refused` y `Failed to connect to /10.0.2.5:9866`.
- **Por qué:** el NameNode registró al DataNode con la IP `10.0.2.5`, que es la del **balanceador interno de la red overlay** de Swarm (el tráfico pasa por un NAT), y no con su IP real (`10.0.2.33`). Spark pedía al NameNode dónde estaban los bloques, recibía esa IP equivocada y la conexión se rechazaba. El exportador no tenía el problema porque WebHDFS redirige por **nombre** (`datanode`).
- **Solución:** que Spark se conecte al DataNode por su nombre: `spark.hadoop.dfs.client.use.datanode.hostname=true`. El DNS de Swarm resuelve `datanode` correctamente.

### 20. El script para lanzar Spark terminaba antes de que el job empezara
- **Qué pasó:** `correr_spark.sh` no mostraba nada y el job nunca corría.
- **Por qué:** el script empezaba a leer los logs antes de que Swarm creara la tarea; `docker service logs` terminaba enseguida y el script volvía a poner 0 réplicas.
- **Solución:** esperar el estado real de la tarea con `docker service ps` hasta `Complete` o `Failed`, y solo entonces mostrar los logs.

### 21. Spark juntaba los archivos en pocas particiones
- **Qué pasó:** el primer job usó solo 7 particiones y reportó "0 archivos".
- **Por qué:** Spark junta archivos pequeños en una misma partición hasta 128 MB (`maxPartitionBytes`). El conteo de archivos se pedía después de transformar los datos.
- **Solución:** `spark.sql.files.maxPartitionBytes = 4 MB` (igual al bloque de HDFS) y contar los archivos sobre la lectura original. Ahora: 28 archivos en 9 particiones procesadas en paralelo con 8 núcleos.

### 22. Los mejores clientes no coincidían entre Spark y el dashboard
- **Qué pasó:** al comparar los resultados de Spark con los de `sales-service`, todo coincidía excepto el ranking de clientes.
- **Por qué:** no era un error de cálculo sino de criterio: el dashboard ordena por **número de compras** y Spark ordenaba por **dinero gastado**.
- **Solución:** usar el mismo criterio en los dos (compras y luego gasto). Ahora los 10 primeros son idénticos.

### 23. El domingo salía con 0 ventas en el dashboard (bug que venía del Proyecto 1)
- **Qué pasó:** al hacer la pantalla de Reportes se notó que la gráfica "Ventas por día" del dashboard nunca mostraba ventas el domingo.
- **Por qué:** la API numera los días 1 = lunes … **7 = domingo**, pero la gráfica buscaba el domingo como día **0**.
- **Solución:** buscar los días 1 a 7 y usar `numero_dia % 7` para la etiqueta. Ahora el domingo aparece (es el día con más ventas).

### Evidencias del paso 4 (2026-11-16)
- **Spark:** leyó 203.708 líneas (94.765 ventas) de 28 archivos en HDFS, 9 particiones con 8 núcleos, en ~26-30 s (con el arranque del contenedor, ~40 s).
- **Exactitud:** los reportes de Spark (sobre HDFS) y los del dashboard (sobre PostgreSQL) dan **exactamente los mismos números**: top 10 de productos, ventas por hora, por día, por mes, por categoría y top 10 de clientes.
- **CQRS:** la pantalla Reportes solo llama a `reporting-service` (`/api/v1/reports/resumen`), que lee `reports_db`; la caja sigue escribiendo en `sales_db`.

---

## Video demo

### 24. Grafana mostraba «0 ventas» aunque sí había ventas
- **Qué pasó:** al grabar el video demo, el panel «Ventas registradas» de Grafana decía 0 después de hacer ventas en la caja.
- **Por qué:** el contador `panaderia_ventas_total` tiene una etiqueta por método de pago, y cada etiqueta solo aparecía con la primera venta de ese método, cuando el contador **ya valía 1**. `increase()` de Prometheus necesita ver el salto 0 → 1; sin el 0, esa venta no se cuenta. Además, al matar una réplica su contador se pierde (los contadores viven en memoria de cada réplica).
- **Solución:** crear las 6 etiquetas en 0 cuando arranca `sales-service` (práctica recomendada por Prometheus) y actualizar con rolling update, sin cortar el servicio. También se cambió la unidad del panel de ingresos para mostrar `$`. Como los configs de Swarm son inmutables, el dashboard pasó a `grafana_dashboard_pos_v2`.
- **Evidencia:** una venta con Daviplata aparece en Grafana como «Ventas: 1» al siguiente scrape (capítulo 6 del video).
