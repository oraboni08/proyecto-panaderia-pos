"""Genera el dataset de la Panadería POS: productos colombianos, clientes y ventas.

Uso (desde la carpeta backend):

    python dataset/generar_dataset.py                 # escribe los CSV en backend/dataset
    python dataset/generar_dataset.py --hasta 2026-11-15

Siempre produce exactamente los mismos datos (semilla fija), así todo el equipo
trabaja con la misma base. Archivos que genera (separador ';', UTF-8):

    productos.csv          catálogo actual: id, nombre, categoría y precio en pesos (COP)
    cambios_producto.csv   historial de catálogo: creación, alza de precios de 2026, temporadas
    clientes.csv           clientes registrados con sus datos (cédula, teléfono, correo, dirección)
    ventas.csv             encabezado de cada venta: fecha y hora, cliente, cajero, método de pago
    lineas_venta.csv       productos de cada venta (cantidad en unidades, precio del momento)

Precios: referencia de cartas de panaderías colombianas 2025-2026 (p. ej. Panadería del
Pandebono: pandebono $3.250, almojábana $3.550, buñuelo $1.850, pastel de pollo $6.550),
ajustados a una panadería de barrio en Cali. Todo se vende POR UNIDAD (no por peso).
"""

import argparse
import csv
import math
import random
import unicodedata
from datetime import date, datetime, time, timedelta
from pathlib import Path

SEMILLA = 2026
DESDE = date(2025, 1, 2)
HASTA = date(2026, 11, 15)
ALZA_2026 = date(2026, 1, 12)          # día en que se actualizaron los precios de 2026
FACTOR_ALZA = 1.065                     # alza de precios 2025 -> 2026 (≈ inflación de alimentos)
NUM_CLIENTES = 3200

DIR = Path(__file__).resolve().parent

