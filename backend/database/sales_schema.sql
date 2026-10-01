-- Esquema de la base de datos de sales-service (sales.db)
-- Lo crea SQLAlchemy automáticamente al iniciar el servicio (app/infrastructure/orm_models.py).

CREATE TABLE clientes (
	id_cliente INTEGER NOT NULL, 
	nombre VARCHAR NOT NULL, 
	creado_en DATETIME, 
	PRIMARY KEY (id_cliente)
);

CREATE TABLE lineas_venta (
	id_linea INTEGER NOT NULL, 
	id_venta INTEGER NOT NULL, 
	id_producto INTEGER NOT NULL, 
	nombre_producto VARCHAR NOT NULL, 
	tipo_venta VARCHAR NOT NULL, 
	cantidad FLOAT NOT NULL, 
	precio_unitario FLOAT NOT NULL, 
	subtotal FLOAT NOT NULL, 
	PRIMARY KEY (id_linea), 
	FOREIGN KEY(id_venta) REFERENCES ventas (id_venta)
);

CREATE TABLE ventas (
	id_venta INTEGER NOT NULL, 
	id_cliente INTEGER NOT NULL, 
	cajero VARCHAR, 
	fecha DATETIME NOT NULL, 
	total FLOAT NOT NULL, 
	PRIMARY KEY (id_venta), 
	FOREIGN KEY(id_cliente) REFERENCES clientes (id_cliente)
);

CREATE INDEX ix_lineas_venta_id_venta ON lineas_venta (id_venta);

CREATE INDEX ix_ventas_fecha ON ventas (fecha);

