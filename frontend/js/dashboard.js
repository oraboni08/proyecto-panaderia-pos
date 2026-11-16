// Dashboard del administrador: indicadores y gráficas del periodo elegido.
// Las gráficas son SVG dibujados aquí mismo (sin librerías) y toman los colores del tema.

renderAdminShell("dashboard");

const RANGOS = [
  { id: "hoy", label: "Hoy" },
  { id: "7d", label: "7 días" },
  { id: "mes", label: "Este mes" },
  { id: "anio", label: "Este año" },
  { id: "custom", label: "Personalizado" },
];

const st = { rango: "7d", desde: null, hasta: null, ordenTop: "ingresos", datos: null };

// ---------- Periodos ----------

function periodo(rango) {
  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  if (rango === "hoy") return [hoy, hoy];
  if (rango === "7d") return [addDays(hoy, -6), hoy];
  if (rango === "mes") return [new Date(hoy.getFullYear(), hoy.getMonth(), 1), hoy];
  if (rango === "anio") return [new Date(hoy.getFullYear(), 0, 1), hoy];
  return [new Date(`${st.desde}T00:00`), new Date(`${st.hasta}T00:00`)];
}

// El periodo anterior tiene la misma duración y termina el día antes de que empiece el actual.
function periodoAnterior([d, h]) {
  const dias = Math.round((h - d) / 864e5) + 1;
  return [addDays(d, -dias), addDays(d, -1)];
}

function textoPeriodo([d, h]) {
  return isoDate(d) === isoDate(h) ? formatDate(d) : `${formatDate(d)} – ${formatDate(h)}`;
}

$("#rangos").innerHTML = RANGOS.map((r) => `<button type="button" role="tab" data-r="${r.id}">${r.label}</button>`).join("");
$("#exportar").innerHTML = `${icon("download", 18)}Exportar`;

function renderRangos() {
  $$("#rangos button").forEach((b) => {
    b.classList.toggle("on", b.dataset.r === st.rango);
    b.setAttribute("aria-selected", b.dataset.r === st.rango);
  });
  $("#personalizado").hidden = st.rango !== "custom";
}

$("#rangos").addEventListener("click", (e) => {
  const b = e.target.closest("[data-r]");
  if (!b) return;
  st.rango = b.dataset.r;
  renderRangos();
  if (st.rango === "custom") {
    if (!st.desde) {
      st.hasta = todayISO();
      st.desde = isoDate(addDays(new Date(), -29));
    }
    $("#desde").value = st.desde;
    $("#hasta").value = st.hasta;
    return;
  }
  cargar();
});

$("#aplicar").addEventListener("click", () => {
  const d = $("#desde").value;
  const h = $("#hasta").value;
  if (!d || !h || d > h) {
    toast("Revisa las fechas: «Desde» debe ser anterior o igual a «Hasta».", "err");
    return;
  }
  st.desde = d;
  st.hasta = h;
  cargar();
});

$("#orden-top").addEventListener("click", async (e) => {
  const b = e.target.closest("[data-o]");
  if (!b || b.dataset.o === st.ordenTop) return;
  st.ordenTop = b.dataset.o;
  $$("#orden-top button").forEach((x) => x.classList.toggle("on", x === b));
  const [d, h] = periodo(st.rango);
  st.datos.top = await api("sales", "/metrics/top-products", { params: { desde: isoDate(d), hasta: isoDate(h), orden: st.ordenTop, limit: 10 } });
  renderTop();
});

// ---------- Carga ----------

async function cargar() {
  const per = periodo(st.rango);
  const ant = periodoAnterior(per);
  const p = { desde: isoDate(per[0]), hasta: isoDate(per[1]) };
  const anio = per[1].getFullYear();
  $("#rango-txt").textContent = `Resumen de ventas · ${textoPeriodo(per)}`;
  esqueleto();

  try {
    const m = (path, params = p) => api("sales", `/metrics/${path}`, { params });
    const [resumen, previo, meses, pagos, horas, dias, categorias, top, clientes, sin] = await Promise.all([
      m("summary"),
      m("summary", { desde: isoDate(ant[0]), hasta: isoDate(ant[1]) }),
      m("sales-by-month", { desde: `${anio - 1}-01-01`, hasta: `${anio}-12-31` }),
      m("sales-by-payment"),
      m("sales-by-hour"),
      m("sales-by-weekday"),
      m("sales-by-category"),
      m("top-products", { ...p, orden: st.ordenTop, limit: 10 }),
      m("top-customers", { ...p, limit: 8 }),
      m("products-without-sales"),
    ]);
    st.datos = { per, ant, anio, resumen, previo, meses, pagos, horas, dias, categorias, top, clientes, sin };
    renderTodo();
  } catch (error) {
    $("#kpis").innerHTML = `<div class="card empty" style="grid-column:1/-1">${icon("alert", 36, 1.5)}<b>No se pudieron cargar las métricas</b><span>${escapeHtml(error.message)}</span></div>`;
  }
}

