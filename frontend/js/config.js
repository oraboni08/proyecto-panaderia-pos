// Direcciones de los microservicios.
// - En Docker Swarm la página y la API llegan por el mismo API Gateway (Nginx),
//   así que basta con rutas relativas: /api/v1/<servicio>.
// - En el computador local (python run_dev.py, front-end en el puerto 8080)
//   cada servicio tiene su propio puerto.

const LOCAL_DEV =
  ["127.0.0.1", "localhost"].includes(window.location.hostname) && window.location.port === "8080";

const API_URLS = LOCAL_DEV
  ? {
      auth: "http://127.0.0.1:8001/api/v1/auth",
      catalog: "http://127.0.0.1:8002/api/v1/catalog",
      sales: "http://127.0.0.1:8003/api/v1/sales",
      reports: "http://127.0.0.1:8004/api/v1/reports",
    }
  : {
      auth: "/api/v1/auth",
      catalog: "/api/v1/catalog",
      sales: "/api/v1/sales",
      reports: "/api/v1/reports",
    };
