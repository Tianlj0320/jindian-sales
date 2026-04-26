# 金典软装销售系统 · API 接口规范

> **目的**：前端不再猜字段名，后端改字段必须通知前端。  
> **原则**：所有 API 返回格式必须写在这里，增删字段走 PR 审查。

---

## 通用规范

### 请求格式
```
Content-Type: application/json
Authorization: Bearer {token}
```

### 成功响应
```json
// 方式A：有 data 字段
{ "success": true, "data": { ... } }

// 方式B：列表数据
{ "success": true, "data": { "items": [...], "total": 100 } }

// 方式C：操作结果
{ "success": true, "message": "操作成功" }
```

### 错误响应
```json
{ "success": false, "error": "错误描述" }
```

---

## 接口列表

---

### 1. 登录
```
POST /api/auth/login
Body: { "phone": "13900001111", "password": "jd8888" }
```
**成功返回** `data`:
```json
{
  "token": "eyJhbGc...",
  "user_id": 1,
  "name": "张三",
  "role": "admin"
}
```

---

### 2. 首页仪表盘
```
GET /api/dashboard
```
**成功返回** `data`:
```json
{
  "today_orders": 3,           // INT   今日新增订单数
  "month_sales": 58000.00,     // FLOAT 本月销售额
  "pending_install": 2,         // INT   待安装订单数
  "overdue_orders": 1,         // INT   逾期订单数
  "pending_payment": 5,         // INT   待收款笔数
  "total_customers": 128       // INT   客户总数
}
```
⚠️ **字段命名**：下划线形式，后端数据库字段直接暴露，不用驼峰。

---

### 3. 订单列表
```
GET /api/orders?page=1&page_size=100&status_key=confirmed&year=2026&month=4
```
**成功返回** `data`:
```json
{
  "items": [
    {
      "id": 1,                                    // INT   订单ID
      "order_no": "ORD20260425001",               // STR   订单号
      "customer_id": 5,                           // INT   客户ID
      "customer_name": "李四",                    // STR   客户名称 ← 前端用这个
      "customer_phone": "18758260712",            // STR   客户手机
      "order_type": "窗帘",                       // STR   订单类型
      "content": "婴儿绒雪尼尔 + 韩褶",           // STR   订单内容摘要
      "amount": 5800.00,                          // FLOAT 订单总额
      "quote_amount": 6800.00,                    // FLOAT 标价合计
      "discount_amount": 500.00,                  // FLOAT 优惠金额
      "round_amount": 0,                          // FLOAT 抹零金额
      "received": 2000.00,                        // FLOAT 已收定金
      "debt": 3800.00,                           // FLOAT 欠款
      "order_date": "2026-04-25",                 // STR   接单日期 ← 前端用这个
      "delivery_date": "2026-05-09",             // STR   交期日期
      "install_date": "2026-05-10",              // STR   安装日期
      "delivery_method": "上门安装",              // STR   提货方式
      "salesperson": "王导购",                    // STR   导购姓名
      "salesperson_id": 3,                       // INT   导购ID
      "status_key": "confirmed",                 // STR   状态英文键 ← 前端用这个做筛选
      "status_label": "已确认",                   // STR   状态中文 ← 前端直接显示用这个！
      "status_color": "#409eff",                 // STR   状态颜色（可选）
      "history": [                                // ARR   状态变更记录
        { "s": "待确认", "s2": "已确认", "c": "confirmed", "time": "2026-04-25 14:30:00" }
      ],
      "items": [                                  // ARR   订单明细
        {
          "id": 1,
          "product_id": 10,                       // INT   产品ID
          "product_name": "婴儿绒雪尼尔-奶白",    // STR   产品名称
          "product_type": "面料",                 // STR   产品类型
          "room": "客厅",                         // STR   安装位置
          "style": "韩褶",                        // STR   款式
          "item_name": "窗帘",                     // STR   项目名
          "width": "2.3",                         // STR   宽度
          "height": "2.5",                        // STR   高度
          "qty": 2,                               // INT   幅数
          "discount": 0.85,                       // FLOAT 折扣（0.85 = 85折）
          "unit_price": 120.00,                   // FLOAT 单价
          "amount": 204.00,                       // FLOAT 小计金额
          "is_material": false                    // BOOL  是否为辅料
        }
      ]
    }
  ],
  "total": 50
}
```

