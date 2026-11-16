// Catálogo: el administrador crea y edita productos, los activa o desactiva y ve su historial de cambios.
// catalog-service registra cada cambio con el usuario y la fecha.

renderAdminShell("catalogo");

const cat = { productos: [], buscar: "", categoria: "", estado: "activos" };

$("#nuevo").innerHTML = `${icon("plus", 18, 2.2)}Nuevo producto`;
$("#ico-buscar").innerHTML = icon("search", 18, 2);
$("#ico-info").innerHTML = icon("info", 16);
$("#categoria").innerHTML += Object.keys(CATEGORIAS).map((c) => `<option>${escapeHtml(c)}</option>`).join("");

function filtrados() {
  const q = normalize(cat.buscar);
  return cat.productos.filter((p) =>
    (cat.estado === "todos" || p.activo === (cat.estado === "activos"))
    && (!cat.categoria || p.categoria === cat.categoria)
    && (!q || normalize(p.nombre).includes(q) || String(p.id_producto) === q)
  );
}

function render() {
  const lista = filtrados();
  const activos = cat.productos.filter((p) => p.activo).length;
  $("#resumen").textContent = `${activos} productos activos · ${cat.productos.length - activos} inactivos`;
  $("#conteo").textContent = `Mostrando ${lista.length} de ${cat.productos.length} productos`;

  if (!lista.length) {
    $("#filas").innerHTML = `<tr><td colspan="6"><div class="empty">${icon("search", 36, 1.5)}<b>No hay productos con esos filtros</b><span>Cambia la búsqueda, la categoría o el estado.</span></div></td></tr>`;
    return;
  }

  $("#filas").innerHTML = lista.map((p) => `
    <tr style="${p.activo ? "" : "opacity:.62"}">
      <td class="num muted">${String(p.id_producto).padStart(3, "0")}</td>
      <td><div style="display:flex;align-items:center;gap:12px">${productImage(p, "thumb")}<b>${escapeHtml(p.nombre)}</b></div></td>
      <td>${categoryChip(p.categoria)}</td>
      <td class="r num" style="font-weight:700">${formatMoney(p.precio)}</td>
      <td><button class="sw ${p.activo ? "on" : ""}" type="button" role="switch" aria-checked="${p.activo}" data-sw="${p.id_producto}"
        aria-label="${p.activo ? "Desactivar" : "Activar"} ${escapeHtml(p.nombre)}"><span class="tr"><span class="th"></span></span>${p.activo ? "Activo" : "Inactivo"}</button></td>
      <td class="r" style="white-space:nowrap">
        <button class="btn sm" type="button" data-edit="${p.id_producto}">${icon("edit", 16)}Editar</button>
        <button class="btn sm" type="button" data-hist="${p.id_producto}">${icon("history", 16)}Historial</button>
      </td>
    </tr>`).join("");
}

function producto(id) {
  return cat.productos.find((p) => p.id_producto === Number(id));
}

async function cargar() {
  $("#filas").innerHTML = Array.from({ length: 8 }, () => `<tr>${'<td><div class="sk" style="height:20px"></div></td>'.repeat(6)}</tr>`).join("");
  try {
    cat.productos = (await api("catalog", "/products")).sort((a, b) => a.id_producto - b.id_producto);
    render();
  } catch (error) {
    $("#filas").innerHTML = `<tr><td colspan="6"><div class="empty">${icon("alert", 36, 1.5)}<b>No se pudo cargar el catálogo</b><span>${escapeHtml(error.message)}</span></div></td></tr>`;
  }
}

$("#buscar").addEventListener("input", (e) => { cat.buscar = e.target.value; render(); });
$("#categoria").addEventListener("change", (e) => { cat.categoria = e.target.value; render(); });
$("#estado").addEventListener("click", (e) => {
  const b = e.target.closest("[data-e]");
  if (!b) return;
  cat.estado = b.dataset.e;
  $$("#estado button").forEach((x) => x.classList.toggle("on", x === b));
  render();
});

$("#filas").addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (!b) return;
  if (b.dataset.sw) cambiarEstado(producto(b.dataset.sw), b);
  if (b.dataset.edit) formulario(producto(b.dataset.edit));
  if (b.dataset.hist) historial(producto(b.dataset.hist));
});

$("#nuevo").addEventListener("click", () => formulario(null));

