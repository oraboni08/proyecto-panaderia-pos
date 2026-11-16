// Clientes: listado paginado con búsqueda, ficha con métricas de compra y edición de datos.

renderAdminShell("clientes");

const POR_PAGINA = 25;
const cl = { buscar: "", pagina: 1, total: 0, clientes: [] };

$("#nuevo").innerHTML = `${icon("plus", 18, 2.2)}Nuevo cliente`;
$("#ico-buscar").innerHTML = icon("search", 18, 2);

async function cargar() {
  $("#filas").innerHTML = Array.from({ length: 10 }, () => `<tr>${'<td><div class="sk" style="height:20px"></div></td>'.repeat(6)}</tr>`).join("");
  try {
    const data = await api("sales", "/customers/page", {
      params: { search: cl.buscar.trim(), limit: POR_PAGINA, offset: (cl.pagina - 1) * POR_PAGINA },
    });
    cl.total = data.total;
    cl.clientes = data.clientes;
    render();
  } catch (error) {
    $("#filas").innerHTML = `<tr><td colspan="6"><div class="empty">${icon("alert", 36, 1.5)}<b>No se pudieron cargar los clientes</b><span>${escapeHtml(error.message)}</span></div></td></tr>`;
  }
}

function render() {
  const paginas = Math.max(1, Math.ceil(cl.total / POR_PAGINA));
  if (!cl.buscar) $("#resumen").textContent = `${formatNumber(cl.total)} clientes registrados en la caja`;

  if (!cl.clientes.length) {
    $("#filas").innerHTML = `<tr><td colspan="6"><div class="empty">${icon("users", 36, 1.5)}<b>Ningún cliente coincide con «${escapeHtml(cl.buscar)}»</b><span>Prueba con el número de cédula o el celular.</span></div></td></tr>`;
  } else {
    $("#filas").innerHTML = cl.clientes.map((c) => `
      <tr data-id="${c.id_cliente}" tabindex="0">
        <td><div style="display:flex;align-items:center;gap:10px"><span class="av">${c.id_cliente === 0 ? "CF" : escapeHtml(initials(c.nombre))}</span><b>${escapeHtml(c.nombre)}</b></div></td>
        <td class="num" style="white-space:nowrap">${c.documento ? `<span class="muted">${escapeHtml(c.tipo_documento || "")}</span> ${formatDocument(c.documento)}` : '<span class="muted">—</span>'}</td>
        <td class="num" style="white-space:nowrap">${formatPhone(c.telefono) || '<span class="muted">—</span>'}</td>
        <td style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(c.correo || "") || '<span class="muted">—</span>'}</td>
        <td>${escapeHtml([c.barrio, c.ciudad].filter(Boolean).join(", ")) || '<span class="muted">—</span>'}</td>
        <td class="muted">${c.creado_en ? formatDate(c.creado_en) : "—"}</td>
      </tr>`).join("");
  }

  const desde = cl.total ? (cl.pagina - 1) * POR_PAGINA + 1 : 0;
  $("#conteo").textContent = `${formatNumber(desde)}–${formatNumber(Math.min(cl.pagina * POR_PAGINA, cl.total))} de ${formatNumber(cl.total)} clientes`;
  $("#pager").innerHTML = pagerHtml(cl.pagina, paginas);
}

$("#buscar").addEventListener("input", debounce((e) => {
  cl.buscar = e.target.value;
  cl.pagina = 1;
  cargar();
}, 280));

$("#pager").addEventListener("click", (e) => {
  const b = e.target.closest("[data-page]");
  if (!b || b.disabled) return;
  cl.pagina = Number(b.dataset.page);
  cargar();
  $(".main").scrollIntoView({ block: "start" });
});

$("#filas").addEventListener("click", (e) => {
  const tr = e.target.closest("tr[data-id]");
  if (tr) ficha(cl.clientes.find((c) => c.id_cliente === Number(tr.dataset.id)));
});
$("#filas").addEventListener("keydown", (e) => {
  if (e.key === "Enter") e.target.closest("tr[data-id]")?.click();
});

// ---------- Nuevo cliente ----------

$("#nuevo").addEventListener("click", () => {
  const d = openDrawer(`${drawerHead("Nuevo cliente", "Podrá elegirse en la caja de inmediato")}
    <form class="drawer-body" id="cf" novalidate>${customerFormHtml({})}</form>
    <div class="drawer-foot"><button class="btn" type="button" data-close>Cancelar</button>
      <button class="btn p" type="submit" form="cf">Guardar cliente</button></div>`, "Nuevo cliente");
  $("#cf", d).addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const datos = readCustomerForm(form);
    if (!datos) return;
    const btn = $('[type="submit"]', d);
    btn.disabled = true;
    try {
      const c = await api("sales", "/customers", { method: "POST", body: datos });
      toast(`Cliente ${c.nombre} registrado`);
      closeDrawer();
      cargar();
    } catch (error) {
      showCustomerApiError(form, error);
      btn.disabled = false;
    }
  });
});

// ---------- Ficha del cliente ----------

