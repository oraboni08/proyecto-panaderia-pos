// Utilidades de presentación compartidas por todas las páginas.

const numberFormat = (decimals) =>
  new Intl.NumberFormat("de-DE", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });

const money2 = numberFormat(2);

function formatMoney(value) {
  return `€ ${money2.format(value || 0)}`;
}

function formatNumber(value, decimals = 0) {
  return numberFormat(decimals).format(value || 0);
}

function formatPrice(product) {
  const unidad = product.tipo_venta === "peso" ? "/kg" : "/u";
  return `${formatMoney(product.precio)} ${unidad}`;
}

// Cantidad guardada (unidades o kg) en texto: "2 u" o "350 g".
function formatQuantity(cantidad, tipoVenta) {
  if (tipoVenta === "peso") return `${formatNumber(Math.round(cantidad * 1000))} g`;
  return `${formatNumber(cantidad, Number.isInteger(cantidad) ? 0 : 1)} u`;
}

function formatDateTime(isoString) {
  const d = new Date(isoString);
  return d.toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" });
}

function formatTime(isoString) {
  return new Date(isoString).toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
}

function todayISO() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function escapeHtml(text) {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function $(selector) {
  return document.querySelector(selector);
}

function showAlert(element, message, type = "error") {
  element.className = `alert alert-${type}`;
  element.textContent = message;
}

function hideAlert(element) {
  element.className = "alert hidden";
  element.textContent = "";
}

// Ventana modal sencilla. Devuelve funciones para abrirla y cerrarla.
function setupModal(backdropSelector) {
  const backdrop = $(backdropSelector);
  const close = () => backdrop.classList.add("hidden");
  const open = () => backdrop.classList.remove("hidden");

  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) close();
  });
  backdrop.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", close));

  return { open, close };
}

// Menú lateral del administrador (se dibuja igual en sus cuatro páginas).
function renderAdminSidebar(active) {
  const session = getSession();
  const items = [
    ["dashboard", "📊", "Dashboard"],
    ["catalogo", "🥖", "Catálogo"],
    ["historial", "🕘", "Historial de cambios"],
    ["usuarios", "👥", "Usuarios"],
  ];

  $("#sidebar").innerHTML = `
    <div class="brand"><div class="logo">🥐</div><span>Panadería POS</span></div>
    <nav class="nav">
      ${items
        .map(
          ([page, icon, label]) =>
            `<a href="/admin/${page}.html" class="${page === active ? "active" : ""}">
               <span class="icon">${icon}</span>${label}</a>`
        )
        .join("")}
    </nav>
    <div class="sidebar-footer">
      <div class="user-name">${escapeHtml(session.nombre)}</div>
      <div class="user-role">Administrador</div>
      <button class="btn btn-outline" id="logout">Cerrar sesión</button>
    </div>`;

  $("#logout").addEventListener("click", logout);
}
