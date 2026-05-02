# 金典软装销售系统 · 代码规范手册

> ⚠️ **必读**：修 Bug 时先查本文档，确认同类问题是否存在于其他模块。

---

## 一、API 响应格式（统一！）

### ✅ 正确做法
```python
from app.core.response import success_response, error_response, list_response

# 单条操作（POST/PUT/DELETE）
return success_response(data={"id": new_id})
return error_response(error="记录不存在")

# 列表查询
return list_response(items=result, total=count)
```

### ❌ 错误做法（已废弃）
```python
# 禁止：直接返回 dict 或自定义格式
return {"code": 0, "data": xxx}
return SomeCustomResponse(...)
```

### 🔍 自检：哪些模块还没统一？
```bash
grep -r "CommonResponse\|success_response\|error_response" app/api/ --include="*.py"
# 对比：哪些 .py 里没有用到这三个函数
```

---

## 二、数据库字段映射（前后端一致）

### 规则：字段名 = 数据库列名 = 前端 JSON key

| 后端 Python | 前端 JS | 数据库 |
|-------------|---------|--------|
| `customer_id` | `customerId` 或 `customer_id` | `customer_id` |
| `order_no` | `orderNo` 或 `order_no` | `order_no` |
| `quote_amount` | `quoteAmount` 或 `quote_amount` | `quote_amount` |

### ⚠️ 自查清单（修字段时必查）
1. `app/models.py` — 列名
2. `app/schemas.py` — Pydantic 字段
3. `app/api/xxx.py` — API 返回的 dict 构造
4. `static/js/01-api.js` — API 调用
5. `static/js/xx-*.js` — 表单/列表的字段绑定

**查同类字段：**
```bash
# 例如：修改了 orders 的 quote_amount，其他表有没有类似金额字段？
grep -rn "quote_amount\|discount_amount\|round_amount" app/ static/js/ --include="*.py" --include="*.js"
```

---

## 三、CRUD 操作规范

### 通用 CRUD 模板（复制到新模块时必须遵循）

```python
# app/api/xxx.py
from fastapi import APIRouter, Body, Path, Query
from app.database import async_session
from app.models import XxxModel
from app.schemas import XxxResponse, CommonResponse
from sqlalchemy import select, func
from app.core.response import success_response, error_response, list_response

router = APIRouter(prefix="/api/xxx", tags=["模块名"])

# ── 列表 ────────────────────────────────────────
@router.get("", response_model=XxxResponse)
async def list_xxx(name: str = Query(None)):
    async with async_session() as session:
        query = select(XxxModel)
        if name:
            query = query.where(XxxModel.name == name)
        result = await session.execute(query)
        items = result.scalars().all()
        return list_response(items=[...], total=len(items))

# ── 详情 ────────────────────────────────────────
@router.get("/{id}", response_model=CommonResponse)
async def get_xxx(id: int = Path(...)):
    async with async_session() as session:
        result = await session.execute(select(XxxModel).where(XxxModel.id == id))
        obj = result.scalar_one_or_none()
        if not obj:
            return error_response(error="记录不存在")
        return success_response(data={...})

# ── 新增 ────────────────────────────────────────
@router.post("", response_model=CommonResponse)
async def create_xxx(req: dict = Body(...)):
    async with async_session() as session:
        obj = XxxModel(...)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return success_response(data={"id": obj.id})

# ── 修改 ────────────────────────────────────────
@router.put("/{id}", response_model=CommonResponse)
async def update_xxx(id: int, req: dict = Body(...)):
    async with async_session() as session:
        result = await session.execute(select(XxxModel).where(XxxModel.id == id))
        obj = result.scalar_one_or_none()
        if not obj:
            return error_response(error="记录不存在")
        # 逐字段更新
        for field in ["name", "phone", ...]:
            if field in req:
                setattr(obj, field, req[field])
        await session.commit()
        return success_response(data={"id": id})

# ── 删除 ────────────────────────────────────────
@router.delete("/{id}", response_model=CommonResponse)
async def delete_xxx(id: int):
    async with async_session() as session:
        result = await session.execute(select(XxxModel).where(XxxModel.id == id))
        obj = result.scalar_one_or_none()
        if not obj:
            return error_response(error="记录不存在")
        await session.delete(obj)
        await session.commit()
        return success_response(message="删除成功")
```

---

## 四、常见错误对照表

### 修了一个模块的 Bug？先检查其他模块！

| 问题类型 | 检查范围 |
|---------|---------|
| 登录/认证问题 | `auth.py` + `middleware.py` + `installer.py` |
| 订单状态流转 | `orders.py` + `installation_orders.py` + `production_feedback.py` |
| 金额计算错误 | `orders.py` + `finance.py` + `reports.py` + `purchase.py` |
| 字段映射不一致 | 搜 `app/schemas.py` 所有 Response 类 |
| 前端表格显示错误 | 搜 `static/js/03-*.js` 所有字段绑定 |
| 日期格式问题 | 搜 `order_date\|delivery_date\|install_date` |
| 删除功能报错 | 所有 `DELETE` 路由，检查是否 `cascade` |

### 快速搜索命令
```bash
# 1. 搜索同类字段（在所有文件中）
grep -rn "field_name" app/ static/js/ --include="*.py" --include="*.js"

# 2. 搜索同类错误模式
grep -rn "select\|where\|scalars" app/api/ --include="*.py" | head -20

# 3. 检查所有 API 路由是否用了统一响应
grep -rn "return {" app/api/ --include="*.py" | grep -v "success_response\|error_response\|list_response"
```

---

## 五、前端 JS 规范

