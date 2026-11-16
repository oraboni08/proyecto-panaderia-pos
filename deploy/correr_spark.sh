#!/usr/bin/env bash
# Ejecuta el job de Spark en el Swarm y muestra su resultado.
#   ./deploy/correr_spark.sh
# Mientras corre, la interfaz de Spark está en http://localhost:4040
set -uo pipefail

SERVICIO=panaderia_spark-job

echo "Lanzando el job de Spark (lee las ventas de HDFS y calcula los reportes)..."
docker service scale -d "$SERVICIO=0" >/dev/null
docker service scale -d "$SERVICIO=1" >/dev/null

# Espera a que Swarm cree la tarea y a que termine (Complete) o falle (Failed).
inicio=$(date +%s)
while true; do
  estado=$(docker service ps "$SERVICIO" --filter desired-state=running --format '{{.CurrentState}}' 2>/dev/null | head -1)
  [ -z "$estado" ] && estado=$(docker service ps "$SERVICIO" --format '{{.CurrentState}}' 2>/dev/null | head -1)
  case "$estado" in
    Complete*) resultado=ok; break ;;
    Failed*|Rejected*) resultado=error; break ;;
  esac
  if [ $(( $(date +%s) - inicio )) -gt 600 ]; then resultado=tiempo; break; fi
  sleep 3
done

# Muestra solo los mensajes del job (sin el detalle interno de Spark).
docker service logs --raw --since "$(( $(date +%s) - inicio + 5 ))s" "$SERVICIO" 2>&1 \
  | grep -E "\[spark\]|Traceback|Error:" | tail -20

docker service scale -d "$SERVICIO=0" >/dev/null

case "$resultado" in
  ok)     echo "Listo en $(( $(date +%s) - inicio )) s. Reportes en http://localhost (admin -> Reportes)." ;;
  error)  echo "El job falló. Detalle: docker service logs $SERVICIO"; exit 1 ;;
  tiempo) echo "El job tardó más de 10 minutos. Revisar: docker service ps $SERVICIO"; exit 1 ;;
esac
