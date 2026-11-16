-- Estructura de sales.db (generada por SQLAlchemy)

CREATE TABLE clientes (
	id_cliente INTEGER NOT NULL, 
	nombre VARCHAR NOT NULL, 
	tipo_documento VARCHAR(3), 
	documento VARCHAR(20), 
	telefono VARCHAR(15), 
	correo VARCHAR, 
	direccion VARCHAR, 
	barrio VARCHAR, 
	ciudad VARCHAR, 
	creado_en DATETIME, 
	PRIMARY KEY (id_cliente), 
	UNIQUE (documento)
);

CREATE TABLE lineas_venta (
	id_linea INTEGER NOT NULL, 
	id_venta INTEGER NOT NULL, 
	id_producto INTEGER NOT NULL, 
	nombre_producto VARCHAR NOT NULL, 
	categoria VARCHAR NOT NULL, 
	cantidad INTEGER NOT NULL, 
	precio_unitario INTEGER NOT NULL, 
	subtotal INTEGER NOT NULL, 
	PRIMARY KEY (id_linea), 
	FOREIGN KEY(id_venta) REFERENCES ventas (id_venta)
);

CREATE TABLE ventas (
	id_venta INTEGER NOT NULL, 
	id_cliente INTEGER NOT NULL, 
	cajero VARCHAR, 
	fecha DATETIME NOT NULL, 
	metodo_pago VARCHAR(20) NOT NULL, 
	total INTEGER NOT NULL, 
	PRIMARY KEY (id_venta), 
	FOREIGN KEY(id_cliente) REFERENCES clientes (id_cliente)
);

CREATE INDEX ix_clientes_nombre ON clientes (nombre);

CREATE INDEX ix_clientes_telefono ON clientes (telefono);

CREATE INDEX ix_lineas_venta_id_producto ON lineas_venta (id_producto);

CREATE INDEX ix_lineas_venta_id_venta ON lineas_venta (id_venta);

CREATE INDEX ix_ventas_cajero ON ventas (cajero);

CREATE INDEX ix_ventas_fecha ON ventas (fecha);

CREATE INDEX ix_ventas_id_cliente ON ventas (id_cliente);
