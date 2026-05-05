#!/usr/bin/env python3
"""Insert missing dict_items for filter fix."""
import sqlite3, sys

db_path = '/home/tianlj0320/sales-system-dev/sales.db'

inserts = [
    # (category_key, item_key, item_value, sort, enabled)
    ('customerType', '个人', '个人', 3, 1),
    ('customerType', '全屋', '全屋', 4, 1),
    ('supplierType', '布艺', '布艺', 3, 1),
    ('supplierType', '配件', '配件', 4, 1),
    ('position', '店长', '店长', 2, 1),
    ('position', '高级导购', '高级导购', 3, 1),
    ('productType', '面料', '面料', 5, 1),
]

conn = sqlite3.connect(db_path)
cur = conn.cursor()

for row in inserts:
    try:
        cur.execute(
            "INSERT OR IGNORE INTO dict_items (category_key, item_key, item_value, sort, enabled) VALUES (?, ?, ?, ?, ?)",
            row
        )
        if cur.rowcount > 0:
            print(f"INSERTED: {row[0]}/{row[1]} -> {row[2]}")
        else:
            print(f"EXISTS: {row[0]}/{row[1]} -> {row[2]}")
    except Exception as e:
        print(f"ERROR {row[0]}/{row[1]}: {e}")

conn.commit()
conn.close()
print("Done.")