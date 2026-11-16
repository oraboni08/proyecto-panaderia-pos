// Formulario de cliente compartido por la caja (modal "Nuevo cliente") y la pantalla Clientes.
// Valida en el navegador lo mismo que valida sales-service y muestra cada error junto a su campo.

const TIPOS_DOC = [
  ["CC", "CC · Cédula de ciudadanía"],
  ["CE", "CE · Cédula de extranjería"],
  ["TI", "TI · Tarjeta de identidad"],
  ["PP", "PP · Pasaporte"],
  ["NIT", "NIT"],
];

function customerFormHtml(c = {}, { compacto = false } = {}) {
  const v = (x) => escapeHtml(x ?? "");
  const campo = (id, label, valor, extra = "", span = false) => `
    <div class="fld ${span ? "span2" : ""}" data-f="${id}">
      <label for="cf-${id}">${label}</label>
      <input id="cf-${id}" name="${id}" class="fi" value="${v(valor)}" ${extra}>
      <span class="ferr" hidden></span>
    </div>`;

  return `
    <div class="grid2">
      ${campo("nombre", "Nombre completo *", c.nombre, 'autocomplete="off" placeholder="Nombre y apellidos"', true)}
      <div class="fld" data-f="tipo_documento">
        <label for="cf-tipo_documento">Tipo de documento</label>
        <select id="cf-tipo_documento" name="tipo_documento" class="fi">
          ${TIPOS_DOC.map(([k, t]) => `<option value="${k}" ${(c.tipo_documento || "CC") === k ? "selected" : ""}>${t}</option>`).join("")}
        </select>
      </div>
      ${campo("documento", "Número de documento", formatDocument(c.documento), 'inputmode="numeric" autocomplete="off"')}
      ${campo("telefono", "Celular", formatPhone(c.telefono), 'inputmode="tel" autocomplete="off" placeholder="300 000 0000"')}
      ${campo("correo", "Correo (opcional)", c.correo, 'type="email" autocomplete="off" placeholder="nombre@correo.com"')}
      ${compacto ? "" : campo("direccion", "Dirección", c.direccion, 'autocomplete="off" placeholder="Cl. 5 # 27-14"', true)}
      ${campo("barrio", "Barrio", c.barrio, 'autocomplete="off"')}
      ${campo("ciudad", "Ciudad", c.ciudad ?? "Cali", 'autocomplete="off"')}
    </div>
    <div class="alert" data-general hidden></div>`;
}

function _setFieldError(root, campo, mensaje) {
  const f = root.querySelector(`[data-f="${campo}"]`);
  if (!f) return false;
  f.querySelector(".fi").classList.add("err");
  const e = f.querySelector(".ferr");
  e.innerHTML = `${icon("alert", 14, 2.2)}${escapeHtml(mensaje)}`;
  e.hidden = false;
  return true;
}

function clearCustomerErrors(root) {
  root.querySelectorAll(".fi.err").forEach((el) => el.classList.remove("err"));
  root.querySelectorAll(".ferr").forEach((el) => (el.hidden = true));
  const g = root.querySelector("[data-general]");
  if (g) g.hidden = true;
}

// Lee el formulario. Devuelve null (y marca los errores) si algo no es válido.
function readCustomerForm(root) {
  clearCustomerErrors(root);
  const val = (n) => root.querySelector(`[name="${n}"]`)?.value.trim() ?? "";
  const datos = {
    nombre: val("nombre").replace(/\s+/g, " "),
    tipo_documento: val("tipo_documento"),
    documento: val("documento").replace(/[.\s]/g, ""),
    telefono: val("telefono").replace(/[\s\-()+]/g, ""),
    correo: val("correo"),
    barrio: val("barrio"),
    ciudad: val("ciudad"),
  };
  if (root.querySelector('[name="direccion"]')) datos.direccion = val("direccion");

  let ok = true;
  if (datos.nombre.length < 3) { _setFieldError(root, "nombre", "Escribe el nombre completo del cliente."); ok = false; }
  if (datos.documento && datos.tipo_documento !== "PP" && !/^\d{5,11}(-\d)?$/.test(datos.documento)) {
    { _setFieldError(root, "documento", "Usa solo números, entre 5 y 11 dígitos."); ok = false; }
  }
  if (datos.telefono.startsWith("57") && datos.telefono.length === 12) datos.telefono = datos.telefono.slice(2);
  if (datos.telefono && !/^(3\d{9}|60\d{8})$/.test(datos.telefono)) {
    { _setFieldError(root, "telefono", "El celular debe tener 10 dígitos y empezar por 3."); ok = false; }
  }
  if (datos.correo && !/^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$/.test(datos.correo)) {
    { _setFieldError(root, "correo", "Revisa el correo: falta la @ o el dominio."); ok = false; }
  }
  if (!ok) return null;

  // Campos vacíos no se envían (el cliente puede no tener cédula o correo).
  Object.keys(datos).forEach((k) => {
    if (datos[k] === "") datos[k] = k === "tipo_documento" ? undefined : null;
  });
  if (!datos.documento) datos.tipo_documento = undefined;
  return datos;
}

// Muestra un error del servidor en el campo que corresponde.
function showCustomerApiError(root, error) {
  const m = error.message || "";
  const n = normalize(m);
  const campo = error.status === 409 || n.includes("documento") ? "documento"
    : n.includes("telefono") ? "telefono"
    : n.includes("correo") ? "correo"
    : n.includes("nombre") ? "nombre" : null;
  if (campo && _setFieldError(root, campo, m)) return;
  const g = root.querySelector("[data-general]");
  if (g) {
    g.innerHTML = `${icon("alert", 18, 2)}<span>${escapeHtml(m)}</span>`;
    g.hidden = false;
  } else {
    toast(m, "err");
  }
}