### API 调用层（01-api.js）
```javascript
// ✅ 统一写法
const api = async (u, m = 'GET', b = null) => {
  const r = await fetch(API + u, { method: m, headers, body: b ? JSON.stringify(b) : null });
  if (!r.ok) throw new Error(u + ' → HTTP ' + r.status);
  const d = await r.json();
  if (d.success === undefined) return d;  // 兼容无包装
  if (!d.success) throw new Error(d.error || 'API 错误');
  return d.data ?? d;
};

// ✅ 模块封装
window.apiOrders = {
  list: (params = {}) => api('/api/orders?' + new URLSearchParams(params)),
  create: (payload) => api('/api/orders', 'POST', payload),
  update: (id, payload) => api(`/api/orders/${id}`, 'PUT', payload),
  delete: (id) => api(`/api/orders/${id}`, 'DELETE'),
};
```

### 表格列字段映射（Vue/JS 中）
```javascript
// ✅ 字段名必须和 API 返回的 key 一致
columns: [
  { prop: 'order_no', label: '订单号' },      // 或 camelCase
  { prop: 'quoteAmount', label: '标价' },     // 看 API 返回什么
  { prop: 'status', label: '状态' },
]
```

---

## 六、Git 提交规范

### 格式
```
cur-gm@金典软装: [模块] 简短描述
cur-gm@金典软装: [orders] 修复 quote_amount 计算错误
cur-gm@金典软装: [auth] 统一登录响应格式
```

### 每次 commit 必须满足
- [ ] 改了什么？
- [ ] 同类问题检查了吗？（在 Git message 里注明）
- [ ] 测试通过了吗？

---

## 七、API 路由命名规范

### 命名规则：使用连字符（kebab-case）

| 正确 | 错误 | 说明 |
|------|------|------|
| `/api/purchase-orders` | `/api/purchase_orders` | 路由路径用连字符 |
| `/api/installation-orders` | `/api/installation_orders` | 路由路径用连字符 |
| `/api/production-feedback` | `/api/production_feedback` | 路由路径用连字符 |

### ⚠️ 为什么用连字符？
- HTTP 路径规范（RFC 3986）：路径区分大小写，下划线易混淆
- Swagger UI 自动转换：下划线可能被当成参数的一部分
- V3.0 新增模块全部使用连字符命名

### 路由注册（main.py）
```python
from app.api import purchase_orders, production_feedback, installation_orders

app.include_router(purchase_orders.router)      # /api/purchase-orders
app.include_router(production_feedback.router)  # /api/production-feedback
app.include_router(installation_orders.router)  # /api/installation-orders
```

### 路由与文件名对照

| 文件 | 前缀 | 说明 |
|------|------|------|
| `purchase_orders.py` | `/api/purchase-orders` | V3.0 采购单 |
| `installation_orders.py` | `/api/installation-orders` | V3.0 安装单 |
| `production_feedback.py` | `/api/production-feedback` | V3.0 生产反馈 |
| `purchase.py` | `/api/purchase` | V2.x 采购（旧） |

---

## 八、测试用例模板

### 8.1 API 功能测试模板

```python
# tests/test_purchase_orders.py
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_split_order_to_purchase_orders():
    """测试：订单拆分生成采购单"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. 创建测试订单
        login_resp = await ac.post("/api/auth/login", json={"phone": "13900000001", "password": "jd8888"})
        token = login_resp.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. 创建带供应商的订单
        order_resp = await ac.post("/api/orders", json={
            "customer_id": 1,
            "order_type": "窗帘",
            "items": [{"product_id": 1, "supplier_id": 1, "qty": 5, "unit_price": 100}]
        }, headers=headers)
        order_id = order_resp.json()["data"]["id"]

        # 3. 拆分订单
        split_resp = await ac.post(f"/api/purchase-orders/split/{order_id}", headers=headers)
        assert split_resp.json()["success"] is True
        assert len(split_resp.json()["purchase_orders"]) >= 1

@pytest.mark.asyncio
async def test_list_purchase_orders_pagination():
    """测试：采购单列表分页"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/purchase-orders?page=1&page_size=10")
        assert resp.json()["success"] is True
        assert "items" in resp.json()
        assert "total" in resp.json()

@pytest.mark.asyncio
async def test_update_installation_order_status():
    """测试：安装单状态更新"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 登录
        login_resp = await ac.post("/api/auth/login", json={"phone": "13900000001", "password": "jd8888"})
        token = login_resp.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 创建安装单
        ins_resp = await ac.post("/api/installation-orders", json={
            "order_id": 1,
            "scheduled_date": "2026-05-01",
            "installer_id": 2
        }, headers=headers)

        # 更新状态
        update_resp = await ac.patch(
            f"/api/installation-orders/{ins_resp.json()['data']['id']}",
            json={"status": "已分配"},
            headers=headers
        )
        assert update_resp.json()["success"] is True
```

### 8.2 测试用例自检清单

- [ ] 测试正常流程（happy path）
- [ ] 测试边界情况（空列表、极限分页）
- [ ] 测试权限控制（未登录返回 401）
- [ ] 测试状态流转（非法状态转换返回 400）
- [ ] 测试关联数据（删除订单后采购单是否清理）

---

## 九、Code Review 自检清单

修完 Bug 提交前：

- [ ] **同类搜索**：用 `grep` 搜同类字段/函数/模式，确认其他模块没问题
- [ ] **API 响应**：确认返回格式是 `{success, data, error}`
- [ ] **字段映射**：检查 `schemas.py` 字段名和前端 JS 一致
- [ ] **边界情况**：空值、None、列表为空 都处理了吗？
- [ ] **删除确认**：删除了关联数据（orders→items）吗？
- [ ] **日志**：新增的 `print` 或 `logging` 删了吗？
- [ ] **路由命名**：新 API 是否使用了连字符（kebab-case）？
