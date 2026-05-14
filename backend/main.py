"""
金典软装ERP V4.0 - FastAPI 入口
"""

from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# ── 应用初始化 ────────────────────────────────────────────────
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import register_middlewares
from app.database import engine
from app.domain.base import Base

# 路由
from app.api.v1 import auth, customers, deposits, products, orders, purchases, warehouses, installations, finance, dashboard, system, production, roles, processing, after_sales, processing_orders, daily_report

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── 注册中间件 ────────────────────────────────────────────────
register_middlewares(app)


# ── 注册路由 ──────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(deposits.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(purchases.router)
app.include_router(warehouses.router)
app.include_router(installations.router)
app.include_router(finance.router)
app.include_router(dashboard.router)
app.include_router(system.router)
app.include_router(production.router)
app.include_router(roles.router)
app.include_router(processing.router)
app.include_router(processing_orders.router)
app.include_router(after_sales.router)
app.include_router(daily_report.router)


# ── 启动事件 ──────────────────────────────────────────────────


@app.on_event("startup")
async def startup():
    """应用启动时初始化数据库表"""
    from app.core.logging import logger

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表初始化完成")

    # 自动迁移：为已有表添加新列（SQLite 不自动添加列）
    async with engine.begin() as conn:
        def run_migration(sync_conn):
            from sqlalchemy import inspect, text
            inspector = inspect(sync_conn)

            # 迁移1: products → processing_type_id
            pcols = [c["name"] for c in inspector.get_columns("products")]
            if "processing_type_id" not in pcols:
                sync_conn.execute(text(
                    "ALTER TABLE products ADD COLUMN processing_type_id INTEGER REFERENCES processing_types(id)"
                ))
                logger.info("迁移: products 表添加了 processing_type_id 列")

            # 迁移2: suppliers → 新字段
            scols = [c["name"] for c in inspector.get_columns("suppliers")]
            for col_spec in [
                ("qq", "VARCHAR(30) DEFAULT ''"),
                ("wechat", "VARCHAR(50) DEFAULT ''"),
                ("bank_account", "VARCHAR(50) DEFAULT ''"),
                ("bank_name", "VARCHAR(100) DEFAULT ''"),
                ("payee", "VARCHAR(50) DEFAULT ''"),
            ]:
                if col_spec[0] not in scols:
                    sync_conn.execute(text(
                        f"ALTER TABLE suppliers ADD COLUMN {col_spec[0]} {col_spec[1]}"
                    ))
                    logger.info(f"迁移: suppliers 表添加了 {col_spec[0]} 列")

            # 迁移3: purchase_orders → 供应商付款信息字段
            pocols = [c["name"] for c in inspector.get_columns("purchase_orders")]
            for col_spec in [
                ("bank_account", "VARCHAR(50) DEFAULT ''"),
                ("bank_name", "VARCHAR(100) DEFAULT ''"),
                ("payee", "VARCHAR(50) DEFAULT ''"),
                ("qq", "VARCHAR(30) DEFAULT ''"),
                ("wechat", "VARCHAR(50) DEFAULT ''"),
            ]:
                if col_spec[0] not in pocols:
                    sync_conn.execute(text(
                        f"ALTER TABLE purchase_orders ADD COLUMN {col_spec[0]} {col_spec[1]}"
                    ))
                    logger.info(f"迁移: purchase_orders 表添加了 {col_spec[0]} 列")

            # 迁移4: orders → 补单关联字段
            ocols = [c["name"] for c in inspector.get_columns("orders")]
            if "parent_order_id" not in ocols:
                sync_conn.execute(text(
                    "ALTER TABLE orders ADD COLUMN parent_order_id INTEGER REFERENCES orders(id)"
                ))
                sync_conn.execute(text(
                    "ALTER TABLE orders ADD COLUMN orig_order_no VARCHAR(30) DEFAULT ''"
                ))
                logger.info("迁移: orders 表添加了 parent_order_id/orig_order_no 列（补单支持）")

            # 迁移5: order_fees 表（订单费用管理模块）
            table_names = inspector.get_table_names()
            if "order_fees" not in table_names:
                sync_conn.execute(text("""
                    CREATE TABLE order_fees (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                        fee_type VARCHAR(30) NOT NULL,
                        fee_type_label VARCHAR(50) DEFAULT '',
                        amount DECIMAL(12,2) DEFAULT 0,
                        remark VARCHAR(200) DEFAULT '',
                        operator_name VARCHAR(50) DEFAULT '',
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                """))
                sync_conn.execute(text(
                    "CREATE INDEX ix_order_fees_order_id ON order_fees(order_id)"
                ))
                logger.info("迁移: 创建了 order_fees 表（订单费用管理）")

            # 迁移6: after_sale_services 表（售后管理模块）
            if "after_sale_services" not in table_names:
                sync_conn.execute(text("""
                    CREATE TABLE after_sale_services (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_no VARCHAR(30) NOT NULL UNIQUE,
                        order_id INTEGER,
                        order_no VARCHAR(30) DEFAULT '',
                        customer_name VARCHAR(50) DEFAULT '',
                        customer_phone VARCHAR(20) DEFAULT '',
                        service_type VARCHAR(30) NOT NULL,
                        service_type_label VARCHAR(50) DEFAULT '',
                        description TEXT DEFAULT '',
                        status VARCHAR(20) DEFAULT '待处理',
                        handler_id INTEGER,
                        handler_name VARCHAR(50) DEFAULT '',
                        resolution TEXT DEFAULT '',
                        resolved_at TIMESTAMP,
                        remark VARCHAR(500) DEFAULT '',
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                """))
                logger.info("迁移: 创建了 after_sale_services 表（售后管理）")

            # 迁移7: warehouse_storage 表 + inventory 新增列（三级分类）
            if "warehouse_storage" not in table_names:
                sync_conn.execute(text("""
                    CREATE TABLE warehouse_storage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
                        level INTEGER NOT NULL,
                        name VARCHAR(50) NOT NULL,
                        code VARCHAR(30) DEFAULT '',
                        parent_id INTEGER,
                        remark VARCHAR(200) DEFAULT '',
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                """))
                logger.info("迁移: 创建了 warehouse_storage 表（仓库三级分类）")
            # 给 inventories 表添加三级分类字段
            inv_cols = [c["name"] for c in inspector.get_columns("inventories")]
            if "zone" not in inv_cols:
                sync_conn.execute(text("ALTER TABLE inventories ADD COLUMN zone VARCHAR(50) DEFAULT ''"))
                sync_conn.execute(text("ALTER TABLE inventories ADD COLUMN shelf VARCHAR(50) DEFAULT ''"))
                sync_conn.execute(text("ALTER TABLE inventories ADD COLUMN bin VARCHAR(50) DEFAULT ''"))
                logger.info("迁移: inventories 表添加了 zone/shelf/bin 三级分类字段")

            # 迁移8: order_items → procurement_type（采购类型：物料/成品/辅料）
            oi_cols = [c["name"] for c in inspector.get_columns("order_items")]
            if "procurement_type" not in oi_cols:
                sync_conn.execute(text(
                    "ALTER TABLE order_items ADD COLUMN procurement_type VARCHAR(10) DEFAULT '物料'"
                ))
                logger.info("迁移: order_items 表添加了 procurement_type 列（物料/成品/辅料）")

            # 迁移9: customers → deposit_balance
            cust_cols = [c["name"] for c in inspector.get_columns("customers")]
            if "deposit_balance" not in cust_cols:
                sync_conn.execute(text(
                    "ALTER TABLE customers ADD COLUMN deposit_balance DECIMAL(12,2) DEFAULT 0"
                ))
                logger.info("迁移: customers 表添加了 deposit_balance 列")

            # 迁移10: deposits 表（定金管理）
            if "deposits" not in table_names:
                sync_conn.execute(text("""
                    CREATE TABLE deposits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_id INTEGER NOT NULL REFERENCES customers(id),
                        amount DECIMAL(12,2) NOT NULL DEFAULT 0,
                        balance DECIMAL(12,2) NOT NULL DEFAULT 0,
                        payment_method VARCHAR(20) DEFAULT '',
                        received_at DATE,
                        operator_id INTEGER REFERENCES users(id),
                        operator_name VARCHAR(50) DEFAULT '',
                        remark TEXT DEFAULT '',
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                """))
                sync_conn.execute(text(
                    "CREATE INDEX ix_deposits_customer_id ON deposits(customer_id)"
                ))
                logger.info("迁移: 创建了 deposits 表（定金管理）")

            # 迁移11: processing_orders 表（加工单）
            if "processing_orders" not in table_names:
                sync_conn.execute(text("""
                    CREATE TABLE processing_orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        po_no VARCHAR(50) NOT NULL UNIQUE,
                        order_id INTEGER NOT NULL REFERENCES orders(id),
                        order_no VARCHAR(30) DEFAULT '',
                        customer_name VARCHAR(50) DEFAULT '',
                        warehouse_id INTEGER REFERENCES warehouses(id),
                        processing_factory VARCHAR(100) DEFAULT '',
                        total_items INTEGER DEFAULT 0,
                        total_process_fee DECIMAL(12,2) DEFAULT 0,
                        status VARCHAR(20) DEFAULT 'pending',
                        printed INTEGER DEFAULT 0,
                        remark TEXT DEFAULT '',
                        completed_at TIMESTAMP,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                """))
                logger.info("迁移: 创建了 processing_orders 表（加工单）")

            # 迁移12: processing_order_items 表（加工单明细）
            if "processing_order_items" not in table_names:
                sync_conn.execute(text("""
                    CREATE TABLE processing_order_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        processing_order_id INTEGER NOT NULL REFERENCES processing_orders(id),
                        order_item_id INTEGER NOT NULL REFERENCES order_items(id),
                        product_name VARCHAR(200) DEFAULT '',
                        product_code VARCHAR(100) DEFAULT '',
                        width DECIMAL(10,2) DEFAULT 0,
                        height DECIMAL(10,2) DEFAULT 0,
                        qty DECIMAL(10,2) DEFAULT 0,
                        unit VARCHAR(20) DEFAULT '',
                        process_desc TEXT DEFAULT '',
                        process_fee_unit DECIMAL(10,2) DEFAULT 0,
                        process_fee_subtotal DECIMAL(12,2) DEFAULT 0,
                        checked INTEGER DEFAULT 0,
                        remark TEXT DEFAULT '',
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                """))
                sync_conn.execute(text(
                    "CREATE INDEX ix_po_items_po_id ON processing_order_items(processing_order_id)"
                ))
                logger.info("迁移: 创建了 processing_order_items 表（加工单明细）")

            # 迁移13: products → is_purchase（是否需采购）
            prod_cols = [c["name"] for c in inspector.get_columns("products")]
            if "is_purchase" not in prod_cols:
                sync_conn.execute(text(
                    "ALTER TABLE products ADD COLUMN is_purchase INTEGER DEFAULT 1"
                ))
                logger.info("迁移: products 表添加了 is_purchase 列（True=需采购, False=外加工）")

            # 迁移14: order_items → is_purchase（订单级采购覆盖）
            oi_cols2 = [c["name"] for c in inspector.get_columns("order_items")]
            if "is_purchase" not in oi_cols2:
                sync_conn.execute(text(
                    "ALTER TABLE order_items ADD COLUMN is_purchase INTEGER DEFAULT 1"
                ))
                logger.info("迁移: order_items 表添加了 is_purchase 列（订单级是否采购覆盖）")

            # 迁移15: purchase_order_items → procurement_type（采购类型）
            poi_cols = [c["name"] for c in inspector.get_columns("purchase_order_items")]
            if "procurement_type" not in poi_cols:
                sync_conn.execute(text(
                    "ALTER TABLE purchase_order_items ADD COLUMN procurement_type VARCHAR(10) DEFAULT '物料'"
                ))
                logger.info("迁移: purchase_order_items 表添加了 procurement_type 列（物料/成品/辅料）")

            # 迁移16: order_items → panel_count（幅数）
            oi_cols3 = [c["name"] for c in inspector.get_columns("order_items")]
            if "panel_count" not in oi_cols3:
                sync_conn.execute(text(
                    "ALTER TABLE order_items ADD COLUMN panel_count DECIMAL(8,2) DEFAULT 0"
                ))
                logger.info("迁移: order_items 表添加了 panel_count 列（幅数）")

            # 迁移17: product_series 表 + products → series_id（系列/木板分类）
            if "product_series" not in table_names:
                sync_conn.execute(text("""
                    CREATE TABLE product_series (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(100) NOT NULL,
                        code VARCHAR(30) DEFAULT '',
                        supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
                        sort_order INTEGER DEFAULT 0,
                        remark TEXT DEFAULT '',
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                """))
                sync_conn.execute(text(
                    "CREATE INDEX ix_product_series_supplier_id ON product_series(supplier_id)"
                ))
                logger.info("迁移: 创建了 product_series 表（系列/木板分类）")
            prod_cols2 = [c["name"] for c in inspector.get_columns("products")]
            if "series_id" not in prod_cols2:
                sync_conn.execute(text(
                    "ALTER TABLE products ADD COLUMN series_id INTEGER REFERENCES product_series(id)"
                ))
                logger.info("迁移: products 表添加了 series_id 列（系列/木板ID）")

            # 迁移18: warehouses → warehouse_type（仓库分类）
            wh_cols = [c["name"] for c in inspector.get_columns("warehouses")]
            if "warehouse_type" not in wh_cols:
                sync_conn.execute(text(
                    "ALTER TABLE warehouses ADD COLUMN warehouse_type VARCHAR(20) DEFAULT 'main'"
                ))
                logger.info("迁移: warehouses 表添加了 warehouse_type 列（main/auxiliary/finished）")

            # 迁移19: 清理冗余仓库
            try:
                wh_rows = sync_conn.execute(text("SELECT id, name FROM warehouses")).all()
                for row in wh_rows:
                    if row[1] in ("辅料仓", "成品仓"):
                        sync_conn.execute(text("DELETE FROM warehouses WHERE id = :id"), [{"id": row[0]}])
                        logger.info(f"迁移: 删除了冗余仓库「{row[1]}」(id={row[0]})")
                    elif row[1] in ("主仓库",):
                        sync_conn.execute(text("UPDATE warehouses SET name = '面料仓库' WHERE id = :id"), [{"id": row[0]}])
                        logger.info(f"迁移: 仓库「{row[1]}」→「面料仓库」(id={row[0]})")
                    elif row[1] in ("面料仓库", "辅料仓库", "成品仓库"):
                        # 保留已正确命名的仓库，仅清理 warehouse_type
                        pass
            except Exception as exc:
                logger.warning(f"迁移19: 仓库清理异常（可忽略）: {exc}")

            # 迁移20: after_sale_services 新增列（售后模块重构 v2）
            as_cols = {c["name"] for c in inspector.get_columns("after_sale_services")}
            new_as_cols = {
                "priority": "VARCHAR(10) DEFAULT 'normal'",
                "source": "VARCHAR(20) DEFAULT 'manual'",
                "reviewer_id": "INTEGER",
                "reviewer_name": "VARCHAR(50) DEFAULT ''",
                "review_remark": "TEXT DEFAULT ''",
                "reviewed_at": "TIMESTAMP",
                "rejected_at": "TIMESTAMP",
                "closed_at": "TIMESTAMP",
                "customer_confirmed": "INTEGER DEFAULT 0",
                "customer_confirmed_at": "TIMESTAMP",
                "order_hold": "INTEGER DEFAULT 0",
                "resolved_type": "VARCHAR(20) DEFAULT ''",
                "refund_amount": "DECIMAL(12,2) DEFAULT 0",
                "compensation_amount": "DECIMAL(12,2) DEFAULT 0",
                "rework_cost": "DECIMAL(12,2) DEFAULT 0",
            }
            for col_name, col_def in new_as_cols.items():
                if col_name not in as_cols:
                    sync_conn.execute(text(f"ALTER TABLE after_sale_services ADD COLUMN {col_name} {col_def}"))
                    logger.info(f"迁移: after_sale_services 表添加了 {col_name} 列")
            # 更新默认状态从「待处理」为「待审核」
            sync_conn.execute(text(
                "UPDATE after_sale_services SET status = '待审核' WHERE status = '待处理'"
            ))
            logger.info("迁移: after_sale_services 状态默认值更新为「待审核」")

            # 迁移21: orders 增加 deposit 列 + deposits 增加 order_id 列
            order_cols = {c["name"] for c in inspector.get_columns("orders")}
            if "deposit" not in order_cols:
                sync_conn.execute(text("ALTER TABLE orders ADD COLUMN deposit DECIMAL(12,2) DEFAULT 0"))
                logger.info("迁移: orders 表添加了 deposit 列")
            dep_cols = {c["name"] for c in inspector.get_columns("deposits")}
            if "order_id" not in dep_cols:
                sync_conn.execute(text("ALTER TABLE deposits ADD COLUMN order_id INTEGER REFERENCES orders(id)"))
                logger.info("迁移: deposits 表添加了 order_id 列")

        await conn.run_sync(run_migration)

    # 检查是否需要初始化种子数据
    from sqlalchemy import select, func
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.database import async_session_factory
    from app.domain.auth import User

    async with async_session_factory() as session:
        # 确保所有 V3.0 字典类型和字典项存在（已有数据库自动补充缺失数据）
        await _ensure_dict_data(session)
        await session.commit()

        count = (await session.execute(select(func.count(User.id)))).scalar() or 0
        if count == 0:
            logger.info("检测到空数据库，开始初始化种子数据...")
            await _seed_data(session)
            await session.commit()
            logger.info("种子数据初始化完成")


