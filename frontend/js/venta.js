const session = requireRole("cajero");

$("#cajero-nombre").textContent = session.nombre;
$("#logout").addEventListener("click", logout);

const CONSUMIDOR_FINAL = { id_cliente: 0, nombre: "Consumidor final" };

const mensaje = $("#mensaje");
const ticketModal = setupModal("#modal-ticket");

let productos = [];
let cliente = CONSUMIDOR_FINAL;
let carrito = []; // [{ producto, cantidad }]  cantidad = unidades o gramos

// ---------- Cliente ----------

function mostrarCliente() {
  $("#cliente-texto").innerHTML = `${escapeHtml(cliente.nombre)} <small>#${cliente.id_cliente}</small>`;
  $("#quitar-cliente").classList.toggle("hidden", cliente.id_cliente === 0);
  $("#cliente-seleccionado").classList.remove("hidden");
  $("#buscador-cliente").classList.add("hidden");
  $("#resultados-cliente").classList.add("hidden");
  $("#form-cliente").classList.add("hidden");
}

function elegirCliente(c) {
  cliente = c;
  mostrarCliente();
}

$("#cambiar-cliente").addEventListener("click", () => {
  $("#cliente-seleccionado").classList.add("hidden");
  $("#buscador-cliente").classList.remove("hidden");
  $("#buscar-cliente").value = "";
  $("#buscar-cliente").focus();
});

$("#quitar-cliente").addEventListener("click", () => elegirCliente(CONSUMIDOR_FINAL));

let busquedaTimer;
$("#buscar-cliente").addEventListener("input", () => {
  clearTimeout(busquedaTimer);
  busquedaTimer = setTimeout(buscarClientes, 250);
});

$("#buscar-cliente").addEventListener("keydown", (e) => {
  if (e.key === "Escape") mostrarCliente();
});

async function buscarClientes() {
  const texto = $("#buscar-cliente").value.trim();
  const resultados = $("#resultados-cliente");

  if (!texto) {
    resultados.classList.add("hidden");
    return;
  }

  try {
    const clientes = await api("sales", "/customers", { params: { search: texto, limit: 8 } });

    resultados.innerHTML = clientes.length
      ? clientes
          .map(
            (c) => `<button type="button" data-id="${c.id_cliente}" data-nombre="${escapeHtml(c.nombre)}">
                      <span>${escapeHtml(c.nombre)}</span><span class="id">#${c.id_cliente}</span>
                    </button>`
          )
          .join("")
      : `<div class="empty">Sin resultados. Puedes registrarlo como cliente nuevo.</div>`;

    resultados.classList.remove("hidden");
  } catch (error) {
    showAlert(mensaje, error.message);
  }
}

$("#resultados-cliente").addEventListener("click", (e) => {
  const boton = e.target.closest("[data-id]");
  if (boton) elegirCliente({ id_cliente: Number(boton.dataset.id), nombre: boton.dataset.nombre });
});

$("#abrir-nuevo-cliente").addEventListener("click", () => {
  $("#form-cliente").classList.remove("hidden");
  $("#resultados-cliente").classList.add("hidden");
  const texto = $("#buscar-cliente").value.trim();
  $("#nuevo-cliente-nombre").value = /^\d+$/.test(texto) ? "" : texto;
  $("#nuevo-cliente-nombre").focus();
});

$("#form-cliente").addEventListener("submit", async (e) => {
  e.preventDefault();
  const nombre = $("#nuevo-cliente-nombre").value.trim();

  if (!nombre) {
    showAlert(mensaje, "Escribe el nombre del cliente nuevo.");
    return;
  }

  try {
    const nuevo = await api("sales", "/customers", { method: "POST", body: { nombre } });
    elegirCliente(nuevo);
    showAlert(mensaje, `Cliente "${nuevo.nombre}" registrado con el número ${nuevo.id_cliente}.`, "success");
  } catch (error) {
    showAlert(mensaje, error.message);
  }
});

// ---------- Productos y carrito ----------

function productoSeleccionado() {
  return productos.find((p) => p.id_producto === Number($("#producto").value));
}

function actualizarCampoCantidad() {
  const p = productoSeleccionado();
  if (!p) return;

  const porPeso = p.tipo_venta === "peso";
  $("#cantidad-label").textContent = porPeso ? "Gramos" : "Unidades";
  $("#cantidad").step = 1;
  $("#cantidad").value = porPeso ? 250 : 1;
  $("#producto-info").textContent = porPeso
    ? `Se vende por peso: ${formatMoney(p.precio)} por kg. Ingresa los gramos.`
    : `Se vende por unidad: ${formatMoney(p.precio)} cada una.`;
}

async function cargarProductos() {
  const seleccionado = $("#producto").value;
  productos = await api("catalog", "/products", { params: { activo: true } });

  $("#producto").innerHTML = productos
    .map((p) => `<option value="${p.id_producto}">${escapeHtml(p.nombre)} — ${formatPrice(p)}</option>`)
    .join("");

  if (seleccionado && productos.some((p) => p.id_producto === Number(seleccionado))) {
    $("#producto").value = seleccionado;
  }
  actualizarCampoCantidad();
}

// Mismo cálculo que el back-end, para que el cajero vea el total mientras arma el carrito.
// El valor oficial lo calcula el back-end al cobrar (RN05).
function subtotal(item) {
  const cantidad = item.producto.tipo_venta === "peso" ? item.cantidad / 1000 : item.cantidad;
  return Math.round(item.producto.precio * cantidad * 100) / 100;
}

function totalCarrito() {
  return Math.round(carrito.reduce((suma, item) => suma + subtotal(item), 0) * 100) / 100;
}

