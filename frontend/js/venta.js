// Caja: el cajero arma la venta tocando productos, elige cliente y método de pago, y cobra.
// La venta completa se envía a sales-service en un solo POST /orders (todo o nada).

const session = requireRole("cajero");

const CONSUMIDOR_FINAL = { id_cliente: 0, nombre: "Consumidor final", sub: "Cliente por defecto" };

const state = {
  productos: [],
  categoria: "Todos",
  buscar: "",
  carrito: new Map(), // id_producto → cantidad
  cliente: CONSUMIDOR_FINAL,
  pago: "efectivo",
  recibido: 0,
  enviando: false,
};

// ---------- Barra superior ----------

$("#brand").innerHTML = `${logo(32)}<span style="font-size:16px;font-weight:800;letter-spacing:-.01em">Pan del Valle</span>`;
$("#cajero-ini").textContent = initials(session.nombre);
$("#cajero-nombre").textContent = session.nombre;
$("#ico-clock").innerHTML = icon("clock", 18);
$("#ico-search").innerHTML = icon("search", 22, 2);
$("#ico-search2").innerHTML = icon("search", 18, 2);
$("#logout").innerHTML = `${icon("logout", 18)}<span class="hide-md">Cerrar sesión</span>`;
$("#logout").addEventListener("click", logout);
$("#nuevo-cliente").innerHTML = `${icon("plus", 18, 2)}Nuevo cliente`;
applyTheme(getTheme());

function tick() {
  const now = new Date();
  $("#reloj").textContent = formatTime(now);
  $("#fecha").textContent = `${DIAS_CORTOS[now.getDay()]} ${formatDate(now)}`;
  const manana = now.getHours() < 14;
  $("#turno").textContent = manana ? "Turno mañana" : "Turno tarde";
  $("#turno-horas").textContent = manana ? "6:00 a. m. – 2:00 p. m." : "2:00 p. m. – 9:00 p. m.";
}
tick();
setInterval(tick, 15000);

async function loadVentasHoy() {
  let n = "–";
  try {
    const hoy = todayISO();
    n = (await api("sales", "/orders", { params: { desde: hoy, hasta: hoy, limit: 2000 } })).length;
  } catch { /* el contador no es crítico */ }
  $("#mis-ventas").innerHTML = `${icon("receipt", 18)}<span class="hide-md">Mis ventas de hoy</span><span class="pill num">${n}</span>`;
}

// ---------- Productos ----------

function productosFiltrados() {
  const q = normalize(state.buscar);
  return state.productos.filter((p) =>
    (state.categoria === "Todos" || p.categoria === state.categoria) && (!q || normalize(p.nombre).includes(q))
  );
}

function renderChips() {
  const cats = ["Todos", ...Object.keys(CATEGORIAS).filter((c) => state.productos.some((p) => p.categoria === c))];
  $("#chips").innerHTML = cats.map((c) => `
    <button class="cchip ${state.categoria === c ? "on" : ""}" type="button" role="tab" aria-selected="${state.categoria === c}" data-cat="${escapeHtml(c)}">
      ${c === "Todos" ? "" : `<span class="dot" style="background:${categoryColor(c)}"></span>`}${escapeHtml(c)}
    </button>`).join("");
}

function renderProductos() {
  const lista = productosFiltrados();
  if (!lista.length) {
    $("#products").innerHTML = `<div class="empty" style="height:100%;justify-content:center">${icon("search", 40, 1.5)}
      <b>No encontramos «${escapeHtml(state.buscar)}»</b><span>Revisa la ortografía o busca en otra categoría.</span></div>`;
    return;
  }
  $("#products").innerHTML = `<div class="pgrid">${lista.map((p) => {
    const qty = state.carrito.get(p.id_producto) || 0;
    return `<button class="pcard ${qty ? "in" : ""}" type="button" data-id="${p.id_producto}"
        aria-label="Agregar ${escapeHtml(p.nombre)}, ${formatMoney(p.precio)}${qty ? `, ${qty} en la venta` : ""}">
      <div class="pphoto">${productImage(p)}</div>
      ${qty ? `<span class="badge num" aria-hidden="true">${qty}</span>` : ""}
      <div class="pbody">
        <span class="pcat"><span class="dot" style="background:${categoryColor(p.categoria)}"></span>${escapeHtml(p.categoria)}</span>
        <span class="pname">${escapeHtml(p.nombre)}</span>
        <div class="prow"><span class="pprice num">${formatMoney(p.precio)}</span><span class="padd">${icon("plus", 16, 2.4)}</span></div>
      </div>
    </button>`;
  }).join("")}</div>`;
}

