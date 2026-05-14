# 金典软装ERP V4.0 — 数据库设计

> 数据库：SQLite（开发）/ PostgreSQL（生产）
> ORM：SQLAlchemy 2.0 Async
> 字符集：UTF-8
> 表总数：28

---

## 约定

| 约定 | 说明 |
|------|------|
| 主键 | 所有表均使用 `id` INTEGER PRIMARY KEY AUTOINCREMENT |
| 时间戳 | 所有表继承 `TimestampMixin`，含 `created_at`、`updated_at` |
| 软删除 | Customer 继承 `SoftDeleteMixin`，含 `is_deleted`、`deleted_at` |
| FK 约束 | SQLite 下外键为逻辑引用，不强制物理约束（除 cascade 场景） |

---

## 1. 用户与认证

### 1.1 users（用户表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| username | String(50) | UNIQUE, NOT NULL | 登录用户名 |
| password_hash | String(200) | NOT NULL | bcrypt 哈希 |
| name | String(50) | NOT NULL | 真实姓名 |
| phone | String(20) | NOT NULL | 手机号 |
| role | String(20) | DEFAULT "staff" | admin / manager / staff / installer |
| position | String(50) | DEFAULT "" | 职位（导购/店长等） |
| is_active | Boolean | DEFAULT True | 是否启用 |
| avatar | String(500) | NULLABLE | 头像路径 |
| remark | Text | NULLABLE | 备注 |

### 1.2 roles（角色表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| name | String(50) | NOT NULL | 角色名称（如"超级管理员"） |
| code | String(50) | UNIQUE, NOT NULL | 角色编码（如 admin） |
| description | String(200) | DEFAULT "" | 角色描述 |
| permissions | Text | DEFAULT "[]" | 权限列表 JSON 数组 |
| sort_order | Integer | DEFAULT 0 | 排序号 |
| is_active | Boolean | DEFAULT True | 是否启用 |

---

## 2. 客户管理

### 2.1 customers（客户表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| name | String(50) | NOT NULL | 客户姓名 |
| phone | String(20) | INDEXED | 联系电话 |
| type | String(20) | DEFAULT "retail" | 类型：retail/project/designer |
| source | String(50) | DEFAULT "" | 客户来源 |
| level | String(10) | DEFAULT "C" | 等级：A/B/C |
| address | String(300) | DEFAULT "" | 地址 |
| community | String(100) | DEFAULT "" | 小区 |
| salesperson_id | Integer | NULLABLE | 业务员 ID |
| salesperson_name | String(50) | DEFAULT "" | 业务员姓名 |
| total_orders | Integer | DEFAULT 0 | 累计订单数 |
| total_amount | Float | DEFAULT 0.0 | 累计消费金额 |
| debt | Float | DEFAULT 0.0 | 欠款金额 |
| next_followup_date | Date | NULLABLE | 下次跟进日期 |
| last_contact_at | String(30) | NULLABLE | 最后联系时间 |
| tags | JSON | DEFAULT [] | 标签 |
| remark | Text | NULLABLE | 备注 |
| is_deleted | Integer | DEFAULT 0 | 软删除标记 |
| deleted_at | DateTime | NULLABLE | 删除时间 |

### 2.2 followup_records（跟进记录表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| customer_id | Integer | INDEXED, NOT NULL | 客户 ID |
| type | String(20) | DEFAULT "电话" | 跟进方式 |
| content | Text | NOT NULL | 跟进内容 |
| result | String(100) | DEFAULT "" | 跟进结果 |
| next_date | Date | NULLABLE | 下次跟进日期 |
| operator_id | Integer | NULLABLE | 操作人 ID |

---

## 3. 产品管理

### 3.1 product_categories（产品分类表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| name | String(50) | NOT NULL | 分类名称 |
| code | String(20) | DEFAULT "" | 分类编码 |
| parent_id | Integer | FK → product_categories(id) | 父分类 ID（支持层级） |
| sort_order | Integer | DEFAULT 0 | 排序号 |
| remark | Text | NULLABLE | 备注 |