function esqueleto() {
  $("#kpis").innerHTML = Array.from({ length: 5 }, () => `<div class="card kpi"><div class="sk" style="height:14px;width:55%"></div><div class="sk" style="height:28px;width:75%"></div><div class="sk" style="height:30px"></div></div>`).join("");
  ["#ch-meses", "#ch-pagos", "#ch-horas", "#ch-dias", "#ch-categorias"].forEach((s) => ($(s).innerHTML = `<div class="sk" style="height:220px"></div>`));
  ["#tb-top", "#tb-clientes", "#tb-sin"].forEach((s) => ($(s).innerHTML = `<div style="padding:12px;display:flex;flex-direction:column;gap:10px">${'<div class="sk" style="height:22px"></div>'.repeat(5)}</div>`));
}

function renderTodo() {
  if (!st.datos) return;
  renderKpis();
  renderMeses();
  renderPagos();
  renderHoras();
  renderDias();
  renderCategorias();
  renderTop();
  renderClientes();
  renderSin();
}

document.addEventListener("themechange", renderTodo);

// ---------- Indicadores ----------

function delta(actual, anterior) {
  if (!anterior) return `<span class="delta flat">Sin datos del periodo anterior</span>`;
  const pct = ((actual - anterior) / anterior) * 100;
  const cls = Math.abs(pct) < 0.5 ? "flat" : pct > 0 ? "up" : "down";
  const flecha = cls === "up" ? "▲" : cls === "down" ? "▼" : "■";
  return `<span class="delta ${cls}" title="Periodo anterior: ${textoPeriodo(st.datos.ant)}">${flecha} ${formatPercent(Math.abs(pct))}<span class="muted" style="font-weight:500;font-size:12px">vs. anterior</span></span>`;
}

