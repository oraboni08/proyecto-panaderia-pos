-- Se ejecuta solo la primera vez que arranca PostgreSQL (volumen vacío).
-- Patrón "database per service": cada microservicio tiene su propia base de datos.
CREATE DATABASE auth_db;
CREATE DATABASE catalog_db;
CREATE DATABASE sales_db;
CREATE DATABASE reports_db;
