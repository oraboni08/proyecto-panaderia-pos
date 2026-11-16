// Gráficas SVG compartidas por el Dashboard y los Reportes (sin librerías; colores del tema).

// Muestra un cuadro con el detalle al pasar el mouse sobre un elemento con data-tip.
function conTooltip(cont) {
  let tip = cont.querySelector(".tip");
  if (!tip) {
    tip = document.createElement("div");
    tip.className = "tip";
    tip.hidden = true;
    cont.appendChild(tip);
  }
  cont.onmousemove = (e) => {
    const t = e.target.closest("[data-tip]");
    if (!t) { tip.hidden = true; return; }
    tip.innerHTML = t.dataset.tip;
    tip.hidden = false;
    const r = cont.getBoundingClientRect();
    const x = Math.min(Math.max(e.clientX - r.left - tip.offsetWidth / 2, 0), r.width - tip.offsetWidth);
    tip.style.left = `${x}px`;
    tip.style.top = `${e.clientY - r.top - tip.offsetHeight - 14}px`;
  };
  cont.onmouseleave = () => (tip.hidden = true);
}

function ejeY(max, pasos = 4) {
  const bruto = max / pasos;
  const mag = 10 ** Math.floor(Math.log10(bruto || 1));
  const paso = [1, 2, 2.5, 5, 10].map((f) => f * mag).find((f) => f >= bruto) || bruto;
  return Array.from({ length: pasos + 1 }, (_, i) => i * paso);
}

function vacio(el, texto = "No hay ventas en este periodo") {
  el.innerHTML = `<div class="empty" style="padding:40px 16px">${icon("info", 30, 1.5)}<span>${texto}</span></div>`;
}

// Barras verticales. items: [{label, valor, tip, destacar}]
function barras(el, items, fmtEje) {
  if (!items.some((i) => i.valor > 0)) return vacio(el);
  const W = 560, H = 230, L = 46, B = 26, T = 22;
  const ticks = ejeY(Math.max(...items.map((i) => i.valor)));
  const top = ticks[ticks.length - 1];
  const ancho = (W - L) / items.length;
  const y = (v) => H - B - (v / top) * (H - B - T);
  el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Gráfica de barras">
    ${ticks.map((t) => `<line x1="${L}" x2="${W}" y1="${y(t)}" y2="${y(t)}" style="stroke:var(--grid)"/><text x="${L - 8}" y="${y(t) + 4}" text-anchor="end" font-size="11" style="fill:var(--muted)">${fmtEje(t)}</text>`).join("")}
    ${items.map((it, i) => {
      const x = L + i * ancho + ancho * 0.18;
      const w = ancho * 0.64;
      const yy = y(it.valor);
      return `<g data-tip="${escapeHtml(it.tip)}" style="cursor:default">
        <rect x="${L + i * ancho}" y="${T}" width="${ancho}" height="${H - B - T}" fill="transparent"/>
        <rect x="${x}" y="${yy}" width="${w}" height="${Math.max(H - B - yy, 0)}" rx="4" style="fill:${it.destacar ? "var(--primary)" : "var(--bar-soft)"}"/>
        ${it.nota ? `<text x="${x + w / 2}" y="${yy - 7}" text-anchor="middle" font-size="11" font-weight="700" style="fill:var(--primary)">${it.nota}</text>` : ""}
        <text x="${x + w / 2}" y="${H - 8}" text-anchor="middle" font-size="11" style="fill:var(--muted)">${it.label}</text>
      </g>`;
    }).join("")}
  </svg>`;
  conTooltip(el);
}
