# 金典软装ERP V4.0 — API 接口设计

> 框架：FastAPI + Pydantic v2
> 认证：JWT Bearer Token（`Authorization: Bearer <token>`）
> 基础路径：`/api/v1`
> 自动文档：`/docs`（Swagger UI）

---

## 通用约定

### 响应格式

所有接口统一使用 `app.core.response` 中的三个响应函数：

**成功响应（带数据）：**
```json
{
  "success": true,
  "data": { ... },
  "message": null
}
```

**成功响应（分页列表）：**
```json
{
  "success": true,
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": [ ... ]
}
```

**错误响应：**
```json
{
  "success": false,
  "error": "错误描述信息",
  "message": "ERROR_CODE_OPTIONAL"
}
```

### 分页参数

| 参数 | 类型 | 默认 | 范围 | 说明 |
|------|------|------|------|------|
| page | int | 1 | ≥ 1 | 页码 |
| page_size | int | 20 | 1-200 | 每页条数 |

### 认证

- 除登录接口外，所有 API 均需 JWT 认证
- 通过 `Authorization: Bearer <token>` 请求头传递
- Token 有效期：72 小时

### 公共依赖

| 名称 | 类型 | 说明 |
|------|------|------|
| SessionDep | AsyncSession | 数据库会话 |
| CurrentUserDep | User | 当前登录用户 |
| PageDep | PageParams | 分页参数 |

---

## 1. 认证 /api/v1/auth

### POST /api/v1/auth/login
登录获取 Token