function sparkline(valores) {
  if (valores.length < 2) return "";
  const max = Math.max(...valores);
  const min = Math.min(...valores);
  const pts = valores.map((v, i) => `${(i / (valores.length - 1)) * 88 + 1},${30 - ((v - min) / (max - min || 1)) * 26}`).join(" ");
  return `<svg viewBox="0 0 90 34" width="64" height="30" aria-hidden="true"><polyline points="${pts}" fill="none" style="stroke:var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}

function renderKpis() {
  const { resumen: r, previo: a, meses } = st.datos;
  // Tendencia de los últimos 12 meses completos (el mes en curso todavía no termina).
  const mesActual = todayISO().slice(0, 7);
  const ult = meses.filter((m) => m.mes < mesActual).slice(-12);
  const kpis = [
    { t: "Ingresos", ic: "money", v: formatMoney(r.ingresos_totales), d: delta(r.ingresos_totales, a.ingresos_totales), s: ult.map((m) => m.ingresos) },
    { t: "Ventas", ic: "receipt", v: formatNumber(r.numero_ventas), d: delta(r.numero_ventas, a.numero_ventas), s: ult.map((m) => m.ventas) },
    { t: "Ticket promedio", ic: "ticket", v: formatMoney(r.ticket_promedio), d: delta(r.ticket_promedio, a.ticket_promedio), s: ult.map((m) => m.ingresos / (m.ventas || 1)) },
    { t: "Unidades vendidas", ic: "box", v: formatNumber(r.unidades_vendidas), d: delta(r.unidades_vendidas, a.unidades_vendidas), s: [] },
    { t: "Clientes que compraron", ic: "users", v: formatNumber(r.clientes_activos), d: delta(r.clientes_activos, a.clientes_activos), s: [] },
  ];
  $("#kpis").innerHTML = kpis.map((k) => `
    <div class="card kpi">
      <div class="kpi-top"><span>${k.t}</span><span class="kpi-ico">${icon(k.ic, 17)}</span></div>
      <div class="kpi-val num">${k.v}</div>
      <div class="kpi-bottom">${k.d}<span title="Últimos 12 meses">${sparkline(k.s)}</span></div>
    </div>`).join("");
}

// ---------- Gráficas ----------

function renderMeses() {
  const { meses, anio } = st.datos;
  const serie = (a) => Array.from({ length: 12 }, (_, i) => meses.find((m) => m.mes === `${a}-${String(i + 1).padStart(2, "0")}`) || null);
  const act = serie(anio);
  const ant = serie(anio - 1);
  const el = $("#ch-meses");
  $("#meses-sub").textContent = `${anio} comparado con ${anio - 1}`;
  $("#meses-leyenda").innerHTML = `<span><svg width="22" height="4"><line x1="0" x2="22" y1="2" y2="2" style="stroke:var(--primary)" stroke-width="3"/></svg>${anio}</span>
    <span><svg width="22" height="4"><line x1="0" x2="22" y1="2" y2="2" style="stroke:var(--accent)" stroke-width="2.5" stroke-dasharray="5 4"/></svg>${anio - 1}</span>`;

  // El mes en curso todavía no termina: se dibuja aparte para que no parezca una caída.
  const hoy = new Date();
  const enCurso = anio === hoy.getFullYear() ? hoy.getMonth() : -1;
  const completos = act.map((m, i) => (i === enCurso ? null : m));
  const vals = [...act, ...ant].filter(Boolean).map((m) => m.ingresos);
  if (!vals.length) return vacio(el);
  const W = 960, H = 280, L = 70, R = 16, B = 28, T = 16;
  const ticks = ejeY(Math.max(...vals));
  const top = ticks[ticks.length - 1];
  const x = (i) => L + (i * (W - L - R)) / 11;
  const y = (v) => H - B - (v / top) * (H - B - T);
  const linea = (s) => s.map((m, i) => (m ? `${x(i)},${y(m.ingresos)}` : null)).filter(Boolean).join(" ");
  const area = completos.filter(Boolean).length > 1
    ? `<polygon points="${x(0)},${H - B} ${linea(completos)} ${x(completos.filter(Boolean).length - 1)},${H - B}" style="fill:var(--primary)" opacity="0.08"/>` : "";

  el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Ingresos por mes de ${anio} y ${anio - 1}">
    ${ticks.map((t) => `<line x1="${L}" x2="${W - R}" y1="${y(t)}" y2="${y(t)}" style="stroke:var(--grid)"/><text x="${L - 10}" y="${y(t) + 4}" text-anchor="end" font-size="12" style="fill:var(--muted)">${formatMillions(t)}</text>`).join("")}
    ${MESES.map((m, i) => `<text x="${x(i)}" y="${H - 6}" text-anchor="middle" font-size="12" style="fill:var(--muted)">${m}</text>`).join("")}
    <polyline points="${linea(ant)}" fill="none" style="stroke:var(--accent)" stroke-width="2.5" stroke-dasharray="6 5" stroke-linejoin="round"/>
    ${area}
    <polyline points="${linea(completos)}" fill="none" style="stroke:var(--primary)" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>
    ${enCurso >= 1 && act[enCurso] && act[enCurso - 1] ? `<polyline points="${x(enCurso - 1)},${y(act[enCurso - 1].ingresos)} ${x(enCurso)},${y(act[enCurso].ingresos)}" fill="none" style="stroke:var(--primary)" stroke-width="2.5" stroke-dasharray="2 5" stroke-linecap="round"/>
      <text x="${x(enCurso)}" y="${y(act[enCurso].ingresos) + 22}" text-anchor="middle" font-size="11" font-weight="600" style="fill:var(--muted)">en curso</text>` : ""}
    ${act.map((m, i) => (m ? `<circle cx="${x(i)}" cy="${y(m.ingresos)}" r="4" style="fill:${i === enCurso ? "var(--primary)" : "var(--surface)"};stroke:var(--primary)" stroke-width="2.5"/>` : "")).join("")}
    ${MESES.map((_, i) => {
      const a = act[i], b = ant[i];
      const dif = a && b ? ` · ${a.ingresos >= b.ingresos ? "▲" : "▼"} ${formatPercent(Math.abs((a.ingresos - b.ingresos) / b.ingresos) * 100)}` : "";
      const tip = `<b>${MESES_LARGOS[i]}${i === enCurso ? " (en curso)" : ""}</b><br>${anio}: ${a ? formatMoney(a.ingresos) : "—"}${dif}<br>${anio - 1}: ${b ? formatMoney(b.ingresos) : "—"}`;
      return `<rect data-tip="${escapeHtml(tip)}" x="${x(i) - (W - L - R) / 22}" y="${T}" width="${(W - L - R) / 11}" height="${H - B - T}" fill="transparent"/>`;
    }).join("")}
  </svg>`;
  conTooltip(el);
}

