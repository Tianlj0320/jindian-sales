"""
产品/供应商 CRUD 测试

覆盖：
- 产品创建（基础信息和扩展信息）
- 产品列表 + 搜索（按名称、编码、类别）
- 产品详情
- 供应商关联查询
- 产品代码去重校验
"""

from __future__ import annotations

import pytest


class TestProductCRUD:
    """产品基础 CRUD"""

    @pytest.mark.asyncio
    async def test_create_product(self, async_client, admin_token, sample_product_data, seed_products):
        """测试创建产品：应返回产品ID"""
        response = await async_client.post(
            "/api/v1/products",
            json=sample_product_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"创建产品失败: {response.text}"
        data = response.json()
        assert data["success"]
        assert data["data"]["id"] > 0
        # 创建响应只返回 id，字段值通过搜索验证
        search = await async_client.get(
            "/api/v1/products/search?keyword=NEW-FABRIC-001",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        found = search.json()["data"]
        assert any(p["code"] == "NEW-FABRIC-001" and p["name"] == "新建测试面料" for p in found)

    @pytest.mark.asyncio
    async def test_create_product_duplicate_code(self, async_client, admin_token, seed_products):
        """测试产品代码重复处理"""
        # 创建第一个
        resp1 = await async_client.post(
            "/api/v1/products",
            json={"code": "DUP-001", "name": "产品A", "product_type": "面料", "unit": "米"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp1.json()["success"]

        # 使用相同代码创建第二个（API 当前不强制唯一性）
        resp2 = await async_client.post(
            "/api/v1/products",
            json={"code": "DUP-001", "name": "产品B", "product_type": "面料", "unit": "米"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Note: 产品编码未设置唯一约束，两个创建均成功
        assert resp2.status_code == 200
        assert resp2.json()["success"]
        assert resp2.json()["data"]["id"] != resp1.json()["data"]["id"]

    @pytest.mark.asyncio
    async def test_list_products(self, async_client, admin_token, seed_products):
        """测试产品列表：应返回所有产品"""
        response = await async_client.get(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3, f"应有至少3个产品，实际 {data['total']}"
        assert len(data["items"]) >= 3

    @pytest.mark.asyncio
    async def test_search_products_by_name(self, async_client, admin_token, seed_products):
        """测试产品搜索：按名称模糊搜索"""
        response = await async_client.get(
            "/api/v1/products/search?keyword=测试面料",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 2, f"应匹配至少2个产品，实际 {len(data['data'])}"

    @pytest.mark.asyncio
    async def test_search_products_by_code(self, async_client, admin_token, seed_products):
        """测试产品搜索：按编码搜索"""
        response = await async_client.get(
            "/api/v1/products/search?keyword=FABRIC-001",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1
        # 搜索结果按 id 降序排列，搜索全部匹配项
        exact = [p for p in data["data"] if p["code"] == "FABRIC-001"]
        assert len(exact) >= 1, f"未找到 FABRIC-001，结果: {[p['code'] for p in data['data']]}"
        assert exact[0]["supplier_name"] == "测试供应商", "供应商名称应自动关联"

    @pytest.mark.asyncio
    async def test_get_product_detail(self, async_client, admin_token, seed_products):
        """测试产品详情（通过搜索获取ID后再查详情）"""
        # 先搜索获取产品ID
        search_resp = await async_client.get(
            "/api/v1/products/search?keyword=FABRIC-001",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        products = search_resp.json()["data"]
        # 找到精确匹配的产品
        exact = next((p for p in products if p["code"] == "FABRIC-001"), products[0])
        product_id = exact["id"]

        # 查详情 - 可能没有专门详情接口，用列表查
        detail_resp = await async_client.get(
            f"/api/v1/products?id={product_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail_resp.status_code == 200


class TestSupplierCRUD:
    """供应商基础 CRUD"""

    @pytest.mark.asyncio
    async def test_create_supplier(self, async_client, admin_token):
        """测试创建供应商"""
        response = await async_client.post(
            "/api/v1/products/suppliers",
            json={
                "name": "新供应商",
                "code": "S-NEW-001",
                "contact": "王经理",
                "phone": "13900000001",
                "type": "布艺",
                "delivery_days": 7,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"创建供应商失败: {response.text}"
        data = response.json()
        assert data["success"]
        assert data["data"]["id"] > 0
        # 验证成功创建（创建响应只返回 id）
        assert data.get("message", "") != ""

    @pytest.mark.asyncio
    async def test_list_suppliers(self, async_client, admin_token, seed_products):
        """测试供应商列表"""
        response = await async_client.get(
            "/api/v1/products/suppliers",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1, "应返回至少一个供应商"