**请求体：**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应：**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGci...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "username": "admin",
      "name": "系统管理员",
      "role": "admin"
    }
  }
}
```

### GET /api/v1/auth/me
获取当前用户信息

### GET /api/v1/auth/users
用户列表

### POST /api/v1/auth/users
创建用户

### PUT /api/v1/auth/users/{user_id}
更新用户

### DELETE /api/v1/auth/users/{user_id}
删除用户（软禁用）

---

## 2. 仪表盘 /api/v1/dashboard

### GET /api/v1/dashboard
Dashboard 统计数据

**响应：**
```json
{
  "success": true,
  "data": {
    "today_orders": 5,
    "month_sales": 125000.00,
    "pending_install": 3,
    "overdue_receivable": 25000.00,
    "low_stock_count": 8,
    "pending_purchase": 2,
    "month_expenses": 18000.00
  }
}
```

### GET /api/v1/dashboard/sales-report
月度销售报表（含状态分布）

### GET /api/v1/dashboard/product-rank
产品销售排行（Top 20）

---

## 3. 客户管理 /api/v1/customers

### GET /api/v1/customers/search
客户搜索（轻量级自动补全，limit 15）

**查询参数：** `keyword`

### GET /api/v1/customers
客户列表（分页）

**查询参数：** `keyword`, `type`, `page`, `page_size`

### GET /api/v1/customers/{customer_id}
客户详情

### POST /api/v1/customers
创建客户（自动填充 salesperson）

**请求体：**
```json
{
  "name": "张三",
  "phone": "13800138000",
  "type": "retail",
  "source": "自然进店",
  "address": "杭州市西湖区",
  "community": "翠苑小区",
  "level": "C",
  "remark": ""
}
```

### PUT /api/v1/customers/{customer_id}
更新客户

### DELETE /api/v1/customers/{customer_id}
删除客户（软删除）

### GET /api/v1/customers/{customer_id}/followups
跟进记录列表

---

## 4. 产品管理 /api/v1/products

### GET /api/v1/products/search
产品搜索（轻量级自动补全，limit 20，仅活跃产品）

**查询参数：** `keyword`

### GET /api/v1/products/categories
产品分类树

### POST /api/v1/products/categories
创建产品分类

### GET /api/v1/products/suppliers
供应商列表（分页）

**查询参数：** `keyword`, `page`, `page_size`

### POST /api/v1/products/suppliers
创建供应商

### PUT /api/v1/products/suppliers/{supplier_id}
更新供应商

### DELETE /api/v1/products/suppliers/{supplier_id}
删除供应商

### GET /api/v1/products
产品列表（分页）

**查询参数：** `keyword`, `category_id`, `product_type`, `is_active`, `page`, `page_size`

### GET /api/v1/products/{product_id}
产品详情

### POST /api/v1/products
创建产品

**请求体：**
```json
{
  "code": "CL-001",
  "name": "高精密遮光布-灰色",
  "product_type": "面料",
  "category_id": 1,
  "supplier_id": 1,
  "unit": "米",
  "unit_price": 88.00,
  "cost_price": 35.00,
  "min_price": 68.00,
  "color": "灰色",
  "width": 280,
  "fold_ratio": 2.0,
  "is_active": true
}
```

### PUT /api/v1/products/{product_id}
更新产品

---

## 5. 订单管理 /api/v1/orders

### GET /api/v1/orders
订单列表（分页，多条件筛选）

**查询参数：** `keyword`, `status_key`, `order_type`, `year`, `month`, `salesperson_id`, `page`, `page_size`

### GET /api/v1/orders/meta/status-options
获取所有订单状态选项

### GET /api/v1/orders/split-preview
采购分单预览（展示预计生成的采购单）

### POST /api/v1/orders/confirm-split
确认执行采购分单

### POST /api/v1/orders
创建订单（含明细行）

**请求体：**
```json
{
  "customer_id": 1,
  "order_type": "窗帘",
  "content": "主卧布帘+纱帘",
  "delivery_method": "上门安装",
  "install_address": "杭州市西湖区xxx",
  "remark": "",
  "items": [
    {
      "item_type": "窗帘",
      "product_id": 1,
      "product_name": "高精密遮光布",
      "room": "主卧",
      "width": 3.2,
      "height": 2.8,
      "fold_ratio": 2.0,
      "qty": 1,
      "unit_price": 88.00,
      "material_type": "主料"
    }
  ]
}
```

### GET /api/v1/orders/{order_id}
订单详情（含明细）

### PUT /api/v1/orders/{order_id}
更新订单（仅 initial/created 状态可编辑）

### DELETE /api/v1/orders/{order_id}
删除订单（级联删除明细）

### POST /api/v1/orders/{order_id}/split
手动触发采购分单

### POST /api/v1/orders/{order_id}/advance
推进到下一个状态

**请求体：**
```json
{
  "remark": "量尺完成"
}
```

### PUT /api/v1/orders/{order_id}/status
跳转到指定状态

**请求体：**
```json
{
  "status_key": "confirmed"
}
```

### GET /api/v1/orders/{order_id}/rollback-options
获取可回滚的状态选项（admin/manager 权限）

### POST /api/v1/orders/{order_id}/rollback
回滚订单状态（admin/manager 权限）

**请求体：**
```json
{
  "target_status": "initial"
}
```

---

## 6. 采购管理 /api/v1/purchases

### GET /api/v1/purchases
采购单列表（分页）

**查询参数：** `keyword`, `status`, `year`, `month`, `page`, `page_size`

### GET /api/v1/purchases/{po_id}
采购单详情（含明细）

### POST /api/v1/purchases
创建采购单

**请求体：**
```json
{
  "supplier_id": 1,
  "order_date": "2026-05-01",
  "expected_date": "2026-05-10",
  "remark": "",
  "items": [
    {
      "product_id": 1,
      "product_name": "高精密遮光布",
      "quantity": 500,
      "unit": "米",
      "unit_price": 35.00,
      "material_type": "主料"
    }
  ]
}
```

### POST /api/v1/purchases/{po_id}/receive
采购入库确认（批量到货）

**请求体：**
```json
{
  "items": [
    { "item_id": 1, "arrived_qty": 500 }
  ]
}
```

### PUT /api/v1/purchases/{po_id}/status
更新采购单状态

### DELETE /api/v1/purchases/{po_id}
删除采购单（级联删除明细）

---

## 7. 仓库管理 /api/v1/warehouses

### GET /api/v1/warehouses
仓库列表

### POST /api/v1/warehouses
创建仓库

### GET /api/v1/warehouses/inventory
库存列表（分页，含低库存筛选）

**查询参数：** `keyword`, `low_stock`, `page`, `page_size`

### GET /api/v1/warehouses/flows
库存流水（分页）

**查询参数：** `product_id`, `flow_type`, `start_date`, `end_date`, `page`, `page_size`

---

## 8. 安装管理 /api/v1/installations

### GET /api/v1/installations/teams
安装队列表（含成员数）

### POST /api/v1/installations/teams
创建安装队

### GET /api/v1/installations/installers
安装工列表

### POST /api/v1/installations/installers
创建安装工

### GET /api/v1/installations/orders
安装单列表（分页）

**查询参数：** `keyword`, `status`, `page`, `page_size`

### GET /api/v1/installations/orders/{ins_id}
安装单详情

### POST /api/v1/installations/orders
创建安装单（手动）

### PUT /api/v1/installations/orders/{ins_id}/status
更新安装状态

**请求体：**
```json
{
  "status": "安装中"
}
```

---

## 9. 财务管理 /api/v1/finance

### GET /api/v1/finance/receivables
应收款列表（分页）

### POST /api/v1/finance/receive
收款确认

**请求体：**
```json
{
  "order_id": 1,
  "amount": 5000.00,
  "payment_method": "微信",
  "remark": "微信转账"
}
```

### GET /api/v1/finance/payables
应付款列表（分页）

### POST /api/v1/finance/pay
付款确认

### GET /api/v1/finance/expenses
费用列表（分页，可按类别/月份筛选）

### POST /api/v1/finance/expenses
创建费用记录

### GET /api/v1/finance/summary
经营概况汇总

**响应：**
```json
{
  "success": true,
  "data": {
    "total_receivable": 500000.00,
    "total_received": 350000.00,
    "total_unpaid": 150000.00,
    "total_payable": 200000.00,
    "total_paid": 180000.00,
    "total_debt": 20000.00,
    "total_expense_month": 15000.00
  }
}
```

---

## 10. 生产反馈 /api/v1/production

### GET /api/v1/production/feedbacks
生产反馈列表（分页）

**查询参数：** `keyword`, `status`, `feedback_type`, `page`, `page_size`

### GET /api/v1/production/feedbacks/{feedback_id}
反馈详情

### POST /api/v1/production/feedbacks
创建反馈（自动生成 FB 编号）

### PUT /api/v1/production/feedbacks/{feedback_id}
更新反馈

### GET /api/v1/production/stats
反馈统计（待处理/处理中/已解决）

---

## 11. 加工类型 /api/v1/processing

### GET /api/v1/processing/types
加工类型列表（含辅料规则）

### GET /api/v1/processing/types/{type_id}
加工类型详情

### POST /api/v1/processing/types
创建加工类型（含规则）

### PUT /api/v1/processing/types/{type_id}
更新加工类型

### DELETE /api/v1/processing/types/{type_id}
删除加工类型

### POST /api/v1/processing/types/{type_id}/rules
添加辅料规则

### PUT /api/v1/processing/rules/{rule_id}
更新辅料规则

### DELETE /api/v1/processing/rules/{rule_id}
删除辅料规则

---

## 12. 角色权限 /api/v1/roles

### GET /api/v1/roles
角色列表

### POST /api/v1/roles
创建角色

**请求体：**
```json
{
  "name": "店长",
  "code": "manager",
  "description": "门店管理者",
  "permissions": ["dashboard", "orders", "customers", "products"],
  "sort_order": 2
}
```

### PUT /api/v1/roles/{role_id}
更新角色

### PUT /api/v1/roles/{role_id}/permissions
更新角色权限

### DELETE /api/v1/roles/{role_id}
删除角色（软禁用）

---

## 13. 系统设置 /api/v1/system

### 字典接口

#### GET /api/v1/system/dict/{dict_type}
获取指定字典类型的字典项列表

**路径参数：** `dict_type` — 字典类型编码（如 order_type, customer_source）

**响应：**
```json
{
  "success": true,
  "data": [
    { "dict_code": "curtain", "dict_label": "窗帘", "sort_order": 1 },
    { "dict_code": "wallpaper", "dict_label": "墙布", "sort_order": 2 }
  ]
}
```

#### GET /api/v1/system/dicts/types
获取所有字典类型编码

#### GET /api/v1/system/dicts
字典项列表（分页，按类型筛选）

#### POST /api/v1/system/dicts
创建字典项

#### PUT /api/v1/system/dicts/{item_id}
更新字典项

#### DELETE /api/v1/system/dicts/{item_id}
删除字典项（软禁用）

#### GET /api/v1/system/dict-types
字典类型列表

#### POST /api/v1/system/dict-types
创建字典类型

#### PUT /api/v1/system/dict-types/{type_id}
更新字典类型

#### DELETE /api/v1/system/dict-types/{type_id}
删除字典类型（级联禁用子项）

### 店铺信息

#### GET /api/v1/system/store-info
获取店铺配置

#### PUT /api/v1/system/store-info
批量更新店铺配置

**请求体：**
```json
{
  "items": {
    "store_name": "金典软装",
    "store_code": "JD001",
    "phone": "0571-xxxxxxx",
    "address": "杭州古墩路欧亚达家居广场",
    "order_header": "金典软装销售订单",
    "order_tips": "感谢您的信任与支持！",
    "contract_header": "金典软装销售合同",
    "contract_tips": "本合同一式两份，双方各执一份"
  }
}
```

### 操作日志

#### GET /api/v1/system/logs
操作日志列表（分页）

**查询参数：** `resource`, `action`, `start_date`, `end_date`, `page`, `page_size`

---

## 14. 健康检查

### GET /health
服务健康检查（无需认证）

**响应：**
```json
{
  "status": "ok",
  "version": "4.0.0"
}
```

---

## 端点统计

| 模块 | 端点数 | 前缀 |
|------|--------|------|
| 认证 | 6 | /api/v1/auth |
| 仪表盘 | 3 | /api/v1/dashboard |
| 客户管理 | 6 | /api/v1/customers |
| 产品管理 | 10 | /api/v1/products |
| 订单管理 | 11 | /api/v1/orders |
| 采购管理 | 6 | /api/v1/purchases |
| 仓库管理 | 4 | /api/v1/warehouses |
| 安装管理 | 8 | /api/v1/installations |
| 财务管理 | 7 | /api/v1/finance |
| 生产反馈 | 5 | /api/v1/production |
| 加工类型 | 8 | /api/v1/processing |
| 角色权限 | 5 | /api/v1/roles |
| 系统设置 | 12 | /api/v1/system |
| 健康检查 | 1 | /health |
| **合计** | **82** | |

---

## HTTP 状态码说明

| 状态码 | 说明 | 典型场景 |
|--------|------|----------|
| 200 | 请求成功 | 正常 CRUD |
| 400 | 业务错误 | BusinessError（如订单已不可编辑） |
| 401 | 未认证 | Token 缺失/过期/无效 |
| 403 | 无权限 | 非管理员尝试敏感操作 |
| 404 | 资源不存在 | 查询不存在的 ID |
| 409 | 数据冲突 | 数据已存在等 |
| 422 | 参数校验失败 | Pydantic 校验未通过 |
| 500 | 服务器内部错误 | 未捕获异常 |
