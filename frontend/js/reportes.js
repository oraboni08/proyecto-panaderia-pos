// Reportes del administrador: los calcula Apache Spark a partir del histórico en HDFS
// y los sirve reporting-service (lado de lectura de CQRS). Esta página no consulta
// la base de datos de ventas: todo sale de GET /api/v1/reports/resumen.

renderAdminShell("reportes");

$("#recargar").innerHTML = `${icon("history", 18)}Actualizar`;
$("#recargar").addEventListener("click", cargar);

let datos = null;

async function cargar() {
  esqueleto();
  try {
    datos = await api("reports", "/resumen");
    datos.nombres = await nombresClientes(datos.clientes);
    renderTodo();
  } catch (error) {
    $("#ejecucion").innerHTML = `<div class="empty" style="padding:24px">${icon("alert", 32, 1.5)}<b>No se pudieron cargar los reportes</b><span>${escapeHtml(error.message)}</span></div>`;
    $("#kpis").innerHTML = "";
  }
}

// Spark solo guarda el id del cliente; el nombre se le pide a sales-service.
async function nombresClientes(clientes) {
  const pares = await Promise.all(clientes.map(async (c) => {
    try {
      const cli = await api("sales", `/customers/${c.id_cliente}`);
      return [c.id_cliente, cli.nombre];
    } catch {
      return [c.id_cliente, `Cliente #${c.id_cliente}`];
    }
  }));
  return Object.fromEntries(pares);
}

function esqueleto() {
  $("#ejecucion").innerHTML = `<div class="sk" style="height:44px"></div>`;
  $("#kpis").innerHTML = Array.from({ length: 4 }, () => `<div class="card kpi"><div class="sk" style="height:14px;width:55%"></div><div class="sk" style="height:28px;width:75%"></div></div>`).join("");
  ["#ch-meses", "#ch-horas", "#ch-dias", "#ch-categorias"].forEach((s) => ($(s).innerHTML = `<div class="sk" style="height:220px"></div>`));
  ["#tb-top", "#tb-clientes"].forEach((s) => ($(s).innerHTML = `<div style="padding:12px;display:flex;flex-direction:column;gap:10px">${'<div class="sk" style="height:22px"></div>'.repeat(5)}</div>`));
}

function renderTodo() {
  if (!datos) return;
  renderEjecucion();
  if (!datos.ultima_ejecucion) return;
  renderKpis();
  renderMeses();
  renderHoras();
  renderDias();
  renderCategorias();
  renderTop();
  renderClientes();
}

document.addEventListener("themechange", renderTodo);

// ---------- Última ejecución de Spark ----------

function renderEjecucion() {
  const e = datos.ultima_ejecucion;
  if (!e) {
    $("#ejecucion").innerHTML = `<div class="empty" style="padding:24px">${icon("info", 32, 1.5)}
      <b>Spark todavía no ha calculado los reportes</b>
      <span>Ejecútalo en el servidor con <code>./deploy/correr_spark.sh</code> y vuelve a cargar esta página.</span></div>`;
    $("#kpis").innerHTML = "";
    ["#ch-meses", "#ch-horas", "#ch-dias", "#ch-categorias", "#tb-top", "#tb-clientes"].forEach((s) => vacio($(s), "Sin datos hasta que corra Spark"));
    return;
  }
  const dato = (valor, texto) => `<div style="display:flex;flex-direction:column"><b class="num" style="font-size:18px">${valor}</b><span class="muted" style="font-size:12px">${texto}</span></div>`;
  $("#ejecucion").innerHTML = `
    <div style="display:flex;flex-wrap:wrap;gap:12px 28px;align-items:center">
      <div style="display:flex;align-items:center;gap:10px;min-width:220px">
        <span class="kpi-ico">${icon("clock", 18)}</span>
        <div><b>Última ejecución de Spark</b><div class="muted" style="font-size:13px">${formatDateTime(e.fin)}</div></div>
      </div>
      ${dato(formatNumber(e.lineas), "líneas leídas de HDFS")}
      ${dato(formatNumber(e.archivos), "archivos CSV")}
      ${dato(formatNumber(e.particiones), "particiones en paralelo")}
      ${dato(formatNumber(e.nucleos), "núcleos")}
      ${dato(`${String(e.segundos).replace(".", ",")} s`, "duración del job")}
    </div>`;
}

// ---------- Indicadores ----------

