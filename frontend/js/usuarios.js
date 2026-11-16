// Usuarios: el administrador crea cajeros y administradores, y les quita o devuelve el acceso.

const yo = renderAdminShell("usuarios");
const us = { usuarios: [], buscar: "", rol: "" };

$("#nuevo").innerHTML = `${icon("plus", 18, 2.2)}Nuevo usuario`;
$("#ico-buscar").innerHTML = icon("search", 18, 2);
$("#ico-info").innerHTML = icon("info", 16);

function render() {
  const q = normalize(us.buscar);
  const lista = us.usuarios.filter((u) => (!us.rol || u.rol === us.rol) && (!q || normalize(`${u.nombre} ${u.usuario}`).includes(q)));
  const cajeros = us.usuarios.filter((u) => u.rol === "cajero" && u.activo).length;
  $("#resumen").textContent = `${cajeros} cajeros con acceso · ${us.usuarios.filter((u) => u.rol === "admin" && u.activo).length} administradores`;
  $("#conteo").textContent = `Mostrando ${lista.length} de ${us.usuarios.length} usuarios`;

  $("#filas").innerHTML = lista.length ? lista.map((u) => {
    const soyYo = u.usuario === yo.usuario;
    return `<tr style="${u.activo ? "" : "opacity:.62"}">
      <td><div style="display:flex;align-items:center;gap:10px"><span class="av ${u.rol === "admin" ? "solid" : ""}">${escapeHtml(initials(u.nombre))}</span>
        <b>${escapeHtml(u.nombre)}</b>${soyYo ? '<span class="chip warn">Tú</span>' : ""}</div></td>
      <td class="num">${escapeHtml(u.usuario)}</td>
      <td>${u.rol === "admin" ? `<span class="chip role-admin">${icon("shield", 14)}Administrador</span>` : `<span class="chip">${icon("store", 14)}Cajero</span>`}</td>
      <td class="muted">${u.creado_en ? formatDate(u.creado_en) : "—"}</td>
      <td><button class="sw ${u.activo ? "on" : ""}" type="button" role="switch" aria-checked="${u.activo}" data-id="${u.id_usuario}" ${soyYo ? 'disabled title="No puedes quitarte el acceso a ti mismo"' : ""}
        aria-label="${u.activo ? "Quitar acceso a" : "Dar acceso a"} ${escapeHtml(u.nombre)}"><span class="tr"><span class="th"></span></span>${u.activo ? "Activo" : "Sin acceso"}</button></td>
    </tr>`;
  }).join("") : `<tr><td colspan="5"><div class="empty">${icon("users", 36, 1.5)}<b>Ningún usuario coincide</b></div></td></tr>`;
}

async function cargar() {
  $("#filas").innerHTML = Array.from({ length: 5 }, () => `<tr>${'<td><div class="sk" style="height:20px"></div></td>'.repeat(5)}</tr>`).join("");
  try {
    us.usuarios = (await api("auth", "/users")).sort((a, b) => (a.rol === b.rol ? a.nombre.localeCompare(b.nombre) : a.rol === "admin" ? -1 : 1));
    render();
  } catch (error) {
    $("#filas").innerHTML = `<tr><td colspan="5"><div class="empty">${icon("alert", 36, 1.5)}<b>No se pudieron cargar los usuarios</b><span>${escapeHtml(error.message)}</span></div></td></tr>`;
  }
}

$("#buscar").addEventListener("input", (e) => { us.buscar = e.target.value; render(); });
$("#rol").addEventListener("click", (e) => {
  const b = e.target.closest("[data-r]");
  if (!b) return;
  us.rol = b.dataset.r;
  $$("#rol button").forEach((x) => x.classList.toggle("on", x === b));
  render();
});

$("#filas").addEventListener("click", async (e) => {
  const b = e.target.closest("[data-id]");
  if (!b || b.disabled) return;
  const u = us.usuarios.find((x) => x.id_usuario === Number(b.dataset.id));
  b.disabled = true;
  try {
    await api("auth", `/users/${u.id_usuario}`, { method: "PATCH", body: { activo: !u.activo } });
    u.activo = !u.activo;
    toast(u.activo ? `${u.nombre} puede volver a entrar` : `${u.nombre} ya no puede entrar al sistema`);
    render();
  } catch (error) {
    toast(error.message, "err");
    b.disabled = false;
  }
});

// ---------- Nuevo usuario ----------