function renderCarrito() {
  $("#carrito").innerHTML = carrito.length
    ? carrito
        .map(
          (item, i) => `<tr>
            <td><strong>${escapeHtml(item.producto.nombre)}</strong></td>
            <td class="num">${item.producto.tipo_venta === "peso" ? `${formatNumber(item.cantidad)} g` : `${item.cantidad} u`}</td>
            <td class="num">${formatPrice(item.producto)}</td>
            <td class="num">${formatMoney(subtotal(item))}</td>
            <td class="num"><button class="btn btn-ghost btn-sm" data-quitar="${i}" title="Quitar">✕</button></td>
          </tr>`
        )
        .join("")
    : `<tr><td colspan="5" class="empty">Agrega productos para empezar la venta</td></tr>`;

  $("#total").textContent = formatMoney(totalCarrito());
  $("#cobrar").disabled = carrito.length === 0;
}

$("#producto").addEventListener("change", actualizarCampoCantidad);

$("#form-agregar").addEventListener("submit", (e) => {
  e.preventDefault();
  hideAlert(mensaje);

  const producto = productoSeleccionado();
  const cantidad = Number($("#cantidad").value);

  // Validación de forma (las reglas completas se validan en el back-end).
  if (!producto) return showAlert(mensaje, "Escoge un producto.");
  if (!(cantidad > 0)) return showAlert(mensaje, "La cantidad debe ser mayor que 0.");
  if (!Number.isInteger(cantidad)) {
    return showAlert(
      mensaje,
      producto.tipo_venta === "peso" ? "Ingresa los gramos sin decimales." : "Las unidades deben ser un número entero."
    );
  }

  // Si el producto ya está en el carrito, se suma la cantidad.
  const existente = carrito.find((item) => item.producto.id_producto === producto.id_producto);
  if (existente) existente.cantidad += cantidad;
  else carrito.push({ producto, cantidad });

  renderCarrito();
});

$("#carrito").addEventListener("click", (e) => {
  const boton = e.target.closest("[data-quitar]");
  if (!boton) return;
  carrito.splice(Number(boton.dataset.quitar), 1);
  renderCarrito();
});

// ---------- Cobrar ----------

function mostrarTicket(venta, totalEsperado) {
  $("#ticket-encabezado").textContent =
    `Venta #${venta.id_venta} · ${formatDateTime(venta.fecha)} · ${venta.cliente.nombre} (#${venta.cliente.id_cliente})`;

  $("#ticket-lineas").innerHTML = venta.lineas
    .map(
      (l) => `<div class="ticket-line">
        <span>${escapeHtml(l.producto)} <span class="hint">${formatQuantity(l.cantidad, l.tipo_venta)} × ${formatMoney(l.precio_unitario)}${l.tipo_venta === "peso" ? "/kg" : ""}</span></span>
        <strong>${formatMoney(l.subtotal)}</strong>
      </div>`
    )
    .join("");

  $("#ticket-total").textContent = formatMoney(venta.total);

  const aviso = $("#ticket-aviso");
  if (Math.abs(venta.total - totalEsperado) > 0.001) {
    showAlert(
      aviso,
      `Un precio cambió mientras armabas la venta. El total cobrado es ${formatMoney(venta.total)} (antes ${formatMoney(totalEsperado)}).`,
      "warning"
    );
  } else {
    hideAlert(aviso);
  }

  ticketModal.open();
}

$("#cobrar").addEventListener("click", async () => {
  hideAlert(mensaje);
  $("#cobrar").disabled = true;
  $("#cobrar").textContent = "Registrando…";

  const totalEsperado = totalCarrito();

  try {
    const venta = await api("sales", "/orders", {
      method: "POST",
      body: {
        id_cliente: cliente.id_cliente,
        lineas: carrito.map((item) => ({ id_producto: item.producto.id_producto, cantidad: item.cantidad })),
      },
    });

    carrito = [];
    elegirCliente(CONSUMIDOR_FINAL);
    renderCarrito();
    mostrarTicket(venta, totalEsperado);
    cargarVentasHoy();
  } catch (error) {
    // La venta es todo o nada: si falla, el carrito se conserva para corregirlo.
    showAlert(mensaje, `No se registró la venta: ${error.message}`);
    cargarProductos().catch(() => {});
  } finally {
    $("#cobrar").textContent = "Cobrar";
    $("#cobrar").disabled = carrito.length === 0;
  }
});

// ---------- Ventas de hoy ----------

async function cargarVentasHoy() {
  try {
    const hoy = todayISO();
    const ventas = await api("sales", "/orders", { params: { desde: hoy, hasta: hoy } });

    $("#hoy-ventas").textContent = ventas.length;
    $("#hoy-total").textContent = formatMoney(ventas.reduce((s, v) => s + v.total, 0));

    $("#ventas-hoy").innerHTML = ventas.length
      ? ventas
          .map(
            (v) => `<tr>
              <td class="nowrap">${formatTime(v.fecha)}</td>
              <td>${escapeHtml(v.cliente.nombre)} <span class="hint">#${v.cliente.id_cliente}</span></td>
              <td>${v.lineas.map((l) => escapeHtml(l.producto)).join(", ")}</td>
              <td class="num"><strong>${formatMoney(v.total)}</strong></td>
            </tr>`
          )
          .join("")
      : `<tr><td colspan="4" class="empty">Aún no has registrado ventas hoy</td></tr>`;
  } catch (error) {
    showAlert(mensaje, error.message);
  }
}

$("#refrescar").addEventListener("click", () => {
  cargarVentasHoy();
  cargarProductos().catch((e) => showAlert(mensaje, e.message));
});

renderCarrito();
cargarProductos().catch((e) => showAlert(mensaje, e.message));
cargarVentasHoy();