# --------------------------------------------------------------------------------------
# Catálogo: (nombre, categoría, precio 2026 en COP, popularidad, franjas donde más se vende)
#   franjas: d = desayuno (6-10 h), m = mediodía (11-14 h), o = onces (15-18 h), n = noche (18-21 h)
# --------------------------------------------------------------------------------------
PRODUCTOS = [
    # Panadería de queso y almidón (lo más vendido en Cali)
    ("Pandebono", "Panadería de queso", 3200, 100, "dmo"),
    ("Pandebono relleno de bocadillo", "Panadería de queso", 3800, 25, "do"),
    ("Almojábana", "Panadería de queso", 3300, 55, "do"),
    ("Pan de yuca", "Panadería de queso", 3000, 40, "do"),
    ("Buñuelo", "Panadería de queso", 1800, 45, "do"),
    ("Pandequeso", "Panadería de queso", 3000, 22, "do"),
    ("Palito de queso", "Panadería de queso", 3000, 30, "dmo"),
    ("Rosquitas de queso (paquete)", "Panadería de queso", 4500, 10, "on"),
    # Panes
    ("Pan aliñado", "Panes", 1800, 50, "dn"),
    ("Pan aliñado grande", "Panes", 7500, 14, "n"),
    ("Pan francés", "Panes", 4500, 18, "mn"),
    ("Pan tajado blanco", "Panes", 8500, 16, "n"),
    ("Pan tajado integral", "Panes", 9500, 10, "n"),
    ("Mogolla integral", "Panes", 1200, 28, "dn"),
    ("Mogolla chicharrona", "Panes", 1500, 20, "dn"),
    ("Pan coco", "Panes", 2000, 18, "do"),
    ("Pan de leche", "Panes", 2200, 18, "dn"),
    ("Pan campesino", "Panes", 2400, 14, "dn"),
    ("Pan bolita", "Panes", 800, 30, "dn"),
    ("Pan de maíz", "Panes", 2400, 10, "do"),
    ("Pan hawaiano", "Panes", 15000, 4, "n"),
    ("Pan de queso grande", "Panes", 7500, 8, "on"),
    ("Roscón de bocadillo", "Panes", 3500, 22, "do"),
    ("Roscón de arequipe", "Panes", 3500, 18, "do"),
    # Hojaldres y pasteles
    ("Pastel de pollo", "Hojaldres", 6000, 35, "mo"),
    ("Pastel de carne", "Hojaldres", 6000, 22, "mo"),
    ("Pastel de jamón y queso", "Hojaldres", 4000, 25, "dmo"),
    ("Pastel de queso", "Hojaldres", 3800, 18, "do"),
    ("Pastel gloria", "Hojaldres", 3500, 20, "o"),
    ("Pastel de guayaba", "Hojaldres", 3200, 18, "o"),
    ("Pastel de arequipe", "Hojaldres", 3200, 14, "o"),
    ("Croissant", "Hojaldres", 4000, 20, "do"),
    ("Croissant de jamón y queso", "Hojaldres", 6500, 16, "dm"),
    ("Croissant de chocolate", "Hojaldres", 3500, 12, "o"),
    ("Palito de salchicha", "Hojaldres", 4000, 16, "mo"),
    ("Milhoja", "Hojaldres", 4500, 10, "o"),
    # Salados y comidas rápidas
    ("Empanada de carne", "Salados", 3000, 35, "mo"),
    ("Empanada de pollo", "Salados", 3000, 28, "mo"),
    ("Aborrajado", "Salados", 4500, 12, "mo"),
    ("Papa rellena", "Salados", 4000, 14, "mo"),
    ("Arepa de choclo con queso", "Salados", 6000, 14, "do"),
    ("Sándwich de jamón y queso", "Salados", 9000, 12, "m"),
    ("Tamal vallecaucano", "Salados", 13000, 6, "d"),
    # Desayunos
    ("Desayuno tradicional", "Desayunos", 14000, 12, "d"),
    ("Huevos pericos con arepa", "Desayunos", 9500, 12, "d"),
    ("Changua", "Desayunos", 11000, 4, "d"),
    ("Calentado con huevo", "Desayunos", 15000, 7, "d"),
    # Tortas y postres
    ("Porción torta de chocolate", "Tortas y postres", 6500, 14, "o"),
    ("Porción torta de zanahoria", "Tortas y postres", 6500, 10, "o"),
    ("Porción tres leches", "Tortas y postres", 7000, 14, "o"),
    ("Porción torta María Luisa", "Tortas y postres", 5500, 9, "o"),
    ("Porción torta negra", "Tortas y postres", 6500, 5, "o"),
    ("Chifón de naranja", "Tortas y postres", 3200, 10, "o"),
    ("Brownie", "Tortas y postres", 4200, 12, "o"),
    ("Pionono", "Tortas y postres", 4200, 8, "o"),
    ("Arroz con leche", "Tortas y postres", 4000, 9, "mo"),
    ("Natilla (porción)", "Tortas y postres", 3500, 6, "on"),
    ("Torta de cumpleaños (libra)", "Tortas y postres", 48000, 2, "o"),
    # Galletas y dulces
    ("Galleta de mantequilla", "Galletas y dulces", 1100, 14, "o"),
    ("Galleta de avena", "Galletas y dulces", 2000, 10, "o"),
    ("Alfajor", "Galletas y dulces", 1500, 12, "o"),
    ("Cocada", "Galletas y dulces", 1500, 10, "o"),
    ("Polvorosa", "Galletas y dulces", 1200, 8, "o"),
    ("Mantecada", "Galletas y dulces", 2500, 12, "do"),
    ("Cuca", "Galletas y dulces", 1000, 10, "o"),
    # Bebidas calientes
    ("Tinto", "Bebidas calientes", 1500, 60, "dmo"),
    ("Pintadito", "Bebidas calientes", 2000, 25, "do"),
    ("Café con leche", "Bebidas calientes", 3000, 40, "do"),
    ("Capuchino", "Bebidas calientes", 4500, 14, "do"),
    ("Chocolate en leche", "Bebidas calientes", 4000, 28, "do"),
    ("Agua de panela con queso", "Bebidas calientes", 4500, 12, "do"),
    ("Aromática", "Bebidas calientes", 1500, 12, "dno"),
    ("Milo caliente", "Bebidas calientes", 4500, 8, "do"),
    # Bebidas frías
    ("Jugo natural en agua", "Bebidas frías", 6000, 18, "mo"),
    ("Jugo natural en leche", "Bebidas frías", 7000, 14, "mo"),
    ("Lulada", "Bebidas frías", 7500, 10, "mo"),
    ("Champús", "Bebidas frías", 4500, 8, "mo"),
    ("Limonada natural", "Bebidas frías", 5000, 12, "mo"),
    ("Avena", "Bebidas frías", 4000, 22, "dmo"),
    ("Kumis", "Bebidas frías", 4000, 14, "dmo"),
    ("Gaseosa 400 ml", "Bebidas frías", 4000, 30, "mo"),
    ("Gaseosa 1,5 L", "Bebidas frías", 7500, 10, "on"),
    ("Pony Malta", "Bebidas frías", 3500, 16, "mo"),
    ("Agua en botella 600 ml", "Bebidas frías", 2800, 14, "mo"),
    # Lácteos y despensa (lo que la gente lleva para la casa)
    ("Leche entera 1 L", "Lácteos y despensa", 5200, 22, "dn"),
    ("Huevo AA (unidad)", "Lácteos y despensa", 650, 24, "dn"),
    ("Queso campesino 250 g", "Lácteos y despensa", 7500, 10, "n"),
    ("Mantequilla 125 g", "Lácteos y despensa", 5000, 8, "n"),
    ("Arequipe 250 g", "Lácteos y despensa", 6500, 6, "n"),
    ("Yogur con cereal", "Lácteos y despensa", 4800, 10, "dm"),
]

