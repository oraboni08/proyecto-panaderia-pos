# Bases de datos

Cada microservicio tiene su propia base de datos SQLite:

| Archivo | Servicio | Tablas | Datos iniciales |
|---|---|---|---|
| `auth.db` | auth-service | `usuarios` | 2 usuarios: `admin` y `cajero` |
| `catalog.db` | catalog-service | `productos`, `cambios_producto` | 42 productos del dataset |
| `sales.db` | sales-service | `clientes`, `ventas`, `lineas_venta` | 210 clientes + Consumidor final, 1.203 ventas |

Los archivos `*_schema.sql` muestran la estructura de cada base (`CREATE TABLE`).

Estas bases son una **copia de referencia** del estado inicial, cargado desde los CSV de `../dataset/`.
Los servicios no las modifican: al arrancar por primera vez, cada uno crea su propia base
(en el servidor, en `/var/lib/panaderia-pos/`) y carga el dataset automáticamente.
Para abrirlas se puede usar [DB Browser for SQLite](https://sqlitebrowser.org/).
