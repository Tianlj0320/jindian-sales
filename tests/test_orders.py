"""
test_orders.py - 订单模块集成测试
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


class TestOrders:
    """订单模块测试"""

    def test_list_orders(self, admin_token):
        """获取订单列表"""
        resp = requests.get(
            f"{BASE}/api/orders?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True
        assert "items" in body.get("data", {})
        assert "total" in body.get("data", {})

    def test_list_orders_filter_by_status(self, admin_token):
        """订单列表 - 按状态筛选"""
        resp = requests.get(
            f"{BASE}/api/orders?status_key=created",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True

    def test_create_order_status_created(self, admin_token):
        """创建订单 → 状态 created"""
        resp = requests.post(
            f"{BASE}/api/orders",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "customer_name": "测试客户",
                "customer_phone": "13800138000",
                "order_type": "窗帘",
                "items": [
                    {
                        "product_name": "测试窗帘",
                        "product_type": "窗帘",
                        "width": 200,
                        "height": 150,
                        "unit": "米",
                        "unit_price": 50,
                        "qty": 1,
                        "amount": 50,
                    }
                ],
                "received": 0,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True
        data = body.get("data", {})
        assert "id" in data
        assert "order_no" in data
        return data["id"]

    def test_order_status_transitions(self, admin_token):
        """测试订单状态流转: created → confirmed → completed"""
        # 1. 创建订单
        create_resp = requests.post(
            f"{BASE}/api/orders",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "customer_name": "状态流转测试客户",
                "customer_phone": "13800138001",
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

        # 2. 确认订单 → confirmed
        adv_resp = requests.post(
            f"{BASE}/api/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert adv_resp.status_code == 200
        body = adv_resp.json()
        assert body.get("success") is True
        assert body["data"]["status_key"] == "confirmed"

        # 3. 推进 → split
        adv_resp = requests.post(
            f"{BASE}/api/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = adv_resp.json()
        assert body.get("success") is True
        assert body["data"]["status_key"] == "split"

        # 4. 推进 → purchasing
        adv_resp = requests.post(
            f"{BASE}/api/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = adv_resp.json()
        assert body.get("success") is True
        assert body["data"]["status_key"] == "purchasing"

        # 5. 推进 → stocked
        adv_resp = requests.post(
            f"{BASE}/api/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = adv_resp.json()
        assert body.get("success") is True
        assert body["data"]["status_key"] == "stocked"

        # 6. 推进 → processing
        adv_resp = requests.post(
            f"{BASE}/api/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = adv_resp.json()
        assert body.get("success") is True
        assert body["data"]["status_key"] == "processing"

        # 7. 推进 → completed（自动生成安装单）
        adv_resp = requests.post(
            f"{BASE}/api/orders/{order_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = adv_resp.json()
        assert body.get("success") is True
        assert body["data"]["status_key"] == "install_order_generated"
        assert "安装单" in body.get("data", {}).get("auto_action", "")

    def test_order_delete(self, admin_token):
        """删除订单"""
        # 先创建订单
        create_resp = requests.post(
            f"{BASE}/api/orders",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "customer_name": "删除测试客户",
                "customer_phone": "13800138002",
                "order_type": "窗帘",
                "items": [
                    {
                        "product_name": "测试窗帘",
                        "width": 100,
                        "height": 100,
                        "unit": "米",
                        "unit_price": 30,
                        "qty": 1,
                        "amount": 30,
                    }
                ],
            },
        )
        order_id = create_resp.json()["data"]["id"]

        # 删除
        del_resp = requests.delete(
            f"{BASE}/api/orders/{order_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert del_resp.status_code == 200
        assert del_resp.json().get("success") is True

        # 确认已删除
        get_resp = requests.get(
            f"{BASE}/api/orders/{order_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert get_resp.json().get("success") is False

    def test_order_detail(self, admin_token):
        """获取订单详情"""
        resp = requests.get(
            f"{BASE}/api/orders/1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True
        assert "order_no" in body.get("data", {})
