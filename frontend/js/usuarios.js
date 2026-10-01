const session = requireRole("admin");
renderAdminSidebar("usuarios");

const mensaje = $("#mensaje");
const formError = $("#form-error");
const modal = setupModal("#modal");

let usuarios = [];

function render() {
  $("#tabla").innerHTML = usuarios
    .map((u) => {
      const esYo = u.usuario === session.usuario;
      const accion = esYo
        ? '<span class="hint">Tu usuario</span>'
        : u.activo
          ? `<button class="btn btn-danger-outline btn-sm" data-id="${u.id_usuario}" data-activo="false">Desactivar</button>`
          : `<button class="btn btn-outline btn-sm" data-id="${u.id_usuario}" data-activo="true">Reactivar</button>`;

      return `<tr>
        <td><strong>${escapeHtml(u.nombre)}</strong></td>
        <td>${escapeHtml(u.usuario)}</td>
        <td>${u.rol === "admin" ? "Administrador" : "Cajero"}</td>
        <td>${u.activo ? '<span class="badge badge-success">Activo</span>' : '<span class="badge badge-muted">Inactivo</span>'}</td>
        <td class="hint">${u.creado_en ? formatDateTime(u.creado_en) : "—"}</td>
        <td class="num">${accion}</td>
      </tr>`;
    })
    .join("");
}

async function cargar() {
  try {
    usuarios = await api("auth", "/users");
    render();
  } catch (error) {
    showAlert(mensaje, error.message);
  }
}

$("#nuevo").addEventListener("click", () => {
  $("#form").reset();
  hideAlert(formError);
  modal.open();
  $("#nombre").focus();
});

$("#form").addEventListener("submit", async (event) => {
  event.preventDefault();
  hideAlert(formError);

  const body = {
    nombre: $("#nombre").value.trim(),
    usuario: $("#usuario").value.trim().toLowerCase(),
    password: $("#password").value,
    rol: $("#rol").value,
  };

  if (!body.nombre || !body.usuario) return showAlert(formError, "Completa el nombre y el usuario.");
  if (/\s/.test(body.usuario)) return showAlert(formError, "El usuario no puede tener espacios.");
  if (body.password.length < 8) return showAlert(formError, "La contraseña debe tener mínimo 8 caracteres.");

  $("#guardar").disabled = true;

  try {
    await api("auth", "/users", { method: "POST", body });
    modal.close();
    showAlert(mensaje, `Usuario "${body.usuario}" creado.`, "success");
    await cargar();
  } catch (error) {
    showAlert(formError, error.message);
  } finally {
    $("#guardar").disabled = false;
  }
});

$("#tabla").addEventListener("click", async (event) => {
  const boton = event.target.closest("[data-id]");
  if (!boton) return;

  const activo = boton.dataset.activo === "true";
  const usuario = usuarios.find((u) => u.id_usuario === Number(boton.dataset.id));

  try {
    await api("auth", `/users/${usuario.id_usuario}`, { method: "PATCH", body: { activo } });
    showAlert(mensaje, `Usuario "${usuario.usuario}" ${activo ? "reactivado" : "desactivado"}.`, "success");
    await cargar();
  } catch (error) {
    showAlert(mensaje, error.message);
  }
});

cargar();