### 3.2 suppliers（供应商表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| code | String(20) | DEFAULT "" | 供应商编码 |
| name | String(100) | NOT NULL | 供应商名称 |
| type | String(20) | DEFAULT "布艺" | 供应商类型 |
| contact | String(50) | DEFAULT "" | 联系人 |
| phone | String(20) | DEFAULT "" | 联系电话 |
| address | String(300) | DEFAULT "" | 地址 |
| delivery_days | Integer | DEFAULT 7 | 交货天数 |
| payment_terms | String(200) | DEFAULT "" | 付款条款 |
| qq | String(30) | DEFAULT "" | QQ |
| wechat | String(50) | DEFAULT "" | 微信 |
| bank_account | String(50) | DEFAULT "" | 银行账号 |
| bank_name | String(100) | DEFAULT "" | 开户行 |
| payee | String(50) | DEFAULT "" | 收款人 |
| is_active | Boolean | DEFAULT True | 是否启用 |
| remark | Text | NULLABLE | 备注 |

### 3.3 products（产品表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| code | String(30) | INDEXED | 产品编码 |
| name | String(200) | NOT NULL | 产品名称 |
| product_type | String(20) | DEFAULT "面料" | 产品类型（面料/辅料） |
| classification | String(20) | DEFAULT "" | 分类标签 |
| category_id | Integer | FK → product_categories(id) | 产品分类 ID |
| supplier_id | Integer | FK → suppliers(id) | 供应商 ID |
| model | String(50) | DEFAULT "" | 型号 |
| material | String(50) | DEFAULT "" | 材质 |
| color | String(50) | DEFAULT "" | 颜色 |
| pattern | String(50) | DEFAULT "" | 花型 |
| width | Integer | DEFAULT 280 | 幅宽（cm） |
| standard_width | DECIMAL(10,2) | DEFAULT 0 | 标准门幅（m） |
| weight | Integer | DEFAULT 0 | 克重 |
| fold_ratio | Float | DEFAULT 2.0 | 褶皱系数 |
| unit | String(10) | DEFAULT "米" | 单位 |
| calc_type | String(20) | DEFAULT "per_meter" | 计算方式 |
| processing_type_id | Integer | FK → processing_types(id) | 加工类型 ID |
| cost_price | DECIMAL(10,2) | DEFAULT 0 | 成本价 |
| min_price | DECIMAL(10,2) | DEFAULT 0 | 最低售价 |
| selling_price | DECIMAL(10,2) | DEFAULT 0 | 销售价 |
| stock | Integer | DEFAULT 0 | 当前库存 |
| safety_stock | Integer | DEFAULT 0 | 安全库存 |
| is_active | Boolean | DEFAULT True | 是否上架 |
| series | String(100) | DEFAULT "" | 系列 |
| remark | Text | NULLABLE | 备注 |

Relationships: `supplier` (joined), `category` (joined), `processing_type` (selectin)

---

## 4. 订单管理

### 4.1 orders（订单主表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| order_no | String(30) | UNIQUE, INDEXED, NOT NULL | 订单号 |
| order_type | String(20) | DEFAULT "窗帘" | 订单类型 |
| customer_id | Integer | FK → customers(id) | 客户 ID |
| customer_name | String(50) | DEFAULT "" | 客户姓名（冗余） |
| customer_phone | String(20) | DEFAULT "" | 客户电话（冗余） |
| salesperson_id | Integer | NULLABLE | 业务员 ID |
| salesperson_name | String(50) | DEFAULT "" | 业务员姓名 |
| quote_amount | DECIMAL(12,2) | DEFAULT 0 | 报价金额 |
| discount_amount | DECIMAL(12,2) | DEFAULT 0 | 折扣金额 |
| round_amount | DECIMAL(12,2) | DEFAULT 0 | 抹零金额 |
| amount | DECIMAL(12,2) | DEFAULT 0 | 实收金额 |
| received | DECIMAL(12,2) | DEFAULT 0 | 已收款 |
| debt | DECIMAL(12,2) | DEFAULT 0 | 欠款 |
| discount_reason | String(200) | DEFAULT "" | 折扣原因 |
| order_date | String(20) | DEFAULT "" | 下单日期 |
| delivery_date | String(20) | DEFAULT "" | 交货日期 |
| delivery_method | String(20) | DEFAULT "上门安装" | 提货方式 |
| status_key | String(30) | INDEXED | 状态编码 (initial/measured/...) |
| status_label | String(30) | DEFAULT "待量尺" | 状态显示名 |
| status_color | String(20) | DEFAULT "#909399" | 状态颜色 |
| content | String(500) | DEFAULT "" | 订单内容摘要 |
| remark | String(500) | DEFAULT "" | 备注 |
| install_address | String(300) | DEFAULT "" | 安装地址 |
| install_date | Date | NULLABLE | 安装日期 |
| install_time_slot | String(20) | DEFAULT "" | 安装时段 |
| measure_data | JSON | NULLABLE | 量尺数据 |
| install_requirements | Text | DEFAULT "" | 安装要求 |
| history | JSON | DEFAULT [] | 状态变更历史 |

