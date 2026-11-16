// Utilidades de presentación compartidas por todas las páginas:
// formatos colombianos, íconos, tema claro/oscuro, avisos, barra lateral y fotos de productos.

// ---------- Formatos ----------

const _miles = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 });

function formatNumber(n) {
  return _miles.format(Math.round(n || 0));
}

// $3.200 · $1.278.771.950 (pesos colombianos sin decimales)
function formatMoney(n) {
  const v = Math.round(n || 0);
  return (v < 0 ? "-$" : "$") + _miles.format(Math.abs(v));
}

// $1.278 M · $132,9 M (para ejes y barras)
function formatMillions(n) {
  const m = (n || 0) / 1e6;
  if (!n) return "$0";
  if (Math.abs(m) < 1) return `$${_miles.format(Math.round(n / 1000))} mil`;
  if (m >= 100) return `$${_miles.format(Math.round(m))} M`;
  return `$${m.toLocaleString("es-CO", { maximumFractionDigits: 1 })} M`;
}

function formatPercent(n, decimals = 1) {
  return `${(n || 0).toLocaleString("es-CO", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })} %`;
}

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const MESES_LARGOS = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
const DIAS_CORTOS = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];

function _toDate(value) {
  if (value instanceof Date) return value;
  // "2026-11-15T08:45:00" (sin zona) se interpreta como hora local de Colombia.
  return new Date(String(value).replace(" ", "T"));
}

// "8:45 a. m."
function formatTime(value) {
  const d = _toDate(value);
  const h = d.getHours();
  return `${(h % 12) || 12}:${String(d.getMinutes()).padStart(2, "0")} ${h < 12 ? "a. m." : "p. m."}`;
}

// "15 nov 2026"
function formatDate(value) {
  const d = _toDate(value);
  return `${d.getDate()} ${MESES[d.getMonth()]} ${d.getFullYear()}`;
}

// "15 nov 2026, 8:45 a. m."
function formatDateTime(value) {
  return `${formatDate(value)}, ${formatTime(value)}`;
}

function isoDate(d) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function todayISO() {
  return isoDate(new Date());
}

function addDays(d, n) {
  const r = new Date(d);
  r.setDate(r.getDate() + n);
  return r;
}

// 1144123456 → "1.144.123.456"
function formatDocument(doc) {
  if (!doc) return "";
  return /^\d+$/.test(doc) ? _miles.format(Number(doc)) : doc;
}

// 3154829910 → "315 482 9910"
function formatPhone(tel) {
  if (!tel) return "";
  return tel.length === 10 ? `${tel.slice(0, 3)} ${tel.slice(3, 6)} ${tel.slice(6)}` : tel;
}

function initials(nombre) {
  const partes = String(nombre || "?").trim().split(/\s+/);
  return ((partes[0]?.[0] || "") + (partes.length > 2 ? partes[partes.length - 2][0] : partes[1]?.[0] || "")).toUpperCase();
}

