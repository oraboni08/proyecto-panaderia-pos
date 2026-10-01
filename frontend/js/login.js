// Si ya hay sesión, va directo a su pantalla.
const existing = getSession();
if (existing) window.location.replace(HOME_BY_ROLE[existing.rol]);

const form = $("#login-form");
const errorBox = $("#error");
const submit = $("#submit");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideAlert(errorBox);

  const usuario = $("#usuario").value.trim();
  const password = $("#password").value;

  // Validación de forma: campos llenos.
  if (!usuario || !password) {
    showAlert(errorBox, "Escribe tu usuario y tu contraseña.");
    return;
  }

  submit.disabled = true;
  submit.textContent = "Ingresando…";

  try {
    const data = await api("auth", "/tokens", { method: "POST", body: { usuario, password } });
    saveSession(data);
    window.location.replace(HOME_BY_ROLE[data.rol]);
  } catch (error) {
    showAlert(errorBox, error.message);
    submit.disabled = false;
    submit.textContent = "Ingresar";
  }
});
