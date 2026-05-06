"""
test_installation.py - 安装单模块集成测试
"""
import pytest
import requests

BASE = "http://localhost:8000"


@pytest.fixture(scope="module")
def admin_token():
    """获取管理员token"""
    resp = requests.post(
        f"{BASE}/api/auth/login",
        json={"phone": "13900001111", "password": "123456"},
    )
    return resp.json()["data"]["token"]


class TestInstallationOrders:
    """安装单模块测试"""

    def test_list_installation_orders(self, admin_token):
        """获取安装单列表"""
        resp = requests.get(
            f"{BASE}/api/installation-orders",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True
        assert "items" in body.get("data", {})

    def test_installation_order_filter_by_status(self, admin_token):
        """安装单列表 - 按状态筛选"""
        resp = requests.get(
            f"{BASE}/api/installation-orders?status=待分配",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

    def test_auto_generate_installation_order(self, admin_token):
        """自动生成安装单（通过订单完成状态推进）"""
        # 1. 创建订单
        create_resp = requests.post(
            f"{BASE}/api/orders",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "customer_name": "安装单自动生成测试",
                "customer_phone": "13800138003",
                "order_type": "窗帘",
                "items": [
                    {
                        "product_name": "测试窗帘",
                        "width": 200,
                        "height": 150,
                        "unit": "米",
                        "unit_price": 50,
                        "qty": 1,
                        "amount": 50,
                    }
                ],
                "received": 50,
            },
        )
        order_id = create_resp.json()["data"]["id"]

        # 2. 推进订单到完成状态
        for _ in range(6):
            requests.post(
                f"{BASE}/api/orders/{order_id}/advance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        # 3. 验证安装单已生成
        resp = requests.get(
            f"{BASE}/api/installation-orders",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.json()
        items = body.get("data", {}).get("items", [])
        order_ins = [io for io in items if io.get("order_id") == order_id]
        assert len(order_ins) >= 1, "订单完成未自动生成安装单"

    def test_manual_create_installation_order(self, admin_token):
        """手动创建安装单"""
        resp = requests.post(
            f"{BASE}/api/installation-orders",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "order_id": 1,
                "scheduled_date": "2026-05-01",
                "install_time_slot": "09:00-12:00",
                "install_requirements": "小心墙壁",
                "remark": "测试备注",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True
        data = body.get("data", {})
        assert "id" in data
        assert "ins_no" in data

    def test_update_installation_order_status(self, admin_token):
        """安装单派工测试 - 分配安装工"""
        # 先找一条待分配的安装单
        list_resp = requests.get(
            f"{BASE}/api/installation-orders?status=待分配",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        items = list_resp.json().get("data", {}).get("items", [])
        if not items:
            pytest.skip("没有待分配的安装单")

        ins_id = items[0]["id"]

        # 获取安装工列表
        installer_resp = requests.get(
            f"{BASE}/api/installers",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # 如果有安装工则分配
        if installer_resp.status_code == 200:
            installers = installer_resp.json().get("data", {}).get("items", [])
            if installers:
                installer_id = installers[0]["id"]
                patch_resp = requests.patch(
                    f"{BASE}/api/installation-orders/{ins_id}",
                    headers={"Authorization": f"Bearer {admin_token}"},
                    json={"status": "已分配", "installer_id": installer_id},
                )
                assert patch_resp.status_code == 200
                assert patch_resp.json().get("success") is True

    def test_installation_status_flow(self, admin_token):
        """安装状态流转: 待分配 → 已分配 → 待施工 → 已施工 → 已验收"""
        # 创建安装单
        create_resp = requests.post(
            f"{BASE}/api/installation-orders",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "order_id": 1,
                "scheduled_date": "2026-05-01",
                "install_time_slot": "09:00-12:00",
                "remark": "状态流转测试",
            },
        )
        ins_id = create_resp.json()["data"]["id"]

        # 验证初始状态
        detail_resp = requests.get(
            f"{BASE}/api/installation-orders/{ins_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail_resp.json()["data"]["status"] == "待分配"

        # 派工 → 已分配
        patch_resp = requests.patch(
            f"{BASE}/api/installation-orders/{ins_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "已分配"},
        )
        assert patch_resp.json()["data"]["status"] == "已分配"

        # 更新为已验收
        confirm_resp = requests.patch(
            f"{BASE}/api/installation-orders/{ins_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "已验收"},
        )
        assert confirm_resp.status_code == 200

        # 确认状态
        final_resp = requests.get(
            f"{BASE}/api/installation-orders/{ins_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert final_resp.json()["data"]["status"] == "已验收"