### 4.2 order_items（订单明细表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| order_id | Integer | FK → orders(id), INDEXED, ON DELETE CASCADE | 订单 ID |
| item_type | String(20) | DEFAULT "窗帘" | 明细类型 |
| product_id | Integer | NULLABLE | 产品 ID |
| product_name | String(200) | DEFAULT "" | 产品名称（冗余） |
| product_code | String(50) | DEFAULT "" | 产品编码（冗余） |
| supplier_id | Integer | NULLABLE | 供应商 ID |
| room | String(50) | DEFAULT "" | 安装房间 |
| width | DECIMAL(8,2) | DEFAULT 0 | 宽度（m） |
| height | DECIMAL(8,2) | DEFAULT 0 | 高度（m） |
| fold_ratio | DECIMAL(4,2) | DEFAULT 2.0 | 褶皱系数 |
| unit | String(10) | DEFAULT "米" | 单位 |
| unit_price | DECIMAL(10,2) | DEFAULT 0 | 单价 |
| qty | DECIMAL(10,2) | DEFAULT 1 | 数量 |
| discount | DECIMAL(4,2) | DEFAULT 1.0 | 折扣率 |
| amount | DECIMAL(12,2) | DEFAULT 0 | 金额 |
| final_amount | DECIMAL(12,2) | DEFAULT 0 | 折后金额 |
| open_type | String(20) | DEFAULT "" | 开向 |
| style_code | String(20) | DEFAULT "" | 款式编码 |
| process_desc | String(200) | DEFAULT "" | 加工说明 |
| classification | String(20) | DEFAULT "" | 分类 |
| material_type | String(20) | DEFAULT "主料" | 主料/辅料标记 |
| calc_type | String(20) | DEFAULT "per_meter" | 计算方式 |
| note | Text | DEFAULT "" | 备注 |

---

## 5. 采购管理

### 5.1 purchase_orders（采购单表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| po_no | String(30) | UNIQUE, NOT NULL | 采购单号 |
| supplier_id | Integer | FK → suppliers(id) | 供应商 ID |
| supplier_name | String(100) | DEFAULT "" | 供应商名称（冗余） |
| contact | String(50) | DEFAULT "" | 联系人（冗余） |
| phone | String(20) | DEFAULT "" | 电话（冗余） |
| bank_account | String(50) | DEFAULT "" | 银行账号（冗余） |
| bank_name | String(100) | DEFAULT "" | 开户行（冗余） |
| payee | String(50) | DEFAULT "" | 收款人（冗余） |
| qq | String(30) | DEFAULT "" | QQ（冗余） |
| wechat | String(50) | DEFAULT "" | 微信（冗余） |
| order_ids | String(500) | DEFAULT "" | 关联订单 ID（逗号分隔） |
| total_amount | DECIMAL(12,2) | DEFAULT 0 | 采购总金额 |
| paid_amount | DECIMAL(12,2) | DEFAULT 0 | 已付款金额 |
| debt_amount | DECIMAL(12,2) | DEFAULT 0 | 欠款金额 |
| status | String(30) | DEFAULT "待采购" | 采购状态 |
| order_date | Date | NULLABLE | 下单日期 |
| expected_date | Date | NULLABLE | 预计到货日期 |
| arrived_date | Date | NULLABLE | 实际到货日期 |
| remark | String(500) | DEFAULT "" | 备注 |
| items | JSON | DEFAULT [] | 冗余的明细 JSON |

