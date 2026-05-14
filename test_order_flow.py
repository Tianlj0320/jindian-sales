#!/usr/bin/env python3
"""订单全流程测试脚本"""
import requests
import json
import time

BASE = "http://localhost:8000"

def login():
    r = requests.post(f"{BASE}/api/auth/login", json={"phone":"13900000001","password":"jd8888"})
    d = r.json()
    assert d.get("success"), f"登录失败: {d}"
    return d["token"]

def api(method, path, token=None, data=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if data:
        headers["Content-Type"] = "application/json"
    r = requests.request(method, f"{BASE}{path}", headers=headers, json=data)
    return r.status_code, r.json()

token = login()
print(f"✅ 登录成功")

# 1. 创建订单
payload = {
    "customer_id": 1,
    "customer_name": "测试客户",
    "customer_phone": "13900001111",
    "order_type": "窗帘",
    "content": "窗帘测试",
    "quote_amount": 1000,
    "discount_amount": 0,
    "round_amount": 0,
    "amount": 1000,
    "received": 500,
    "order_date": "2026-04-25",
    "delivery_date": "2026-05-01",
    "delivery_method": "上门安装",
    "items": []
}
code, resp = api("POST", "/api/orders", token, payload)
print(f"1. 创建订单: {code} -> {resp}")
order_id = resp.get("id") or resp.get("data", {}).get("id")
assert order_id, f"创建订单失败: {resp}"
print(f"   订单ID={order_id}, 状态=created")

# 状态流转列表
STATUS_FLOW = [
    ("confirmed",    "已确认"),
    ("split",        "已拆分(采购)"),
    ("purchasing",   "采购中"),
    ("stocked",      "已到货"),
    ("processing",   "生产中"),
    ("completed",    "已完成"),
    ("install_order_generated", "安装单已生成"),
    ("shipped",      "已发货"),
    ("installed",    "已安装"),
    ("accepted",     "已验收"),
]

print(f"\n2. 开始状态流转测试:")
for status_key, status_name in STATUS_FLOW:
    code, resp = api("PUT", f"/api/orders/{order_id}/status", token, {"new_status_key": status_key})
    if code == 200:
        print(f"   ✅ {status_name} ({status_key})")
    else:
        print(f"   ❌ {status_name} ({status_key}) -> {code} {resp}")
    time.sleep(0.3)

# 3. 检查订单状态历史
code, resp = api("GET", f"/api/orders/{order_id}", token)
print(f"\n3. 订单最终状态:")
if isinstance(resp, dict):
    order = resp.get("data") or resp
    print(f"   status_key={order.get('status_key')}")
    print(f"   history={json.dumps(order.get('history', []), ensure_ascii=False)}")

# 4. 测试采购管理接口
code, resp = api("GET", "/api/purchase-orders", token)
print(f"\n4. 采购管理: {code} -> {resp}")

# 5. 测试生产管理接口
code, resp = api("GET", "/api/orders?status_key=processing", token)
print(f"5. 生产管理(processing): {code} -> items={len(resp.get('data', {}).get('items', []))}")

# 6. 测试安装管理接口
code, resp = api("GET", "/api/installation-orders", token)
print(f"6. 安装管理: {code} -> {resp}")

print("\n✅ 流程测试完成")