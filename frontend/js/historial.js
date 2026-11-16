// Historial de ventas. Lo usan el administrador (todas las ventas) y el cajero (solo las suyas).
// El filtro por cajero lo aplica sales-service: a un cajero siempre le devuelve únicamente sus ventas.

const ROL = document.body.dataset.rol;
const POR_PAGINA = 25;
const hs = { ventas: [], pagina: 1, buscar: "", cajeros: new Map(), limite: false };

let sesion;
if (ROL === "admin") {
  sesion = renderAdminShell("historial");
} else {
  sesion = requireRole("cajero");
  $("#brand").innerHTML = `${logo(32)}<span style="font-size:16px;font-weight:800">Pan del Valle</span>`;
  $("#volver").innerHTML = `${icon("left", 18, 2)}Volver a la caja`;
  $("#logout").innerHTML = `${icon("logout", 18)}<span>Cerrar sesión</span>`;
  $("#logout").addEventListener("click", logout);
  applyTheme(getTheme());
  hs.cajeros.set(sesion.usuario, sesion.nombre);
}

const hoy = todayISO();
const hace7 = isoDate(addDays(new Date(), -6));

$("#historial").innerHTML = `
  <div class="page-head">
    <div><h1>${ROL === "admin" ? "Historial de ventas" : "Mis ventas"}</h1>
      <p>${ROL === "admin" ? "Todas las ventas registradas en la caja" : "Las ventas que has cobrado"}</p></div>
    <div style="display:flex;gap:10px">
      <div class="card stat"><span>Ventas</span><b class="num" id="st-ventas">–</b></div>
      <div class="card stat"><span>Total vendido</span><b class="num" id="st-total">–</b></div>
    </div>
  </div>
  ${ROL === "cajero" ? `<div class="alert info">${icon("info", 18, 2)}<span>Solo ves las ventas que cobraste tú. Si necesitas anular una venta, pídeselo al administrador.</span></div>` : ""}
  <div class="card">
    <div class="toolbar">
      <div class="fld"><label for="f-desde" class="lbl">Desde</label><input type="date" id="f-desde" class="sel" value="${ROL === "admin" ? hace7 : hoy}" max="${hoy}"></div>
      <div class="fld"><label for="f-hasta" class="lbl">Hasta</label><input type="date" id="f-hasta" class="sel" value="${hoy}" max="${hoy}"></div>
      ${ROL === "admin" ? `<div class="fld"><label for="f-cajero" class="lbl">Cajero</label><select id="f-cajero" class="sel"><option value="">Todos los cajeros</option></select></div>` : ""}
      <div class="fld"><label for="f-metodo" class="lbl">Método de pago</label><select id="f-metodo" class="sel"><option value="">Todos</option>
        ${METODOS_PAGO.map((m) => `<option value="${m.id}">${m.nombre}</option>`).join("")}</select></div>
      <div class="fld" style="flex:1;min-width:220px"><label for="f-buscar" class="lbl">Buscar</label>
        <label class="srch" style="max-width:none"><span class="muted">${icon("search", 18, 2)}</span><input type="search" id="f-buscar" placeholder="Cliente o N.º de venta"></label></div>
    </div>
    <div class="tbl-wrap">
      <table class="tbl head-bg hover">
        <thead><tr><th>N.º venta</th><th>Fecha y hora</th><th>Cliente</th>${ROL === "admin" ? "<th>Cajero</th>" : ""}<th>Método</th><th class="r">Productos</th><th class="r">Total</th></tr></thead>
        <tbody id="filas"></tbody>
      </table>
    </div>
    <div class="tbl-foot"><span id="conteo"></span><div class="pager" id="pager"></div></div>
  </div>`;

const COLS = ROL === "admin" ? 7 : 6;

function nombreCajero(usuario) {
  return hs.cajeros.get(usuario) || usuario || "—";
}

function filtradas() {
  const q = normalize(hs.buscar.trim()).replace(/^n\.?º?\s*/, "");
  if (!q) return hs.ventas;
  return hs.ventas.filter((v) => String(v.id_venta).startsWith(q.replace(/\./g, "")) || normalize(v.cliente.nombre).includes(q));
}

async function cargar() {
  const desde = $("#f-desde").value;
  const hasta = $("#f-hasta").value;
  if (desde && hasta && desde > hasta) {
    toast("La fecha «Desde» no puede ser posterior a «Hasta».", "err");
    return;
  }
  $("#filas").innerHTML = Array.from({ length: 8 }, () => `<tr>${'<td><div class="sk" style="height:20px"></div></td>'.repeat(COLS)}</tr>`).join("");
  try {
    hs.ventas = await api("sales", "/orders", {
      params: { desde, hasta, cajero: $("#f-cajero")?.value, metodo_pago: $("#f-metodo").value, limit: 2000 },
    });
    hs.limite = hs.ventas.length >= 2000;
    hs.pagina = 1;
    render();
  } catch (error) {
    $("#filas").innerHTML = `<tr><td colspan="${COLS}"><div class="empty">${icon("alert", 36, 1.5)}<b>No se pudo cargar el historial</b><span>${escapeHtml(error.message)}</span></div></td></tr>`;
  }
}

