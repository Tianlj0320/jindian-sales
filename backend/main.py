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
from app.api.v1 import auth, customers, products, orders, purchases, warehouses, installations, finance, dashboard, system, production, roles, processing

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
    session.add(Warehouse(name="主仓库", code="WH-01", address="杭州古墩路欧亚达家居广场"))

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
        ("warehouse", "main", "主仓库", 1),
        ("warehouse", "auxiliary", "辅料仓", 2),
        ("warehouse", "finished", "成品仓", 3),
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
        port=8001,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