async function cambiarEstado(p, boton) {
  boton.disabled = true;
  try {
    await api("catalog", `/products/${p.id_producto}`, { method: "PATCH", body: { activo: !p.activo } });
    p.activo = !p.activo;
    toast(p.activo ? `${p.nombre} vuelve a estar disponible en caja` : `${p.nombre} ya no aparece en caja`);
    render();
  } catch (error) {
    toast(error.message, "err");
    boton.disabled = false;
  }
}

// ---------- Crear / editar ----------

function formulario(p) {
  const nuevo = !p;
  const d = openDrawer(`
    ${drawerHead(nuevo ? "Nuevo producto" : "Editar producto", nuevo ? "Aparecerá en la caja apenas lo guardes" : `Código ${String(p.id_producto).padStart(3, "0")}`)}
    <form class="drawer-body" id="pf" novalidate>
      <div class="fld" data-f="nombre"><label for="pf-nombre">Nombre *</label>
        <input id="pf-nombre" class="fi" maxlength="80" value="${escapeHtml(p?.nombre || "")}" placeholder="Ej.: Pandebono relleno de arequipe" autocomplete="off">
        <span class="ferr" hidden></span></div>
      <div class="fld" data-f="categoria"><label for="pf-categoria">Categoría *</label>
        <select id="pf-categoria" class="fi">${Object.keys(CATEGORIAS).map((c) => `<option ${p?.categoria === c ? "selected" : ""}>${escapeHtml(c)}</option>`).join("")}</select></div>
      <div class="fld" data-f="precio"><label for="pf-precio">Precio por unidad *</label>
        <div class="money" id="pf-money"><span>COP $</span><input id="pf-precio" inputmode="numeric" value="${p ? formatNumber(p.precio) : ""}" placeholder="0" autocomplete="off"></div>
        <span class="help">Sin decimales. Todos los productos se venden por unidad.</span>
        <span class="ferr" hidden></span></div>
      ${nuevo ? "" : `<button class="sw ${p.activo ? "on" : ""}" type="button" role="switch" aria-checked="${p.activo}" id="pf-activo"><span class="tr"><span class="th"></span></span>Disponible en caja</button>`}
      <div class="fld"><span class="lbl">Así se verá en la caja</span>
        <div id="pf-preview" style="width:200px"></div></div>
      <div class="alert" id="pf-error" hidden></div>
    </form>
    <div class="drawer-foot">
      <button class="btn" type="button" data-close>Cancelar</button>
      <button class="btn p" type="submit" form="pf" id="pf-guardar">${nuevo ? "Crear producto" : "Guardar cambios"}</button>
    </div>`, nuevo ? "Nuevo producto" : "Editar producto");

  const precioNum = () => Number($("#pf-precio", d).value.replace(/\D/g, "")) || 0;
  const preview = () => {
    const q = { id_producto: p?.id_producto ?? 0, nombre: $("#pf-nombre", d).value.trim() || "Nombre del producto", categoria: $("#pf-categoria", d).value, precio: precioNum() };
    $("#pf-preview", d).innerHTML = `<div class="pcard" style="pointer-events:none"><div class="pphoto">${productImage(q)}</div>
      <div class="pbody"><span class="pcat"><span class="dot" style="background:${categoryColor(q.categoria)}"></span>${escapeHtml(q.categoria)}</span>
      <span class="pname">${escapeHtml(q.nombre)}</span><div class="prow"><span class="pprice num">${formatMoney(q.precio)}</span><span class="padd">${icon("plus", 16, 2.4)}</span></div></div></div>`;
  };
  preview();
  d.addEventListener("input", preview);
  d.addEventListener("change", preview);
  $("#pf-precio", d).addEventListener("blur", (e) => { e.target.value = precioNum() ? formatNumber(precioNum()) : ""; });
  $("#pf-activo", d)?.addEventListener("click", (e) => {
    const b = e.currentTarget;
    b.classList.toggle("on");
    b.setAttribute("aria-checked", b.classList.contains("on"));
  });

  const marcar = (campo, msg) => {
    const f = $(`[data-f="${campo}"]`, d);
    (f.querySelector(".fi") || f.querySelector(".money")).classList.add("err");
    const e = f.querySelector(".ferr");
    e.innerHTML = `${icon("alert", 14, 2.2)}${escapeHtml(msg)}`;
    e.hidden = false;
  };

  $("#pf", d).addEventListener("submit", async (e) => {
    e.preventDefault();
    $$(".err", d).forEach((x) => x.classList.remove("err"));
    $$(".ferr", d).forEach((x) => (x.hidden = true));
    $("#pf-error", d).hidden = true;

    const body = { nombre: $("#pf-nombre", d).value.trim().replace(/\s+/g, " "), categoria: $("#pf-categoria", d).value, precio: precioNum() };
    let ok = true;
    if (body.nombre.length < 3) { marcar("nombre", "Escribe un nombre de al menos 3 letras."); ok = false; }
    if (body.precio <= 0) { marcar("precio", "Escribe el precio en pesos."); ok = false; }
    else if (body.precio > 1000000) { marcar("precio", "El precio no puede superar $1.000.000."); ok = false; }
    if (!ok) return;

    const btn = $("#pf-guardar", d);
    btn.disabled = true;
    try {
      if (nuevo) {
        const creado = await api("catalog", "/products", { method: "POST", body });
        toast(`${creado.nombre} creado con el código ${String(creado.id_producto).padStart(3, "0")}`);
      } else {
        // Solo se envían los campos que cambiaron, así el historial queda limpio.
        const cambios = {};
        Object.keys(body).forEach((k) => { if (body[k] !== p[k]) cambios[k] = body[k]; });
        const activo = $("#pf-activo", d).classList.contains("on");
        if (activo !== p.activo) cambios.activo = activo;
        if (Object.keys(cambios).length) {
          await api("catalog", `/products/${p.id_producto}`, { method: "PATCH", body: cambios });
          toast(`Cambios guardados en ${body.nombre}`);
        }
      }
      closeDrawer();
      cargar();
    } catch (error) {
      $("#pf-error", d).innerHTML = `${icon("alert", 18, 2)}<span>${escapeHtml(error.message)}</span>`;
      $("#pf-error", d).hidden = false;
      btn.disabled = false;
    }
  });
}

