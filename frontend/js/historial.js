requireRole("admin");
renderAdminSidebar("historial");

const errorBox = $("#error");

const ACCIONES = {
  CREAR: '<span class="badge badge-success">Creado</span>',
  EDITAR: '<span class="badge">Editado</span>',
  DESACTIVAR: '<span class="badge badge-danger">Desactivado</span>',
  REACTIVAR: '<span class="badge badge-success">Reactivado</span>',
};

const CAMPOS = { nombre: "Nombre", precio: "Precio", tipo_venta: "Tipo de venta", activo: "Estado" };

async function cargarProductos() {
  const productos = await api("catalog", "/products");
  $("#producto").innerHTML += productos
    .map((p) => `<option value="${p.id_producto}">${escapeHtml(p.nombre)}</option>`)
    .join("");
}

async function cargarHistorial() {
  hideAlert(errorBox);

  try {
    const cambios = await api("catalog", "/changes", { params: { product_id: $("#producto").value } });

    $("#tabla").innerHTML = cambios.length
      ? cambios
          .map(
            (c) => `<tr>
              <td style="white-space:nowrap">${formatDateTime(c.fecha)}</td>
              <td><strong>${escapeHtml(c.producto)}</strong></td>
              <td>${ACCIONES[c.accion] || c.accion}</td>
              <td>${c.campo ? CAMPOS[c.campo] || c.campo : "—"}</td>
              <td class="hint">${escapeHtml(c.valor_anterior ?? "")}</td>
              <td class="hint">${c.valor_anterior ? "→" : ""}</td>
              <td><strong>${escapeHtml(c.valor_nuevo)}</strong></td>
              <td>${escapeHtml(c.usuario)}</td>
            </tr>`
          )
          .join("")
      : `<tr><td colspan="8" class="empty">Todavía no hay cambios registrados</td></tr>`;
  } catch (error) {
    showAlert(errorBox, error.message);
  }
}

$("#producto").addEventListener("change", cargarHistorial);

cargarProductos().catch((e) => showAlert(errorBox, e.message));
cargarHistorial();