$("#nuevo").addEventListener("click", () => {
  const d = openDrawer(`${drawerHead("Nuevo usuario", "Podrá entrar con estos datos de inmediato")}
    <form class="drawer-body" id="uf" novalidate>
      <div class="fld" data-f="nombre"><label for="uf-nombre">Nombre completo *</label><input id="uf-nombre" class="fi" autocomplete="off" placeholder="Nombre y apellido"><span class="ferr" hidden></span></div>
      <div class="fld" data-f="usuario"><label for="uf-usuario">Usuario *</label><input id="uf-usuario" class="fi" autocomplete="off" autocapitalize="none" spellcheck="false" placeholder="Ej.: mcastillo">
        <span class="help">Inicial del nombre y el apellido, sin espacios ni tildes.</span><span class="ferr" hidden></span></div>
      <div class="fld" data-f="password"><label for="uf-password">Contraseña inicial *</label><input id="uf-password" class="fi" type="password" autocomplete="new-password">
        <span class="help">Mínimo 8 caracteres. Entrégasela a la persona en privado.</span><span class="ferr" hidden></span></div>
      <div class="fld"><span class="lbl">Rol</span>
        <div class="seg" id="uf-rol"><button type="button" class="on" data-r="cajero">${icon("store", 16)}Cajero</button><button type="button" data-r="admin">${icon("shield", 16)}Administrador</button></div>
        <span class="help" id="uf-rol-help">Solo puede vender y ver sus propias ventas.</span></div>
      <div class="alert" id="uf-error" hidden></div>
    </form>
    <div class="drawer-foot"><button class="btn" type="button" data-close>Cancelar</button><button class="btn p" type="submit" form="uf">Crear usuario</button></div>`, "Nuevo usuario");

  let rol = "cajero";
  $("#uf-rol", d).addEventListener("click", (e) => {
    const b = e.target.closest("[data-r]");
    if (!b) return;
    rol = b.dataset.r;
    $$("#uf-rol button", d).forEach((x) => x.classList.toggle("on", x === b));
    $("#uf-rol-help", d).textContent = rol === "admin" ? "Acceso completo: catálogo, clientes, métricas y usuarios." : "Solo puede vender y ver sus propias ventas.";
  });

  // Propone el usuario a partir del nombre (María Castillo → mcastillo).
  let tocado = false;
  $("#uf-usuario", d).addEventListener("input", () => { tocado = true; });
  $("#uf-nombre", d).addEventListener("input", (e) => {
    if (tocado) return;
    const p = normalize(e.target.value).replace(/[^a-z\s]/g, "").trim().split(/\s+/);
    $("#uf-usuario", d).value = p.length > 1 ? p[0][0] + p[1] : p[0] || "";
  });

  const marcar = (campo, msg) => {
    const f = $(`[data-f="${campo}"]`, d);
    f.querySelector(".fi").classList.add("err");
    f.querySelector(".ferr").innerHTML = `${icon("alert", 14, 2.2)}${escapeHtml(msg)}`;
    f.querySelector(".ferr").hidden = false;
  };

  $("#uf", d).addEventListener("submit", async (e) => {
    e.preventDefault();
    $$(".err", d).forEach((x) => x.classList.remove("err"));
    $$(".ferr", d).forEach((x) => (x.hidden = true));
    $("#uf-error", d).hidden = true;
    const body = { nombre: $("#uf-nombre", d).value.trim(), usuario: $("#uf-usuario", d).value.trim().toLowerCase(), password: $("#uf-password", d).value, rol };
    let ok = true;
    if (body.nombre.length < 3) { marcar("nombre", "Escribe el nombre completo."); ok = false; }
    if (!/^[a-z0-9._]{3,30}$/.test(body.usuario)) { marcar("usuario", "Usa de 3 a 30 letras o números, sin espacios ni tildes."); ok = false; }
    if (body.password.length < 8) { marcar("password", "La contraseña debe tener al menos 8 caracteres."); ok = false; }
    if (!ok) return;

    const btn = $('[form="uf"]', d);
    btn.disabled = true;
    try {
      await api("auth", "/users", { method: "POST", body });
      toast(`Usuario ${body.usuario} creado`);
      closeDrawer();
      cargar();
    } catch (error) {
      if (error.status === 409) marcar("usuario", error.message);
      else {
        $("#uf-error", d).innerHTML = `${icon("alert", 18, 2)}<span>${escapeHtml(error.message)}</span>`;
        $("#uf-error", d).hidden = false;
      }
      btn.disabled = false;
    }
  });
});

cargar();
