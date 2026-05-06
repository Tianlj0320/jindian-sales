# 金典软装销售系统 V4.0 — 接口设计

> 基于 FastAPI + RESTful 风格
> 认证：JWT Bearer Token
> 所有接口前缀：`/api`

---

## 通用说明

### 通用响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

错误响应：

```json
{
  "code": 400,
  "message": "参数错误：xxx",
  "data": null
}
```

### 通用分页参数

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码，默认 1 |
| page_size | int | 每页条数，默认 20 |

### 权限说明

| 角色 | 说明 |
|------|------|
| admin | 超级管理员，全权限 |
| manager | 经理，查看+管理 |
| staff | 员工，仅基础 CRUD |

---

## 1. /api/auth（认证模块）

### POST /api/auth/login
登录系统

**入参：**
```json
{
  "username": "string",
  "password": "string"
}
```

**出参：**
```json
{
  "code": 200,
  "data": {
    "token": "jwt_token_string",
    "user": {
      "id": 1,
      "username": "admin",
      "real_name": "管理员",
      "role": "admin"
    }
  }
}
```

### POST /api/auth/logout
退出登录

### GET /api/auth/me
获取当前用户信息

---

## 2. /api/customers（客户管理）

### GET /api/customers
客户列表（支持分页、关键词搜索）

**Query 参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |
| keyword | string | 搜索：姓名/电话/地址 |
| source | string | 客户来源 |
| status | string | 客户状态 |
| start_date | date | 创建起始日期 |
| end_date | date | 创建结束日期 |

