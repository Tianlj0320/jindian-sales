"""
test_customers.py - 客户模块集成测试
"""
import pytest
import requests
import time

BASE = "http://localhost:8000"


@pytest.fixture(scope="module")
def admin_token():
    """获取管理员token"""
    resp = requests.post(
        f"{BASE}/api/auth/login",
        json={"phone": "13900001111", "password": "123456"},
    )
    return resp.json()["data"]["token"]


class TestCustomers:
    """客户模块测试"""

    def test_list_customers(self, admin_token):
        """获取客户列表"""
        resp = requests.get(
            f"{BASE}/api/customers",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True
        assert "items" in body.get("data", {})

    def test_create_customer(self, admin_token):
        """创建客户"""
        phone = f"138{int(time.time()) % 100000000:08d}"
        resp = requests.post(
            f"{BASE}/api/customers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "QA测试客户",
                "phone": phone,
                "type": "零售",
                "address": "测试地址",
                "community": "测试小区",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True
        data = body.get("data", {})
        assert "id" in data
        assert data.get("phone") == phone
        return data["id"]

    def test_create_duplicate_phone(self, admin_token):
        """客户手机号查重 - 重复手机号应被拒绝"""
        phone = f"138{int(time.time()) % 100000000:08d}"
        # 第一次创建
        resp1 = requests.post(
            f"{BASE}/api/customers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "重复测试客户A", "phone": phone, "type": "零售"},
        )
        assert resp1.status_code == 200
        assert resp1.json().get("success") is True

        # 第二次创建相同手机号 → 应失败
        resp2 = requests.post(
            f"{BASE}/api/customers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "重复测试客户B", "phone": phone, "type": "零售"},
        )
        body2 = resp2.json()
        assert body2.get("success") is False, "相同手机号应拒绝创建"

    def test_get_customer_detail(self, admin_token):
        """获取客户详情"""
        resp = requests.get(
            f"{BASE}/api/customers/1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True
        assert "name" in body.get("data", {})
        assert "phone" in body.get("data", {})

    def test_update_customer(self, admin_token):
        """更新客户信息"""
        phone = f"138{int(time.time()) % 100000000:08d}"
        # 创建
        create_resp = requests.post(
            f"{BASE}/api/customers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "更新测试客户", "phone": phone, "type": "零售"},
        )
        customer_id = create_resp.json()["data"]["id"]

        # 更新
        update_resp = requests.put(
            f"{BASE}/api/customers/{customer_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "更新后客户名", "phone": phone, "type": "全屋"},
        )
        assert update_resp.status_code == 200
        body = update_resp.json()
        assert body.get("success") is True
        assert body["data"]["name"] == "更新后客户名"