TEMPORADA_NAVIDAD = {"Natilla (porción)", "Porción torta negra"}   # solo en diciembre

# Cantidad típica por línea: la mayoría de productos se lleva de a 1; algunos por varios
CANTIDADES = {
    "Pandebono": [1, 1, 2, 2, 3, 4, 6], "Almojábana": [1, 1, 2, 3, 4], "Pan de yuca": [1, 1, 2, 3],
    "Buñuelo": [1, 2, 2, 3, 4, 6], "Pan aliñado": [1, 2, 3, 4], "Mogolla integral": [2, 3, 4, 6],
    "Mogolla chicharrona": [2, 3, 4, 6], "Pan bolita": [3, 5, 6, 10], "Pan de leche": [1, 2, 4],
    "Pan coco": [1, 2, 3], "Pan campesino": [1, 2, 3], "Tinto": [1, 1, 1, 2, 3], "Pintadito": [1, 1, 2],
    "Café con leche": [1, 1, 2], "Chocolate en leche": [1, 1, 2], "Huevo AA (unidad)": [3, 6, 6, 10, 12, 15, 30],
    "Empanada de carne": [1, 1, 2, 3], "Empanada de pollo": [1, 1, 2, 3], "Galleta de mantequilla": [1, 2, 3, 5],
    "Cuca": [1, 2, 3], "Polvorosa": [1, 2, 4], "Gaseosa 400 ml": [1, 1, 2], "Palito de queso": [1, 1, 2, 3],
}

