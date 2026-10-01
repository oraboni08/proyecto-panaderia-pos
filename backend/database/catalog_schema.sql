-- Esquema de la base de datos de catalog-service (catalog.db)
-- Lo crea SQLAlchemy automáticamente al iniciar el servicio (app/infrastructure/orm_models.py).

CREATE TABLE cambios_producto (
	id_cambio INTEGER NOT NULL, 
	id_producto INTEGER NOT NULL, 
	accion VARCHAR NOT NULL, 
	campo VARCHAR, 
	valor_anterior VARCHAR, 
	valor_nuevo VARCHAR NOT NULL, 
	usuario VARCHAR NOT NULL, 
	fecha DATETIME NOT NULL, 
	PRIMARY KEY (id_cambio), 
	FOREIGN KEY(id_producto) REFERENCES productos (id_producto)
);

CREATE TABLE productos (
	id_producto INTEGER NOT NULL, 
	nombre VARCHAR NOT NULL, 
	precio FLOAT NOT NULL, 
	tipo_venta VARCHAR NOT NULL, 
	activo BOOLEAN NOT NULL, 
	PRIMARY KEY (id_producto), 
	UNIQUE (nombre)
);

