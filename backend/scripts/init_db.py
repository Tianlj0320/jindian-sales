"""
数据库初始化脚本
创建数据库表并填充种子数据
"""

import asyncio
import os
import sys

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.logging import setup_logging
from app.database import async_session_factory, engine
from app.domain.base import Base


async def init_database():
    setup_logging()

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ 数据库表创建完成")

    # 导入种子数据
    from app.core.security import hash_password
    from app.domain.auth import User
    from app.domain.warehouse import Warehouse
    from app.domain.product import ProductCategory, Supplier
    from app.domain.system import DictItem
    from sqlalchemy import select, func

    async with async_session_factory() as session:
        # 检查是否已有数据
        count = (await session.execute(select(func.count(User.id)))).scalar() or 0
        if count > 0:
            print("✓ 数据库已有数据，跳过种子初始化")
            return

        # 用户
        session.add_all([
            User(username="admin", password_hash=hash_password("admin123"),
                 name="系统管理员", phone="13800000000", role="admin", position="管理员"),
            User(username="13900000001", password_hash=hash_password("jd8888"),
                 name="韩霜", phone="13900000001", role="admin", position="老板"),
            User(username="13900001111", password_hash=hash_password("jd8888"),
                 name="小王", phone="13900001111", role="staff", position="导购"),
        ])
        print("✓ 用户数据创建完成")

        # 仓库
        session.add(Warehouse(name="主仓库", code="WH-01", address="杭州古墩路"))
        print("✓ 仓库数据创建完成")

        # 产品分类
        session.add_all([
            ProductCategory(name="布艺窗帘", code="C01", sort_order=1),
            ProductCategory(name="窗纱", code="C02", sort_order=2),
            ProductCategory(name="墙布", code="C03", sort_order=3),
            ProductCategory(name="辅料配件", code="C04", sort_order=4),
        ])
        print("✓ 产品分类创建完成")

        # 供应商
        session.add_all([
            Supplier(name="杭州布艺供应商", code="S01", type="布艺", contact="李经理", phone="13800138001"),
            Supplier(name="广州辅料批发", code="S02", type="配件", contact="张先生", phone="13900139001"),
        ])
        print("✓ 供应商数据创建完成")

        # 字典
        session.add_all([
            DictItem(dict_type="order_type", dict_code="curtain", dict_label="窗帘", sort_order=1),
            DictItem(dict_type="order_type", dict_code="wallpaper", dict_label="墙布", sort_order=2),
            DictItem(dict_type="order_type", dict_code="hardsheet", dict_label="硬包", sort_order=3),
            DictItem(dict_type="customer_source", dict_code="self", dict_label="自然进店", sort_order=1),
            DictItem(dict_type="customer_source", dict_code="referral", dict_label="老客介绍", sort_order=2),
            DictItem(dict_type="customer_source", dict_code="online", dict_label="线上引流", sort_order=3),
            DictItem(dict_type="expense_category", dict_code="rent", dict_label="房租", sort_order=1),
            DictItem(dict_type="expense_category", dict_code="salary", dict_label="工资", sort_order=2),
        ])
        print("✓ 字典数据创建完成")

        await session.commit()
        print("✓ 所有种子数据初始化完成！")


if __name__ == "__main__":
    asyncio.run(init_database())
