"""
全链路整合测试 — 共享 Fixture 和测试数据

本 conftest.py 为 integration 目录下的测试提供模块级共享数据。
使用 scope="module" 确保全链路测试共享同一份数据。
"""

from __future__ import annotations

from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 必须在导入应用模块前设置测试数据库
import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "integration-test-secret"
os.environ["DB_ECHO"] = "false"

from app.domain.base import Base
from main import app
from app.api.deps import get_session
from app.core.security import create_access_token, hash_password


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="module")
async def test_engine():
    """模块级：创建测试数据库引擎并建表"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def _set_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="module")
async def session_factory(test_engine):
    """模块级：提供 session factory"""
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="module")
async def async_client(test_engine) -> AsyncClient:
    """
    模块级：提供测试 HTTP 客户端。
    全链路测试共享同一个客户端和数据库。
    """
    test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client
    await client.aclose()
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="module")
async def admin_token(session_factory) -> str:
    """模块级：创建 admin 用户并返回 Token"""
    from app.domain.auth import User
    from sqlalchemy import select

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.username == "test_admin"))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                username="test_admin",
                password_hash=hash_password("admin123"),
                name="测试管理员",
                phone="13800000000",
                role="admin",
                position="管理员",
            )
            session.add(user)
            await session.flush()
        token = create_access_token(sub=user.id, name=user.name, role=user.role)
        await session.commit()
    return token


# ── 种子数据：基础资料 ───────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def seed_master_data(session_factory, admin_token) -> dict:
    """
    模块级：初始化全链路测试所需的全部基础资料。

    返回一个 dict 包含所有创建记录的 ID，供测试用例引用。
    """
    from app.domain.product import Product, ProductCategory, Supplier
    from app.domain.customer import Customer
    from app.domain.warehouse import Warehouse
    from app.domain.installation import InstallTeam, Installer
    from sqlalchemy import select

    data = {}

    async with session_factory() as session:
        # ── 产品分类 ──
        categories = [
            ProductCategory(name="布艺窗帘", code="C01", sort_order=1),
            ProductCategory(name="窗纱", code="C02", sort_order=2),
            ProductCategory(name="辅料配件", code="C03", sort_order=3),
        ]
        session.add_all(categories)
        await session.flush()
        data["cat_curtain"] = categories[0].id
        data["cat_screen"] = categories[1].id
        data["cat_accessory"] = categories[2].id

        # ── 供应商 ──
        suppliers = [
            Supplier(
                name="杭州布艺供应商", code="S-HZ-001", type="布艺",
                contact="李经理", phone="13800138001", delivery_days=7,
                qq="hzfabric", wechat="hz_fabric",
                bank_account="6222021234567801", bank_name="中国工商银行杭州分行",
                payee="杭州布艺有限公司",
            ),
            Supplier(
                name="广州辅料批发", code="S-GZ-002", type="配件",
                contact="张先生", phone="13900139002", delivery_days=10,
                qq="gzfitting", wechat="gz_fitting",
                bank_account="6222021234567802", bank_name="中国建设银行广州分行",
                payee="广州辅料批发有限公司",
            ),
        ]
        session.add_all(suppliers)
        await session.flush()
        data["sup_hz"] = suppliers[0].id
        data["sup_gz"] = suppliers[1].id

        # ── 产品（每个供应商 3 个） ──
        products = [
            # 杭州布艺：主料
            Product(code="FAB-HZ-001", name="高档雪尼尔布料", product_type="面料",
                    unit="米", selling_price=120.0, cost_price=80.0, supplier_id=suppliers[0].id,
                    category_id=categories[0].id, color="深灰", pattern="简约纹理", standard_width=1.4),
            Product(code="FAB-HZ-002", name="棉麻混纺布料", product_type="面料",
                    unit="米", selling_price=80.0, cost_price=55.0, supplier_id=suppliers[0].id,
                    category_id=categories[0].id, color="米白", pattern="平纹", standard_width=1.4),
            Product(code="FAB-HZ-003", name="丝绒遮光布", product_type="面料",
                    unit="米", selling_price=150.0, cost_price=100.0, supplier_id=suppliers[0].id,
                    category_id=categories[0].id, color="墨绿", pattern="绒面", standard_width=1.4),
            # 广州辅料：辅料 + 配件
            Product(code="ACC-GZ-001", name="罗马杆", product_type="辅料",
                    unit="根", selling_price=35.0, cost_price=20.0, supplier_id=suppliers[1].id,
                    category_id=categories[2].id),
            Product(code="ACC-GZ-002", name="挂钩（20只装）", product_type="辅料",
                    unit="包", selling_price=15.0, cost_price=8.0, supplier_id=suppliers[1].id,
                    category_id=categories[2].id),
            Product(code="ACC-GZ-003", name="窗纱面料", product_type="面料",
                    unit="米", selling_price=60.0, cost_price=35.0, supplier_id=suppliers[1].id,
                    category_id=categories[1].id, color="白色", pattern="提花", standard_width=2.8),
        ]
        session.add_all(products)
        await session.flush()
        for i, p in enumerate(products):
            data[f"prod_{i+1}"] = p.id

        # ── 客户 ──
        customers = [
            Customer(name="王建国", phone="13958123456", address="杭州市西湖区文三路100号",
                     source="自然进店", level="C"),
            Customer(name="李明华", phone="13705718888", address="杭州市滨江区江南大道200号",
                     source="老客介绍", level="A"),
        ]
        session.add_all(customers)
        await session.flush()
        data["cust_wang"] = customers[0].id
        data["cust_li"] = customers[1].id

        # ── 仓库 ──
        wh = Warehouse(name="主仓库", code="WH-01", address="杭州余杭区物流中心")
        session.add(wh)
        await session.flush()
        data["wh_main"] = wh.id

        # ── 安装队 ──
        team = InstallTeam(name="第一安装队", leader_name="赵师傅", leader_phone="13800000111")
        session.add(team)
        await session.flush()
        data["team_1"] = team.id

        installers = [
            Installer(name="赵师傅", phone="13800000111"),
            Installer(name="钱师傅", phone="13800000222"),
        ]
        session.add_all(installers)
        await session.flush()
        data["installer_zhao"] = installers[0].id
        data["installer_qian"] = installers[1].id

        await session.commit()

    return data