# --------------------------------------------------------------------------------------
# Personas: nombres y apellidos frecuentes en Colombia (Valle del Cauca)
# --------------------------------------------------------------------------------------
NOMBRES_M = [
    "Juan", "Carlos", "Andrés", "Jorge", "Luis", "José", "Diego", "Santiago", "Sebastián", "Daniel",
    "Alejandro", "Felipe", "Camilo", "Julián", "Mauricio", "Óscar", "Fernando", "Jhon", "Édgar", "Ricardo",
    "Javier", "Alexander", "Cristian", "Esteban", "Mateo", "Samuel", "Nicolás", "David", "Miguel", "Hernán",
    "Gustavo", "Wilson", "Fabio", "Harold", "Jairo", "Álvaro", "Germán", "Iván", "Brayan", "Kevin",
    "Duván", "Yeison", "Jhonatan", "Emiliano", "Tomás", "Martín", "Héctor", "Rubén", "Armando", "Eduardo",
]
NOMBRES_F = [
    "María", "Luisa", "Ana", "Carolina", "Diana", "Paola", "Andrea", "Natalia", "Valentina", "Daniela",
    "Camila", "Laura", "Alejandra", "Juliana", "Mariana", "Sofía", "Isabella", "Gabriela", "Paula", "Catalina",
    "Claudia", "Gloria", "Martha", "Luz", "Sandra", "Patricia", "Adriana", "Liliana", "Marcela", "Ángela",
    "Lorena", "Yolanda", "Rosa", "Beatriz", "Mónica", "Viviana", "Jessica", "Leidy", "Yuliana", "Tatiana",
    "Stefany", "Karen", "Manuela", "Salomé", "Antonella", "Melissa", "Nathalia", "Ximena", "Esperanza", "Amparo",
]
SEGUNDOS_M = ["Andrés", "Felipe", "David", "Alberto", "Eduardo", "José", "Mario", "Antonio", "Camilo", "Esteban"]
SEGUNDOS_F = ["Fernanda", "Alejandra", "Isabel", "Camila", "Andrea", "Patricia", "Cristina", "Lucía", "Victoria", "Elena"]
APELLIDOS = [
    "Rodríguez", "Gómez", "González", "Martínez", "García", "López", "Hernández", "Sánchez", "Ramírez", "Pérez",
    "Díaz", "Muñoz", "Rojas", "Moreno", "Jiménez", "Vargas", "Castro", "Gutiérrez", "Álvarez", "Ortiz",
    "Valencia", "Mosquera", "Rengifo", "Cárdenas", "Ospina", "Quintero", "Zapata", "Caicedo", "Cuero", "Hurtado",
    "Valencia", "Lozano", "Grisales", "Arboleda", "Murillo", "Riascos", "Angulo", "Banguero", "Escobar", "Salazar",
    "Restrepo", "Giraldo", "Marín", "Correa", "Mejía", "Agudelo", "Bedoya", "Londoño", "Castaño", "Ocampo",
    "Herrera", "Castillo", "Torres", "Ruiz", "Mendoza", "Velasco", "Bolaños", "Erazo", "Burbano", "Narváez",
]
BARRIOS_CALI = [
    "San Fernando", "El Peñón", "Granada", "San Antonio", "Tequendama", "El Ingenio", "Ciudad Jardín",
    "Pance", "Capri", "Ciudad Córdoba", "El Limonar", "Champagnat", "Alameda", "San Bosco", "Junín",
    "Santa Mónica", "La Flora", "Versalles", "Chipichape", "Prados del Norte", "Vipasa", "La Merced",
    "Los Guaduales", "Floralia", "Calima", "El Jardín", "Valle del Lili", "Mariano Ramos", "Siloé",
    "Meléndez", "El Refugio", "Caney", "Bochalema", "Las Granjas", "Primero de Mayo", "Unicentro",
    "Ciudad Modelo", "Departamental", "El Templete", "Olímpico", "Lido", "Panamericano", "Cristóbal Colón",
]
OTRAS_CIUDADES = [("Jamundí", ["Ciudad Country", "Alfaguara", "El Rosario"]),
                  ("Yumbo", ["Belalcázar", "Las Américas"]),
                  ("Palmira", ["Zamorano", "Altamira"])]
DOMINIOS = ["gmail.com"] * 8 + ["hotmail.com"] * 3 + ["outlook.com"] * 2 + ["yahoo.com", "icloud.com"]

