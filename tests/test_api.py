#!/usr/bin/env python3
"""
金典软装销售系统 · API 冒烟测试
用法: python tests/test_api.py
"""
import sys, os, json, time
import requests

BASE = "http://localhost:8000"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

passed = failed = 0
token  = ""

def check(name, ok, detail=""):
    global passed, failed
    if ok:
        print(f"  {GREEN}✓{RESET} {name}")
        passed += 1
    else:
        print(f"  {RED}✗{RESET} {name}  {YELLOW}{detail}{RESET}")
        failed += 1

def GET(path, expected=200):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.get(BASE + path, headers=h, timeout=5)
    ok = r.status_code == expected
    try:
        body = r.json()
        return r.status_code, body
    except:
        return r.status_code, {}

def POST(path, data, expected=200):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.post(BASE + path, json=data, headers=h, timeout=5)
    ok = r.status_code == expected
    try:
        body = r.json()
        return r.status_code, body
    except:
        return r.status_code, {}

# ── 1. 服务启动 ────────────────────────────────────
print("\n[1] 服务启动")
r = requests.get(BASE + "/health", timeout=3)
check("健康检查 /health", r.status_code == 200 and r.json().get("status") == "ok")
r = requests.get(BASE + "/", timeout=3, allow_redirects=False)
check("根路径 / → redirect", r.status_code in (301, 302, 307))
r = requests.get(BASE + "/static/index.html", timeout=5)
check("静态页面 /static/index.html", r.status_code == 200)
check("Vue.js 加载", r.status_code == 200 and "<script" in r.text)

# ── 2. 认证 ────────────────────────────────────────
print("\n[2] 认证")
code, body = POST("/api/auth/login", {"phone": "13900001111", "password": "jd8888"})
check("登录成功", code == 200 and "token" in body, str(body))
token = body.get("token", "") if isinstance(body, dict) else ""

# ── 3. 基础资料（需认证） ────────────────────────────
print("\n[3] 供应商管理")
code, body = GET("/api/products/suppliers")
check("获取供应商列表", code == 200 and isinstance(body, dict) and "items" in body)

print("\n[4] 产品资料")
code, body = GET("/api/products")
check("获取产品列表", code == 200 and isinstance(body, dict) and "items" in body)

print("\n[5] 客户资料")
code, body = GET("/api/customers")
check("获取客户列表", code == 200 and isinstance(body, dict) and "items" in body)

print("\n[6] 员工资料")
code, body = GET("/api/employees")
check("获取员工列表", code == 200 and isinstance(body, dict) and "items" in body)

# ── 4. 订单 ────────────────────────────────────────
print("\n[7] 订单管理")
code, body = GET("/api/orders?page=1&page_size=10")
check("获取订单列表", code == 200 and isinstance(body, (dict, list)))

# ── 5. 报表 ───────────────────────────────────────
print("\n[8] 报表")
code, body = GET("/api/dashboard")
check("仪表盘 /api/dashboard", code == 200 and isinstance(body, dict))
code, body = GET("/api/reports/sales?year=2026&month=4")
check("销售趋势 /api/reports/sales", code == 200 and isinstance(body, (dict, list)))
code, body = GET("/api/reports/product-rank?year=2026&month=4")
check("产品排名 /api/reports/product-rank", code == 200 and isinstance(body, (dict, list)))

# ── 6. 打印 ───────────────────────────────────────
print("\n[9] 打印功能")
if token:
    _, orders = GET("/api/orders?page=1&page_size=1")
    order_id = None
    if isinstance(orders, dict):
        order_id = orders.get("items", [{}])[0].get("id") if orders.get("items") else None
    elif isinstance(orders, list) and orders:
        order_id = orders[0].get("id")
    if order_id:
        r = requests.get(f"{BASE}/api/print/contract/{order_id}",
                         headers={"Authorization": f"Bearer {token}"}, timeout=5)
        check(f"打印合同 /api/print/contract/{order_id}", r.status_code == 200, f"got {r.status_code}")
        r = requests.get(f"{BASE}/api/print/measurement/{order_id}",
                         headers={"Authorization": f"Bearer {token}"}, timeout=5)
        check(f"测量单 /api/print/measurement/{order_id}", r.status_code == 200, f"got {r.status_code}")
    else:
        print(f"  {YELLOW}⚠{RESET} 无订单，跳过打印测试")
else:
    print(f"  {YELLOW}⚠{RESET} 无 token，跳过打印测试")

# ── 摘要 ───────────────────────────────────────────
print(f"\n{'─'*40}")
total  = passed + failed
color  = GREEN if failed == 0 else RED
print(f"{color}结果: {passed}/{total} 通过{RESET}")
print(f"失败: {failed}")
sys.exit(0 if failed == 0 else 1)
