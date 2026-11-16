// Inicio de sesión: pide el token a auth-service y lleva a cada rol a su pantalla.

const existing = getSession();
if (existing) window.location.replace(HOME_BY_ROLE[existing.rol]);

$("#art-logo").innerHTML = `
  <svg viewBox="0 0 64 64" width="56" height="56" aria-hidden="true"><circle cx="32" cy="32" r="30" fill="none" stroke="#fff" stroke-width="2.4"/><path d="M32 51V20" stroke="#fff" stroke-width="2.6" stroke-linecap="round"/><g fill="#fff"><ellipse cx="32" cy="15.5" rx="3.3" ry="5.4"/><ellipse cx="26.9" cy="24.5" rx="3.1" ry="5.4" transform="rotate(-38 26.9 24.5)"/><ellipse cx="37.1" cy="24.5" rx="3.1" ry="5.4" transform="rotate(38 37.1 24.5)"/><ellipse cx="26.9" cy="33" rx="3.1" ry="5.4" transform="rotate(-38 26.9 33)"/><ellipse cx="37.1" cy="33" rx="3.1" ry="5.4" transform="rotate(38 37.1 33)"/><ellipse cx="26.9" cy="41.5" rx="3.1" ry="5.4" transform="rotate(-38 26.9 41.5)"/><ellipse cx="37.1" cy="41.5" rx="3.1" ry="5.4" transform="rotate(38 37.1 41.5)"/></g></svg>
  <div><b>Pan del Valle</b><span>Panadería · Cafetería</span></div>`;
$("#ico-user").innerHTML = icon("user", 20);
$("#ico-lock").innerHTML = icon("lock", 20);
applyTheme(getTheme());

const form = $("#login-form");
const errorBox = $("#error");
const submit = $("#submit");
const password = $("#password");
const ver = $("#ver");

function showError(message) {
  errorBox.innerHTML = `${icon("alert", 20, 2)}<span>${escapeHtml(message)}</span>`;
  errorBox.hidden = false;
  $("#usuario-box").classList.add("err");
  $("#password-box").classList.add("err");
}

function clearError() {
  errorBox.hidden = true;
  $("#usuario-box").classList.remove("err");
  $("#password-box").classList.remove("err");
}

function renderVer() {
  const visible = password.type === "text";
  ver.innerHTML = icon(visible ? "eyeoff" : "eye", 20);
  ver.setAttribute("aria-label", visible ? "Ocultar contraseña" : "Mostrar contraseña");
}

ver.addEventListener("click", () => {
  password.type = password.type === "password" ? "text" : "password";
  renderVer();
});
renderVer();

$("#olvide").addEventListener("click", (e) => {
  e.preventDefault();
  toast("Pídele al administrador que te asigne una contraseña nueva.");
});

form.addEventListener("input", clearError);

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  const usuario = $("#usuario").value.trim();
  if (!usuario || !password.value) {
    showError("Escribe tu usuario y tu contraseña.");
    return;
  }

  submit.disabled = true;
  submit.innerHTML = `<span class="spin" aria-hidden="true"></span>Verificando…`;

  try {
    const data = await api("auth", "/tokens", { method: "POST", body: { usuario, password: password.value } });
    saveSession(data);
    window.location.replace(HOME_BY_ROLE[data.rol]);
  } catch (error) {
    showError(error.status === 401 ? "Usuario o contraseña incorrectos. Revisa los datos e inténtalo de nuevo." : error.message);
    submit.disabled = false;
    submit.textContent = "Ingresar";
  }
});

$("#usuario").focus();