function renderKpis() {
  const e = datos.ultima_ejecucion;
  const ingresos = datos.meses.reduce((s, m) => s + m.ingresos, 0);
  const kpis = [
    { t: "Ingresos históricos", ic: "money", v: formatMoney(ingresos) },
    { t: "Ventas", ic: "receipt", v: formatNumber(e.ventas) },
    { t: "Ticket promedio", ic: "ticket", v: formatMoney(Math.round(ingresos / (e.ventas || 1))) },
    { t: "Meses en el data lake", ic: "calendar", v: formatNumber(datos.meses.length) },
  ];
  $("#kpis").innerHTML = kpis.map((k) => `
    <div class="card kpi">
      <div class="kpi-top"><span>${k.t}</span><span class="kpi-ico">${icon(k.ic, 17)}</span></div>
      <div class="kpi-val num">${k.v}</div>
    </div>`).join("");
}

// ---------- Gráficas ----------

function renderMeses() {
  const meses = datos.meses;
  const max = Math.max(...meses.map((m) => m.ingresos));
  barras($("#ch-meses"), meses.map((m) => {
    const [a, mm] = m.mes.split("-").map(Number);
    return {
      // Con ~2 años de meses no caben todas las etiquetas: el año en enero y luego
      // una por trimestre. El detalle de cada mes aparece al pasar el mouse.
      label: mm === 1 ? String(a) : [4, 7, 10].includes(mm) ? MESES[mm - 1] : "",
      valor: m.ingresos,
      destacar: m.ingresos === max,
      tip: `<b>${MESES_LARGOS[mm - 1]} de ${a}</b><br>${formatNumber(m.ventas)} ventas · ${formatMoney(m.ingresos)}`,
    };
  }), formatMillions);
}

function renderHoras() {
  const horas = datos.horas;
  const max = Math.max(...horas.map((h) => h.ventas));
  barras($("#ch-horas"), horas.map((h) => ({
    label: h.hora % 2 === 0 ? `${(h.hora % 12) || 12}${h.hora < 12 ? "a" : "p"}` : "",
    valor: h.ventas,
    destacar: h.ventas === max,
    tip: `<b>${(h.hora % 12) || 12} ${h.hora < 12 ? "a. m." : "p. m."}</b><br>${formatNumber(h.ventas)} ventas · ${formatMoney(h.ingresos)}`,
  })), formatNumber);
}

function renderDias() {
  // Spark numera los días 1 = lunes ... 7 = domingo; DIAS_CORTOS empieza en domingo.
  const dias = datos.dias;
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
  const cats = datos.categorias;
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
  const top = datos.productos;
  if (!top.length) return vacio($("#tb-top"));
  const max = top[0].unidades;
  $("#tb-top").innerHTML = `<table class="tbl compact"><thead><tr><th>#</th><th>Producto</th><th>Categoría</th><th class="r">Ventas</th><th class="r">Unidades</th><th class="r">Ingresos</th></tr></thead><tbody>
    ${top.map((p, i) => `<tr>
      <td class="num muted" style="width:36px">${i + 1}</td>
      <td style="min-width:200px"><b>${escapeHtml(p.producto)}</b><div class="mini-track"><div class="mini-fill" style="width:${(p.unidades / max) * 100}%"></div></div></td>
      <td>${categoryChip(p.categoria)}</td>
      <td class="r num">${formatNumber(p.ventas)}</td>
      <td class="r num">${formatNumber(p.unidades)}</td>
      <td class="r num" style="font-weight:700">${formatMoney(p.ingresos)}</td></tr>`).join("")}
  </tbody></table>`;
}

function renderClientes() {
  const cl = datos.clientes;
  if (!cl.length) return vacio($("#tb-clientes"), "No hay clientes registrados con compras");
  $("#tb-clientes").innerHTML = `<table class="tbl compact"><thead><tr><th>Cliente</th><th class="r">Compras</th><th class="r">Gasto</th></tr></thead><tbody>
    ${cl.map((c) => {
      const nombre = datos.nombres[c.id_cliente] || `Cliente #${c.id_cliente}`;
      return `<tr>
      <td><div style="display:flex;align-items:center;gap:10px"><span class="av">${escapeHtml(initials(nombre))}</span><b style="font-size:13px">${escapeHtml(nombre)}</b></div></td>
      <td class="r num">${formatNumber(c.compras)}</td>
      <td class="r num" style="font-weight:700">${formatMoney(c.gasto)}</td></tr>`;
    }).join("")}
  </tbody></table>`;
}

cargar();