### 5.2 purchase_order_items（采购明细表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| purchase_order_id | Integer | FK → purchase_orders(id), INDEXED, ON DELETE CASCADE | 采购单 ID |
| product_id | Integer | NULLABLE | 产品 ID |
| product_name | String(200) | DEFAULT "" | 产品名称（冗余） |
| product_code | String(50) | DEFAULT "" | 产品编码（冗余） |
| spec | String(100) | DEFAULT "" | 规格 |
| quantity | DECIMAL(10,2) | DEFAULT 1 | 采购数量 |
| unit | String(10) | DEFAULT "米" | 单位 |
| unit_price | DECIMAL(10,2) | DEFAULT 0 | 单价 |
| subtotal | DECIMAL(12,2) | DEFAULT 0 | 小计 |
| arrived_qty | DECIMAL(10,2) | DEFAULT 0 | 已到货数量 |
| material_type | String(20) | DEFAULT "主料" | 主料/辅料标记 |
| remark | String(200) | DEFAULT "" | 备注 |

---

## 6. 仓库管理

### 6.1 warehouses（仓库表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| name | String(50) | NOT NULL | 仓库名称 |
| code | String(20) | DEFAULT "" | 仓库编码 |
| address | String(300) | DEFAULT "" | 仓库地址 |
| is_active | Boolean | DEFAULT True | 是否启用 |
| remark | String(200) | DEFAULT "" | 备注 |

### 6.2 inventories（库存表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| product_id | Integer | FK → products(id), INDEXED, NOT NULL | 产品 ID |
| warehouse_id | Integer | FK → warehouses(id), NOT NULL | 仓库 ID |
| quantity | DECIMAL(10,2) | DEFAULT 0 | 当前库存数量 |
| safety_stock | DECIMAL(10,2) | DEFAULT 0 | 安全库存 |

### 6.3 inventory_flows（库存流水表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| product_id | Integer | FK → products(id), INDEXED, NOT NULL | 产品 ID |
| warehouse_id | Integer | FK → warehouses(id), NOT NULL | 仓库 ID |
| flow_type | String(10) | NOT NULL | 流转类型 |
| qty_before | DECIMAL(10,2) | DEFAULT 0 | 变动前数量 |
| qty_change | DECIMAL(10,2) | DEFAULT 0 | 变动数量 |
| qty_after | DECIMAL(10,2) | DEFAULT 0 | 变动后数量 |
| ref_type | String(20) | DEFAULT "" | 关联单据类型 |
| ref_id | Integer | NULLABLE | 关联单据 ID |
| operator_id | Integer | NULLABLE | 操作人 ID |
| remark | Text | DEFAULT "" | 备注 |

**流转类型（flow_type）：**

| 编码 | 说明 |
|------|------|
| purchase_in | 采购入库 |
| sale_out | 销售出库 |
| adjust | 盘点调整 |

---

## 7. 安装管理

### 7.1 install_teams（安装队表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| name | String(50) | NOT NULL | 队名 |
| leader_name | String(50) | DEFAULT "" | 队长姓名 |
| leader_phone | String(20) | DEFAULT "" | 队长电话 |
| is_active | Boolean | DEFAULT True | 是否启用 |
| remark | String(200) | DEFAULT "" | 备注 |

### 7.2 installers（安装人员表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| name | String(50) | NOT NULL | 姓名 |
| phone | String(20) | UNIQUE, NOT NULL | 电话 |
| password_hash | String(200) | NULLABLE | 登录密码（可选） |
| is_active | Boolean | DEFAULT True | 是否在职 |
| remark | String(200) | DEFAULT "" | 备注 |

### 7.3 install_team_members（安装队成员关联表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| team_id | Integer | FK → install_teams(id), NOT NULL | 安装队 ID |
| installer_id | Integer | FK → installers(id), NOT NULL | 安装工 ID |

