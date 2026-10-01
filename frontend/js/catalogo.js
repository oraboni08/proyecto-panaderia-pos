requireRole("admin");
renderAdminSidebar("catalogo");

const mensaje = $("#mensaje");
const formError = $("#form-error");
const modal = setupModal("#modal");

let productos = [];
let editando = null; // producto en edición, o null si es nuevo

function filtrados() {
  const texto = $("#buscar").value.trim().toLowerCase();
  const estado = $("#filtro-estado").value;
  const tipo = $("#filtro-tipo").value;

  return productos.filter(
    (p) =>
      (!texto || p.nombre.toLowerCase().includes(texto)) &&
      (!estado || (estado === "activos") === p.activo) &&
      (!tipo || p.tipo_venta === tipo)
  );
}

function render() {
  const lista = filtrados();
  const activos = productos.filter((p) => p.activo).length;
  $("#conteo").textContent = `${productos.length} productos · ${activos} activos`;

  $("#tabla").innerHTML = lista.length
    ? lista
        .map(
          (p) => `<tr>
            <td class="hint">${p.id_producto}</td>
            <td><strong>${escapeHtml(p.nombre)}</strong></td>
            <td class="num">${formatPrice(p)}</td>
            <td>${p.tipo_venta === "peso" ? "⚖️ Por peso" : "🔢 Por unidad"}</td>
            <td>${p.activo ? '<span class="badge badge-success">Activo</span>' : '<span class="badge badge-muted">Inactivo</span>'}</td>
            <td class="num">
              <button class="btn btn-outline btn-sm" data-editar="${p.id_producto}">Editar</button>
              ${
                p.activo
                  ? `<button class="btn btn-danger-outline btn-sm" data-estado="${p.id_producto}" data-activo="false">Desactivar</button>`
                  : `<button class="btn btn-outline btn-sm" data-estado="${p.id_producto}" data-activo="true">Reactivar</button>`
              }
            </td>
          </tr>`
        )
        .join("")
    : `<tr><td colspan="6" class="empty">No hay productos con esos filtros</td></tr>`;
}

async function cargar() {
  try {
    productos = await api("catalog", "/products");
    render();
  } catch (error) {
    showAlert(mensaje, error.message);
  }
}

function actualizarEtiquetaPrecio() {
  $("#precio-label").textContent =
    $("#tipo_venta").value === "peso" ? "Precio por kg (€)" : "Precio por unidad (€)";
}

function abrirFormulario(producto = null) {
  editando = producto;
  hideAlert(formError);
  $("#form-titulo").textContent = producto ? `Editar: ${producto.nombre}` : "Nuevo producto";
  $("#nombre").value = producto ? producto.nombre : "";
  $("#precio").value = producto ? producto.precio : "";
  $("#tipo_venta").value = producto ? producto.tipo_venta : "unidad";
  actualizarEtiquetaPrecio();
  modal.open();
  $("#nombre").focus();
}

$("#form").addEventListener("submit", async (event) => {
  event.preventDefault();
  hideAlert(formError);

  const body = {
    nombre: $("#nombre").value.trim(),
    precio: parseFloat($("#precio").value),
    tipo_venta: $("#tipo_venta").value,
  };

  // Validación de forma; las reglas (nombre repetido, etc.) las valida el back-end.
  if (!body.nombre) return showAlert(formError, "Escribe el nombre del producto.");
  if (!(body.precio > 0)) return showAlert(formError, "El precio debe ser un número mayor que 0.");

  $("#guardar").disabled = true;

  try {
    if (editando) {
      await api("catalog", `/products/${editando.id_producto}`, { method: "PUT", body });
      showAlert(mensaje, `Producto "${body.nombre}" actualizado.`, "success");
    } else {
      await api("catalog", "/products", { method: "POST", body });
      showAlert(mensaje, `Producto "${body.nombre}" creado.`, "success");
    }
    modal.close();
    await cargar();
  } catch (error) {
    showAlert(formError, error.message);
  } finally {
    $("#guardar").disabled = false;
  }
});

$("#tabla").addEventListener("click", async (event) => {
  const editar = event.target.closest("[data-editar]");
  const estado = event.target.closest("[data-estado]");

  if (editar) {
    abrirFormulario(productos.find((p) => p.id_producto === Number(editar.dataset.editar)));
  }

  if (estado) {
    const id = Number(estado.dataset.estado);
    const activo = estado.dataset.activo === "true";
    const producto = productos.find((p) => p.id_producto === id);

    try {
      await api("catalog", `/products/${id}`, { method: "PATCH", body: { activo } });
      showAlert(mensaje, `"${producto.nombre}" ${activo ? "reactivado" : "desactivado"}.`, "success");
      await cargar();
    } catch (error) {
      showAlert(mensaje, error.message);
    }
  }
});

$("#nuevo").addEventListener("click", () => abrirFormulario());
$("#tipo_venta").addEventListener("change", actualizarEtiquetaPrecio);
["#buscar", "#filtro-estado", "#filtro-tipo"].forEach((s) => $(s).addEventListener("input", render));

cargar();