function skeletonProductos() {
  $("#products").innerHTML = `<div class="pgrid">${Array.from({ length: 12 }, () => `
    <div class="pcard" style="pointer-events:none"><div class="pphoto sk" style="border-radius:0"></div>
    <div class="pbody"><div class="sk" style="height:10px;width:60%"></div><div class="sk" style="height:16px;width:85%"></div><div class="sk" style="height:20px;width:45%;margin-top:8px"></div></div></div>`).join("")}</div>`;
}

$("#chips").addEventListener("click", (e) => {
  const b = e.target.closest("[data-cat]");
  if (!b) return;
  state.categoria = b.dataset.cat;
  renderChips();
  renderProductos();
});

$("#products").addEventListener("click", (e) => {
  const card = e.target.closest(".pcard[data-id]");
  if (card) agregar(Number(card.dataset.id), 1);
});

$("#buscar").addEventListener("input", (e) => {
  state.buscar = e.target.value;
  renderProductos();
});

$("#buscar").addEventListener("keydown", (e) => {
  // Enter agrega el producto si la búsqueda deja uno solo.
  if (e.key === "Enter") {
    const lista = productosFiltrados();
    if (lista.length === 1) {
      agregar(lista[0].id_producto, 1);
      e.target.value = "";
      state.buscar = "";
      renderProductos();
    }
  }
});

// ---------- Carrito ----------

function producto(id) {
  return state.productos.find((p) => p.id_producto === id);
}

function agregar(id, delta) {
  const nueva = (state.carrito.get(id) || 0) + delta;
  if (nueva <= 0) state.carrito.delete(id);
  else state.carrito.set(id, Math.min(nueva, 500));
  renderCarrito();
  renderProductos();
}

function totales() {
  let total = 0;
  let unidades = 0;
  state.carrito.forEach((q, id) => {
    total += q * producto(id).precio;
    unidades += q;
  });
  return { total, unidades };
}

function renderCarrito() {
  const { total, unidades } = totales();
  const lineas = [...state.carrito.entries()];

  $("#cancelar").hidden = !lineas.length;
  $("#lines").innerHTML = lineas.length
    ? lineas.map(([id, q]) => {
      const p = producto(id);
      return `<div class="line">
        ${productImage(p, "thumb")}
        <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:2px">
          <span style="font-size:14px;font-weight:700;line-height:1.25">${escapeHtml(p.nombre)}</span>
          <span class="num muted" style="font-size:12px">${formatMoney(p.precio)} c/u</span>
        </div>
        <div class="step">
          <button type="button" data-dec="${id}" aria-label="Quitar una unidad de ${escapeHtml(p.nombre)}">${icon("minus", 18, 2.2)}</button>
          <span class="num" aria-live="polite">${q}</span>
          <button type="button" data-inc="${id}" aria-label="Sumar una unidad de ${escapeHtml(p.nombre)}">${icon("plus", 18, 2.2)}</button>
        </div>
        <span class="num" style="width:76px;text-align:right;font-size:15px;font-weight:800">${formatMoney(q * p.precio)}</span>
        <button class="ibtn del" type="button" data-del="${id}" aria-label="Eliminar ${escapeHtml(p.nombre)} de la venta">${icon("trash", 18)}</button>
      </div>`;
    }).join("")
    : `<div class="empty" style="height:100%;min-height:180px;justify-content:center">
        <svg viewBox="0 0 120 80" width="120" height="80" aria-hidden="true">
          <ellipse cx="60" cy="68" rx="48" ry="6" fill="var(--surface2)"/>
          <path d="M18 44h84l-8 22H26z" fill="none" stroke="var(--border-strong)" stroke-width="2.5" stroke-linejoin="round"/>
          <path d="M30 52h60M36 59h48" stroke="var(--border)" stroke-width="2" stroke-linecap="round"/>
          <circle cx="46" cy="34" r="12" fill="var(--accent-soft)" stroke="var(--accent)" stroke-width="2.5"/>
          <circle cx="70" cy="36" r="9" fill="var(--accent-soft)" stroke="var(--accent)" stroke-width="2.5"/>
          <path d="M42 30a6 6 0 0 1 6-3" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" fill="none"/>
        </svg>
        <b style="font-size:17px">Toca un producto para empezar</b>
        <span style="font-size:13px;display:flex;align-items:center;gap:6px">o presiona <span class="kbd">/</span> para buscar</span>
      </div>`;

  $("#total").textContent = formatMoney(total);
  $("#unidades").textContent = unidades === 1 ? "1 unidad" : `${formatNumber(unidades)} unidades`;
  $("#cobrar-txt").textContent = `Cobrar ${formatMoney(total)}`;
  renderCambio();
}

