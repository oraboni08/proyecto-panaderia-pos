"""Recorta las cuadrículas de fotos de productos y genera frontend/js/fotos.js.

Cada lote_NN.png es una cuadrícula de 3 x 3 (lote N, casilla k de izquierda a derecha
y de arriba abajo → producto (N - 1) * 9 + k). Un archivo producto_<id>.png reemplaza
la casilla de ese producto.

Uso:
    python frontend/img/recortar_fotos.py "C:/ruta/a/fotos_productos"

Requiere Pillow (pip install pillow).
"""

import re
import sys
from pathlib import Path

from PIL import Image

LADO = 480          # las fotos se guardan cuadradas de 480 px
RECORTE_BORDE = 0.015  # se quita un poco del borde de cada casilla por si la cuadrícula no es exacta

FRONTEND = Path(__file__).resolve().parent.parent
DESTINO = FRONTEND / "img" / "productos"
FOTOS_JS = FRONTEND / "js" / "fotos.js"


def guardar(imagen: Image.Image, id_producto: int) -> None:
    imagen = imagen.convert("RGB")
    ancho, alto = imagen.size
    lado = min(ancho, alto)
    imagen = imagen.crop(((ancho - lado) // 2, (alto - lado) // 2, (ancho + lado) // 2, (alto + lado) // 2))
    imagen = imagen.resize((LADO, LADO), Image.LANCZOS)
    imagen.save(DESTINO / f"{id_producto}.jpg", "JPEG", quality=82, optimize=True, progressive=True)


def main(origen: Path) -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    ids = set()

    for archivo in sorted(origen.glob("lote_*.png")):
        lote = int(re.search(r"lote_(\d+)", archivo.stem).group(1))
        cuadricula = Image.open(archivo)
        celda_w = cuadricula.width / 3
        celda_h = cuadricula.height / 3
        mx, my = celda_w * RECORTE_BORDE, celda_h * RECORTE_BORDE

        for fila in range(3):
            for col in range(3):
                id_producto = (lote - 1) * 9 + fila * 3 + col + 1
                caja = (
                    round(col * celda_w + mx), round(fila * celda_h + my),
                    round((col + 1) * celda_w - mx), round((fila + 1) * celda_h - my),
                )
                guardar(cuadricula.crop(caja), id_producto)
                ids.add(id_producto)
        print(f"{archivo.name}: productos {(lote - 1) * 9 + 1} a {lote * 9}")

    for archivo in sorted(origen.glob("producto_*.png")):
        id_producto = int(re.search(r"producto_(\d+)", archivo.stem).group(1))
        guardar(Image.open(archivo), id_producto)
        ids.add(id_producto)
        print(f"{archivo.name}: reemplaza la foto del producto {id_producto}")

    lista = ", ".join(str(i) for i in sorted(ids))
    FOTOS_JS.write_text(
        "// Productos que tienen foto en /img/productos/<id>.jpg.\n"
        "// Este archivo lo regenera el script que recorta las fotos (frontend/img/recortar_fotos.py).\n"
        f"const FOTOS_PRODUCTOS = new Set([{lista}]);\n",
        encoding="utf-8",
    )
    print(f"{len(ids)} fotos en {DESTINO}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
