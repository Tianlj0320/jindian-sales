"""
全局测试配置 — 金典软装ERP V4.0 测试基础设施

提供：
- 异步测试支持（pytest-asyncio）
- 测试用内存 SQLite 数据库（每模块独立）
- 测试用 HTTP 客户端（httpx.AsyncClient，挂载真实 FastAPI 应用）
- 测试用户认证 Token
- 种子数据（管理员账号、产品、供应商）
"""

from __future__ import annotations

from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── 必须先设置测试数据库 URL 再导入应用模块 ────────────
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-not-for-production"
os.environ["DB_ECHO"] = "false"

# 现在安全导入应用模块
from app.database import async_session_factory, engine as prod_engine
from app.domain.base import Base
from main import app
from app.api.deps import get_session
from app.core.security import create_access_token, hash_password


# ── 测试配置 ──────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ── Fixtures ──────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def test_engine():
    """模块级：创建测试数据库引擎并建表"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # 启用 SQLite WAL 模式 + 外键
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


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """函数级：提供独立的数据库会话（事务隔离）"""
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        # 开启事务
        async with session.begin():
            yield session
            # 回滚事务以隔离测试
            await session.rollback()


@pytest_asyncio.fixture
async def async_client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    """
    函数级：提供测试 HTTP 客户端

    重写 app.database.async_session_factory 使所有请求使用测试数据库。
    同时重写 get_session 依赖以确保一致性。
    """
    # 创建与 test_engine 关联的 session_factory
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

    # 重写 FastAPI 依赖
    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # 清理依赖重写
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_token(test_engine) -> str:
    """
    获取管理员认证 Token。

    先在测试数据库中创建 admin 用户，然后签发 JWT。
    """
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        from app.domain.auth import User
        from sqlalchemy import select, func

        # 检查是否已存在
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                username="admin",
                password_hash=hash_password("admin123"),
                name="系统管理员",
                phone="13800000000",
                role="admin",
                position="管理员",
            )
            session.add(user)
            await session.flush()

        token = create_access_token(sub=user.id, name=user.name, role=user.role)
        await session.commit()

    return token


@pytest_asyncio.fixture
async def seed_products(test_engine):
    """种子数据：创建测试用产品和供应商"""
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        from app.domain.product import Product, Supplier, ProductCategory
        from app.domain.warehouse import Warehouse
        from sqlalchemy import select

        # 检查是否已有数据 — 如有则返回已有 ID（跨测试共享数据库场景）
        existing = await session.execute(select(Supplier).limit(1))
        existing_supplier = existing.scalar_one_or_none()
        if existing_supplier is not None:
            existing_wh = await session.execute(select(Warehouse).limit(1))
            wh = existing_wh.scalar_one_or_none()
            await session.close()
            return {"supplier_id": existing_supplier.id, "wh_id": wh.id if wh else 1}

        # 创建供应商
        supplier = Supplier(
            name="测试供应商",
            code="S-TEST-001",
            type="布艺",
            contact="李经理",
            phone="13800138001",
            delivery_days=7,
            qq="123456",
            wechat="test_supplier",
            bank_account="6222021234567890",
            bank_name="中国工商银行",
            payee="测试供应商有限公司",
        )
        session.add(supplier)

        # 创建产品分类
        cat = ProductCategory(name="布艺窗帘", code="C01", sort_order=1)
        session.add(cat)
        await session.flush()

        # 创建产品
        products = [
            Product(
                code="FABRIC-001",
                name="测试面料A",
                product_type="面料",
                unit="米",
                selling_price=100.0,
                cost_price=80.0,
                supplier_id=supplier.id,
                category_id=cat.id,
            ),
            Product(
                code="FABRIC-002",
                name="测试面料B",
                product_type="面料",
                unit="米",
                selling_price=150.0,
                cost_price=120.0,
                supplier_id=supplier.id,
                category_id=cat.id,
            ),
            Product(
                code="ACCESSORY-001",
                name="测试配件",
                product_type="辅料",
                unit="个",
                selling_price=10.0,
                cost_price=8.0,
                supplier_id=supplier.id,
                category_id=cat.id,
            ),
        ]
        session.add_all(products)
        await session.flush()

        # 创建仓库（用于采购收货测试）
        from app.domain.warehouse import Warehouse
        wh = Warehouse(name="测试仓库", code="WH-TEST-001", address="测试地址")
        session.add(wh)

        await session.commit()

    return {"supplier_id": supplier.id, "wh_id": wh.id}


@pytest_asyncio.fixture
async def sample_order_data(seed_products) -> dict:
    """示例订单数据（含供应商ID，支持采购拆分流程）"""
    return {
        "customer_name": "测试客户",
        "customer_phone": "13800138000",
        "order_type": "窗帘",
        "order_date": "2026-05-10",
        "delivery_method": "上门安装",
        "remark": "测试订单备注",
        "items": [
            {
                "product_name": "测试面料A",
                "product_code": "FABRIC-001",
                "width": 2.0,
                "height": 2.8,
                "qty": 1,
                "unit_price": 100.0,
                "material_type": "主料",
                "supplier_id": seed_products["supplier_id"],
            }
        ],
    }


@pytest.fixture
def sample_product_data() -> dict:
    """示例产品数据"""
    return {
        "code": "NEW-FABRIC-001",
        "name": "新建测试面料",
        "product_type": "面料",
        "unit": "米",
        "selling_price": 100.0,
        "cost_price": 80.0,
    }


@pytest_asyncio.fixture
async def created_order(async_client, admin_token, sample_order_data) -> dict:
    """创建一个测试订单并返回完整数据"""
    response = await async_client.post(
        "/api/v1/orders",
        json=sample_order_data,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"]
    return data["data"]