$("#lines").addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (!b) return;
  if (b.dataset.inc) agregar(Number(b.dataset.inc), 1);
  if (b.dataset.dec) agregar(Number(b.dataset.dec), -1);
  if (b.dataset.del) agregar(Number(b.dataset.del), -state.carrito.get(Number(b.dataset.del)));
});

function limpiarVenta() {
  state.carrito.clear();
  state.cliente = CONSUMIDOR_FINAL;
  state.pago = "efectivo";
  state.recibido = 0;
  $("#recibido").value = "";
  renderCliente();
  renderPagos();
  renderCarrito();
  renderProductos();
}

$("#cancelar").addEventListener("click", limpiarVenta);

// ---------- Método de pago y efectivo ----------

function renderPagos() {
  $("#pagos").innerHTML = METODOS_PAGO.map((m) => `
    <button class="pay ${state.pago === m.id ? "on" : ""}" type="button" role="radio" aria-checked="${state.pago === m.id}"
      data-pago="${m.id}" style="--pm:var(--pm-${m.id})">
      <span class="pico">${icon(m.icon, 16, 2)}</span><span>${m.nombre}</span>
    </button>`).join("");
  $("#efectivo").hidden = state.pago !== "efectivo";
  renderCambio();
}

$("#pagos").addEventListener("click", (e) => {
  const b = e.target.closest("[data-pago]");
  if (!b) return;
  state.pago = b.dataset.pago;
  renderPagos();
});

$("#rapidos").innerHTML = [10000, 20000, 50000, 100000]
  .map((v) => `<button class="qbtn" type="button" data-v="${v}">${formatMoney(v)}</button>`).join("");

$("#rapidos").addEventListener("click", (e) => {
  const b = e.target.closest("[data-v]");
  if (!b) return;
  state.recibido = Number(b.dataset.v);
  $("#recibido").value = formatMoney(state.recibido);
  renderCambio();
});

$("#recibido").addEventListener("input", (e) => {
  state.recibido = Number(e.target.value.replace(/\D/g, "")) || 0;
  renderCambio();
});

$("#recibido").addEventListener("blur", (e) => {
  e.target.value = state.recibido ? formatMoney(state.recibido) : "";
});

$("#recibido").addEventListener("focus", (e) => {
  e.target.value = state.recibido ? String(state.recibido) : "";
});

function renderCambio() {
  const { total } = totales();
  const efectivo = state.pago === "efectivo";
  // Si no escriben cuánto recibieron, se asume que pagan exacto.
  const diff = (state.recibido || total) - total;
  const box = $("#cambio-box");
  box.classList.toggle("short", diff < 0);
  $("#cambio-lbl").textContent = diff < 0 ? "Faltan" : "Cambio";
  $("#cambio").textContent = formatMoney(Math.abs(diff));
  $("#cobrar").disabled = state.enviando || !state.carrito.size || (efectivo && diff < 0);
}

// ---------- Cliente ----------

function renderCliente() {
  const c = state.cliente;
  $("#cliente-btn").innerHTML = `
    <span class="av">${c.id_cliente === 0 ? "CF" : escapeHtml(initials(c.nombre))}</span>
    <span style="flex:1;min-width:0;display:flex;flex-direction:column;line-height:1.2">
      <span style="font-size:14px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escapeHtml(c.nombre)}</span>
      <span class="num muted" style="font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escapeHtml(c.sub)}</span>
    </span>
    <span class="muted">${icon("chevron", 18, 2)}</span>`;
}

function clienteSub(c) {
  const partes = [];
  if (c.documento) partes.push(`${c.tipo_documento || "CC"} ${formatDocument(c.documento)}`);
  if (c.telefono) partes.push(formatPhone(c.telefono));
  return partes.join(" · ") || c.barrio || "Sin documento";
}

function abrirClientes(abrir) {
  const drop = $("#cliente-drop");
  drop.hidden = !abrir;
  $("#cliente-btn").setAttribute("aria-expanded", String(abrir));
  if (abrir) {
    $("#cliente-buscar").value = "";
    buscarClientes("");
    $("#cliente-buscar").focus();
  }
}

let ultimaBusqueda = 0;

