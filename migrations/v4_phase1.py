"""
V4.0 Phase 1 数据库迁移脚本
运行方式: python -m migrations.v4_phase1
"""

import asyncio
import sys
import os
from datetime import datetime

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


async def migrate() -> None:
    print("[V4.0 Phase 1] 开始数据库迁移...")

    async with engine.begin() as conn:
        # ── 1. orders 表扩展 ────────────────────────────────────────────────
        print("  [1/6] 扩展 orders 表...")
        orders_alters = [
            ("ADD COLUMN measure_width DECIMAL(8,2)", "measure_width"),
            ("ADD COLUMN measure_height DECIMAL(8,2)", "measure_height"),
            ("ADD COLUMN window_width DECIMAL(8,2)", "window_width"),
            ("ADD COLUMN window_height DECIMAL(8,2)", "window_height"),
            ("ADD COLUMN measure_datetime VARCHAR(30)", "measure_datetime"),
            ("ADD COLUMN measure_operator_id INTEGER", "measure_operator_id"),
            ("ADD COLUMN order_type_ext VARCHAR(20) DEFAULT 'retail'", "order_type_ext"),
            ("ADD COLUMN price_locked_at VARCHAR(30)", "price_locked_at"),
            ("ADD COLUMN discount_reason VARCHAR(200)", "discount_reason"),
            ("ADD COLUMN install_date DATE", "install_date"),
            ("ADD COLUMN install_slot VARCHAR(10)", "install_slot"),
            ("ADD COLUMN paid_amount DECIMAL(12,2) DEFAULT 0", "paid_amount"),
            ("ADD COLUMN after_sale_reason VARCHAR(500)", "after_sale_reason"),
            ("ADD COLUMN after_sale_status VARCHAR(30)", "after_sale_status"),
            ("ADD COLUMN last_contact_at VARCHAR(30)", "last_contact_at"),
            ("ADD COLUMN salesperson_id INTEGER", "salesperson_id"),
            ("ADD COLUMN creator_id INTEGER", "creator_id"),
            ("ADD COLUMN reviewer_id INTEGER", "reviewer_id"),
            ("ADD COLUMN remark VARCHAR(500)", "remark"),
            ("ADD COLUMN deleted_at DATETIME", "deleted_at"),
        ]

        for alter_sql, col_name in orders_alters:
            try:
                await conn.execute(text(f"ALTER TABLE orders {alter_sql}"))
                print(f"    + orders.{col_name}")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"    ~ orders.{col_name} 已存在，跳过")
                else:
                    print(f"    ! orders.{col_name} 错误: {e}")

        # ── 2. customers 表扩展 ──────────────────────────────────────────────
        print("  [2/6] 扩展 customers 表...")
        customer_alters = [
            ("ADD COLUMN customer_type VARCHAR(20) DEFAULT 'retail'", "customer_type"),
            ("ADD COLUMN level VARCHAR(5) DEFAULT 'C'", "level"),
            ("ADD COLUMN measure_status VARCHAR(20) DEFAULT 'pending'", "measure_status"),
            ("ADD COLUMN tags TEXT DEFAULT '[]'", "tags"),
            ("ADD COLUMN salesperson_id INTEGER", "salesperson_id"),
            ("ADD COLUMN total_orders INTEGER DEFAULT 0", "total_orders"),
            ("ADD COLUMN total_amount DECIMAL(14,2) DEFAULT 0", "total_amount"),
            ("ADD COLUMN next_followup_date DATE", "next_followup_date"),
            ("ADD COLUMN followup_history TEXT DEFAULT '[]'", "followup_history"),
            ("ADD COLUMN credit_limit DECIMAL(12,2) DEFAULT 0", "credit_limit"),
            ("ADD COLUMN deleted_at DATETIME", "deleted_at"),
        ]

        for alter_sql, col_name in customer_alters:
            try:
                await conn.execute(text(f"ALTER TABLE customers {alter_sql}"))
                print(f"    + customers.{col_name}")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"    ~ customers.{col_name} 已存在，跳过")
                else:
                    print(f"    ! customers.{col_name} 错误: {e}")

        # ── 3. 新建 installation_orders 表 ─────────────────────────────────
        print("  [3/6] 创建 installation_orders 表...")
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS installation_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    ins_no VARCHAR(30) UNIQUE,
                    install_date DATE,
                    install_slot VARCHAR(10),
                    team_id INTEGER,
                    operator_id INTEGER,
                    address TEXT,
                    contact_phone VARCHAR(20),
                    status VARCHAR(20) DEFAULT '待派工',
                    note TEXT,
                    actual_start_time DATETIME,
                    actual_end_time DATETIME,
                    quality_score INTEGER,
                    signature_image TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("    + installation_orders 表创建成功")
        except Exception as e:
            print(f"    ! installation_orders: {e}")

        # ── 4. 新建 inventory_flow 表（库存流水）─────────────────────────────
        print("  [4/6] 创建 inventory_flow 表...")
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS inventory_flow (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    warehouse_id INTEGER,
                    flow_type VARCHAR(10) NOT NULL,
                    qty_before INTEGER DEFAULT 0,
                    qty_change INTEGER NOT NULL,
                    qty_after INTEGER DEFAULT 0,
                    ref_type VARCHAR(20),
                    ref_id INTEGER,
                    operator_id INTEGER,
                    remark TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("    + inventory_flow 表创建成功")
        except Exception as e:
            print(f"    ! inventory_flow: {e}")

        # ── 5. 新建 followup_records 表 ──────────────────────────────────────
        print("  [5/6] 创建 followup_records 表...")
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS followup_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    type VARCHAR(20) NOT NULL,
                    content TEXT,
                    next_date DATE,
                    operator_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("    + followup_records 表创建成功")
        except Exception as e:
            print(f"    ! followup_records: {e}")

        # ── 6. 新建 login_attempts 表（P0 安全修复）──────────────────────────
        print("  [6/6] 创建 login_attempts 表（防暴力破解）...")
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS login_attempts (
                    phone VARCHAR(20) NOT NULL,
                    ip_address VARCHAR(50) NOT NULL,
                    attempt_count INTEGER DEFAULT 0,
                    first_attempt_at DATETIME,
                    locked_until DATETIME,
                    PRIMARY KEY(phone, ip_address)
                )
            """))
            print("    + login_attempts 表创建成功")
        except Exception as e:
            print(f"    ! login_attempts: {e}")

    print("\n[V4.0 Phase 1] 迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())