function renderPagos() {
  const el = $("#ch-pagos");
  const pagos = st.datos.pagos;
  const total = pagos.reduce((s, p) => s + p.ingresos, 0);
  if (!total) return vacio(el);
  const R = 70, C = 2 * Math.PI * R;
  let acum = 0;
  const arcos = pagos.map((p) => {
    const largo = (p.ingresos / total) * C;
    const s = `<circle cx="90" cy="90" r="${R}" fill="none" style="stroke:var(--pm-${p.metodo_pago})" stroke-width="26"
      stroke-dasharray="${Math.max(largo - 2, 0)} ${C}" stroke-dashoffset="${-acum}" transform="rotate(-90 90 90)">
      <title>${p.nombre}: ${formatMoney(p.ingresos)}</title></circle>`;
    acum += largo;
    return s;
  }).join("");
  const ventas = pagos.reduce((s, p) => s + p.ventas, 0);
  el.innerHTML = `<div class="donut-wrap">
    <svg viewBox="0 0 180 180" width="190" height="190" role="img" aria-label="Participación por método de pago">${arcos}
      <text x="90" y="86" text-anchor="middle" font-size="12" style="fill:var(--muted)">Ventas</text>
      <text x="90" y="106" text-anchor="middle" font-size="20" font-weight="800" style="fill:var(--text)">${formatNumber(ventas)}</text></svg>
    <div class="donut-legend">${pagos.map((p) => `<div><i style="background:var(--pm-${p.metodo_pago})"></i><span>${escapeHtml(p.nombre)}</span>
      <b class="num">${formatPercent((p.ingresos / total) * 100)}</b></div>`).join("")}</div>
  </div>`;
}

function renderHoras() {
  const horas = st.datos.horas;
  // Se marcan los picos de la mañana (desayuno) y de la tarde (onces).
  const pico = (desde, hasta) => horas.filter((h) => h.hora >= desde && h.hora <= hasta).sort((a, b) => b.ventas - a.ventas)[0];
  const desayuno = pico(6, 11);
  const onces = pico(14, 19);
  barras($("#ch-horas"), horas.map((h) => ({
    label: h.hora % 2 === 0 ? `${(h.hora % 12) || 12}${h.hora < 12 ? "a" : "p"}` : "",
    valor: h.ventas,
    destacar: h === desayuno || h === onces,
    nota: h === desayuno && h.ventas ? "Desayuno" : h === onces && h.ventas ? "Onces" : "",
    tip: `<b>${h.etiqueta}</b><br>${formatNumber(h.ventas)} ventas · ${formatMoney(h.ingresos)}`,
  })), formatNumber);
}

function renderDias() {
  // La API numera los días 1 = lunes ... 7 = domingo; DIAS_CORTOS empieza en domingo (índice 0).
  const orden = [1, 2, 3, 4, 5, 6, 7];
  const dias = orden.map((n) => st.datos.dias.find((d) => d.numero_dia === n) || { numero_dia: n, dia: DIAS_CORTOS[n % 7], ventas: 0, ingresos: 0 });
  const max = Math.max(...dias.map((d) => d.ventas));
  barras($("#ch-dias"), dias.map((d) => ({
    label: DIAS_CORTOS[d.numero_dia % 7],
    valor: d.ventas,
    destacar: d.ventas === max,
    tip: `<b>${escapeHtml(d.dia)}</b><br>${formatNumber(d.ventas)} ventas · ${formatMoney(d.ingresos)}`,
  })), formatNumber);
}

function renderCategorias() {
  const el = $("#ch-categorias");
  const cats = st.datos.categorias;
  if (!cats.length) return vacio(el);
  const max = cats[0].ingresos;
  const total = cats.reduce((s, c) => s + c.ingresos, 0);
  el.innerHTML = cats.map((c) => `
    <div class="catbar" title="${formatNumber(c.unidades)} unidades · ${formatPercent((c.ingresos / total) * 100)} de los ingresos">
      <span class="n"><span class="dot" style="background:${categoryColor(c.categoria)}"></span>${escapeHtml(c.categoria)}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${(c.ingresos / max) * 100}%;background:${categoryColor(c.categoria)}"></div></div>
      <span class="num" style="text-align:right;font-weight:700">${formatMillions(c.ingresos)}</span>
    </div>`).join("");
}

