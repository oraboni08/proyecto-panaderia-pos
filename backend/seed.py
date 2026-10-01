import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, 'dataset')

CATALOG_DB = os.path.join(BASE_DIR, 'catalog_db.sqlite')
SALES_DB = os.path.join(BASE_DIR, 'sales_db.sqlite')

def seed_database():
    prod_path = os.path.join(DATASET_DIR, 'producto.csv')
    op_path = os.path.join(DATASET_DIR, 'operacion.csv')
    cli_path = os.path.join(DATASET_DIR, 'cliente.csv')

    if not (os.path.exists(prod_path) and os.path.exists(op_path)):
        print("❌ Archivos CSV no encontrados en backend/dataset/")
        return

    df_prod = pd.read_csv(prod_path, sep=';')
    df_op = pd.read_csv(op_path, sep=';')
    df_cli = pd.read_csv(cli_path, sep=';')

    df_prod['nombre_producto'] = df_prod['nombre_producto'].astype(str).str.strip()

    conn_cat = sqlite3.connect(CATALOG_DB)
    df_prod.to_sql('Product', conn_cat, if_exists='replace', index=False)
    conn_cat.close()

    conn_sales = sqlite3.connect(SALES_DB)
    df_op.to_sql('Operation', conn_sales, if_exists='replace', index=False)
    df_cli.to_sql('Client', conn_sales, if_exists='replace', index=False)
    conn_sales.close()

    print("✅ Bases de datos inicializadas con producto.csv, operacion.csv y cliente.csv")

if __name__ == '__main__':
    seed_database()