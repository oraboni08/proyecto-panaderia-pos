import sqlite3
import os
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SALES_DB = os.path.join(BASE_DIR, 'sales_db.sqlite')
CATALOG_DB = os.path.join(BASE_DIR, 'catalog_db.sqlite')

router = APIRouter(prefix="/api/v1/sales", tags=["Sales"])

def get_sales_db():
    conn = sqlite3.connect(SALES_DB)
    conn.row_factory = sqlite3.Row
    return conn

class NewOrderRequest(BaseModel):
    id_cliente: int = 1
    id_producto: int
    cantidad_producto: float

@router.post("/orders")
def create_order(order: NewOrderRequest):
    conn = get_sales_db()
    cur = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    cur.execute("""
        INSERT INTO Operation (id_cliente, id_producto, fecha_operacion, cantidad_producto)
        VALUES (?, ?, ?, ?)
    """, (order.id_cliente, order.id_producto, today, order.cantidad_producto))
    
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"message": "Transacción registrada", "id_operacion": new_id}

@router.get("/metrics/summary")
def get_summary():
    conn_sales = get_sales_db()
    cur = conn_sales.cursor()
    cur.execute(f"ATTACH DATABASE '{CATALOG_DB}' AS catalog")
    
    query = """
        SELECT 
            COUNT(o.id_operacion) as total_operaciones,
            SUM(o.cantidad_producto) as total_unidades,
            ROUND(SUM(o.cantidad_producto * p.precio_unidad), 2) as total_ventas
        FROM Operation o
        JOIN catalog.Product p ON o.id_producto = p.id_producto
    """
    cur.execute(query)
    result = dict(cur.fetchone())
    conn_sales.close()
    return result

@router.get("/metrics/top-products")
def get_top_products():
    conn_sales = get_sales_db()
    cur = conn_sales.cursor()
    cur.execute(f"ATTACH DATABASE '{CATALOG_DB}' AS catalog")
    
    query = """
        SELECT 
            p.nombre_producto,
            SUM(o.cantidad_producto) as unidades_vendidas,
            ROUND(SUM(o.cantidad_producto * p.precio_unidad), 2) as total_recaudado
        FROM Operation o
        JOIN catalog.Product p ON o.id_producto = p.id_producto
        GROUP BY p.id_producto
        ORDER BY total_recaudado DESC
        LIMIT 7
    """
    cur.execute(query)
    results = [dict(row) for row in cur.fetchall()]
    conn_sales.close()
    return results