// Función común para llamar a la API REST.
// Agrega el token, convierte la respuesta JSON y transforma los errores HTTP en mensajes.

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function errorMessage(status, data) {
  if (data && typeof data.detail === "string") return data.detail;

  if (status === 422 && data && Array.isArray(data.detail)) {
    const campos = data.detail.map((e) => e.loc[e.loc.length - 1]).join(", ");
    return `Datos inválidos en: ${campos}`;
  }

  if (status === 503) return "Un servicio no está disponible. Intenta de nuevo.";
  if (status >= 500) return "Ocurrió un error en el servidor.";
  return `Error ${status}`;
}

async function api(service, path, { method = "GET", body, params } = {}) {
  let url = API_URLS[service] + path;

  if (params) {
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")
    );
    if ([...query].length) url += `?${query}`;
  }

  const headers = { "Content-Type": "application/json" };
  const session = getSession();
  if (session) headers.Authorization = `Bearer ${session.token}`;

  let response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "No se pudo conectar con el servidor.");
  }

  const data = await response.json().catch(() => null);

  // Token vencido o inválido: se cierra la sesión.
  if (response.status === 401 && session) {
    logout();
  }

  if (!response.ok) {
    throw new ApiError(response.status, errorMessage(response.status, data));
  }

  return data;
}