# Cajeros de la panadería (deben existir en auth-service con rol cajero)
CAJEROS_MANANA = ["mcastillo", "jrengifo"]   # 6:00 - 14:00
CAJEROS_TARDE = ["lvalencia", "dmosquera"]   # 14:00 - 21:00

METODOS_PAGO = ["efectivo", "nequi", "daviplata", "tarjeta_debito", "tarjeta_credito", "transferencia"]


def sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def redondear_100(valor: float) -> int:
    return int(round(valor / 100.0)) * 100


def precio_en(fecha: date, precio_2026: int) -> int:
    """Precio vigente en una fecha: en 2025 (antes del alza) era menor."""
    return precio_2026 if fecha >= ALZA_2026 else redondear_100(precio_2026 / FACTOR_ALZA)


# --------------------------------------------------------------------------------------
# Clientes
# --------------------------------------------------------------------------------------
def generar_clientes(rng: random.Random) -> list[dict]:

    clientes, documentos, correos = [], set(), set()
    dias_totales = (HASTA - DESDE).days

    for i in range(1, NUM_CLIENTES + 1):

        mujer = rng.random() < 0.56
        nombre = rng.choice(NOMBRES_F if mujer else NOMBRES_M)
        if rng.random() < 0.45:
            segundo = rng.choice(SEGUNDOS_F if mujer else SEGUNDOS_M)
            if segundo != nombre:
                nombre = f"{nombre} {segundo}"
        apellido1, apellido2 = rng.choice(APELLIDOS), rng.choice(APELLIDOS)

        # Cédula según la edad: las antiguas del Valle (16, 29-31, 66-67, 94 millones)
        # y las de 10 dígitos que empiezan por 1.1xx para los más jóvenes.
        edad = rng.choices([rng.randint(18, 30), rng.randint(31, 50), rng.randint(51, 78)], [35, 40, 25])[0]
        while True:
            if edad <= 33:
                doc = rng.randint(1_107_000_000, 1_151_999_999)
            elif mujer:
                doc = rng.choice([rng.randint(29_000_000, 31_999_999), rng.randint(66_700_000, 67_099_999)])
            else:
                doc = rng.choice([rng.randint(16_200_000, 16_999_999), rng.randint(94_300_000, 94_599_999)])
            if doc not in documentos:
                documentos.add(doc)
                break

        if rng.random() < 0.88:
            ciudad, barrio = "Cali", rng.choice(BARRIOS_CALI)
        else:
            ciudad, barrios = rng.choice(OTRAS_CIUDADES)
            barrio = rng.choice(barrios)

        via = rng.choice(["Calle", "Carrera", "Calle", "Carrera", "Avenida", "Transversal", "Diagonal"])
        direccion = f"{via} {rng.randint(1, 125)}{rng.choice(['', '', '', 'A', 'B', 'C'])} # " \
                    f"{rng.randint(1, 99)}-{rng.randint(2, 98):02d}"
        if rng.random() < 0.3:
            direccion += f" Apto {rng.randint(1, 18)}{rng.randint(0, 4)}{rng.randint(1, 4)}"

        telefono = f"3{rng.choice(['00', '01', '02', '04', '05', '10', '11', '12', '13', '14', '15', '16', '17', '18', '20', '21', '50', '23'])}" \
                   f"{rng.randint(1_000_000, 9_999_999)}"

        correo = ""
        if rng.random() < 0.82:
            base = sin_tildes(f"{nombre.split()[0]}.{apellido1}").lower().replace(" ", "")
            for intento in range(20):
                sufijo = "" if intento == 0 and rng.random() < 0.4 else str(rng.randint(1, 99) if intento < 10 else rng.randint(100, 9999))
                correo = f"{base}{sufijo}@{rng.choice(DOMINIOS)}"
                if correo not in correos:
                    correos.add(correo)
                    break

        # 35 % ya eran clientes al iniciar el sistema; el resto se registró con el tiempo
        if rng.random() < 0.35:
            registro = DESDE
        else:
            registro = DESDE + timedelta(days=int(dias_totales * (rng.random() ** 1.15)))
        hora_registro = datetime.combine(registro, time(rng.randint(6, 19), rng.randint(0, 59)))

        clientes.append({
            "id_cliente": i,
            "nombre": f"{nombre} {apellido1} {apellido2}",
            "tipo_documento": "CC",
            "documento": str(doc),
            "telefono": telefono,
            "correo": correo,
            "direccion": direccion,
            "barrio": barrio,
            "ciudad": ciudad,
            "fecha_registro": hora_registro.strftime("%Y-%m-%d %H:%M:%S"),
            # Interno (no se escribe): qué tan frecuente es y cuándo empezó a comprar
            # 2 % son "habituales" que pasan casi a diario; el resto compra de vez en cuando
            "_peso": 45.0 if rng.random() < 0.02 else min(rng.lognormvariate(0, 1.1), 12.0),
            "_desde": registro,
            "_mujer": mujer,
        })

    return clientes


