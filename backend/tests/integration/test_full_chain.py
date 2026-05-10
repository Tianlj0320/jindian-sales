"""
全链路整合测试 — 完整业务流程验证

模拟真实场景：客户王先生到店订购窗帘 → 量尺 → 确认 → 采购 → 入库 → 安装 → 验收 → 收款

数据流：
  基础资料（客户/产品/供应商）
    → 订单（含物料明细）
    → 采购拆分预览 → 生成采购单
    → 收货入库 → 库存更新
    → 安装派工 → 安装完成
    → 验收 → 收款 → 应收款结清

API 响应格式约定：
  - 单对象响应: {success, data: {...}}
  - 分页响应:   {success, total, page, page_size, items: [...]}
  - Advance 返回: {success, data: {status_key, status_label, ...}}
  - confirmed→split 的特殊 advance 返回 {success, data: {need_preview: True, ...}}
  - 订单详情: {success, data: {status_key, customer_name, items: [...], ...}}
  - 创建订单: {success, data: {id, order_no}}
"""

from __future__ import annotations

import pytest

# 测试间共享状态（pytest 每个测试方法独立实例，不能用 self）
_SHARED: dict = {}


class TestFullChainIntegration:
    """全链路整合测试"""

    # ═══════════════════════════════════════════════════════════
    # Phase 1: 基础资料验证
    # ═══════════════════════════════════════════════════════════

    def test_phase1_master_data_exists(self, seed_master_data):
        """Phase 1 — 验证种子数据已正确创建"""
        assert seed_master_data["cust_wang"] > 0
        assert seed_master_data["cust_li"] > 0
        assert seed_master_data["sup_hz"] > 0
        assert seed_master_data["sup_gz"] > 0
        assert len([k for k in seed_master_data if k.startswith("prod_")]) == 6

    @pytest.mark.asyncio
    async def test_phase1_customer_query(self, async_client, admin_token, seed_master_data):
        """Phase 1 — 客户列表"""
        resp = await async_client.get(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_phase1_product_search(self, async_client, admin_token, seed_master_data):
        """Phase 1 — 产品搜索（含供应商关联验证）"""
        resp = await async_client.get(
            "/api/v1/products/search?keyword=雪尼尔",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) >= 1
        assert items[0].get("supplier_name") == "杭州布艺供应商"

        resp = await async_client.get(
            "/api/v1/products/search?keyword=ACC-GZ-001",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        items = resp.json()["data"]
        assert len(items) == 1
        assert items[0]["name"] == "罗马杆"

    @pytest.mark.asyncio
    async def test_phase1_supplier_detail(self, async_client, admin_token, seed_master_data):
        """Phase 1 — 供应商列表验证银行信息"""
        resp = await async_client.get(
            "/api/v1/products/suppliers",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        hz = [s for s in items if s["name"] == "杭州布艺供应商"]
        assert len(hz) == 1
        assert hz[0].get("bank_account", "") != ""

    # ═══════════════════════════════════════════════════════════
    # Phase 2: 创建订单
    # ═══════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_phase2_create_order(self, async_client, admin_token, seed_master_data):
        """Phase 2 — 创建订单（客厅窗帘 + 阳台窗纱）

        创建订单 API 返回 {success, data: {id, order_no}}，
        完整数据需通过详情接口验证。
        """
        resp = await async_client.post(
            "/api/v1/orders",
            json={
                "customer_name": "王建国",
                "customer_phone": "13958123456",
                "order_type": "窗帘",
                "order_date": "2026-05-10",
                "delivery_method": "上门安装",
                "install_address": "杭州市西湖区文三路100号",
                "remark": "客厅落地窗，阳台推拉窗",
                "items": [
                    {"product_id": seed_master_data["prod_1"],
                     "product_name": "高档雪尼尔布料", "product_code": "FAB-HZ-001",
                     "width": 2.0, "height": 2.8, "qty": 2, "unit_price": 120.0,
                     "amount": 240.0, "material_type": "主料",
                     "supplier_id": seed_master_data["sup_hz"],
                     "supplier_name": "杭州布艺供应商"},
                    {"product_id": seed_master_data["prod_6"],
                     "product_name": "窗纱面料", "product_code": "ACC-GZ-003",
                     "width": 3.0, "height": 2.5, "qty": 1, "unit_price": 60.0,
                     "amount": 60.0, "material_type": "主料",
                     "supplier_id": seed_master_data["sup_gz"],
                     "supplier_name": "广州辅料批发"},
                    {"product_id": seed_master_data["prod_4"],
                     "product_name": "罗马杆", "product_code": "ACC-GZ-001",
                     "qty": 2, "unit_price": 35.0, "amount": 70.0,
                     "material_type": "辅料",
                     "supplier_id": seed_master_data["sup_gz"],
                     "supplier_name": "广州辅料批发"},
                ],
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200, f"创建订单失败: {resp.text}"
        data = resp.json()
        assert data["success"]
        order_create = data["data"]
        order_id = order_create["id"]
        assert order_id > 0
        assert order_create["order_no"] != ""
        _SHARED["order_id"] = order_id

        # 通过详情接口验证完整数据
        detail = await async_client.get(
            f"/api/v1/orders/{order_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail.status_code == 200
        order = detail.json()["data"]
        assert order["customer_name"] == "王建国"
        assert order["status_key"] == "initial"
        assert len(order["items"]) == 3

    @pytest.mark.asyncio
    async def test_phase2_order_detail(self, async_client, admin_token):
        """Phase 2 — 订单详情"""
        resp = await async_client.get(
            f"/api/v1/orders/{_SHARED['order_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == _SHARED["order_id"]
        assert data["customer_name"] == "王建国"
        assert len(data["items"]) == 3
        for item in data["items"]:
            assert "supplier_name" in item

    # ═══════════════════════════════════════════════════════════
    # Phase 3: 订单状态推进
    # ═══════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_phase3_advance_to_confirmed(self, async_client, admin_token):
        """Phase 3 — 状态推进 initial → measured → confirmed

        Advance 返回 {success, data: {status_key, status_label, ...}}
        """
        for expected in ["measured", "confirmed"]:
            resp = await async_client.post(
                f"/api/v1/orders/{_SHARED['order_id']}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert resp.status_code == 200
            assert resp.json()["data"]["status_key"] == expected

    # ═══════════════════════════════════════════════════════════
    # Phase 4: 采购拆分与生成
    # ═══════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_phase4_purchase_split(self, async_client, admin_token, seed_master_data):
        """Phase 4 — 采购拆分预览 + 生成 + 详情验证（完整子流程）

        confirmed → split 需要两步：
          1. advance 返回 need_preview 确认请求
          2. purchase generate 实际将订单推进到 split

        预览返回 {success, data: {groups: [...], order_ids: [...], ...}}
        生成返回 {success, data: {po_nos: [...]}}
        采购列表为分页响应: {success, total, items: [...]}
        采购详情为单对象响应: {success, data: {bank_account, contact, ...}}
        """
        oid = _SHARED["order_id"]

        # 推进到 split：confirmed → [need_preview] → purchase generate → split
        resp = await async_client.post(
            f"/api/v1/orders/{oid}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        advance_data = resp.json()["data"]
        assert advance_data.get("need_preview"), "confirmed 后 advance 应返回 need_preview"

        # 预览
        resp = await async_client.post(
            "/api/v1/purchases/preview",
            json={"order_ids": [oid]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        preview = resp.json()
        assert preview["success"]
        groups = preview["data"]["groups"]
        assert len(groups) >= 2

        sup_names = [s["supplier_name"] for s in groups]
        assert "杭州布艺供应商" in sup_names
        assert "广州辅料批发" in sup_names
        for s in groups:
            assert s["total_amount"] > 0
            assert len(s["items"]) > 0

        # 生成采购单
        supplier_ids = [s["supplier_id"] for s in groups]
        resp = await async_client.post(
            "/api/v1/purchases/generate",
            json={"order_ids": [oid], "supplier_ids": supplier_ids},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200, f"生成采购单失败: {resp.text}"
        gen_data = resp.json()
        assert gen_data["success"]
        po_nos = gen_data["data"]["po_nos"]
        assert len(po_nos) >= 2

        # 验证订单已推进到 split
        detail = await async_client.get(
            f"/api/v1/orders/{oid}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail.json()["data"]["status_key"] == "split"

        # 保存采购单 ID（通过列表查询）
        list_resp = await async_client.get(
            "/api/v1/purchases",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        pos = list_resp.json()["items"]
        # 过滤属于当前订单的 PO
        pos_for_order = [po for po in pos if po["po_no"] in po_nos]
        assert len(pos_for_order) >= 2

        _SHARED["purchase_orders"] = pos_for_order

    @pytest.mark.asyncio
    async def test_phase4_purchase_list(self, async_client, admin_token):
        """Phase 4 — 采购单列表"""
        resp = await async_client.get(
            "/api/v1/purchases",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        for po in data["items"]:
            assert po["supplier_name"] != ""
            assert po["contact"] != ""

    @pytest.mark.asyncio
    async def test_phase4_purchase_detail(self, async_client, admin_token):
        """Phase 4 — 采购单详情验证供应商信息"""
        po = _SHARED["purchase_orders"][0]
        resp = await async_client.get(
            f"/api/v1/purchases/{po['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        detail = resp.json()["data"]
        assert detail.get("bank_account", "") != ""
        assert detail.get("contact", "") != ""
        assert detail.get("phone", "") != ""

    # ═══════════════════════════════════════════════════════════
    # Phase 5: 采购收货
    # ═══════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_phase5_receive_purchase(self, async_client, admin_token, seed_master_data):
        """Phase 5 — 全部采购单收货 + 订单推进到 stocked"""
        oid = _SHARED["order_id"]
        pos = _SHARED["purchase_orders"]

        # 收货前查询库存可用
        resp = await async_client.get(
            "/api/v1/warehouses/inventory",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

        # 逐个 PO 获取明细并执行收货（必须全部收货才能推进到 stocked）
        for po in pos:
            detail = await async_client.get(
                f"/api/v1/purchases/{po['id']}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert detail.status_code == 200
            po_detail = detail.json()["data"]

            receive_items = [
                {"product_id": item["product_id"], "qty": item["quantity"],
                 "product_name": item["product_name"]}
                for item in po_detail.get("po_items", [])
            ]
            if not receive_items:
                continue

            resp = await async_client.post(
                f"/api/v1/purchases/{po['id']}/receive",
                json={"items": receive_items, "warehouse_id": seed_master_data["wh_main"]},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert resp.status_code == 200, f"收货失败 (PO {po['id']}): {resp.text}"

        # 全部收货后推进订单到 stocked（split → purchasing → stocked）
        resp = await async_client.post(
            f"/api/v1/orders/{oid}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json()["data"]["status_key"] == "purchasing"

        resp = await async_client.post(
            f"/api/v1/orders/{oid}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json()["data"]["status_key"] == "stocked"

    # ═══════════════════════════════════════════════════════════
    # Phase 6: 加工 → 安装
    # ═══════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_phase6_create_install(self, async_client, admin_token, seed_master_data):
        """Phase 6 — 状态推进至 install_scheduled + 创建安装单"""
        oid = _SHARED["order_id"]

        # 先推进到 completed
        for expected in ["processing", "completed"]:
            resp = await async_client.post(
                f"/api/v1/orders/{oid}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert resp.json()["data"]["status_key"] == expected

        # 先手动创建安装单，再 advance 到 install_scheduled
        # （advance 端点会检测到已有安装单，不会重复自动创建）
        resp = await async_client.post(
            "/api/v1/installations/orders",
            json={
                "order_id": oid,
                "team_id": seed_master_data["team_1"],
                "installer_id": seed_master_data["installer_zhao"],
                "scheduled_date": "2026-05-15",
                "install_time_slot": "上午",
                "labor_cost": 300.0,
                "material_cost": 50.0,
                "remark": "客厅落地窗+阳台推拉窗",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200, f"创建安装单失败: {resp.text}"
        ins_data = resp.json()
        assert ins_data["success"]
        _SHARED["ins_id"] = ins_data["data"]["id"]

        # 推进到 install_scheduled（已有安装单，不会重复创建）
        resp = await async_client.post(
            f"/api/v1/orders/{oid}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json()["data"]["status_key"] == "install_scheduled"

        # 推进安装状态
        for status in ["安装中", "已完成"]:
            resp = await async_client.put(
                f"/api/v1/installations/orders/{_SHARED['ins_id']}/status",
                params={"status": status},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert resp.status_code == 200

        # 订单状态推进到 accepted
        for expected in ["installed", "accepted"]:
            resp = await async_client.post(
                f"/api/v1/orders/{oid}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert resp.json()["data"]["status_key"] == expected

    # ═══════════════════════════════════════════════════════════
    # Phase 7: 财务
    # ═══════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_phase7_receive_payment(self, async_client, admin_token):
        """Phase 7 — 收款确认"""
        resp = await async_client.post(
            "/api/v1/finance/receive",
            json={
                "order_id": _SHARED["order_id"],
                "amount": 370.0,
                "method": "微信",
                "remark": "客户王建国全额付款",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200, f"收款失败: {resp.text}"
        assert resp.json()["success"]

    # ═══════════════════════════════════════════════════════════
    # Phase 8: 仪表盘
    # ═══════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_phase8_dashboard(self, async_client, admin_token):
        """Phase 8 — 仪表盘 KPI 数据"""
        resp = await async_client.get(
            "/api/v1/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