// ---------- Historial de cambios ----------

const ACCIONES = {
  CREAR: { t: "Producto creado", ic: "plus", c: "var(--success)", bg: "var(--success-soft)" },
  EDITAR: { t: "Edición", ic: "edit", c: "var(--primary)", bg: "var(--primary-soft)" },
  DESACTIVAR: { t: "Desactivado", ic: "x", c: "var(--danger)", bg: "var(--danger-soft)" },
  REACTIVAR: { t: "Reactivado", ic: "check", c: "var(--success)", bg: "var(--success-soft)" },
};

const CAMPOS = { nombre: "Nombre", categoria: "Categoría", precio: "Precio", activo: "Estado" };

async function historial(p) {
  const d = openDrawer(`${drawerHead(`Historial · ${p.nombre}`, `Código ${String(p.id_producto).padStart(3, "0")}`)}
    <div class="drawer-body" id="hist"><div class="sk" style="height:60px"></div><div class="sk" style="height:60px"></div></div>`, "Historial de cambios");
  try {
    const cambios = (await api("catalog", "/changes", { params: { product_id: p.id_producto } }))
      .sort((a, b) => b.id_cambio - a.id_cambio);
    $("#hist", d).innerHTML = cambios.length
      ? `<ul class="timeline">${cambios.map((c) => {
        const a = ACCIONES[c.accion] || ACCIONES.EDITAR;
        const val = (v) => (c.campo === "precio" && v ? formatMoney(Number(v)) : escapeHtml(v ?? "—"));
        const detalle = c.accion === "EDITAR"
          ? `${CAMPOS[c.campo] || c.campo}: <span class="muted" style="text-decoration:line-through">${val(c.valor_anterior)}</span> → <b>${val(c.valor_nuevo)}</b>`
          : c.accion === "CREAR" ? escapeHtml(c.valor_nuevo.replace(/\| (\d+)$/, (_, n) => `· ${formatMoney(Number(n))}`).replace(" | ", " · ")) : "";
        return `<li><div class="rail"><span class="ico" style="background:${a.bg};color:${a.c}">${icon(a.ic, 16, 2.2)}</span><span class="line"></span></div>
          <div class="txt"><b>${a.t}</b>${detalle ? `<span style="font-size:13px;color:var(--text)">${detalle}</span>` : ""}
          <span>${formatDateTime(c.fecha)} · por ${escapeHtml(c.usuario)}</span></div></li>`;
      }).join("")}</ul>`
      : `<div class="empty">${icon("history", 36, 1.5)}<b>Sin cambios registrados</b><span>Este producto viene del catálogo inicial y nadie lo ha modificado.</span></div>`;
  } catch (error) {
    $("#hist", d).innerHTML = `<div class="alert">${icon("alert", 18, 2)}<span>${escapeHtml(error.message)}</span></div>`;
  }
}

cargar();