async def _seed_data(session):
    """初始化种子数据"""
    from app.core.security import hash_password
    from app.domain.auth import User
    from app.domain.customer import Customer
    from app.domain.product import ProductCategory, Supplier, Product
    from app.domain.warehouse import Warehouse
    from app.domain.role import Role
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    # ── 管理员账号 ──
    session.add_all([
        User(username="admin", password_hash=hash_password("admin123"),
             name="系统管理员", phone="13800000000", role="admin", position="管理员"),
        User(username="13900000001", password_hash=hash_password("jd8888"),
             name="韩霜", phone="13900000001", role="admin", position="老板"),
        User(username="13900001111", password_hash=hash_password("jd8888"),
             name="小王", phone="13900001111", role="staff", position="导购"),
    ])

    # ── 仓库 ──
    session.add(Warehouse(name="面料仓库", code="WH-01", address="杭州古墩路欧亚达家居广场"))

    # ── 产品分类 ──
    session.add_all([
        ProductCategory(name="布艺窗帘", code="C01", sort_order=1),
        ProductCategory(name="窗纱", code="C02", sort_order=2),
        ProductCategory(name="墙布", code="C03", sort_order=3),
        ProductCategory(name="辅料配件", code="C04", sort_order=4),
    ])

    # ── 供应商 ──
    session.add_all([
        Supplier(name="杭州布艺供应商", code="S01", type="布艺", contact="李经理", phone="13800138001", delivery_days=7),
        Supplier(name="广州辅料批发", code="S02", type="配件", contact="张先生", phone="13900139001", delivery_days=10),
    ])

    # ── 字典数据（V3.0 全量类型和项） ──
    await _ensure_dict_data(session)

    # ── 默认角色 ──
    import json
    session.add_all([
        Role(name="超级管理员", code="admin", description="系统超级管理员，拥有全部权限",
             permissions=json.dumps(["*"], ensure_ascii=False), sort_order=1),
        Role(name="店长", code="manager", description="门店管理者，可查看和审批所有门店数据",
             permissions=json.dumps(["dashboard", "orders", "customers", "products", "purchases",
                                      "warehouse", "installations", "finance", "reports"], ensure_ascii=False),
             sort_order=2),
        Role(name="导购", code="staff", description="门店销售人员，负责开单和客户跟进",
             permissions=json.dumps(["dashboard", "orders", "customers", "products"], ensure_ascii=False),
             sort_order=3),
        Role(name="安装工", code="installer", description="安装工人，仅可查看安装任务",
             permissions=json.dumps(["installations"], ensure_ascii=False),
             sort_order=4),
    ])


