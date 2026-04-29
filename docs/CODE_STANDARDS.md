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

## 七、Code Review 自检清单

修完 Bug 提交前：

- [ ] **同类搜索**：用 `grep` 搜同类字段/函数/模式，确认其他模块没问题
- [ ] **API 响应**：确认返回格式是 `{success, data, error}`
- [ ] **字段映射**：检查 `schemas.py` 字段名和前端 JS 一致
- [ ] **边界情况**：空值、None、列表为空 都处理了吗？
- [ ] **删除确认**：删除了关联数据（orders→items）吗？
- [ ] **日志**：新增的 `print` 或 `logging` 删了吗？