**出参：**
```json
{
  "code": 200,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### POST /api/customers
新建客户

**入参：**
```json
{
  "name": "张三",
  "phone": "13800138000",
  "address": "杭州市西湖区xxx",
  "decoration_stage": "软装中",
  "source": "自然到店",
  "remark": ""
}
```

### GET /api/customers/{id}
获取客户详情

### PUT /api/customers/{id}
更新客户信息

### DELETE /api/customers/{id}
删除客户（软删除）

### GET /api/customers/{id}/orders
获取客户关联订单列表

### GET /api/customers/{id}/followups
获取客户跟进记录

### POST /api/customers/{id}/followups
添加客户跟进记录

**入参：**
```json
{
  "followup_type": "电话",
  "followup_date": "2026-05-04",
  "next_followup_date": "2026-05-10",
  "content": "客户对高精密窗帘有意向",
  "intent_level": "中",
  "status": "意向"
}
```

---

## 3. /api/products（产品管理）

### GET /api/products
产品列表

**Query：**
| 参数 | 类型 | 说明 |
|------|------|------|
| keyword | string | 搜索：编码/名称 |
| category | string | 分类 |
| is_active | bool | 是否上架 |

### POST /api/products
新建产品

**入参：**
```json
{
  "code": "CL-001",
  "name": "高精密遮光布-灰色",
  "category": "布帘",
  "sub_category": "高精密",
  "unit": "米",
  "standard_width": 2.8,
  "cost_price": 35.00,
  "selling_price": 88.00,
  "min_price": 68.00,
  "color": "灰色",
  "stock": 0,
  "safety_stock": 100,
  "is_active": true
}
```

### GET /api/products/{id}
产品详情

### PUT /api/products/{id}
更新产品

### DELETE /api/products/{id}
删除/下架产品

### GET /api/products/{id}/inventory
查询产品库存（按仓库+批次）

---

## 4. /api/orders（销售订单）

### GET /api/orders
订单列表

**Query：**
| 参数 | 类型 | 说明 |
|------|------|------|
| keyword | string | 订单号/客户名 |
| status | string | 订单状态 |
| payment_status | string | 付款状态 |
| start_date | date | 创建起始 |
| end_date | date | 创建结束 |
| salesman | string | 业务员 |

### POST /api/orders
创建订单

**入参：**
```json
{
  "customer_id": 1,
  "order_type": "零售",
  "discount_amount": 200.00,
  "delivery_address": "杭州市西湖区xxx",
  "expected_install_date": "2026-05-20",
  "source": "门店",
  "salesman": "李四",
  "remark": "",
  "items": [
    {
      "product_id": 1,
      "quantity": 10.5,
      "width": 3.2,
      "height": 2.8,
      "unit_price": 88.00,
      "process_fee": 50.00,
      "remark": "打孔式"
    }
  ]
}
```

**响应：** 返回新建订单详情（包含 order_no）

### GET /api/orders/{id}
订单详情（含明细）

### PUT /api/orders/{id}
更新订单（基础信息，不含明细）

### DELETE /api/orders/{id}
取消订单

### PUT /api/orders/{id}/status
更新订单状态

**入参：**
```json
{
  "status": "生产中",
  "remark": "已确认生产"
}
```

### PUT /api/orders/{id}/payment
更新付款信息

**入参：**
```json
{
  "received_amount": 5000.00,
  "payment_method": "转账",
  "received_date": "2026-05-04"
}
```

### GET /api/orders/{id}/items
获取订单明细列表

### POST /api/orders/{id}/items
添加订单明细

### PUT /api/orders/{id}/items/{item_id}
更新订单明细

### DELETE /api/orders/{id}/items/{item_id}
删除订单明细

### GET /api/orders/{id}/install
获取订单关联的安装单

### POST /api/orders/{id}/install
为订单创建安装单

### GET /api/orders/{id}/finance
获取订单的应收款记录

---

## 5. /api/installation（安装管理）

### GET /api/installation
安装单列表

**Query：**
| 参数 | 类型 | 说明 |
|------|------|------|
| keyword | string | 安装单号/客户名 |
| status | string | 安装状态 |
| team_id | int | 安装队ID |
| start_date | date | 预约起始日期 |
| end_date | date | 预约结束日期 |

### POST /api/installation
创建安装单

**入参：**
```json
{
  "order_id": 1,
  "customer_id": 1,
  "install_team_id": 1,
  "installer_id": 2,
  "scheduled_date": "2026-05-20",
  "scheduled_time": "09:00",
  "install_address": "杭州市西湖区xxx",
  "install_type": "新装",
  "difficulty_level": "一般",
  "labor_fee": 300.00,
  "material_fee": 50.00
}
```

### GET /api/installation/{id}
安装单详情

### PUT /api/installation/{id}
更新安装单

### PUT /api/installation/{id}/status
更新安装状态

**入参：**
```json
{
  "status": "已完成",
  "actual_start_time": "2026-05-20 09:05",
  "actual_end_time": "2026-05-20 12:30",
  "quality_check": "合格"
}
```

### GET /api/installation/{id}/photos
上传安装前后照片

---

## 6. /api/purchase（采购管理）

### GET /api/purchase
采购单列表

**Query：**
| 参数 | 类型 | 说明 |
|------|------|------|
| keyword | string | 采购单号 |
| status | string | 采购状态 |
| supplier_id | int | 供应商ID |
| start_date | date | 订货起始日期 |

### POST /api/purchase
创建采购单

**入参：**
```json
{
  "supplier_id": 1,
  "warehouse_id": 1,
  "order_date": "2026-05-04",
  "expected_date": "2026-05-10",
  "remark": "",
  "items": [
    {
      "product_id": 1,
      "quantity": 500,
      "unit_price": 35.00,
      "batch_no": "B20260501"
    }
  ]
}
```

### GET /api/purchase/{id}
采购单详情

### PUT /api/purchase/{id}
更新采购单

### DELETE /api/purchase/{id}
删除采购单

### PUT /api/purchase/{id}/status
审核/完成采购单

### POST /api/purchase/{id}/receive
采购入库确认

**入参：**
```json
{
  "items": [
    {
      "item_id": 1,
      "received_quantity": 500
    }
  ]
}
```

---

## 7. /api/warehouse（仓库管理）

### GET /api/warehouse
仓库列表

### POST /api/warehouse
新建仓库

**入参：**
```json
{
  "code": "WH01",
  "name": "主仓库",
  "type": "成品库",
  "address": "杭州市余杭区xxx",
  "manager": "王五",
  "capacity": 1000.00
}
```

### GET /api/warehouse/{id}
仓库详情

### PUT /api/warehouse/{id}
更新仓库

### GET /api/warehouse/{id}/inventory
仓库库存列表

### GET /api/warehouse/{id}/flows
仓库流水记录

**Query：**
| 参数 | 类型 | 说明 |
|------|------|------|
| product_id | int | 产品ID |
| flow_type | string | 流转类型 |
| start_date | date | 起始日期 |
| end_date | date | 结束日期 |

### POST /api/warehouse/adjust
库存盘点调整

**入参：**
```json
{
  "warehouse_id": 1,
  "product_id": 1,
  "batch_no": "B20260501",
  "adjust_type": "add",
  "quantity": 5.00,
  "remark": "盘点盘盈"
}
```

---

## 8. /api/finance（财务管理）

### GET /api/finance/receivables
应收账款列表

**Query：**
| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | 状态 |
| customer_id | int | 客户ID |
| start_date | date | 起始日期 |
| end_date | date | 结束日期 |

### GET /api/finance/receivables/{id}
应收款详情

### PUT /api/finance/receivables/{id}/receive
收款确认

**入参：**
```json
{
  "received_amount": 3000.00,
  "payment_method": "转账",
  "received_date": "2026-05-04"
}
```

### GET /api/finance/payables
应付账款列表

### PUT /api/finance/payables/{id}/pay
付款确认

**入参：**
```json
{
  "paid_amount": 1000.00,
  "payment_method": "转账",
  "paid_date": "2026-05-04"
}
```

### GET /api/finance/expenses
费用列表

### POST /api/finance/expenses
新增费用记录

**入参：**
```json
{
  "expense_type": "房租",
  "amount": 5000.00,
  "expense_date": "2026-05-01",
  "payee": "房东",
  "payment_method": "转账",
  "remark": "5月房租"
}
```

### GET /api/finance/balance
经营概况（实时）

**响应：**
```json
{
  "code": 200,
  "data": {
    "total_receivable": 500000.00,
    "total_received": 350000.00,
    "total_outstanding": 150000.00,
    "total_payable": 200000.00,
    "total_paid": 180000.00,
    "total_outstanding_pay": 20000.00,
    "total_expense_month": 15000.00
  }
}
```

---

## 9. /api/reports（报表模块）

### GET /api/reports/sales-summary
销售汇总报表

**Query：**
| 参数 | 类型 | 说明 |
|------|------|------|
| start_date | date | 起始日期 |
| end_date | date | 结束日期 |
| group_by | string | 分组维度：day/month/salesman/product |

### GET /api/reports/customer-analysis
客户分析报表

**Query：**
| 参数 | 类型 | 说明 |
|------|------|------|
| start_date | date | 起始日期 |
| end_date | date | 结束日期 |

### GET /api/reports/product-analysis
产品销售排行

**Query：**
| 参数 | 类型 | 说明 |
|------|------|------|
| start_date | date | 起始日期 |
| end_date | date | 结束日期 |
| limit | int | 返回条数，默认20 |

### GET /api/reports/inventory-warning
库存预警报表

### GET /api/reports/profit-summary
利润汇总

### GET /api/reports/install-summary
安装统计

---

## 10. /api/system（系统管理）

### GET /api/system/users
用户列表

### POST /api/system/users
新建用户

### PUT /api/system/users/{id}
更新用户

### DELETE /api/system/users/{id}
删除用户

### GET /api/system/roles
角色列表

### GET /api/system/logs
操作日志

**Query：**
| 参数 | 类型 | 说明 |
|------|------|------|
| module | string | 模块名 |
| user_id | int | 用户ID |
| start_date | date | 起始日期 |
| end_date | date | 结束日期 |

### GET /api/system/dict/{type}
通用字典接口

**Path：**
| type | 说明 |
|------|------|
| order_status | 订单状态 |
| payment_status | 付款状态 |
| install_status | 安装状态 |
| expense_type | 费用类型 |
| customer_source | 客户来源 |
| decoration_stage | 装修阶段 |
| flow_type | 库存流转类型 |

---

## 11. /api/installers（安装工管理）

### GET /api/installers
安装工列表

### POST /api/installers
新建安装工

**入参：**
```json
{
  "name": "赵六",
  "phone": "13900139000",
  "id_card": "330101199001011234",
  "team_id": 1,
  "skill_level": "高级",
  "join_date": "2023-01-01",
  "hourly_rate": 50.00
}
```

### GET /api/installers/{id}
安装工详情

### PUT /api/installers/{id}
更新安装工信息

### GET /api/installers/{id}/install-records
安装工历史安装记录

---

## 12. /api/teams（安装队管理）

### GET /api/teams
安装队列表

### POST /api/teams
新建安装队

### GET /api/teams/{id}
安装队详情

### PUT /api/teams/{id}
更新安装队

### GET /api/teams/{id}/members
获取队员列表

### POST /api/teams/{id}/members
添加队员

### DELETE /api/teams/{id}/members/{installer_id}
移除队员
