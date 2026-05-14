#!/usr/bin/env python3
"""Fix: add V4.0 missing columns to installation_orders table."""
import sqlite3, sys
from pathlib import Path

DB = Path("/home/tianlj0320/sales-system-dev/sales.db")
ADDS = [
    ("team_id", "INTEGER"),
    ("actual_start_time", "DATETIME"),
    ("actual_end_time", "DATETIME"),
    ("quality_score", "INTEGER"),
    ("contact_phone", "VARCHAR(20)"),
]

def cols(table):
    cur.execute(f"PRAGMA table_info({table})")
    return {r[1] for r in cur.fetchall()}

with sqlite3.connect(DB) as conn:
    cur = conn.cursor()
    existing = cols("installation_orders")
    for name, typ in ADDS:
        if name not in existing:
            cur.execute(f"ALTER TABLE installation_orders ADD COLUMN {name} {typ}")
            print(f"  ✓ Added {name} {typ}")
        else:
            print(f"  - Skipped {name} (exists)")
    conn.commit()
print("Done.")