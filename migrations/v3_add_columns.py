"""
V3.0 数据库迁移脚本
执行: python -m migrations.v3_add_columns
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "sales.db")
DB_PATH = os.path.abspath(DB_PATH)

def migrate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. orders 表新增字段
    for col, col_type in [
        ("measure_data",    "TEXT"),
        ("install_requires","TEXT"),
    ]:
        c.execute(f"PRAGMA table_info(orders)")
        existing = {row[1] for row in c.fetchall()}
        if col not in existing:
            c.execute(f"ALTER TABLE orders ADD COLUMN {col} {col_type}")
            print(f"  + orders.{col} {col_type} [OK]")
        else:
            print(f"  = orders.{col} already exists [SKIP]")

    # 2. order_items 表新增字段
    for col, col_type in [
        ("supplier_id",    "INTEGER"),
        ("material_type",  "VARCHAR(20) DEFAULT '主料'"),
    ]:
        c.execute(f"PRAGMA table_info(order_items)")
        existing = {row[1] for row in c.fetchall()}
        if col not in existing:
            c.execute(f"ALTER TABLE order_items ADD COLUMN {col} {col_type}")
            print(f"  + order_items.{col} {col_type} [OK]")
        else:
            print(f"  = order_items.{col} already exists [SKIP]")

    conn.commit()
    conn.close()
    print("\nMigration done!")

if __name__ == "__main__":
    migrate()