function render() {
  const lista = filtradas();
  const paginas = Math.max(1, Math.ceil(lista.length / POR_PAGINA));
  hs.pagina = Math.min(hs.pagina, paginas);
  $("#st-ventas").textContent = formatNumber(lista.length) + (hs.limite && !hs.buscar ? "+" : "");
  $("#st-total").textContent = formatMoney(lista.reduce((s, v) => s + v.total, 0));

  if (!lista.length) {
    $("#filas").innerHTML = `<tr><td colspan="${COLS}"><div class="empty">${icon("receipt", 36, 1.5)}<b>No hay ventas con estos filtros</b><span>Amplía el rango de fechas o quita algún filtro.</span></div></td></tr>`;
  } else {
    const pagina = lista.slice((hs.pagina - 1) * POR_PAGINA, hs.pagina * POR_PAGINA);
    $("#filas").innerHTML = pagina.map((v) => `
      <tr data-id="${v.id_venta}" tabindex="0">
        <td class="num" style="font-weight:700">${formatNumber(v.id_venta)}</td>
        <td style="white-space:nowrap">${formatDateTime(v.fecha)}</td>
        <td>${v.cliente.id_cliente === 0 ? `<span class="muted">${escapeHtml(v.cliente.nombre)}</span>` : escapeHtml(v.cliente.nombre)}</td>
        ${ROL === "admin" ? `<td style="white-space:nowrap">${escapeHtml(nombreCajero(v.cajero))}</td>` : ""}
        <td>${paymentChip(v.metodo_pago)}</td>
        <td class="r num">${formatNumber(v.lineas.reduce((s, l) => s + l.cantidad, 0))}</td>
        <td class="r num" style="font-weight:700">${formatMoney(v.total)}</td>
      </tr>`).join("");
  }

  const desde = lista.length ? (hs.pagina - 1) * POR_PAGINA + 1 : 0;
  $("#conteo").textContent = hs.limite
    ? `Se muestran las 2.000 ventas más recientes del rango. Acorta las fechas para ver las demás.`
    : `${formatNumber(desde)}–${formatNumber(Math.min(hs.pagina * POR_PAGINA, lista.length))} de ${formatNumber(lista.length)} ventas`;
  $("#pager").innerHTML = pagerHtml(hs.pagina, paginas);
}

["#f-desde", "#f-hasta", "#f-cajero", "#f-metodo"].forEach((s) => $(s)?.addEventListener("change", cargar));
$("#f-buscar").addEventListener("input", debounce((e) => { hs.buscar = e.target.value; hs.pagina = 1; render(); }, 200));
$("#pager").addEventListener("click", (e) => {
  const b = e.target.closest("[data-page]");
  if (!b || b.disabled) return;
  hs.pagina = Number(b.dataset.page);
  render();
});
$("#filas").addEventListener("click", (e) => {
  const tr = e.target.closest("tr[data-id]");
  if (tr) detalle(hs.ventas.find((v) => v.id_venta === Number(tr.dataset.id)));
});
$("#filas").addEventListener("keydown", (e) => {
  if (e.key === "Enter") e.target.closest("tr[data-id]")?.click();
});

// ---------- Detalle ----------

function detalle(v) {
  const unidades = v.lineas.reduce((s, l) => s + l.cantidad, 0);
  const d = openDrawer(`${drawerHead(`Venta N.º ${formatNumber(v.id_venta)}`, formatDateTime(v.fecha))}
    <div class="drawer-body">
      <div class="grid2">
        <div class="kv"><span>Cliente</span><b>${escapeHtml(v.cliente.nombre)}</b></div>
        <div class="kv"><span>Cajero</span><b>${escapeHtml(nombreCajero(v.cajero))}</b></div>
        <div class="kv"><span>Método de pago</span><span>${paymentChip(v.metodo_pago)}</span></div>
        <div class="kv"><span>Unidades</span><b class="num">${formatNumber(unidades)}</b></div>
      </div>
      <table class="tbl compact" style="border:1px solid var(--border);border-radius:10px;border-collapse:separate;border-spacing:0">
        <thead><tr><th>Producto</th><th class="r">Cant.</th><th class="r">Precio</th><th class="r">Subtotal</th></tr></thead>
        <tbody>${v.lineas.map((l) => `<tr><td><b style="font-size:13px">${escapeHtml(l.producto)}</b><div class="pcat" style="margin-top:2px"><span class="dot" style="background:${categoryColor(l.categoria)}"></span>${escapeHtml(l.categoria)}</div></td>
          <td class="r num">${l.cantidad}</td><td class="r num">${formatMoney(l.precio_unitario)}</td><td class="r num" style="font-weight:700">${formatMoney(l.subtotal)}</td></tr>`).join("")}</tbody>
      </table>
      <div style="display:flex;justify-content:space-between;align-items:baseline"><span class="lbl">Total</span><span class="num" style="font-size:28px;font-weight:800">${formatMoney(v.total)}</span></div>
      <div hidden id="recibo">${reciboHtml(v, null, nombreCajero(v.cajero))}</div>
    </div>
    <div class="drawer-foot"><button class="btn" type="button" data-close>Cerrar</button>
      <button class="btn p" type="button" id="reimprimir">${icon("print", 18)}Reimprimir recibo</button></div>`, `Venta ${v.id_venta}`);

  $("#reimprimir", d).addEventListener("click", () => {
    $("#recibo", d).hidden = false;
    window.print();
    $("#recibo", d).hidden = true;
  });
}

// ---------- Inicio ----------

async function iniciar() {
  if (ROL === "admin") {
    try {
      const usuarios = await api("auth", "/users");
      usuarios.forEach((u) => hs.cajeros.set(u.usuario, u.nombre));
      $("#f-cajero").innerHTML += usuarios.filter((u) => u.rol === "cajero")
        .sort((a, b) => a.nombre.localeCompare(b.nombre))
        .map((u) => `<option value="${escapeHtml(u.usuario)}">${escapeHtml(u.nombre)}${u.activo ? "" : " (inactivo)"}</option>`).join("");
    } catch { /* sin nombres se muestra el usuario */ }
  }
  cargar();
}

iniciar();