# --------------------------------------------------------------------------------------
# Ventas
# --------------------------------------------------------------------------------------
FESTIVOS = {  # festivos de Colombia (abre, pero con más movimiento de familias)
    date(2025, 1, 6), date(2025, 3, 24), date(2025, 4, 17), date(2025, 4, 18), date(2025, 5, 1), date(2025, 6, 2),
    date(2025, 6, 23), date(2025, 6, 30), date(2025, 7, 20), date(2025, 8, 7), date(2025, 8, 18), date(2025, 10, 13),
    date(2025, 11, 3), date(2025, 11, 17), date(2025, 12, 8), date(2025, 12, 25), date(2026, 1, 1), date(2026, 1, 12),
    date(2026, 3, 23), date(2026, 4, 2), date(2026, 4, 3), date(2026, 5, 1), date(2026, 5, 18), date(2026, 6, 8),
    date(2026, 6, 15), date(2026, 6, 29), date(2026, 7, 20), date(2026, 8, 7), date(2026, 8, 17), date(2026, 10, 12),
    date(2026, 11, 2), date(2026, 11, 16),
}

# Distribución de clientes por hora (6:00 a 20:00). Picos: desayuno y onces.
PESO_HORA = {6: 8, 7: 13, 8: 12, 9: 8, 10: 5, 11: 5, 12: 6, 13: 5, 14: 4, 15: 6, 16: 9, 17: 10, 18: 8, 19: 6, 20: 3}


def franja(hora: int) -> str:
    if hora < 11:
        return "d"
    if hora < 15:
        return "m"
    if hora < 18:
        return "o"
    return "n"


def ventas_del_dia(dia: date, rng: random.Random) -> int:
    base = {0: 118, 1: 112, 2: 115, 3: 118, 4: 132, 5: 158, 6: 172}[dia.weekday()]
    if dia in FESTIVOS:
        base = max(base, 160)
    if dia.month == 12:
        base *= 1.30 if dia.day >= 8 else 1.12
    if dia.month == 12 and dia.day in (24, 31):
        base *= 0.75                     # cierran temprano
    if dia.month in (6, 7) or (dia.month == 1 and dia.day < 15):
        base *= 0.93                     # vacaciones: menos movimiento de oficinistas
    meses = (dia.year - DESDE.year) * 12 + dia.month - DESDE.month
    base *= 1 + 0.004 * meses           # la panadería crece ~5 % al año
    return max(30, int(rng.gauss(base, base * 0.08)))


def metodo_pago(rng: random.Random, dia: date, total: int) -> str:
    if dia.year == 2025:
        pesos = [52, 18, 6, 14, 5, 5]
    else:
        pesos = [44, 23, 7, 14, 5, 7]
    if total < 6000:                     # compras pequeñas casi siempre en efectivo o Nequi
        pesos = [pesos[0] * 2.2, pesos[1] * 1.3, pesos[2], pesos[3] * 0.4, pesos[4] * 0.2, pesos[5] * 0.5]
    elif total > 30000:
        pesos = [pesos[0] * 0.6, pesos[1], pesos[2], pesos[3] * 1.5, pesos[4] * 2.2, pesos[5] * 1.4]
    return rng.choices(METODOS_PAGO, pesos)[0]