### 7.4 installation_orders（安装单表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| ins_no | String(30) | UNIQUE, NOT NULL | 安装单号 |
| order_id | Integer | FK → orders(id), NOT NULL | 关联订单 ID |
| order_no | String(30) | DEFAULT "" | 订单号（冗余） |
| customer_name | String(50) | DEFAULT "" | 客户姓名（冗余） |
| customer_phone | String(20) | DEFAULT "" | 客户电话（冗余） |
| address | String(300) | DEFAULT "" | 安装地址 |
| product_details | JSON | DEFAULT {} | 产品详情 JSON |
| measure_summary | Text | DEFAULT "" | 量尺摘要 |
| install_requirements | Text | DEFAULT "" | 安装要求 |
| team_id | Integer | FK → install_teams(id) | 安装队 ID |
| installer_id | Integer | NULLABLE | 安装工 ID |
| installer_name | String(50) | DEFAULT "" | 安装工姓名 |
| scheduled_date | Date | NULLABLE | 预约日期 |
| install_time_slot | String(20) | DEFAULT "" | 安装时段 |
| status | String(20) | DEFAULT "待分配" | 安装状态 |
| labor_cost | DECIMAL(10,2) | DEFAULT 0 | 人工费 |
| material_cost | DECIMAL(10,2) | DEFAULT 0 | 材料费 |
| total_cost | DECIMAL(10,2) | DEFAULT 0 | 总费用 |
| quality_score | Integer | NULLABLE | 质量评分 (1-5) |
| install_photos | JSON | DEFAULT [] | 安装照片列表 |
| customer_signature | Text | DEFAULT "" | 客户签名 |
| actual_start_time | DateTime | NULLABLE | 实际开始时间 |
| actual_end_time | DateTime | NULLABLE | 实际结束时间 |
| confirmed_at | DateTime | NULLABLE | 确认时间 |
| receivable_amount | DECIMAL(12,2) | DEFAULT 0 | 应收金额 |
| received_amount | DECIMAL(12,2) | DEFAULT 0 | 已收金额 |
| unpaid_amount | DECIMAL(12,2) | DEFAULT 0 | 未收金额 |
| remark | String(500) | DEFAULT "" | 备注 |

---

## 8. 财务管理

### 8.1 finance_receivables（应收款表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| order_id | Integer | FK → orders(id), NOT NULL | 关联订单 ID |
| order_no | String(30) | DEFAULT "" | 订单号（冗余） |
| customer_name | String(50) | DEFAULT "" | 客户名（冗余） |
| total_amount | DECIMAL(12,2) | DEFAULT 0 | 应收总额 |
| received_amount | DECIMAL(12,2) | DEFAULT 0 | 已收金额 |
| unpaid_amount | DECIMAL(12,2) | DEFAULT 0 | 未收金额 |
| status | String(20) | DEFAULT "待收款" | 状态 |
| due_date | Date | NULLABLE | 到期日期 |
| remark | String(300) | DEFAULT "" | 备注 |

### 8.2 finance_payables（应付款表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| ref_type | String(20) | NOT NULL | 关联类型（purchase/install） |
| ref_id | Integer | NOT NULL | 关联 ID |
| supplier_name | String(100) | DEFAULT "" | 供应商名（冗余） |
| total_amount | DECIMAL(12,2) | DEFAULT 0 | 应付总额 |
| paid_amount | DECIMAL(12,2) | DEFAULT 0 | 已付金额 |
| unpaid_amount | DECIMAL(12,2) | DEFAULT 0 | 未付金额 |
| status | String(20) | DEFAULT "待付款" | 状态 |
| due_date | Date | NULLABLE | 到期日期 |
| remark | String(300) | DEFAULT "" | 备注 |

### 8.3 finance_expenses（日常费用表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| category | String(30) | NOT NULL | 费用类别 |
| amount | DECIMAL(12,2) | NOT NULL | 金额 |
| expense_date | Date | NOT NULL | 费用日期 |
| operator_id | Integer | NULLABLE | 操作人 ID |
| remark | String(300) | DEFAULT "" | 备注 |

---

## 9. 生产反馈

### 9.1 production_feedbacks（生产反馈表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| feedback_no | String(30) | UNIQUE, NOT NULL | 反馈编号 |
| order_id | Integer | NULLABLE | 关联订单 ID |
| order_no | String(30) | DEFAULT "" | 订单号（冗余） |
| purchase_order_id | Integer | NULLABLE | 关联采购单 ID |
| feedback_type | String(20) | NOT NULL | 反馈类型 |
| description | Text | DEFAULT "" | 反馈描述 |
| photos | JSON | DEFAULT [] | 照片列表 |
| status | String(20) | DEFAULT "待处理" | 处理状态 |
| resolver | String(50) | DEFAULT "" | 处理人 |
| resolution | Text | DEFAULT "" | 处理结果 |
| resolved_at | DateTime | NULLABLE | 处理时间 |

---

## 10. 系统管理

