-- Esquema de la base de datos de auth-service (auth.db)
-- Lo crea SQLAlchemy automáticamente al iniciar el servicio (app/infrastructure/orm_models.py).

CREATE TABLE usuarios (
	id_usuario INTEGER NOT NULL, 
	nombre VARCHAR NOT NULL, 
	usuario VARCHAR NOT NULL, 
	password_hash VARCHAR NOT NULL, 
	rol VARCHAR NOT NULL, 
	activo BOOLEAN NOT NULL, 
	creado_en DATETIME NOT NULL, 
	PRIMARY KEY (id_usuario), 
	UNIQUE (usuario)
);