⚠️ **前端显示状态规则**：
- `status_label` = 显示用（中文）
- `status_key` = 筛选/状态流转用
- ⚠️ 禁止直接用 `status_key` 做显示，必须用 `status_label`

---

### 4. 创建订单
```
POST /api/orders
Body: {
  "customer_id": 5,
  "customer_name": "李四",
  "customer_phone": "18758260712",
  "order_type": "窗帘",
  "content": "婴儿绒雪尼尔",
  "quote_amount": 6800.00,
  "discount_amount": 500.00,
  "round_amount": 0,
  "amount": 6300.00,
  "received": 2000.00,
  "order_date": "2026-04-25",
  "delivery_date": "2026-05-09",
  "delivery_method": "上门安装",
  "salesperson_id": 3,
  "install_address": "杭州市西湖区...",
  "install_date": "2026-05-10",
  "items": [
    {
      "product_id": 10,
      "product_name": "婴儿绒雪尼尔-奶白",
      "product_type": "面料",
      "room": "客厅",
      "style": "韩褶",
      "item_name": "窗帘",
      "width": "2.3",
      "height": "2.5",
      "qty": 2,
      "discount": 0.85,
      "price": 120.00,
      "amount": 204.00
    }
  ]
}
```
**成功返回** `data`:
```json
{
  "id": 15,
  "order_no": "ORD20260425015"
}
```

---

### 5. 修改订单状态
```
PUT /api/orders/{id}/status
Body: { "new_status_key": "confirmed" }
```
**成功返回** `data`: `null` 或 `{}`

---

### 6. 删除订单
```
DELETE /api/orders/{id}
```
**成功返回** `data`: `null`

---

### 7. 供应商列表
```
GET /api/products/suppliers
```
**成功返回** `data`:
```json
{
  "items": [
    {
      "id": 1,
      "code": "01",                               // STR   供应商编号
      "name": "杭州诺雅布业",                      // STR   供应商名称
      "type": "布艺",                             // STR   类型：成品/布艺/配件
      "contact": "张经理",                         // STR   联系人
      "phone": "13800001111",                     // STR   电话
      "delivery_days": 7,                         // INT   交货期（天）
      "address": "杭州市余杭区...",               // STR   地址
      "payment": "月结30天"                        // STR   收付款说明
    }
  ]
}
```

⚠️ **字段映射**：`delivery_days` 后端返回，下划线；前端用 `deliveryDays`

---

### 8. 产品列表
```
GET /api/products
GET /api/products?supplier_id=1
```
**成功返回** `data`:
```json
{
  "items": [
    {
      "id": 10,
      "code": "P001",                             // STR   货号
      "name": "婴儿绒雪尼尔-奶白",                 // STR   产品名称
      "supplier_id": 1,                           // INT   供应商ID
      "category_id": 3,                           // INT   布版系列ID
      "product_type": "面料",                     // STR   分类：面料/辅料
      "classification": "定高",                    // STR   产品分类：定高/定宽/配件
      "model": "A2026",                           // STR   型号
      "material": "雪尼尔",                        // STR   材质
      "width": 280,                               // INT   门幅(cm)
      "weight": 1200,                             // INT   克重(g/㎡)
      "unit_price": 120.00,                       // FLOAT 单价
      "stock": 50.0,                              // FLOAT 库存
      "unit": "米",                               // STR   单位
      "remark": ""                                 // STR   备注
    }
  ]
}
```

---

### 9. 布版分类列表
```
GET /api/products/categories
```
**成功返回** `data`:
```json
{
  "items": [
    {
      "id": 3,
      "code": "0101",                             // STR   布版编号
      "name": "奶油风系列",                        // STR   布版名称
      "supplier_id": 1,                           // INT   供应商ID
      "description": ""                            // STR   描述
    }
  ]
}
```

---