### 10.1 dict_types（字典类型表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| dict_type | String(50) | UNIQUE, NOT NULL | 类型编码 |
| dict_name | String(100) | NOT NULL | 类型名称 |
| description | String(200) | DEFAULT "" | 描述 |
| sort_order | Integer | DEFAULT 0 | 排序号 |
| is_active | Boolean | DEFAULT True | 是否启用 |

内置 28 种字典类型：order_type, customer_source, expense_category, delivery_method, supplier_type, product_unit, fabric_width, material_composition, customer_category, install_location, finished_type, style_item, after_sale_category, bank_account, payment_type, order_fee_type, waste_type, self_use_type, purchase_return_type, expense_type, department, position, memo_type, message_type, order_status, product_category, warehouse, store_info

### 10.2 dict_items（字典项表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| dict_type | String(50) | INDEXED, NOT NULL | 所属字典类型编码 |
| dict_code | String(50) | NOT NULL | 项编码 |
| dict_label | String(100) | NOT NULL | 项名称（显示值） |
| sort_order | Integer | DEFAULT 0 | 排序号 |
| is_active | Boolean | DEFAULT True | 是否启用 |
| remark | String(200) | DEFAULT "" | 备注 |

### 10.3 store_configs（店铺配置表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| key | String(50) | UNIQUE, NOT NULL | 配置键 |
| value | Text | DEFAULT "" | 配置值 |
| description | String(200) | DEFAULT "" | 描述 |

### 10.4 operational_logs（操作日志表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| operator_id | Integer | NULLABLE | 操作人 ID |
| operator_name | String(50) | DEFAULT "" | 操作人姓名 |
| action | String(20) | NOT NULL | 操作类型（CREATE/UPDATE/DELETE） |
| resource | String(50) | NOT NULL | 操作资源（表名） |
| resource_id | Integer | NULLABLE | 资源 ID |
| detail | Text | DEFAULT "" | 变更详情 JSON |
| ip_address | String(50) | DEFAULT "" | IP 地址 |

---

## 11. 加工管理

### 11.1 processing_types（加工类型表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| name | String(50) | NOT NULL | 加工类型名称 |
| code | String(30) | UNIQUE, NOT NULL | 加工类型编码 |
| description | String(200) | DEFAULT "" | 描述 |
| sort_order | Integer | DEFAULT 0 | 排序号 |
| is_active | Boolean | DEFAULT True | 是否启用 |

### 11.2 processing_material_rules（加工辅料规则表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| processing_type_id | Integer | FK → processing_types(id), INDEXED, ON DELETE CASCADE | 加工类型 ID |
| material_name | String(100) | NOT NULL | 辅料名称 |
| default_product_name | String(200) | DEFAULT "" | 默认产品名称 |
| product_id | Integer | FK → products(id) | 关联产品 ID |
| unit | String(10) | DEFAULT "米" | 单位 |
| qty_formula | String(100) | DEFAULT "1" | 用量公式 |
| unit_price | Float | DEFAULT 0 | 单价 |
| sort_order | Integer | DEFAULT 0 | 排序号 |
| is_required | Boolean | DEFAULT True | 是否必选 |

---

## 12. 关系总览

```
users 1 ──N orders (salesperson)
users 1 ──N followup_records (operator)
users 1 ──N operational_logs (operator)

customers 1 ──N orders
customers 1 ──N followup_records
customers 1 ──N installation_orders

orders 1 ──N order_items
orders 1 ──N purchase_orders (via order_ids)
orders 1 ──N installation_orders
orders 1 ──N finance_receivables
orders 1 ──N production_feedbacks

product_categories 1 ──N product_categories (parent)
product_categories 1 ──N products

suppliers 1 ──N products
suppliers 1 ──N purchase_orders

products 1 ──N order_items
products 1 ──N inventories
products 1 ──N inventory_flows
products 1 ──N purchase_order_items
products 1 ──N processing_material_rules

warehouses 1 ──N inventories
warehouses 1 ──N inventory_flows

purchase_orders 1 ──N purchase_order_items
purchase_orders 1 ──N finance_payables

install_teams 1 ──N install_team_members
install_teams 1 ──N installation_orders
installers 1 ──N install_team_members
installers 1 ──N installation_orders

processing_types 1 ──N processing_material_rules
```