async function buscarClientes(texto) {
  const opts = $("#cliente-opts");
  const id = ++ultimaBusqueda;
  let clientes = [];

  if (texto.trim().length >= 2) {
    opts.innerHTML = `<div class="sk" style="height:48px;margin:4px 0"></div><div class="sk" style="height:48px;margin:4px 0"></div>`;
    try {
      clientes = await api("sales", "/customers", { params: { search: texto.trim(), limit: 8 } });
    } catch (error) {
      opts.innerHTML = `<div class="empty" style="padding:16px">${escapeHtml(error.message)}</div>`;
      return;
    }
    if (id !== ultimaBusqueda) return;
  }

  const lista = [CONSUMIDOR_FINAL, ...clientes.map((c) => ({ ...c, sub: clienteSub(c) }))];
  opts.innerHTML = lista.map((c, i) => `
    <button class="opt" type="button" role="option" data-i="${i}">
      <span class="av">${c.id_cliente === 0 ? "CF" : escapeHtml(initials(c.nombre))}</span>
      <span style="display:flex;flex-direction:column;line-height:1.25;min-width:0">
        <span style="font-size:14px;font-weight:700">${escapeHtml(c.nombre)}</span>
        <span class="num muted" style="font-size:12px">${escapeHtml(c.sub)}</span>
      </span>
    </button>`).join("") + (texto.trim().length < 2
    ? `<p class="muted" style="font-size:13px;margin:8px 10px">Escribe al menos 2 letras o números para buscar entre los clientes registrados.</p>`
    : clientes.length ? "" : `<p class="muted" style="font-size:13px;margin:8px 10px">Ningún cliente coincide con «${escapeHtml(texto)}».</p>`);
  opts._lista = lista;
}

$("#cliente-btn").addEventListener("click", () => abrirClientes($("#cliente-drop").hidden));
$("#cliente-buscar").addEventListener("input", debounce((e) => buscarClientes(e.target.value), 220));
$("#cliente-buscar").addEventListener("keydown", (e) => {
  // Enter elige el primer resultado de la búsqueda (o Consumidor final si no hay resultados).
  if (e.key === "Enter") ($("#cliente-opts .opt:nth-child(2)") || $("#cliente-opts .opt"))?.click();
});
$("#cliente-opts").addEventListener("click", (e) => {
  const b = e.target.closest("[data-i]");
  if (!b) return;
  state.cliente = $("#cliente-opts")._lista[Number(b.dataset.i)];
  renderCliente();
  abrirClientes(false);
});
document.addEventListener("click", (e) => {
  if (!$("#cliente-drop").hidden && !e.target.closest("#cliente-drop, #cliente-btn")) abrirClientes(false);
});

// Modal "Nuevo cliente": se crea y queda asignado a la venta.
function modalNuevoCliente() {
  abrirClientes(false);
  const ov = document.createElement("div");
  ov.className = "overlay";
  ov.innerHTML = `
    <form class="modal" style="width:580px;max-width:100%;padding:24px;display:flex;flex-direction:column;gap:16px" role="dialog" aria-modal="true" aria-label="Nuevo cliente" novalidate>
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div><span style="font-size:19px;font-weight:800;display:block">Nuevo cliente</span>
        <span class="muted" style="font-size:13px">Quedará asignado a esta venta.</span></div>
        <button class="ibtn" type="button" data-cerrar aria-label="Cerrar">${icon("x", 20, 2)}</button>
      </div>
      ${customerFormHtml({}, { compacto: true })}
      <div style="display:flex;gap:10px;justify-content:flex-end">
        <button class="btn" type="button" data-cerrar>Cancelar</button>
        <button class="btn p" type="submit">Guardar cliente</button>
      </div>
    </form>`;
  document.body.appendChild(ov);
  const form = ov.querySelector("form");
  const cerrar = () => ov.remove();
  ov.addEventListener("click", (e) => { if (e.target === ov || e.target.closest("[data-cerrar]")) cerrar(); });
  ov.addEventListener("keydown", (e) => { if (e.key === "Escape") { e.stopPropagation(); cerrar(); } });
  form.querySelector("input").focus();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const datos = readCustomerForm(form);
    if (!datos) return;
    const btn = form.querySelector('[type="submit"]');
    btn.disabled = true;
    try {
      const c = await api("sales", "/customers", { method: "POST", body: datos });
      state.cliente = { ...c, sub: clienteSub(c) };
      renderCliente();
      cerrar();
      toast(`Cliente ${c.nombre} registrado`);
    } catch (error) {
      showCustomerApiError(form, error);
      btn.disabled = false;
    }
  });
}

