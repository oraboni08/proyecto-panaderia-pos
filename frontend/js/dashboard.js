requireRole("admin");
renderAdminSidebar("dashboard");

const errorBox = $("#error");
const charts = {};

const BAR_COLORS = ["#a5582c", "#c47a45", "#d4935e", "#e2ab78", "#efc595", "#f7dbb6", "#fbe9d3"];

Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
Chart.defaults.color = "#8a7563";

function filters() {
  return { desde: $("#desde").value, hasta: $("#hasta").value };
}

function drawChart(id, config) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart($(`#${id}`), config);
}

function renderSummary(s) {
  $("#kpi-ingresos").textContent = formatMoney(s.ingresos_totales);
  $("#kpi-ventas").textContent = formatNumber(s.numero_ventas);
  $("#kpi-unidades").textContent = formatNumber(s.unidades_vendidas);
  $("#kpi-kg").textContent = s.kg_vendidos ? `+ ${formatNumber(s.kg_vendidos, 2)} kg por peso` : "";
  $("#kpi-ticket").textContent = formatMoney(s.ticket_promedio);
  $("#kpi-clientes").textContent = formatNumber(s.clientes_activos);
}

function renderWeekdays(dias) {
  // El domingo solo se muestra si tiene ventas.
  const visibles = dias.filter((d) => d.numero_dia < 7 || d.ventas > 0);

  drawChart("chart-dias", {
    type: "bar",
    data: {
      labels: visibles.map((d) => d.dia),
      datasets: [{
        label: "Ventas",
        data: visibles.map((d) => d.ventas),
        backgroundColor: BAR_COLORS,
        borderRadius: 8,
      }],
    },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            afterLabel: (ctx) => `Ingresos: ${formatMoney(visibles[ctx.dataIndex].ingresos)}`,
          },
        },
      },
      scales: { y: { beginAtZero: true, grid: { color: "#f3e8da" } }, x: { grid: { display: false } } },
    },
  });
}

function renderTopProducts(productos, orden) {
  const valor = (p) => (orden === "ingresos" ? p.ingresos : p.cantidad);
  const etiqueta = (p) =>
    orden === "ingresos" ? formatMoney(p.ingresos) : formatQuantity(p.cantidad, p.tipo_venta);

  drawChart("chart-productos", {
    type: "bar",
    data: {
      labels: productos.map((p) => p.producto),
      datasets: [{
        label: orden === "ingresos" ? "Ingresos" : "Cantidad",
        data: productos.map(valor),
        backgroundColor: BAR_COLORS,
        borderRadius: 8,
      }],
    },
    options: {
      indexAxis: "y",
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (ctx) => etiqueta(productos[ctx.dataIndex]) } },
      },
      scales: { x: { beginAtZero: true, grid: { color: "#f3e8da" } }, y: { grid: { display: false } } },
    },
  });
}

function renderTopCustomers(clientes) {
  $("#tabla-clientes").innerHTML = clientes.length
    ? clientes
        .map(
          (c) => `<tr>
            <td><strong>${escapeHtml(c.nombre)}</strong> <span class="hint">#${c.id_cliente}</span></td>
            <td class="num">${c.compras}</td>
            <td class="num">${formatMoney(c.gasto)}</td>
          </tr>`
        )
        .join("")
    : `<tr><td colspan="3" class="empty">Sin ventas en este periodo</td></tr>`;
}

function renderWithoutSales(productos) {
  $("#titulo-sin-ventas").textContent = `Productos sin ventas (${productos.length})`;
  $("#tabla-sin-ventas").innerHTML = productos.length
    ? productos
        .map(
          (p) => `<tr>
            <td><strong>${escapeHtml(p.nombre)}</strong></td>
            <td class="num">${formatPrice(p)}</td>
            <td class="num"><span class="badge">Sin ventas</span></td>
          </tr>`
        )
        .join("")
    : `<tr><td colspan="3" class="empty">Todos los productos activos tuvieron ventas 🎉</td></tr>`;
}

async function loadTopProducts() {
  const orden = $("#orden-productos").value;
  const productos = await api("sales", "/metrics/top-products", { params: { ...filters(), orden, limit: 7 } });
  renderTopProducts(productos, orden);
}

async function loadDashboard() {
  hideAlert(errorBox);

  const { desde, hasta } = filters();
  $("#periodo").textContent =
    desde || hasta ? `Del ${desde || "inicio"} al ${hasta || "hoy"}` : "Todas las ventas registradas";

  try {
    const params = filters();
    const [resumen, dias, clientes, sinVentas] = await Promise.all([
      api("sales", "/metrics/summary", { params }),
      api("sales", "/metrics/sales-by-weekday", { params }),
      api("sales", "/metrics/top-customers", { params: { ...params, limit: 6 } }),
      api("sales", "/metrics/products-without-sales", { params }),
      loadTopProducts(),
    ]);

    renderSummary(resumen);
    renderWeekdays(dias);
    renderTopCustomers(clientes);
    renderWithoutSales(sinVentas);
  } catch (error) {
    showAlert(errorBox, error.message);
  }
}

$("#filtro").addEventListener("submit", (e) => {
  e.preventDefault();
  const { desde, hasta } = filters();
  if (desde && hasta && desde > hasta) {
    showAlert(errorBox, "La fecha inicial no puede ser mayor que la final.");
    return;
  }
  loadDashboard();
});

$("#limpiar").addEventListener("click", () => {
  $("#desde").value = "";
  $("#hasta").value = "";
  loadDashboard();
});

$("#orden-productos").addEventListener("change", () => loadTopProducts().catch((e) => showAlert(errorBox, e.message)));

loadDashboard();
