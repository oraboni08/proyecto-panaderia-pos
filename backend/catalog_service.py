import sqlite3
import os
from fastapi import APIRouter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_DB = os.path.join(BASE_DIR, 'catalog_db.sqlite')

router = APIRouter(prefix="/api/v1/catalog", tags=["Catalog"])

def get_db():
    conn = sqlite3.connect(CATALOG_DB)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/products")
def get_products():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id_producto, nombre_producto, precio_unidad FROM Product ORDER BY nombre_producto ASC")
    products = [dict(row) for row in cur.fetchall()]
    conn.close()
    return products