$("#nuevo-cliente").addEventListener("click", modalNuevoCliente);

// ---------- Cobrar ----------

async function cobrar() {
  if ($("#cobrar").disabled) return;
  state.enviando = true;
  renderCambio();
  const { total } = totales();
  const recibido = state.recibido || total;

  try {
    const venta = await api("sales", "/orders", {
      method: "POST",
      body: {
        id_cliente: state.cliente.id_cliente,
        metodo_pago: state.pago,
        lineas: [...state.carrito.entries()].map(([id_producto, cantidad]) => ({ id_producto, cantidad })),
      },
    });
    mostrarRecibo(venta, state.pago === "efectivo" ? recibido : null);
    loadVentasHoy();
  } catch (error) {
    toast(error.message, "err");
    // Si un producto ya no está disponible, se recarga el catálogo.
    if (error.status === 400 || error.status === 404) cargarProductos(false);
  } finally {
    state.enviando = false;
    renderCambio();
  }
}

function mostrarRecibo(venta, recibido) {
  const ov = document.createElement("div");
  ov.className = "overlay";
  ov.innerHTML = `
    <div class="modal" style="width:440px;max-width:100%;padding:24px;display:flex;flex-direction:column;gap:18px" role="dialog" aria-modal="true" aria-label="Venta registrada">
      <div style="display:flex;align-items:center;gap:12px">
        <div style="width:44px;height:44px;border-radius:50%;background:var(--success-soft);color:var(--success);display:flex;align-items:center;justify-content:center">${icon("check", 24, 2.4)}</div>
        <div><span style="font-size:19px;font-weight:800;display:block">Venta registrada</span>
        <span class="muted" style="font-size:13px">Pago recibido por ${escapeHtml(paymentName(venta.metodo_pago))}</span></div>
      </div>
      ${reciboHtml(venta, recibido, session.nombre)}
      <div style="display:flex;gap:10px">
        <button class="btn lg" type="button" style="flex:1" data-print>${icon("print", 18)}Imprimir</button>
        <button class="btn p lg" type="button" style="flex:1" data-nueva>Nueva venta</button>
      </div>
    </div>`;
  document.body.appendChild(ov);
  const nueva = () => { ov.remove(); limpiarVenta(); $("#buscar").focus(); };
  ov.querySelector("[data-nueva]").addEventListener("click", nueva);
  ov.querySelector("[data-print]").addEventListener("click", () => window.print());
  ov.addEventListener("keydown", (e) => { if (e.key === "Escape" || e.key === "Enter") { e.preventDefault(); nueva(); } });
  ov.querySelector("[data-nueva]").focus();
}

$("#cobrar").addEventListener("click", cobrar);

// ---------- Atajos de teclado ----------

document.addEventListener("keydown", (e) => {
  if ($(".overlay")) return;
  const escribiendo = ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName);
  if (e.key === "/" && !escribiendo) {
    e.preventDefault();
    $("#buscar").focus();
  } else if (e.key === "F2") {
    e.preventDefault();
    cobrar();
  } else if (e.key === "Escape") {
    if (!$("#cliente-drop").hidden) abrirClientes(false);
    else if (document.activeElement === $("#buscar") && state.buscar) {
      $("#buscar").value = "";
      state.buscar = "";
      renderProductos();
    } else if (state.carrito.size) limpiarVenta();
  }
});

// ---------- Inicio ----------

async function cargarProductos(conEsqueleto = true) {
  if (conEsqueleto) skeletonProductos();
  try {
    // Orden de la caja: por categoría (como en la vitrina) y dentro de cada una por código.
    const orden = Object.keys(CATEGORIAS);
    state.productos = (await api("catalog", "/products", { params: { activo: true } }))
      .filter((p) => p.activo)
      .sort((a, b) => orden.indexOf(a.categoria) - orden.indexOf(b.categoria) || a.id_producto - b.id_producto);
    // Si algo del carrito se desactivó, se quita.
    [...state.carrito.keys()].forEach((id) => { if (!producto(id)) state.carrito.delete(id); });
    renderChips();
    renderProductos();
    renderCarrito();
  } catch (error) {
    $("#products").innerHTML = `<div class="empty">${icon("alert", 36, 1.5)}<b>No se pudo cargar el catálogo</b><span>${escapeHtml(error.message)}</span>
      <button class="btn" type="button" id="reintentar">Reintentar</button></div>`;
    $("#reintentar").addEventListener("click", () => cargarProductos());
  }
}

renderCliente();
renderPagos();
renderCarrito();
cargarProductos();
loadVentasHoy();
