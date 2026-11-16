#!/usr/bin/env bash
# Despliega la Panadería POS completa en Docker Swarm.
#   ./deploy/desplegar.sh
#
# 1. Activa Swarm en este equipo si todavía no está activo (nodo manager).
# 2. Crea los secretos que falten en deploy/secrets/ (nunca sobrescribe los existentes).
# 3. Construye las imágenes propias y despliega el stack "panaderia".
set -euo pipefail

cd "$(dirname "$0")/.."
STACK=panaderia
SECRETOS=deploy/secrets

aleatorio() {
  # 32 caracteres alfanuméricos
  LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32
}

secreto() {
  # secreto <nombre> <valor>: lo crea solo si no existe
  local archivo="$SECRETOS/$1.txt"
  if [ ! -s "$archivo" ]; then
    printf '%s' "$2" >"$archivo"
    echo "  creado  $archivo"
  else
    echo "  existe  $archivo"
  fi
}

echo "1/3 Docker Swarm"
if [ "$(docker info --format '{{.Swarm.LocalNodeState}}')" != "active" ]; then
  docker swarm init >/dev/null
  echo "  Swarm inicializado: este equipo es el nodo manager"
else
  echo "  Swarm ya está activo"
fi

echo "2/3 Secretos"
mkdir -p "$SECRETOS"
secreto db_password "$(aleatorio)"
secreto jwt_secret "$(aleatorio)"
# Contraseñas iniciales de la aplicación y de Grafana (cámbielas en estos archivos antes del primer despliegue).
secreto admin_password admin12345
secreto cajero_password cajero12345
secreto grafana_password admin12345

echo "3/3 Imágenes y stack"
docker compose -f docker-stack.yml build
docker stack deploy -c docker-stack.yml "$STACK"

echo
echo "Listo. Swarm está levantando los servicios (la primera vez tarda 1-2 minutos)."
echo "  Estado:        docker service ls"
echo "  Aplicación:    http://localhost          (admin / cajero)"
echo "  Grafana:       http://localhost:3000     (admin)"
echo "  Prometheus:    http://localhost:9090"
echo "  HDFS:          http://localhost:9870"
echo "  Job de Spark:  ./deploy/correr_spark.sh"