// ---------- Tablas ----------

function renderTop() {
  const top = st.datos.top;
  if (!top.length) return vacio($("#tb-top"));
  const campo = st.ordenTop === "ingresos" ? "ingresos" : "cantidad";
  const max = top[0][campo];
  $("#tb-top").innerHTML = `<table class="tbl compact"><thead><tr><th>#</th><th>Producto</th><th>Categoría</th><th class="r">Unidades</th><th class="r">Ingresos</th></tr></thead><tbody>
    ${top.map((p, i) => `<tr>
      <td class="num muted" style="width:36px">${i + 1}</td>
      <td style="min-width:200px"><b>${escapeHtml(p.producto)}</b><div class="mini-track"><div class="mini-fill" style="width:${(p[campo] / max) * 100}%"></div></div></td>
      <td>${categoryChip(p.categoria)}</td>
      <td class="r num">${formatNumber(p.cantidad)}</td>
      <td class="r num" style="font-weight:700">${formatMoney(p.ingresos)}</td></tr>`).join("")}
  </tbody></table>`;
}

function renderClientes() {
  const cl = st.datos.clientes;
  if (!cl.length) return vacio($("#tb-clientes"), "Ningún cliente registrado compró en este periodo");
  $("#tb-clientes").innerHTML = `<table class="tbl compact"><thead><tr><th>Cliente</th><th class="r">Compras</th><th class="r">Gasto</th></tr></thead><tbody>
    ${cl.map((c) => `<tr>
      <td><div style="display:flex;align-items:center;gap:10px"><span class="av">${escapeHtml(initials(c.nombre))}</span><b style="font-size:13px">${escapeHtml(c.nombre)}</b></div></td>
      <td class="r num">${formatNumber(c.compras)}</td>
      <td class="r num" style="font-weight:700">${formatMoney(c.gasto)}</td></tr>`).join("")}
  </tbody></table>`;
}

function renderSin() {
  const sin = st.datos.sin;
  if (!sin.length) {
    $("#tb-sin").innerHTML = `<div class="empty" style="padding:40px 16px">${icon("check", 30, 2)}<b>Todos los productos se vendieron</b><span>Ningún producto activo se quedó sin ventas en el periodo.</span></div>`;
    return;
  }
  $("#tb-sin").innerHTML = `<table class="tbl compact"><thead><tr><th>Producto</th><th>Categoría</th><th class="r">Precio</th></tr></thead><tbody>
    ${sin.map((p) => `<tr><td><b style="font-size:13px">${escapeHtml(p.nombre)}</b></td><td>${categoryChip(p.categoria)}</td><td class="r num">${formatMoney(p.precio)}</td></tr>`).join("")}
  </tbody></table>`;
}

// ---------- Exportar ----------

$("#exportar").addEventListener("click", () => {
  if (!st.datos) return;
  const { per, resumen: r, categorias, pagos, top } = st.datos;
  const filas = [
    ["Pan del Valle · Resumen de ventas", textoPeriodo(per)],
    [],
    ["Indicador", "Valor"],
    ["Ingresos", r.ingresos_totales],
    ["Ventas", r.numero_ventas],
    ["Ticket promedio", r.ticket_promedio],
    ["Unidades vendidas", r.unidades_vendidas],
    ["Clientes que compraron", r.clientes_activos],
    [],
    ["Categoría", "Ventas", "Unidades", "Ingresos"],
    ...categorias.map((c) => [c.categoria, c.ventas, c.unidades, c.ingresos]),
    [],
    ["Método de pago", "Ventas", "Ingresos"],
    ...pagos.map((p) => [p.nombre, p.ventas, p.ingresos]),
    [],
    ["Producto", "Categoría", "Unidades", "Ingresos"],
    ...top.map((p) => [p.producto, p.categoria, p.cantidad, p.ingresos]),
  ];
  downloadCsv(`resumen_ventas_${isoDate(per[0])}_${isoDate(per[1])}.csv`, filas);
});

renderRangos();
cargar();