### 10. 客户列表
```
GET /api/customers
```
**成功返回** `data`:
```json
{
  "items": [
    {
      "id": 5,
      "name": "李四",                             // STR   客户名称
      "phone": "18758260712",                     // STR   手机号
      "type": "零售",                             // STR   类型：零售/工程/设计师
      "contact": "",                              // STR   联系人
      "community": "翡翠城",                      // STR   小区
      "address": "杭州市西湖区...",               // STR   安装地址
      "salesperson": "王导购",                    // STR   导购
      "salesperson_id": 3,                        // INT   导购ID
      "source": "抖音",                            // STR   来源渠道
      "debt": 3800.00,                            // FLOAT 欠款
      "debt_limit": 10000.00,                     // FLOAT 欠款额度
      "remark": ""                                 // STR   备注
    }
  ]
}
```

---

### 11. 员工列表
```
GET /api/employees
```
**成功返回** `data`:
```json
{
  "items": [
    {
      "id": 3,
      "code": "E003",                             // STR   工号
      "name": "王导购",                            // STR   姓名
      "gender": "女",                             // STR   性别
      "phone": "13800003333",                     // STR   手机
      "position": "导购",                         // STR   职务
      "department": "销售部",                      // STR   部门
      "max_discount": 0.80,                       // FLOAT 最大折扣（0.80=8折）
      "round_limit": 10.00,                        // FLOAT 抹零限额
      "status": "启用",                            // STR   状态
      "join_date": "2024-03-01"                   // STR   入职日期
    }
  ]
}
```

⚠️ **字段映射**：`max_discount` → 前端 `maxDiscount`；`round_limit` → 前端 `roundLimit`

---

### 12. 采购单列表
```
GET /api/purchase-orders
```
**成功返回** `data`:
```json
{
  "items": [
    {
      "id": 1,
      "po_no": "PO20260425001",                   // STR   采购单号
      "supplier_id": 1,                           // INT   供应商ID
      "supplier_name": "杭州诺雅布业",             // STR   供应商名称 ← 前端用这个
      "order_ids": "1,3,5",                        // STR   来源订单ID列表
      "items": [                                   // ARR   采购物料
        { "product_name": "婴儿绒雪尼尔", "qty": 20, "unit": "米" }
      ],
      "total_amount": 2400.00,                    // FLOAT 采购总额
      "status": "待采购",                          // STR   状态
      "expected_date": "2026-05-02",              // STR   预计到货
      "remark": ""                                 // STR   备注
    }
  ]
}
```

---

### 13. 生成采购单（批量拆分）
```
POST /api/purchase-orders/batch-split
Body: [1, 3, 5]    // 订单ID数组
```
**成功返回** `data`:
```json
{
  "message": "成功生成 2 张采购单",
  "purchase_orders": [ ... ]
}
```

---

### 14. 仓库记录
```
GET /api/warehouse/records
```
**成功返回** `data`:
```json
{
  "items": [
    {
      "id": 1,
      "record_type": "in",                       // STR   记录类型：in=入库/out=出库
      "product_name": "婴儿绒雪尼尔",              // STR   物料名称
      "product_code": "P001",                     // STR   物料编码
      "quantity": 50.0,                           // FLOAT 数量
      "unit": "米",                               // STR   单位
      "created_at": "2026-04-25 14:00:00"        // STR   创建时间
    }
  ]
}
```

---

### 15. 财务汇总
```
GET /api/finance/summary
```
**成功返回** `data`:
```json
{
  "month_receive": 58000.00,                      // FLOAT 本月收入
  "month_pay": 32000.00,                         // FLOAT 本月支出
  "total_debt": 128000.00,                       // FLOAT 总欠款
  "pending_commission": 8500.00                   // FLOAT 待结提成
}
```

---

### 16. 销售趋势
```
GET /api/reports/trend?year=2026&month=4
```
**成功返回** `data`:
```json
{
  "items": [
    { "day": 1, "amount": 5800.00 },
    { "day": 2, "amount": 3200.00 }
  ]
}
```

---

### 17. 员工业绩
```
GET /api/reports/employee-performance?year=2026&month=4
```
**成功返回** `data`:
```json
{
  "items": [
    {
      "salesperson": "王导购",                    // STR   员工姓名
      "total_amount": 28000.00,                   // FLOAT 销售总额
      "order_count": 8                            // INT   签单数
    }
  ]
}
```

---

### 18. 产品排行
```
GET /api/reports/product-rank?year=2026&month=4
```
**成功返回** `data`:
```json
{
  "items": [
    {
      "product": "婴儿绒雪尼尔-奶白",              // STR   产品名称
      "qty": 156.5,                               // FLOAT 销售数量（米）
      "amount": 18780.00                          // FLOAT 销售额
    }
  ]
}
```

