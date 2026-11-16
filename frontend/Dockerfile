# Imagen del front-end: archivos estáticos servidos por Nginx.
#   docker build -t panaderia/frontend frontend
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY . /usr/share/nginx/html

# Archivos que no deben quedar publicados.
RUN rm -f /usr/share/nginx/html/Dockerfile /usr/share/nginx/html/nginx.conf \
          /usr/share/nginx/html/img/recortar_fotos.py

HEALTHCHECK --interval=15s --timeout=3s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
