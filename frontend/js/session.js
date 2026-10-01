// Manejo de la sesión en el navegador.
// El token se guarda en sessionStorage: se borra al cerrar el navegador.
// Proteger las páginas aquí es solo comodidad; la protección real la hace el back-end (401/403).

const SESSION_KEY = "panaderia-pos-session";

const HOME_BY_ROLE = {
  admin: "/admin/dashboard.html",
  cajero: "/cajero/venta.html",
};

function saveSession(data) {
  sessionStorage.setItem(
    SESSION_KEY,
    JSON.stringify({
      token: data.access_token,
      usuario: data.usuario,
      nombre: data.nombre,
      rol: data.rol,
    })
  );
}

function getSession() {
  try {
    return JSON.parse(sessionStorage.getItem(SESSION_KEY));
  } catch {
    return null;
  }
}

function logout() {
  sessionStorage.removeItem(SESSION_KEY);
  window.location.href = "/";
}

// Si no hay sesión o el rol no corresponde, redirige. Devuelve la sesión.
function requireRole(rol) {
  const session = getSession();

  if (!session) {
    window.location.replace("/");
    throw new Error("Sin sesión");
  }

  if (session.rol !== rol) {
    window.location.replace(HOME_BY_ROLE[session.rol] || "/");
    throw new Error("Rol no autorizado");
  }

  return session;
}
