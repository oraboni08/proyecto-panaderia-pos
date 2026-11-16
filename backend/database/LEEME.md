# Bases de datos

Cada microservicio tiene su propia base de datos SQLite:

| Archivo | Servicio | Tablas | Datos iniciales |
|---|---|---|---|
| `auth.db` | auth-service | `usuarios` | 6 usuarios: `admin`, `cajero` y los 4 cajeros del dataset (`mcastillo`, `jrengifo`, `lvalencia`, `dmosquera`) |
| `catalog.db` | catalog-service | `productos`, `cambios_producto` | 90 productos colombianos en 10 categorías y 185 cambios (incluye el alza de precios de enero de 2026) |
| `sales.db` | sales-service | `clientes`, `ventas`, `lineas_venta` | 3.200 clientes + Consumidor final, 94.758 ventas y 203.696 líneas (2 ene 2025 – 15 nov 2026) |

Los archivos `*_schema.sql` muestran la estructura de cada base (`CREATE TABLE`).

Estas bases son una **copia de referencia** del estado inicial, cargado desde los CSV de `../dataset/`.
El dataset se genera con `python ../dataset/generar_dataset.py` (semilla fija: siempre produce los mismos datos).
Los servicios no las modifican: al arrancar por primera vez, cada uno crea su propia base
(en el servidor, en `/var/lib/panaderia-pos/`) y carga el dataset automáticamente.
Para abrirlas se puede usar [DB Browser for SQLite](https://sqlitebrowser.org/).
