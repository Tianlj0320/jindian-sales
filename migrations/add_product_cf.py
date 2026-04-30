"""
Migration: Add cf column to products table
执行: python -m migrations.add_product_cf
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "sales.db")
DB_PATH = os.path.abspath(DB_PATH)

def migrate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("PRAGMA table_info(products)")
    existing = {row[1] for row in c.fetchall()}
    if "cf" not in existing:
        c.execute("ALTER TABLE products ADD COLUMN cf INTEGER DEFAULT 0")
        print("  + products.cf INTEGER DEFAULT 0 [OK]")
    else:
        print("  = products.cf already exists [SKIP]")

    conn.commit()
    conn.close()
    print("\nMigration done!")

if __name__ == "__main__":
    migrate()
