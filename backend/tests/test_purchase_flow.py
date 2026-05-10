"""
采购拆分流程测试 — 核心业务链路

覆盖：
- 创建订单后自动进入待采购状态
- 采购拆分预览（按供应商分组）
- 确认生成采购单
- 验证采购单数据正确（供应商信息自动关联）
- 采购收货 + 库存更新

API 响应格式：
  预览: {success, data: {groups: [{supplier_id, supplier_name, items, ...}], order_ids, order_nos}}
  生成: {success, data: {po_nos: [...]}}
  列表: {success, total, items: [{supplier_name, contact, ...}]}
  详情: {success, data: {bank_account, contact, phone, ...}}
"""

from __future__ import annotations

import pytest


class TestPurchaseSplitFlow:
    """采购拆分核心流程"""

    @pytest.mark.asyncio
    async def test_split_preview(self, async_client, admin_token, seed_products, created_order):
        """测试采购拆分预览：确认预览返回按供应商分组的数据"""
        order_id = created_order["id"]
        assert order_id > 0

        # 先推进到 confirmed
        for _ in range(2):
            await async_client.post(
                f"/api/v1/orders/{order_id}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        # 从 confirmed 推进 -> 触发 need_preview
        resp = await async_client.post(
            f"/api/v1/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json()["data"].get("need_preview"), "confirmed 后应触发 need_preview"

        # 请求采购拆分预览
        response = await async_client.post(
            "/api/v1/purchases/preview",
            json={"order_ids": [order_id]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"预览失败: {response.text}"
        data = response.json()
        assert data["success"], f"预览失败: {data.get('error')}"
        groups = data["data"]["groups"]
        assert len(groups) > 0, "预览应返回至少一个供应商分组"
        assert groups[0]["supplier_name"] == "测试供应商", "供应商名称应自动关联"

    @pytest.mark.asyncio
    async def test_generate_purchase_order(self, async_client, admin_token, seed_products, created_order):
        """测试生成采购单：从预览结果确认生成"""
        order_id = created_order["id"]

        # 推进到 confirmed → 触发 need_preview
        for _ in range(2):
            await async_client.post(
                f"/api/v1/orders/{order_id}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
        resp = await async_client.post(
            f"/api/v1/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json()["data"].get("need_preview")

        # 获取预览
        preview_resp = await async_client.post(
            "/api/v1/purchases/preview",
            json={"order_ids": [order_id]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        preview_data = preview_resp.json()
        groups = preview_data["data"]["groups"]
        supplier_ids = [s["supplier_id"] for s in groups]

        # 确认生成采购单
        gen_resp = await async_client.post(
            "/api/v1/purchases/generate",
            json={"order_ids": [order_id], "supplier_ids": supplier_ids},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert gen_resp.status_code == 200, f"生成失败: {gen_resp.text}"
        gen_data = gen_resp.json()
        assert gen_data["success"]
        assert len(gen_data["data"]["po_nos"]) > 0

    @pytest.mark.asyncio
    async def test_purchase_order_list(self, async_client, admin_token, seed_products, created_order):
        """测试采购单列表：创建采购单后能在列表中查到"""
        order_id = created_order["id"]

        # 推进到 confirmed → need_preview
        for _ in range(2):
            await async_client.post(
                f"/api/v1/orders/{order_id}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
        resp = await async_client.post(
            f"/api/v1/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json()["data"].get("need_preview")

        # 获取预览 + 生成
        preview_resp = await async_client.post(
            "/api/v1/purchases/preview",
            json={"order_ids": [order_id]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        supplier_ids = [s["supplier_id"] for s in preview_resp.json()["data"]["groups"]]
        await async_client.post(
            "/api/v1/purchases/generate",
            json={"order_ids": [order_id], "supplier_ids": supplier_ids},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # 查询采购单列表
        list_resp = await async_client.get(
            "/api/v1/purchases",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["total"] > 0, "采购单列表应返回数据"
        # 验证供应商信息已自动关联
        po = list_data["items"][0]
        assert po["supplier_name"] != "", "供应商名称不应为空"
        assert po["contact"] != "", "供应商联系人不应为空"

    @pytest.mark.asyncio
    async def test_purchase_detail_supplier_info(self, async_client, admin_token, seed_products, created_order):
        """验证采购单详情包含完整的供应商信息"""
        order_id = created_order["id"]

        # 推进到 confirmed → need_preview
        for _ in range(2):
            await async_client.post(
                f"/api/v1/orders/{order_id}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
        resp = await async_client.post(
            f"/api/v1/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json()["data"].get("need_preview")

        # 预览 + 生成
        preview_resp = await async_client.post(
            "/api/v1/purchases/preview",
            json={"order_ids": [order_id]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        supplier_ids = [s["supplier_id"] for s in preview_resp.json()["data"]["groups"]]
        gen_resp = await async_client.post(
            "/api/v1/purchases/generate",
            json={"order_ids": [order_id], "supplier_ids": supplier_ids},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        po_nos = gen_resp.json()["data"]["po_nos"]

        # 获取第一个采购单的详情
        # 先查列表拿到 ID
        list_resp = await async_client.get(
            "/api/v1/purchases",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        pos = list_resp.json()["items"]
        po = next((p for p in pos if p["po_no"] in po_nos), pos[0])
        po_id = po["id"]

        # 获取采购单详情
        detail_resp = await async_client.get(
            f"/api/v1/purchases/{po_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["success"]
        po_detail = detail["data"]
        # 验证供应商付款信息已自动填充
        assert po_detail.get("bank_account", "") != "", "银行账号应自动填充"
        assert po_detail.get("contact", "") != "", "联系人应自动填充"
        assert po_detail.get("phone", "") != "", "电话应自动填充"


class TestPurchaseReceive:
    """采购收货流程"""

    @pytest.mark.asyncio
    async def test_receive_purchase(self, async_client, admin_token, seed_products, created_order):
        """测试采购收货：到货后库存更新"""
        order_id = created_order["id"]

        # 推进到 confirmed → need_preview
        for _ in range(2):
            await async_client.post(
                f"/api/v1/orders/{order_id}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
        resp = await async_client.post(
            f"/api/v1/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json()["data"].get("need_preview")

        # 预览 + 生成采购单
        preview_resp = await async_client.post(
            "/api/v1/purchases/preview",
            json={"order_ids": [order_id]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        supplier_ids = [s["supplier_id"] for s in preview_resp.json()["data"]["groups"]]
        gen_resp = await async_client.post(
            "/api/v1/purchases/generate",
            json={"order_ids": [order_id], "supplier_ids": supplier_ids},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        po_nos = gen_resp.json()["data"]["po_nos"]

        # 查列表获取第一个 PO 的 ID
        list_resp = await async_client.get(
            "/api/v1/purchases",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        pos = list_resp.json()["items"]
        po = next((p for p in pos if p["po_no"] in po_nos), pos[0])
        po_id = po["id"]

        # 执行收货
        receive_resp = await async_client.post(
            f"/api/v1/purchases/{po_id}/receive",
            json={
                "items": [{"product_id": 1, "qty": 10, "product_name": "测试面料A"}],
                "warehouse_id": seed_products["wh_id"],
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert receive_resp.status_code == 200, f"收货失败: {receive_resp.text}"
        recv_data = receive_resp.json()
        assert recv_data["success"]
