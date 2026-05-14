"""
占位测试 — 验证测试基础设施正常工作

当需要快速验证 pytest 环境时可使用此文件。
实际业务测试请移步：
  test_purchase_flow.py  — 采购拆分流程
  test_order_status.py   — 订单状态管理
  test_products.py       — 产品/供应商 CRUD
"""

from __future__ import annotations


def test_imports():
    """验证框架导入正常"""
    import httpx
    import pytest_asyncio
    from sqlalchemy import text
    assert text("SELECT 1") is not None


def test_async_support():
    """验证 pytest-asyncio 正常工作（同步测试）"""
    assert 1 + 1 == 2