def cajero_para(dia: date, hora: int) -> str:
    # Turnos que se alternan día a día (y por eso cada semana cambia quién trabaja el sábado).
    turno = CAJEROS_MANANA if hora < 14 else CAJEROS_TARDE
    return turno[dia.toordinal() % 2]


def generar_ventas(rng: random.Random, clientes: list[dict], productos: list[dict]):

    from itertools import accumulate

    por_franja = {f: (productos, list(accumulate(p["_popularidad"] * (3.0 if f in p["_franjas"] else 0.35)
                                                 for p in productos))) for f in "dmon"}
    calientes = [p for p in productos if p["categoria"] == "Bebidas calientes"]
    cum_calientes = list(accumulate(p["_popularidad"] for p in calientes))
    cum_horas = list(accumulate(PESO_HORA.values()))
    horas = list(PESO_HORA)

    ventas, lineas = [], []
    id_venta = 0
    dia = DESDE

    while dia <= HASTA:

        activos = [c for c in clientes if c["_desde"] <= dia]
        cum_clientes = list(accumulate(c["_peso"] for c in activos))
        cantidad = ventas_del_dia(dia, rng)
        hora_cierre = 18 if (dia.month == 12 and dia.day in (24, 31)) else 21

        momentos = []
        for _ in range(cantidad):
            h = rng.choices(horas, cum_weights=cum_horas)[0]
            if h >= hora_cierre:
                h = rng.randint(6, hora_cierre - 1)
            momentos.append(datetime.combine(dia, time(h, rng.randint(0, 59), rng.randint(0, 59))))
        momentos.sort()

        for momento in momentos:

            id_venta += 1
            f = franja(momento.hour)
            candidatos, pesos = por_franja[f]

            # Número de productos distintos en la venta
            n_items = rng.choices([1, 2, 3, 4, 5], [38, 33, 18, 8, 3])[0]
            elegidos = {}
            intentos = 0
            while len(elegidos) < n_items and intentos < 20:
                intentos += 1
                p = rng.choices(candidatos, cum_weights=pesos)[0]
                if p["nombre"] in TEMPORADA_NAVIDAD and dia.month != 12:
                    continue
                if p["nombre"] in elegidos:
                    continue
                elegidos[p["nombre"]] = p

            # En las mañanas casi siempre hay café o chocolate junto al pan
            if f == "d" and rng.random() < 0.35 and not any(p["categoria"] == "Bebidas calientes" for p in elegidos.values()):
                bebida = rng.choices(calientes, cum_weights=cum_calientes)[0]
                elegidos[bebida["nombre"]] = bebida

            total = 0
            filas = []
            for p in elegidos.values():
                cant = rng.choice(CANTIDADES.get(p["nombre"], [1, 1, 1, 1, 2, 2, 3]))
                precio = precio_en(dia, p["precio"])
                subtotal = precio * cant
                total += subtotal
                filas.append({"id_venta": id_venta, "id_producto": p["id_producto"], "cantidad": cant,
                              "precio_unitario": precio, "subtotal": subtotal})

            # 42 % de las ventas son a "Consumidor final" (cliente 0, no se registra)
            if rng.random() < 0.42 or not activos:
                id_cliente = 0
            else:
                id_cliente = rng.choices(activos, cum_weights=cum_clientes)[0]["id_cliente"]

            ventas.append({
                "id_venta": id_venta,
                "fecha": momento.strftime("%Y-%m-%d %H:%M:%S"),
                "id_cliente": id_cliente,
                "cajero": cajero_para(dia, momento.hour),
                "metodo_pago": metodo_pago(rng, dia, total),
                "total": total,
            })
            lineas.extend(filas)

        dia += timedelta(days=1)

    return ventas, lineas


