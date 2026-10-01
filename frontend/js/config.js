// Direcciones de los microservicios.
// En el servidor todas las peticiones pasan por el API Gateway (api.panaderia-pos.test);
// en el computador local (python run_dev.py) cada servicio tiene su propio puerto.
// Al desplegar, Ansible reemplaza este archivo con la dirección del gateway.

const LOCAL = ["127.0.0.1", "localhost"].includes(window.location.hostname);

const API_GATEWAY = "http://api.panaderia-pos.test";

const API_URLS = LOCAL
  ? {
      auth: "http://127.0.0.1:8001/api/v1/auth",
      catalog: "http://127.0.0.1:8002/api/v1/catalog",
      sales: "http://127.0.0.1:8003/api/v1/sales",
    }
  : {
      auth: `${API_GATEWAY}/api/v1/auth`,
      catalog: `${API_GATEWAY}/api/v1/catalog`,
      sales: `${API_GATEWAY}/api/v1/sales`,
    };