function normalize(text) {
  return String(text || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
}

function escapeHtml(text) {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function $(selector, root = document) {
  return root.querySelector(selector);
}

function $$(selector, root = document) {
  return [...root.querySelectorAll(selector)];
}

function debounce(fn, ms = 250) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

// ---------- Catálogos de la interfaz ----------

const CATEGORIAS = {
  "Panadería de queso": "#E3A44A",
  "Panes": "#A8743F",
  "Hojaldres": "#D9822B",
  "Salados": "#C0532E",
  "Desayunos": "#6F8F2F",
  "Tortas y postres": "#C2577A",
  "Galletas y dulces": "#8E6BB0",
  "Bebidas calientes": "#8A6247",
  "Bebidas frías": "#2F8F9D",
  "Lácteos y despensa": "#4F7CAC",
};

function categoryColor(categoria) {
  return CATEGORIAS[categoria] || "#9A8B7E";
}

function categoryChip(categoria) {
  return `<span class="chip"><span class="dot" style="background:${categoryColor(categoria)}"></span>${escapeHtml(categoria)}</span>`;
}

const METODOS_PAGO = [
  { id: "efectivo", nombre: "Efectivo", icon: "cash" },
  { id: "nequi", nombre: "Nequi", icon: "phone" },
  { id: "daviplata", nombre: "Daviplata", icon: "wallet" },
  { id: "tarjeta_debito", nombre: "Tarjeta débito", icon: "card" },
  { id: "tarjeta_credito", nombre: "Tarjeta crédito", icon: "cardc" },
  { id: "transferencia", nombre: "Transferencia", icon: "transfer" },
];

function paymentName(id) {
  return METODOS_PAGO.find((m) => m.id === id)?.nombre || id;
}

function paymentChip(id) {
  return `<span class="chip"><span class="dot" style="background:var(--pm-${id})"></span>${escapeHtml(paymentName(id))}</span>`;
}

// ---------- Íconos (trazos de línea, estilo Lucide) ----------

const ICONS = {
  search: "M11 3a8 8 0 1 0 0 16a8 8 0 1 0 0-16zM21 21l-4.3-4.3",
  plus: "M12 5v14M5 12h14",
  minus: "M5 12h14",
  x: "M18 6L6 18M6 6l12 12",
  check: "M20 6L9 17l-5-5",
  trash: "M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6M10 11v6M14 11v6",
  edit: "M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1l1-4z",
  history: "M3 12a9 9 0 1 0 9-9a9.7 9.7 0 0 0-6.7 2.7L3 8M3 3v5h5M12 7v5l4 2",
  clock: "M12 2a10 10 0 1 0 0 20a10 10 0 1 0 0-20zM12 6v6l4 2",
  receipt: "M4 2v20l2-1l2 1l2-1l2 1l2-1l2 1l2-1l2 1V2l-2 1l-2-1l-2 1l-2-1l-2 1l-2-1l-2 1zM8 8h8M8 12h8M8 16h5",
  logout: "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5l-5-5M21 12H9",
  sun: "M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8zM12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M6.3 17.7l-1.4 1.4M19.1 4.9l-1.4 1.4",
  moon: "M12 3a6 6 0 0 0 9 9a9 9 0 1 1-9-9z",
  chevron: "M6 9l6 6l6-6",
  left: "M15 18l-6-6l6-6",
  right: "M9 18l6-6l-6-6",
  panel: "M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zM9 3v18",
  dashboard: "M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z",
  box: "M16.5 9.4L7.5 4.2M21 16V8a2 2 0 0 0-1-1.7l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.7l7 4a2 2 0 0 0 2 0l7-4a2 2 0 0 0 1-1.7zM3.3 7L12 12l8.7-5M12 22V12",
  users: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 3a4 4 0 1 0 0 8a4 4 0 1 0 0-8zM22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8",
  shield: "M12 22s8-4 8-10V5l-8-3l-8 3v7c0 6 8 10 8 10zM12 8a2 2 0 1 0 0 4a2 2 0 1 0 0-4zM8.5 16a3.5 3.5 0 0 1 7 0",
  store: "M3 9l1-5h16l1 5M3 9h18v2a3 3 0 0 1-6 0a3 3 0 0 1-6 0a3 3 0 0 1-6 0zM5 13v8h14v-8M10 21v-5h4v5",
  user: "M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2M12 3a4 4 0 1 0 0 8a4 4 0 1 0 0-8z",
  lock: "M5 11h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2zM7 11V7a5 5 0 0 1 10 0v4",
  eye: "M2 12s3.5-7 10-7s10 7 10 7s-3.5 7-10 7S2 12 2 12zM12 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6z",
  eyeoff: "M10.7 5.1A10 10 0 0 1 22 12a13 13 0 0 1-1.7 2.7M6.6 6.6A13.5 13.5 0 0 0 2 12s3.5 7 10 7a9.7 9.7 0 0 0 5.4-1.6M9.9 9.9a3 3 0 1 0 4.2 4.2M2 2l20 20",
  alert: "M12 2a10 10 0 1 0 0 20a10 10 0 1 0 0-20zM12 8v4M12 16h.01",
  info: "M12 2a10 10 0 1 0 0 20a10 10 0 1 0 0-20zM12 16v-4M12 8h.01",
  print: "M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2M6 14h12v8H6z",
  download: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5l5-5M12 15V3",
  calendar: "M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zM16 2v4M8 2v4M3 10h18",
  money: "M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6",
  ticket: "M3 7h18v10H3zM7 7v10M17 7v10",
  cash: "M4 6h16a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2zM12 10a2 2 0 1 0 0 4a2 2 0 1 0 0-4zM6 12h.01M18 12h.01",
  phone: "M7 2h10a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zM12 18h.01",
  wallet: "M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4",
  card: "M4 5h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2zM2 10h20",
  cardc: "M4 5h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2zM2 10h20M6 15h4",
  transfer: "M8 3L4 7l4 4M4 7h16M16 21l4-4l-4-4M20 17H4",
  spark: "M13 2L3 14h9l-1 8l10-12h-9z",
};

function icon(name, size = 18, width = 1.8) {
  return `<svg class="i" viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="${width}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${ICONS[name]}"/></svg>`;
}

// Isotipo de Pan del Valle (espiga dentro de un sello).
function logo(size = 36) {
  return `<svg viewBox="0 0 64 64" width="${size}" height="${size}" aria-hidden="true" style="flex:none"><circle cx="32" cy="32" r="31" fill="#9A4A22"/><path d="M32 51V20" stroke="#FBF8F3" stroke-width="3.4" stroke-linecap="round"/><g fill="#E3A44A"><ellipse cx="32" cy="15.5" rx="3.6" ry="5.6"/><ellipse cx="26.6" cy="25" rx="3.6" ry="5.6" transform="rotate(-38 26.6 25)"/><ellipse cx="37.4" cy="25" rx="3.6" ry="5.6" transform="rotate(38 37.4 25)"/><ellipse cx="26.6" cy="34.5" rx="3.6" ry="5.6" transform="rotate(-38 26.6 34.5)"/><ellipse cx="37.4" cy="34.5" rx="3.6" ry="5.6" transform="rotate(38 37.4 34.5)"/></g></svg>`;
}

// ---------- Fotos de productos ----------
// Las fotos viven en /img/productos/<id>.jpg. FOTOS_PRODUCTOS (js/fotos.js) dice cuáles existen,
// así no se piden imágenes que no están. Sin foto se dibuja una ilustración con el color de la categoría.

function productPlaceholder(producto) {
  const c = categoryColor(producto.categoria);
  const letra = escapeHtml((producto.nombre || "?")[0].toUpperCase());
  return `<svg viewBox="0 0 160 120" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" aria-hidden="true" style="display:block">
    <rect width="160" height="120" fill="${c}" opacity="0.16"/>
    <circle cx="128" cy="18" r="34" fill="${c}" opacity="0.12"/>
    <ellipse cx="80" cy="92" rx="46" ry="7" fill="${c}" opacity="0.18"/>
    <circle cx="80" cy="58" r="30" fill="${c}" opacity="0.85"/>
    <text x="80" y="69" text-anchor="middle" font-size="30" font-weight="800" fill="#fff" font-family="Plus Jakarta Sans, system-ui, sans-serif">${letra}</text>
  </svg>`;
}

function hasPhoto(id) {
  return typeof FOTOS_PRODUCTOS !== "undefined" && FOTOS_PRODUCTOS.has(Number(id));
}

function productImage(producto, cls = "") {
  if (hasPhoto(producto.id_producto)) {
    return `<img class="${cls}" src="/img/productos/${producto.id_producto}.jpg" alt="" loading="lazy">`;
  }
  return cls ? `<span class="${cls}" style="overflow:hidden">${productPlaceholder(producto)}</span>` : productPlaceholder(producto);
}

// ---------- Tema claro / oscuro ----------

const THEME_KEY = "panaderia-pos-tema";

function getTheme() {
  try {
    return localStorage.getItem(THEME_KEY) || "light";
  } catch {
    return "light";
  }
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem(THEME_KEY, theme); } catch { /* sin almacenamiento */ }
  $$("[data-theme-toggle]").forEach((b) => {
    b.innerHTML = icon(theme === "dark" ? "sun" : "moon", 20);
    b.setAttribute("aria-label", theme === "dark" ? "Cambiar a modo claro" : "Cambiar a modo oscuro");
    b.title = b.getAttribute("aria-label");
  });
  document.dispatchEvent(new CustomEvent("themechange"));
}

function toggleTheme() {
  applyTheme(getTheme() === "dark" ? "light" : "dark");
}

document.documentElement.dataset.theme = getTheme();
document.addEventListener("click", (e) => {
  if (e.target.closest("[data-theme-toggle]")) toggleTheme();
});

// ---------- Avisos ----------

function toast(message, type = "ok") {
  let box = $(".toasts");
  if (!box) {
    box = document.createElement("div");
    box.className = "toasts";
    box.setAttribute("role", "status");
    box.setAttribute("aria-live", "polite");
    document.body.appendChild(box);
  }
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  t.innerHTML = `<span class="ti">${icon(type === "ok" ? "check" : "alert", 15, 2.4)}</span><span>${escapeHtml(message)}</span>`;
  box.appendChild(t);
  setTimeout(() => t.remove(), type === "ok" ? 3200 : 5200);
}

// ---------- Panel lateral (drawer) ----------
// openDrawer(html) muestra un panel a la derecha; devuelve el elemento. Se cierra con Esc, la X o el fondo.

function closeDrawer() {
  $$(".backdrop, .drawer").forEach((el) => el.remove());
  document.removeEventListener("keydown", _drawerEsc);
}

function _drawerEsc(e) {
  if (e.key === "Escape") closeDrawer();
}

function openDrawer(html, label = "Panel") {
  closeDrawer();
  const back = document.createElement("div");
  back.className = "backdrop";
  back.addEventListener("click", closeDrawer);
  const drawer = document.createElement("aside");
  drawer.className = "drawer";
  drawer.setAttribute("role", "dialog");
  drawer.setAttribute("aria-modal", "true");
  drawer.setAttribute("aria-label", label);
  drawer.innerHTML = html;
  drawer.addEventListener("click", (e) => {
    if (e.target.closest("[data-close]")) closeDrawer();
  });
  document.body.append(back, drawer);
  document.addEventListener("keydown", _drawerEsc);
  setTimeout(() => drawer.querySelector("input, select, button:not([data-close])")?.focus(), 50);
  return drawer;
}

function drawerHead(titulo, subtitulo = "") {
  return `<div class="drawer-head"><div><span class="t">${escapeHtml(titulo)}</span><span class="s num">${escapeHtml(subtitulo)}</span></div>
    <button class="ibtn" type="button" data-close aria-label="Cerrar panel">${icon("x", 20, 2)}</button></div>`;
}

// ---------- Estructura del administrador ----------

const ADMIN_NAV = [
  { id: "dashboard", label: "Dashboard", href: "/admin/dashboard.html", icon: "dashboard" },
  { id: "reportes", label: "Reportes (Spark)", href: "/admin/reportes.html", icon: "spark" },
  { id: "catalogo", label: "Catálogo", href: "/admin/catalogo.html", icon: "box" },
  { id: "clientes", label: "Clientes", href: "/admin/clientes.html", icon: "users" },
  { id: "historial", label: "Historial de ventas", href: "/admin/historial.html", icon: "receipt" },
  { id: "usuarios", label: "Usuarios", href: "/admin/usuarios.html", icon: "shield" },
];

const SIDE_KEY = "panaderia-pos-barra";

// Dibuja la barra lateral dentro de <nav class="side" id="side"> y devuelve la sesión.
function renderAdminShell(activo) {
  const session = requireRole("admin");
  const shell = $(".shell");
  try { if (localStorage.getItem(SIDE_KEY) === "col") shell.classList.add("col"); } catch { /* */ }

  $("#side").innerHTML = `
    <div class="brand">${logo(36)}<div class="hide"><b>Pan del Valle</b><span>Panadería · Cafetería</span></div></div>
    <span class="side-label hide">Administración</span>
    ${ADMIN_NAV.map((n) => `<a class="nav ${n.id === activo ? "on" : ""}" href="${n.href}" title="${n.label}" ${n.id === activo ? 'aria-current="page"' : ""}>${icon(n.icon, 20)}<span class="hide">${n.label}</span></a>`).join("")}
    <div style="flex:1;min-height:24px"></div>
    <div style="display:flex;gap:4px;justify-content:space-between">
      <button class="ibtn" type="button" id="toggle-side" title="Colapsar barra lateral" aria-label="Colapsar barra lateral">${icon("panel", 20)}</button>
      <button class="ibtn hide" type="button" data-theme-toggle></button>
    </div>
    <div class="side-user"><span class="av solid">${escapeHtml(initials(session.nombre))}</span>
      <div class="hide" style="min-width:0"><b>${escapeHtml(session.nombre)}</b><span>Administrador</span></div></div>
    <button class="nav" type="button" id="logout" title="Cerrar sesión">${icon("logout", 20)}<span class="hide">Cerrar sesión</span></button>`;

  $("#toggle-side").addEventListener("click", () => {
    shell.classList.toggle("col");
    try { localStorage.setItem(SIDE_KEY, shell.classList.contains("col") ? "col" : "open"); } catch { /* */ }
  });
  $("#logout").addEventListener("click", logout);
  applyTheme(getTheme());
  return session;
}

// Paginador: devuelve HTML con botones; onPage(n) se llama al hacer clic.
function pagerHtml(page, pages) {
  if (pages <= 1) return "";
  const nums = new Set([1, pages, page - 1, page, page + 1].filter((n) => n >= 1 && n <= pages));
  let html = `<button class="pg" type="button" data-page="${page - 1}" ${page === 1 ? "disabled" : ""} aria-label="Página anterior">${icon("left", 16, 2)}</button>`;
  let prev = 0;
  [...nums].sort((a, b) => a - b).forEach((n) => {
    if (n - prev > 1) html += `<span class="muted">…</span>`;
    html += `<button class="pg num ${n === page ? "on" : ""}" type="button" data-page="${n}" ${n === page ? 'aria-current="page"' : ""}>${formatNumber(n)}</button>`;
    prev = n;
  });
  html += `<button class="pg" type="button" data-page="${page + 1}" ${page === pages ? "disabled" : ""} aria-label="Página siguiente">${icon("right", 16, 2)}</button>`;
  return html;
}

// Descarga un CSV (separado por ; para que Excel en español lo abra bien).
function downloadCsv(nombre, filas) {
  const texto = filas.map((f) => f.map((c) => `"${String(c ?? "").replace(/"/g, '""')}"`).join(";")).join("\r\n");
  const url = URL.createObjectURL(new Blob(["﻿" + texto], { type: "text/csv;charset=utf-8" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: nombre });
  a.click();
  URL.revokeObjectURL(url);
}

// ---------- Recibo ----------
// Lo usan la caja (al cobrar) y el historial (reimprimir).

function reciboHtml(venta, recibido = null, cajeroNombre = venta.cajero) {
  return `<div class="receipt print-area">
    <div class="rhead"><b style="font-size:16px">Pan del Valle</b>
      <span class="muted" style="font-size:12px">Panadería · Cafetería · NIT 901.482.337-5</span>
      <span class="muted" style="font-size:12px">Cra. 24 # 5-31, San Fernando, Cali</span></div>
    <div class="rrow num"><span>Venta</span><b>N.º ${formatNumber(venta.id_venta)}</b></div>
    <div class="rrow"><span>Fecha</span><span>${formatDateTime(venta.fecha)}</span></div>
    <div class="rrow"><span>Cajero</span><span>${escapeHtml(cajeroNombre || "—")}</span></div>
    <div class="rrow"><span>Cliente</span><span>${escapeHtml(venta.cliente.nombre)}</span></div>
    <div class="ritems">${venta.lineas.map((l) => `<div class="rrow num"><span style="color:var(--text)">${l.cantidad} × ${escapeHtml(l.producto)}</span><span style="font-weight:600">${formatMoney(l.subtotal)}</span></div>`).join("")}</div>
    <div class="rrow num" style="font-size:18px"><b>Total</b><b>${formatMoney(venta.total)}</b></div>
    <div class="rrow"><span>Método de pago</span><span style="font-weight:600">${escapeHtml(paymentName(venta.metodo_pago))}</span></div>
    ${recibido !== null ? `<div class="rrow num"><span>Recibido · Cambio</span><span>${formatMoney(recibido)} · ${formatMoney(recibido - venta.total)}</span></div>` : ""}
    <div class="muted" style="font-size:12px;text-align:center;padding-top:6px">¡Gracias por su compra!</div>
  </div>`;
}