def generar_cambios(productos: list[dict]) -> list[dict]:
    """Historial del catálogo: creación, alza de precios de enero 2026 y productos de temporada."""

    cambios = []
    inicio = datetime.combine(DESDE, time(7, 15))
    alza = datetime.combine(ALZA_2026, time(6, 5))

    for p in productos:
        precio_2025 = redondear_100(p["precio"] / FACTOR_ALZA)
        cambios.append({"id_producto": p["id_producto"], "accion": "CREAR", "campo": "",
                        "valor_anterior": "", "valor_nuevo": f"{p['nombre']} | {p['categoria']} | {precio_2025}",
                        "usuario": "admin", "fecha": inicio.strftime("%Y-%m-%d %H:%M:%S")})
        if precio_2025 != p["precio"]:
            cambios.append({"id_producto": p["id_producto"], "accion": "EDITAR", "campo": "precio",
                            "valor_anterior": str(precio_2025), "valor_nuevo": str(p["precio"]),
                            "usuario": "admin", "fecha": alza.strftime("%Y-%m-%d %H:%M:%S")})

    for p in productos:
        if p["nombre"] in TEMPORADA_NAVIDAD:
            for fecha, accion, ant, nuevo in [
                (datetime(2025, 1, 8, 6, 30), "DESACTIVAR", "activo", "inactivo"),
                (datetime(2025, 12, 1, 6, 30), "REACTIVAR", "inactivo", "activo"),
                (datetime(2026, 1, 8, 6, 30), "DESACTIVAR", "activo", "inactivo"),
            ]:
                cambios.append({"id_producto": p["id_producto"], "accion": accion, "campo": "activo",
                                "valor_anterior": ant, "valor_nuevo": nuevo, "usuario": "admin",
                                "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S")})

    cambios.sort(key=lambda c: c["fecha"])
    return cambios


def escribir(nombre: str, filas: list[dict], columnas: list[str]) -> None:
    with open(DIR / nombre, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columnas, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    print(f"  {nombre:<24} {len(filas):>8,} filas".replace(",", "."))


def main() -> None:

    global HASTA
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hasta", type=date.fromisoformat, default=HASTA, help="último día con ventas (AAAA-MM-DD)")
    HASTA = parser.parse_args().hasta

    rng = random.Random(SEMILLA)

    productos = [
        {"id_producto": i, "nombre": n, "categoria": c, "precio": precio,
         "activo": "false" if n in TEMPORADA_NAVIDAD else "true", "_popularidad": pop, "_franjas": fr}
        for i, (n, c, precio, pop, fr) in enumerate(PRODUCTOS, start=1)
    ]
    assert len({p["nombre"].lower() for p in productos}) == len(productos), "nombres de producto repetidos"

    clientes = generar_clientes(rng)
    ventas, lineas = generar_ventas(rng, clientes, productos)
    cambios = generar_cambios(productos)

    print(f"Dataset de {DESDE} a {HASTA} (semilla {SEMILLA}):")
    escribir("productos.csv", productos, ["id_producto", "nombre", "categoria", "precio", "activo"])
    escribir("cambios_producto.csv", cambios, ["id_producto", "accion", "campo", "valor_anterior", "valor_nuevo", "usuario", "fecha"])
    escribir("clientes.csv", clientes, ["id_cliente", "nombre", "tipo_documento", "documento", "telefono", "correo",
                                        "direccion", "barrio", "ciudad", "fecha_registro"])
    escribir("ventas.csv", ventas, ["id_venta", "fecha", "id_cliente", "cajero", "metodo_pago", "total"])
    escribir("lineas_venta.csv", lineas, ["id_venta", "id_producto", "cantidad", "precio_unitario", "subtotal"])

    ingresos = sum(v["total"] for v in ventas)
    print(f"Ingresos totales: ${ingresos:,.0f}  ·  ticket promedio: ${ingresos / len(ventas):,.0f}".replace(",", "."))


if __name__ == "__main__":
    main()