---

### 19. 安装单列表
```
GET /api/installation-orders
```
**成功返回** `data`:
```json
{
  "items": [
    {
      "id": 1,
      "ins_no": "INS20260425001",                // STR   安装单号
      "order_id": 5,                              // INT   订单ID
      "order_no": "ORD20260425005",              // STR   订单号
      "customer_name": "李四",                   // STR   客户名称
      "address": "杭州市西湖区...",               // STR   安装地址
      "installer_name": "张师傅",                 // STR   安装师傅
      "scheduled_date": "2026-05-10",            // STR   预约日期
      "status": "待分配"                          // STR   状态
    }
  ]
}
```

---

## 状态码（status_key）对照表

| status_key | status_label | 颜色 | 说明 |
|-----------|-------------|------|------|
| `created` | 待确认 | #909399 | 订单新建 |
| `confirmed` | 已确认 | #409eff | 已审核 |
| `split` | 已拆分 | #7c3aed | 已生成采购单 |
| `purchasing` | 采购中 | #f59e0b | 采购中 |
| `stocked` | 已到货 | #10b981 | 材料到货 |
| `processing` | 生产中 | #f97316 | 生产加工中 |
| `production_exception` | 生产异常 | #ef4444 | 生产异常 |
| `install_order_generated` | 安装单已生成 | #8b5cf6 | 安装单已出 |
| `shipped` | 已发货 | #06b6d4 | 已发货 |
| `installed` | 已安装 | #1a3a5c | 已安装 |
| `accepted` | 已验收 | #059669 | 已验收 |
| `completed` | 已完成 | #6366f1 | 订单完成 |
| `cancelled` | 已取消 | #d9d9d9 | 已取消 |

---

## 前端变量命名规范（API → 前端）

所有来自 API 的数据，字段名转换规则：

| 后端字段（snake_case） | 前端变量（camelCase） | 说明 |
|----------------------|---------------------|------|
| `order_no` | `orderNo` | 订单号 |
| `customer_id` | `customerId` | 客户ID |
| `customer_name` | `customerName` | 客户名称（显示用） |
| `order_date` | `orderDate` | 订单日期 |
| `delivery_date` | `deliveryDate` | 交期 |
| `install_date` | `installDate` | 安装日期 |
| `order_type` | `orderType` | 订单类型 |
| `delivery_method` | `deliveryMethod` | 提货方式 |
| `salesperson_id` | `salespersonId` | 导购ID |
| `salesperson` | `salesperson` | 导购姓名（显示用） |
| `quote_amount` | `quoteAmount` | 标价 |
| `discount_amount` | `discountAmount` | 优惠 |
| `round_amount` | `roundAmount` | 抹零 |
| `received` | `received` | 已收 |
| `debt` | `debt` | 欠款 |
| `status_key` | `statusKey` | 状态英文键 |
| `status_label` | `status`（或 `statusLabel`） | 状态中文 |
| `status_color` | `statusColor` | 状态颜色 |
| `supplier_id` | `supplierId` | 供应商ID |
| `supplier_name` | `supplierName` | 供应商名称 |
| `category_id` | `categoryId` | 分类ID |
| `product_id` | `productId` | 产品ID |
| `product_name` | `productName` | 产品名称 |
| `product_type` | `productType` | 产品类型 |
| `unit_price` | `unitPrice` | 单价 |
| `max_discount` | `maxDiscount` | 最大折扣 |
| `round_limit` | `roundLimit` | 抹零限额 |
| `join_date` | `joinDate` | 入职日期 |
| `total_amount` | `totalAmount` | 总额 |
| `expected_date` | `expectedDate` | 预计日期 |
| `order_ids` | `orderIds` | 订单ID列表 |
| `created_at` | `createdAt` | 创建时间 |
| `install_address` | `installAddress` | 安装地址 |

---

## 改动协议

1. 后端新增字段 → 必须同步更新本文档 + 通知前端
2. 后端删除字段 → 必须同步更新本文档 + 通知前端
3. 后端改字段名 → 视为删除+新增，走同样流程
4. 违反以上，bug 由后端负责