function ficha(c) {
  const editable = c.id_cliente !== 0;
  const d = openDrawer(`
    <div class="drawer-head">
      <div style="display:flex;gap:14px;align-items:center">
        <span class="av xl">${c.id_cliente === 0 ? "CF" : escapeHtml(initials(c.nombre))}</span>
        <div><span class="t">${escapeHtml(c.nombre)}</span>
          <span class="s num">${c.documento ? `${escapeHtml(c.tipo_documento || "CC")} ${formatDocument(c.documento)} · ` : ""}Cliente desde ${c.creado_en ? formatDate(c.creado_en) : "el inicio"}</span></div>
      </div>
      <button class="ibtn" type="button" data-close aria-label="Cerrar panel">${icon("x", 20, 2)}</button>
    </div>
    <div style="padding:16px 20px 4px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px" id="metricas">
      ${'<div class="sk" style="height:62px"></div>'.repeat(4)}
    </div>
    <div class="tabs" role="tablist">
      <button type="button" class="on" data-tab="datos" role="tab">Datos</button>
      <button type="button" data-tab="compras" role="tab">Historial de compras</button>
    </div>
    <form class="drawer-body" id="tab-datos" novalidate>
      ${editable ? customerFormHtml(c) : `<div class="alert info">${icon("info", 18, 2)}<span>Consumidor final agrupa las ventas sin cliente registrado. No tiene datos para editar.</span></div>`}
    </form>
    <div class="drawer-body" id="tab-compras" hidden></div>
    ${editable ? `<div class="drawer-foot" id="foot-datos"><button class="btn" type="button" data-close>Cancelar</button><button class="btn p" type="submit" form="tab-datos">Guardar cambios</button></div>` : ""}`,
  `Cliente ${c.nombre}`);

  $(".tabs", d).addEventListener("click", (e) => {
    const b = e.target.closest("[data-tab]");
    if (!b) return;
    $$(".tabs button", d).forEach((x) => x.classList.toggle("on", x === b));
    $("#tab-datos", d).hidden = b.dataset.tab !== "datos";
    $("#tab-compras", d).hidden = b.dataset.tab !== "compras";
    if ($("#foot-datos", d)) $("#foot-datos", d).hidden = b.dataset.tab !== "datos";
  });

  if (editable) {
    $("#tab-datos", d).addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = e.currentTarget;
      const datos = readCustomerForm(form);
      if (!datos) return;
      // Solo se envía lo que cambió.
      const cambios = {};
      Object.keys(datos).forEach((k) => {
        if (datos[k] !== undefined && (datos[k] ?? null) !== (c[k] ?? null)) cambios[k] = datos[k];
      });
      if (!Object.keys(cambios).length) { closeDrawer(); return; }
      const btn = $('[form="tab-datos"]', d);
      btn.disabled = true;
      try {
        await api("sales", `/customers/${c.id_cliente}`, { method: "PATCH", body: cambios });
        toast("Datos del cliente actualizados");
        closeDrawer();
        cargar();
      } catch (error) {
        showCustomerApiError(form, error);
        btn.disabled = false;
      }
    });
  }

  comprasCliente(c, d);
}

async function comprasCliente(c, d) {
  try {
    const ventas = await api("sales", "/orders", { params: { id_cliente: c.id_cliente, limit: 2000 } });
    const gasto = ventas.reduce((s, v) => s + v.total, 0);
    const porProducto = new Map();
    ventas.forEach((v) => v.lineas.forEach((l) => porProducto.set(l.producto, (porProducto.get(l.producto) || 0) + l.cantidad)));
    const favorito = [...porProducto.entries()].sort((a, b) => b[1] - a[1])[0];
    const metric = (t, v) => `<div class="metric"><span>${t}</span><b class="num">${v}</b></div>`;

    $("#metricas", d).innerHTML = [
      metric("Compras", formatNumber(ventas.length) + (ventas.length >= 2000 ? "+" : "")),
      metric("Gasto total", formatMoney(gasto)),
      metric("Ticket promedio", ventas.length ? formatMoney(gasto / ventas.length) : "—"),
      metric("Última compra", ventas.length ? formatDate(ventas[0].fecha) : "—"),
    ].join("") + (favorito ? `<div class="metric" style="grid-column:span 2"><span>Producto favorito</span><b style="font-size:15px">${escapeHtml(favorito[0])} <span class="muted num" style="font-weight:600">· ${formatNumber(favorito[1])} unidades</span></b></div>` : "");

    $("#tab-compras", d).innerHTML = ventas.length
      ? `<table class="tbl compact"><thead><tr><th>N.º</th><th>Fecha</th><th>Pago</th><th class="r">Total</th></tr></thead><tbody>
          ${ventas.slice(0, 100).map((v) => `<tr><td class="num">${formatNumber(v.id_venta)}</td><td>${formatDateTime(v.fecha)}</td><td>${paymentChip(v.metodo_pago)}</td><td class="r num" style="font-weight:700">${formatMoney(v.total)}</td></tr>`).join("")}
        </tbody></table>${ventas.length > 100 ? `<p class="muted" style="font-size:13px;margin:0">Se muestran las 100 compras más recientes. El resto está en Historial de ventas.</p>` : ""}`
      : `<div class="empty">${icon("receipt", 36, 1.5)}<b>Todavía no ha comprado</b><span>Sus compras aparecerán aquí.</span></div>`;
  } catch (error) {
    $("#metricas", d).innerHTML = `<div class="alert" style="grid-column:span 2">${icon("alert", 18, 2)}<span>${escapeHtml(error.message)}</span></div>`;
  }
}

cargar();
