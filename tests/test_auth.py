"""
test_auth.py - 认证模块集成测试
"""
import pytest
import requests
import time

BASE = "http://localhost:8000"


class TestAuth:
    """认证模块测试"""

    def test_login_success(self):
        """登录成功 - 正确手机号+密码"""
        resp = requests.post(
            f"{BASE}/api/auth/login",
            json={"phone": "13900001111", "password": "123456"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True
        assert "token" in body.get("data", {})
        assert body["data"]["user_id"] == 1

    def test_login_wrong_password(self):
        """登录失败 - 错误密码"""
        resp = requests.post(
            f"{BASE}/api/auth/login",
            json={"phone": "13900001111", "password": "wrongpassword"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is False
        assert "密码错误" in body.get("error", "")

    def test_login_wrong_phone(self):
        """登录失败 - 不存在的手机号"""
        resp = requests.post(
            f"{BASE}/api/auth/login",
            json={"phone": "13999999999", "password": "any"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is False

    def test_token_me(self):
        """验证Token - 获取当前用户信息"""
        # 先登录获取token
        login_resp = requests.post(
            f"{BASE}/api/auth/login",
            json={"phone": "13900001111", "password": "123456"},
        )
        token = login_resp.json()["data"]["token"]

        resp = requests.get(
            f"{BASE}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True
        assert body["data"]["user_id"] == 1

    def test_token_invalid(self):
        """验证Token - 无效token"""
        resp = requests.get(
            f"{BASE}/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_12345"},
        )
        assert resp.status_code == 401

    def test_protected_api_without_token(self):
        """受保护API - 无token返回401"""
        resp = requests.get(f"{BASE}/api/products")
        assert resp.status_code == 401
        body = resp.json()
        assert body.get("success") is False
        assert "登录" in body.get("error", "")

    def test_protected_api_with_valid_token(self):
        """受保护API - 有效token可访问"""
        login_resp = requests.post(
            f"{BASE}/api/auth/login",
            json={"phone": "13900001111", "password": "123456"},
        )
        token = login_resp.json()["data"]["token"]

        resp = requests.get(
            f"{BASE}/api/products",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