async def _ensure_dict_data(session):
    """确保所有 V3.0 字典类型和字典项存在（已存在的跳过），同时适用于新库和已有库"""
    from app.domain.system import DictItem, DictType
    from sqlalchemy import select

    # V3.0 全量字典类型数据
    dict_type_seed = [
        ("order_type", "订单类型", 1),
        ("customer_source", "客户来源", 2),
        ("expense_category", "费用类别", 3),
        ("delivery_method", "提货方式", 4),
        ("supplier_type", "供应商类型", 5),
        ("product_unit", "产品单位", 6),
        ("fabric_width", "门幅", 7),
        ("material_composition", "材质成分", 8),
        ("customer_category", "客户类别", 9),
        ("install_location", "安装位置", 10),
        ("finished_type", "成品类型", 11),
        ("style_item", "款式项目", 12),
        ("after_sale_category", "售后分类", 13),
        ("bank_account", "银行账号", 14),
        ("payment_type", "收款类型", 15),
        ("order_fee_type", "订单费用类型", 16),
        ("waste_type", "损耗类型", 17),
        ("self_use_type", "自用类型", 18),
        ("purchase_return_type", "采购退货类型", 19),
        ("expense_type", "开销类型", 20),
        ("department", "部门", 21),
        ("position", "职务", 22),
        ("memo_type", "备忘录类型", 23),
        ("message_type", "留言类型", 24),
        ("order_status", "订单状态", 25),
        ("product_category", "产品分类", 26),
        ("warehouse", "仓库", 27),
        ("store_info", "店铺信息", 28),
        ("processing_type", "加工类型", 29),
    ]

    # V3.0 全量字典项数据
    dict_item_seed = [
        # 订单类型
        ("order_type", "curtain", "窗帘", 1),
        ("order_type", "wallpaper", "墙布", 2),
        ("order_type", "hardsheet", "硬包", 3),
        ("order_type", "wholehouse", "全屋", 4),
        ("order_type", "rockboard", "岩板", 5),
        # 客户来源
        ("customer_source", "self", "自然进店", 1),
        ("customer_source", "referral", "老客介绍", 2),
        ("customer_source", "online", "线上引流", 3),
        ("customer_source", "community", "小区推广", 4),
        ("customer_source", "old", "老客户", 5),
        # 费用类别
        ("expense_category", "rent", "房租", 1),
        ("expense_category", "utilities", "水电", 2),
        ("expense_category", "salary", "工资", 3),
        ("expense_category", "office", "办公", 4),
        ("expense_category", "other", "其他", 5),
        # 提货方式
        ("delivery_method", "install", "上门安装", 1),
        ("delivery_method", "pickup", "自提", 2),
        ("delivery_method", "express", "快递", 3),
        # 供应商类型
        ("supplier_type", "fabric", "布艺", 1),
        ("supplier_type", "finished", "成品", 2),
        ("supplier_type", "accessory", "配件", 3),
        ("supplier_type", "other", "其他", 4),
        # 产品单位
        ("product_unit", "meter", "米", 1),
        ("product_unit", "piece", "个", 2),
        ("product_unit", "set", "套", 3),
        ("product_unit", "strip", "条", 4),
        ("product_unit", "block", "块", 5),
        ("product_unit", "roll", "卷", 6),
        ("product_unit", "sqm", "平方米", 7),
        # 门幅
        ("fabric_width", "w140", "1.4m", 1),
        ("fabric_width", "w280", "2.8m", 2),
        ("fabric_width", "w300", "3.0m", 3),
        # 材质成分
        ("material_composition", "cotton", "棉", 1),
        ("material_composition", "linen", "麻", 2),
        ("material_composition", "polyester", "涤纶", 3),
        ("material_composition", "blend", "混纺", 4),
        ("material_composition", "velvet", "丝绒", 5),
        ("material_composition", "silk", "真丝", 6),
        ("material_composition", "cottonlinen", "棉麻", 7),
        # 客户类别
        ("customer_category", "normal", "普通客户", 1),
        ("customer_category", "vip", "VIP客户", 2),
        ("customer_category", "wholesale", "批发客户", 3),
        ("customer_category", "partner", "合作客户", 4),
        # 安装位置
        ("install_location", "living", "客厅", 1),
        ("install_location", "master_bed", "主卧", 2),
        ("install_location", "second_bed", "次卧", 3),
        ("install_location", "dining", "餐厅", 4),
        ("install_location", "study", "书房", 5),
        ("install_location", "kitchen", "厨房", 6),
        ("install_location", "bathroom", "卫生间", 7),
        ("install_location", "balcony", "阳台", 8),
        # 成品类型
        ("finished_type", "curtain", "成品帘", 1),
        ("finished_type", "roman", "罗马帘", 2),
        ("finished_type", "vertical", "垂直帘", 3),
        ("finished_type", "roller", "卷帘", 4),
        ("finished_type", "hundred", "百叶帘", 5),
        # 款式项目
        ("style_item", "plain", "平帘", 1),
        ("style_item", "pleated", "褶皱帘", 2),
        ("style_item", "eyelet", "打孔帘", 3),
        ("style_item", "hook", "挂钩帘", 4),
        ("style_item", "sash", "穿杆帘", 5),
        # 售后分类
        ("after_sale_category", "quality", "质量问题", 1),
        ("after_sale_category", "install_issue", "安装问题", 2),
        ("after_sale_category", "size_issue", "尺寸问题", 3),
        ("after_sale_category", "damage", "人为损坏", 4),
        ("after_sale_category", "other_issue", "其他售后", 5),
        # 银行账号
        ("bank_account", "icbc", "工商银行", 1),
        ("bank_account", "abc", "农业银行", 2),
        ("bank_account", "ccb", "建设银行", 3),
        ("bank_account", "boc", "中国银行", 4),
        ("bank_account", "cib", "兴业银行", 5),
        # 收款类型
        ("payment_type", "cash", "现金", 1),
        ("payment_type", "wechat", "微信", 2),
        ("payment_type", "alipay", "支付宝", 3),
        ("payment_type", "bank_transfer", "银行转账", 4),
        ("payment_type", "pos", "POS机刷卡", 5),
        # 订单费用类型
        ("order_fee_type", "measure_fee", "量尺费", 1),
        ("order_fee_type", "install_fee", "安装费", 2),
        ("order_fee_type", "delivery_fee", "运费", 3),
        ("order_fee_type", "lift_fee", "上楼费", 4),
        ("order_fee_type", "other_fee", "其他费用", 5),
        # 损耗类型
        ("waste_type", "cut_waste", "裁剪损耗", 1),
        ("waste_type", "joint_waste", "拼接损耗", 2),
        ("waste_type", "pattern_waste", "对花损耗", 3),
        ("waste_type", "transport_waste", "运输损耗", 4),
        # 自用类型
        ("self_use_type", "sample", "样品", 1),
        ("self_use_type", "display", "展厅展示", 2),
        ("self_use_type", "office_use", "办公自用", 3),
        ("self_use_type", "gift", "赠品", 4),
        # 采购退货类型
        ("purchase_return_type", "defective", "质量问题退货", 1),
        ("purchase_return_type", "overstock", "库存积压退货", 2),
        ("purchase_return_type", "wrong_spec", "规格不符", 3),
        ("purchase_return_type", "order_cancel", "订单取消退货", 4),
        # 开销类型
        ("expense_type", "rent", "房租", 1),
        ("expense_type", "utilities", "水电物业", 2),
        ("expense_type", "salary", "工资", 3),
        ("expense_type", "office_supplies", "办公用品", 4),
        ("expense_type", "transport", "交通差旅", 5),
        ("expense_type", "meal", "餐饮招待", 6),
        ("expense_type", "advertising", "广告推广", 7),
        ("expense_type", "decoration", "装修维修", 8),
        ("expense_type", "other", "其他", 9),
        # 部门
        ("department", "sales", "销售部", 1),
        ("department", "install", "安装部", 2),
        ("department", "purchase", "采购部", 3),
        ("department", "finance", "财务部", 4),
        ("department", "admin", "行政部", 5),
        # 职务
        ("position", "boss", "老板", 1),
        ("position", "manager", "店长", 2),
        ("position", "sales", "导购", 3),
        ("position", "designer", "设计师", 4),
        ("position", "installer", "安装工", 5),
        ("position", "finance", "财务", 6),
        ("position", "purchaser", "采购", 7),
        # 备忘录类型
        ("memo_type", "work", "工作备忘", 1),
        ("memo_type", "customer", "客户备忘", 2),
        ("memo_type", "order", "订单备忘", 3),
        ("memo_type", "personal", "个人备忘", 4),
        # 留言类型
        ("message_type", "order_msg", "订单留言", 1),
        ("message_type", "customer_msg", "客户留言", 2),
        ("message_type", "install_msg", "安装留言", 3),
        ("message_type", "internal", "内部留言", 4),
        # 订单状态
        ("order_status", "initial", "初始", 1),
        ("order_status", "measured", "已量尺", 2),
        ("order_status", "confirmed", "已确认", 3),
        ("order_status", "split", "已分单", 4),
        ("order_status", "purchasing", "采购中", 5),
        ("order_status", "stocked", "已入库", 6),
        ("order_status", "processing", "加工中", 7),
        ("order_status", "completed", "加工完成", 8),
        ("order_status", "install_scheduled", "已排安装", 9),
        ("order_status", "installed", "已安装", 10),
        ("order_status", "accepted", "已验收", 11),
        # 产品分类
        ("product_category", "curtain", "布艺窗帘", 1),
        ("product_category", "window_screen", "窗纱", 2),
        ("product_category", "wallcovering", "墙布", 3),
        ("product_category", "accessory", "辅料配件", 4),
        ("product_category", "hard_package", "硬包", 5),
        ("product_category", "rockboard", "岩板", 6),
        # 仓库
        ("warehouse", "main", "面料仓库", 1),
        # 店铺信息（配置项）
        ("store_info", "store_name", "店铺名称", 1),
        ("store_info", "store_code", "店铺编号", 2),
        ("store_info", "phone", "联系电话", 3),
        ("store_info", "address", "店铺地址", 4),
        ("store_info", "order_header", "订单抬头", 5),
        ("store_info", "order_template", "订单模板", 6),
        ("store_info", "order_tips", "订单提示/声明", 7),
        ("store_info", "contract_header", "合同抬头", 8),
        ("store_info", "contract_tips", "合同提示/声明", 9),
        # 加工类型
        ("processing_type", "curtain", "常规窗帘", 1),
        ("processing_type", "roman_rod", "罗马杆窗帘", 2),
        ("processing_type", "electric", "电动窗帘", 3),
        ("processing_type", "blind", "百叶帘", 4),
        ("processing_type", "soft_sheer", "柔纱帘", 5),
        ("processing_type", "roller", "卷帘", 6),
        ("processing_type", "valance", "幔头", 7),
        ("processing_type", "wallpaper", "墙布", 8),
        ("processing_type", "hard_package", "硬包", 9),
    ]

    # 插入缺失的字典类型
    for dt_code, dt_name, sort_order in dict_type_seed:
        exists = (await session.execute(
            select(DictType).where(DictType.dict_type == dt_code)
        )).scalar_one_or_none()
        if not exists:
            session.add(DictType(dict_type=dt_code, dict_name=dt_name, sort_order=sort_order, description=""))

    # 插入缺失的字典项
    for dt_code, dict_code, dict_label, sort_order in dict_item_seed:
        exists = (await session.execute(
            select(DictItem).where(DictItem.dict_type == dt_code, DictItem.dict_code == dict_code)
        )).scalar_one_or_none()
        if not exists:
            session.add(DictItem(
                dict_type=dt_code, dict_code=dict_code,
                dict_label=dict_label, sort_order=sort_order, is_active=True, remark=""
            ))

    await session.flush()

    # ── 同步加工类型字典项到 ProcessingType 表 ──
    from app.domain.processing import ProcessingType
    proc_dict_items = (await session.execute(
        select(DictItem).where(DictItem.dict_type == "processing_type", DictItem.is_active == True)
        .order_by(DictItem.sort_order)
    )).scalars().all()
    for item in proc_dict_items:
        exists = (await session.execute(
            select(ProcessingType).where(ProcessingType.code == item.dict_code)
        )).scalar_one_or_none()
        if not exists:
            session.add(ProcessingType(
                name=item.dict_label,
                code=item.dict_code,
                description=item.remark or "",
                sort_order=item.sort_order,
                is_active=True,
            ))
    await session.flush()


# ── 根路径 ────────────────────────────────────────────────────
# 注释掉根路由，让静态文件服务接管（前端已构建时）
# 访问 /docs 可查看 API 文档


# @app.get("/")
# async def root():
#     return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


# ── 静态文件 ───────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(settings.BASE_DIR, "..", "frontend", "dist")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


# ── 启动 ──────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8108,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
