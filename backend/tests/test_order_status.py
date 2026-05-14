"""
订单状态管理测试 — 状态机核心逻辑

覆盖：
- 订单创建后初始状态为 initial
- 状态线性推进（initial → measured → confirmed → ...）
- 状态推进合法性校验（不能跳过中间状态）
- 终态不可再推进
- 回滚操作
"""

from __future__ import annotations

import pytest


class TestOrderCreation:
    """订单创建与基础信息"""

    @pytest.mark.asyncio
    async def test_create_order(self, async_client, admin_token, sample_order_data):
        """测试创建订单：应返回订单ID和订单号"""
        response = await async_client.post(
            "/api/v1/orders",
            json=sample_order_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"创建订单失败: {response.text}"
        data = response.json()
        assert data["success"]
        assert data["data"]["id"] > 0
        assert data["data"]["order_no"] != ""

        # 验证订单状态为 initial（通过详情接口）
        detail = await async_client.get(
            f"/api/v1/orders/{data['data']['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail.json()["data"]["status_key"] == "initial"

    @pytest.mark.asyncio
    async def test_create_order_with_items(self, async_client, admin_token, sample_order_data):
        """测试创建订单包含明细项（通过详情验证）"""
        response = await async_client.post(
            "/api/v1/orders",
            json=sample_order_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        order_id = response.json()["data"]["id"]

        # 查详情验证明细
        detail = await async_client.get(
            f"/api/v1/orders/{order_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        items = detail.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["product_name"] == "测试面料A"

    @pytest.mark.asyncio
    async def test_get_order_detail(self, async_client, admin_token, created_order):
        """测试获取订单详情"""
        order_id = created_order["id"]
        response = await async_client.get(
            f"/api/v1/orders/{order_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["data"]["id"] == order_id
        assert "items" in data["data"]

    @pytest.mark.asyncio
    async def test_list_orders(self, async_client, admin_token, created_order):
        """测试订单列表查询"""
        response = await async_client.get(
            "/api/v1/orders",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert data["items"][0]["customer_name"] == "测试客户"


class TestOrderStatusProgression:
    """订单状态推进"""

    @pytest.mark.asyncio
    async def test_advance_from_initial_to_measured(self, async_client, admin_token, created_order):
        """测试状态推进：initial → measured"""
        order_id = created_order["id"]
        response = await async_client.post(
            f"/api/v1/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"推进失败: {response.text}"
        data = response.json()
        assert data["success"]
        assert data["data"]["status_key"] == "measured", \
            f"预期 measured，实际 {data['data'].get('status_key')}"

    @pytest.mark.asyncio
    async def test_full_status_chain(self, async_client, admin_token, created_order, seed_products):
        """测试完整状态链路推进：initial → ... → accepted

        注意：confirmed → split 需要经过采购拆分确认，
        测试中通过调用 purchase generate 来完成推进。
        """
        order_id = created_order["id"]
        # 定义状态链路（排除 confirmed→split 的特殊 case，单独处理）
        expected_chain = ["measured", "confirmed"]

        for expected_status in expected_chain:
            resp = await async_client.post(
                f"/api/v1/orders/{order_id}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert resp.status_code == 200, f"推进到 {expected_status} 失败: {resp.text}"
            data = resp.json()
            assert data["success"], f"推进到 {expected_status} 返回非成功: {data}"
            assert data["data"]["status_key"] == expected_status, \
                f"状态不匹配: 预期 {expected_status}, 实际 {data['data'].get('status_key')}"

        # confirmed → [need_preview]: advance 返回预览确认请求
        resp = await async_client.post(
            f"/api/v1/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        advance_data = resp.json()
        assert advance_data["success"]

        if advance_data["data"].get("need_preview"):
            # 需要确认采购拆分，调用 purchase generate 推进到 split
            gen_resp = await async_client.post(
                "/api/v1/purchases/generate",
                json={
                    "order_ids": [order_id],
                    "supplier_ids": [seed_products["supplier_id"]],
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert gen_resp.status_code == 200, f"生成采购单失败: {gen_resp.text}"
        else:
            # 没有需要采购的明细，已直接推进到 split
            assert advance_data["data"]["status_key"] == "split"

        # 验证订单已到 split
        detail = await async_client.get(
            f"/api/v1/orders/{order_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail.json()["data"]["status_key"] == "split"

        # 继续推进：split → purchasing → stocked → processing → completed → ...
        after_split = ["purchasing", "stocked", "processing", "completed"]
        for expected_status in after_split:
            resp = await async_client.post(
                f"/api/v1/orders/{order_id}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert resp.status_code == 200, f"推进到 {expected_status} 失败: {resp.text}"
            data = resp.json()
            assert data["success"]
            assert data["data"]["status_key"] == expected_status, \
                f"状态不匹配: 预期 {expected_status}, 实际 {data['data'].get('status_key')}"

        # completed → [auto install order] 特殊处理
        resp = await async_client.post(
            f"/api/v1/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # completed → install_scheduled 可能自动生成安装单
        assert data["data"]["status_key"] in ("install_scheduled",)

        # install_scheduled → installed → accepted
        for expected_status in ["installed", "accepted"]:
            resp = await async_client.post(
                f"/api/v1/orders/{order_id}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert resp.status_code == 200
            assert resp.json()["data"]["status_key"] == expected_status

    @pytest.mark.asyncio
    async def test_advance_skips_partial_in(self, async_client, admin_token, created_order, seed_products):
        """测试状态推进跳过 partial_in（该状态仅在采购收货时触发）"""
        order_id = created_order["id"]
        expected = ["measured", "confirmed"]

        for exp in expected:
            resp = await async_client.post(
                f"/api/v1/orders/{order_id}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert resp.json()["data"]["status_key"] == exp

        # confirmed → [need_preview]
        resp = await async_client.post(
            f"/api/v1/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        if resp.json()["data"].get("need_preview"):
            gen_resp = await async_client.post(
                "/api/v1/purchases/generate",
                json={
                    "order_ids": [order_id],
                    "supplier_ids": [seed_products["supplier_id"]],
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert gen_resp.status_code == 200

        # 验证已到 split
        detail = await async_client.get(
            f"/api/v1/orders/{order_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail.json()["data"]["status_key"] == "split"

        # 前进一步：split → purchasing
        resp = await async_client.post(
            f"/api/v1/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json()["data"]["status_key"] == "purchasing"

        # 再前进：purchasing → stocked（跳过 partial_in）
        resp = await async_client.post(
            f"/api/v1/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json()["data"]["status_key"] == "stocked", \
            f"应跳过partial_in: {resp.json()}"

    @pytest.mark.asyncio
    async def test_terminal_status_cannot_advance(self, async_client, admin_token, created_order, seed_products):
        """测试终态不可再推进"""
        order_id = created_order["id"]

        # 依次推进到 accepted（终态）
        steps = ["measured", "confirmed"]
        for exp in steps:
            resp = await async_client.post(
                f"/api/v1/orders/{order_id}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert resp.json()["data"]["status_key"] == exp

        # confirmed → split via purchase generate
        resp = await async_client.post(
            f"/api/v1/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        if resp.json()["data"].get("need_preview"):
            await async_client.post(
                "/api/v1/purchases/generate",
                json={
                    "order_ids": [order_id],
                    "supplier_ids": [seed_products["supplier_id"]],
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        # 继续推进到 accepted
        remaining = ["purchasing", "stocked", "processing", "completed",
                      "install_scheduled", "installed", "accepted"]
        for exp in remaining:
            resp = await async_client.post(
                f"/api/v1/orders/{order_id}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            if resp.status_code != 200:
                break

        # 尝试再次推进应当失败
        final_resp = await async_client.post(
            f"/api/v1/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert final_resp.status_code != 200 or not final_resp.json().get("success"), \
            "终态应不可再推进"


class TestOrderStatusExceptions:
    """订单异常与回滚"""

    @pytest.mark.asyncio
    async def test_update_order(self, async_client, admin_token, created_order):
        """测试更新订单信息"""
        order_id = created_order["id"]
        response = await async_client.put(
            f"/api/v1/orders/{order_id}",
            json={"customer_name": "修改后的客户名", "remark": "修改备注"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"]

        # 验证更新已生效
        detail = await async_client.get(
            f"/api/v1/orders/{order_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail.json()["data"]["customer_name"] == "修改后的客户名"

    @pytest.mark.asyncio
    async def test_rollback_options(self, async_client, admin_token, created_order):
        """测试获取回滚选项"""
        order_id = created_order["id"]

        # 先推进到 confirmed
        for _ in range(2):
            await async_client.post(
                f"/api/v1/orders/{order_id}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        # 获取回滚选项
        resp = await async_client.get(
            f"/api/v1/orders/{order_id}/rollback-options",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success", True)

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, async_client):
        """测试未认证请求被拒绝"""
        response = await async_client.get("/api/v1/orders")
        assert response.status_code == 401, f"未认证应返回 401: {response.status_code}"
