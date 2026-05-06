# 金典软装销售系统 V4.0 — 数据库设计

> 数据库：SQLite（开发）/ PostgreSQL（生产）
> ORM：SQLAlchemy 2.0
> 字符集：UTF-8

---

## 1. customers（客户表）

记录所有客户基本信息。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| name | VARCHAR(100) | 客户姓名 | NOT NULL |
| phone | VARCHAR(20) | 联系电话 | UNIQUE, NOT NULL |
| address | VARCHAR(500) | 收货/安装地址 | |
| decoration_stage | VARCHAR(50) | 装修阶段 | 如：硬装中/软装中/已入住 |
| source | VARCHAR(50) | 客户来源 | 如：自然到店/转介绍/网络 |
| remark | TEXT | 备注 | |
| created_at | DATETIME | 创建时间 | DEFAULT NOW |
| updated_at | DATETIME | 更新时间 | AUTO |

---

## 2. products（产品表）

窗帘及配件产品目录。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| code | VARCHAR(50) | 产品编码 | UNIQUE, NOT NULL |
| name | VARCHAR(200) | 产品名称 | NOT NULL |
| category | VARCHAR(50) | 分类 | 如：布帘/纱帘/卷帘/配件 |
| sub_category | VARCHAR(50) | 子分类 | 如：涤纶/棉麻/高精密 |
| unit | VARCHAR(20) | 单位 | 如：米/套/个 |
| standard_width | DECIMAL(10,2) | 标准门幅（米） | |
| standard_height | DECIMAL(10,2) | 标准高度（米） | |
| cost_price | DECIMAL(12,2) | 成本价 | |
| selling_price | DECIMAL(12,2) | 销售单价 | |
| min_price | DECIMAL(12,2) | 最低售价 | |
| color | VARCHAR(50) | 颜色 | |
| pattern | VARCHAR(50) | 花型 | |
| supplier_id | INTEGER | 供应商 FK | FK → suppliers(id) |
| stock | DECIMAL(12,2) | 当前库存 | |
| safety_stock | DECIMAL(12,2) | 安全库存 | |
| is_active | BOOLEAN | 是否上架 | DEFAULT TRUE |
| remark | TEXT | 备注 | |
| created_at | DATETIME | 创建时间 | |
| updated_at | DATETIME | 更新时间 | |

---

## 3. orders（订单表 — 重大升级）

销售订单主表，V4.0 核心表之一。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| order_no | VARCHAR(50) | 订单号 | UNIQUE, NOT NULL |
| customer_id | INTEGER | 客户 FK | FK → customers(id), NOT NULL |
| status | VARCHAR(30) | 订单状态 | 见状态说明 |
| order_type | VARCHAR(30) | 订单类型 | 如：零售/工程/样品 |
| total_amount | DECIMAL(14,2) | 订单总价 | |
| discount_amount | DECIMAL(14,2) | 折扣金额 | DEFAULT 0 |
| final_amount | DECIMAL(14,2) | 实付金额 | |
| measure_type | VARCHAR(20) | 测量方式 | 如：上门测量/自报尺寸 |
| measure_worker | VARCHAR(50) | 测量人员 | |
| measure_date | DATE | 预约测量日期 | |
| measure_status | VARCHAR(20) | 测量状态 | 待测量/已测量/无需测量 |
| expected_install_date | DATE | 预计安装日期 | |
| actual_install_date | DATE | 实际安装日期 | |
| delivery_address | VARCHAR(500) | 送货地址 | |
| delivery_status | VARCHAR(20) | 送货状态 | 待送货/已送货/无需送货 |
| delivery_date | DATE | 送货日期 | |
| production_status | VARCHAR(20) | 生产状态 | 待生产/生产中/已完成 |
| production_finished_date | DATE | 生产完成日期 | |
| payment_status | VARCHAR(20) | 付款状态 | 待付款/部分付款/已付清 |
| payment_method | VARCHAR(30) | 付款方式 | 如：现金/转账/刷卡 |
| received_amount | DECIMAL(14,2) | 已收金额 | DEFAULT 0 |
| received_date | DATE | 收款日期 | |
| invoice_status | VARCHAR(20) | 发票状态 | 未开/已开 |
| source | VARCHAR(50) | 订单来源 | 如：门店/线上/电话 |
| salesman | VARCHAR(50) | 业务员 | |
| remark | TEXT | 备注 | |
| created_by | INTEGER | 创建人 | FK → users(id) |
| created_at | DATETIME | 创建时间 | |
| updated_at | DATETIME | 更新时间 | |

### 订单状态（status）流转

```
待确认 → 已确认 → 生产中 → 已完成
   │                        │
   └──▶ 已取消 ◀─────────────┘
```

---

## 4. order_items（订单明细表）

订单产品明细，支持多产品组合。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| order_id | INTEGER | 订单 FK | FK → orders(id), NOT NULL |
| product_id | INTEGER | 产品 FK | FK → products(id) |
| product_code | VARCHAR(50) | 产品编码（冗余） | |
| product_name | VARCHAR(200) | 产品名称（冗余） | |
| category | VARCHAR(50) | 产品分类 | |
| unit | VARCHAR(20) | 单位 | |
| quantity | DECIMAL(12,2) | 数量 | NOT NULL |
| width | DECIMAL(10,2) | 宽度（米） | |
| height | DECIMAL(10,2) | 高度（米） | |
| area | DECIMAL(12,4) | 面积（平方米） | 自动计算 |
| unit_price | DECIMAL(12,2) | 单价 | |
| cost_price | DECIMAL(12,2) | 成本价（冗余） | |
| subtotal | DECIMAL(14,2) | 小计 | |
| process_fee | DECIMAL(12,2) | 加工费 | |
| install_fee | DECIMAL(12,2) | 安装费 | |
| remark | TEXT | 备注/特殊要求 | |
| created_at | DATETIME | 创建时间 | |

---

## 5. installation_orders（安装单表）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| install_no | VARCHAR(50) | 安装单号 | UNIQUE, NOT NULL |
| order_id | INTEGER | 关联订单 | FK → orders(id) |
| customer_id | INTEGER | 客户 FK | FK → customers(id) |
| install_team_id | INTEGER | 安装队 FK | FK → install_teams(id) |
| installer_id | INTEGER | 安装人员 FK | FK → installers(id) |
| status | VARCHAR(20) | 安装状态 | 待安装/安装中/已完成/已取消 |
| scheduled_date | DATE | 预约安装日期 | |
| scheduled_time | TIME | 预约时间 | |
| actual_start_time | DATETIME | 实际开始时间 | |
| actual_end_time | DATETIME | 实际结束时间 | |
| install_address | VARCHAR(500) | 安装地址 | |
| install_type | VARCHAR(30) | 安装类型 | 如：新装/拆旧/维修 |
| difficulty_level | VARCHAR(20) | 难度等级 | 简单/一般/复杂 |
| labor_fee | DECIMAL(12,2) | 人工费 | |
| material_fee | DECIMAL(12,2) | 材料费 | |
| total_fee | DECIMAL(12,2) | 安装总费用 | |
| quality_check | VARCHAR(20) | 质检结果 | 合格/返工 |
| quality_remark | TEXT | 质检备注 | |
| customer_signature | VARCHAR(200) | 客户签名（路径） | |
| photo_before | VARCHAR(500) | 安装前照片 | |
| photo_after | VARCHAR(500) | 安装后照片 | |
| remark | TEXT | 备注 | |
| created_by | INTEGER | 创建人 | FK → users(id) |
| created_at | DATETIME | 创建时间 | |
| updated_at | DATETIME | 更新时间 | |

---

## 6. installers（安装人员表）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| name | VARCHAR(50) | 姓名 | NOT NULL |
| phone | VARCHAR(20) | 联系电话 | UNIQUE |
| id_card | VARCHAR(30) | 身份证号 | |
| team_id | INTEGER | 所属队伍 | FK → install_teams(id) |
| skill_level | VARCHAR(20) | 技能等级 | 初级/中级/高级/组长 |
| status | VARCHAR(20) | 在职状态 | 在职/离职/休假 |
| join_date | DATE | 入职日期 | |
| hourly_rate | DECIMAL(10,2) | 时薪 | |
| monthly_salary | DECIMAL(10,2) | 月薪 | |
| bank_account | VARCHAR(50) | 银行账号 | |
| remark | TEXT | 备注 | |
| created_at | DATETIME | 创建时间 | |

---

## 7. install_teams（安装队表）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| name | VARCHAR(50) | 队名 | NOT NULL |
| leader_id | INTEGER | 队长 | FK → installers(id) |
| region | VARCHAR(50) | 服务区域 | |
| vehicle_no | VARCHAR(30) | 车辆牌照 | |
| contact_phone | VARCHAR(20) | 联系电话 | |
| status | VARCHAR(20) | 状态 | 正常/暂停 |
| remark | TEXT | 备注 | |
| created_at | DATETIME | 创建时间 | |

---

## 8. purchase_orders（采购单表）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| purchase_no | VARCHAR(50) | 采购单号 | UNIQUE, NOT NULL |
| supplier_id | INTEGER | 供应商 | FK → suppliers(id) |
| warehouse_id | INTEGER | 目标仓库 | FK → warehouse(id) |
| status | VARCHAR(20) | 采购状态 | 待审核/已审核/部分到货/已完成/已取消 |
| order_date | DATE | 订货日期 | |
| expected_date | DATE | 预计到货日期 | |
| actual_date | DATE | 实际到货日期 | |
| total_amount | DECIMAL(14,2) | 采购总价 | |
| paid_amount | DECIMAL(14,2) | 已付款 | DEFAULT 0 |
| payment_status | VARCHAR(20) | 付款状态 | 未付款/部分付款/已付清 |
| invoice_status | VARCHAR(20) | 发票状态 | 未开/已开 |
| delivery_no | VARCHAR(100) | 物流单号 | |
| handler | VARCHAR(50) | 经手人 | |
| remark | TEXT | 备注 | |
| created_by | INTEGER | 创建人 | FK → users(id) |
| created_at | DATETIME | 创建时间 | |

---

## 9. purchase_items（采购明细表）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| purchase_id | INTEGER | 采购单 FK | FK → purchase_orders(id) |
| product_id | INTEGER | 产品 FK | FK → products(id) |
| product_code | VARCHAR(50) | 产品编码（冗余） | |
| product_name | VARCHAR(200) | 产品名称（冗余） | |
| unit | VARCHAR(20) | 单位 | |
| quantity | DECIMAL(12,2) | 采购数量 | |
| received_quantity | DECIMAL(12,2) | 已到货数量 | DEFAULT 0 |
| unit_price | DECIMAL(12,2) | 采购单价 | |
| subtotal | DECIMAL(14,2) | 小计 | |
| batch_no | VARCHAR(50) | 批次号 | |
| production_date | DATE | 生产日期 | |
| expire_date | DATE | 有效期 | |
| remark | TEXT | 备注 | |

---

## 10. warehouse（仓库表）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| code | VARCHAR(30) | 仓库编码 | UNIQUE, NOT NULL |
| name | VARCHAR(100) | 仓库名称 | NOT NULL |
| type | VARCHAR(30) | 类型 | 如：原材料库/成品库/在途库 |
| address | VARCHAR(500) | 地址 | |
| manager | VARCHAR(50) | 负责人 | |
| phone | VARCHAR(20) | 联系电话 | |
| capacity | DECIMAL(14,2) | 容量（平方米） | |
| status | VARCHAR(20) | 状态 | 正常/停用 |
| remark | TEXT | 备注 | |
| created_at | DATETIME | 创建时间 | |

---

## 11. inventory（库存表）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| warehouse_id | INTEGER | 仓库 FK | FK → warehouse(id), NOT NULL |
| product_id | INTEGER | 产品 FK | FK → products(id), NOT NULL |
| batch_no | VARCHAR(50) | 批次号 | |
| quantity | DECIMAL(12,2) | 当前库存数量 | DEFAULT 0 |
| reserved_quantity | DECIMAL(12,2) | 预留数量 | DEFAULT 0 |
| available_quantity | DECIMAL(12,2) | 可用数量 | 计算得出 |
| unit_cost | DECIMAL(12,4) | 单位成本 | |
| total_cost | DECIMAL(14,4) | 库存总成本 | |
| production_date | DATE | 生产日期 | |
| expire_date | DATE | 过期日期 | |
| supplier_id | INTEGER | 供应商 | FK → suppliers(id) |
| last_check_date | DATE | 最后盘点日期 | |
| created_at | DATETIME | 创建时间 | |
| updated_at | DATETIME | 更新时间 | |
| **复合唯一** | | (warehouse_id, product_id, batch_no) | UNIQUE |

---

## 12. inventory_flow（库存流水表）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| warehouse_id | INTEGER | 仓库 FK | FK → warehouse(id) |
| product_id | INTEGER | 产品 FK | FK → products(id) |
| batch_no | VARCHAR(50) | 批次号 | |
| flow_type | VARCHAR(30) | 流转类型 | 见下方说明 |
| flow_no | VARCHAR(50) | 关联单号 | 如：订单号/采购单号 |
| order_type | VARCHAR(30) | 关联单据类型 | 如：sale_order/purchase_order/install |
| in_quantity | DECIMAL(12,2) | 入库数量 | DEFAULT 0 |
| out_quantity | DECIMAL(12,2) | 出库数量 | DEFAULT 0 |
| before_quantity | DECIMAL(12,2) | 变动前库存 | |
| after_quantity | DECIMAL(12,2) | 变动后库存 | |
| unit_cost | DECIMAL(12,4) | 单位成本 | |
| total_cost | DECIMAL(14,4) | 成本合计 | |
| operator | VARCHAR(50) | 操作人 | |
| operate_time | DATETIME | 操作时间 | |
| remark | TEXT | 备注 | |

### 流转类型（flow_type）

- `purchase_in` — 采购入库
- `sale_out` — 销售出库
- `install_out` — 安装领料
- `return_in` — 退货入库
- `return_out` — 退货出库（发给供应商）
- `adjust_in` — 盘点调整（盘盈）
- `adjust_out` — 盘点调整（盘亏）
- `transfer_in` — 调拨入库
- `transfer_out` — 调拨出库
- `sample_out` — 样品领用

---

## 13. finance_receivables（应收账款表）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| receivable_no | VARCHAR(50) | 单据编号 | UNIQUE, NOT NULL |
| source_type | VARCHAR(30) | 来源类型 | 如：sale_order/install |
| source_id | INTEGER | 来源ID | 关联订单或安装单 |
| source_no | VARCHAR(50) | 来源单号 | 冗余便于查询 |
| customer_id | INTEGER | 客户 FK | FK → customers(id) |
| amount | DECIMAL(14,2) | 应收金额 | NOT NULL |
| received_amount | DECIMAL(14,2) | 已收金额 | DEFAULT 0 |
| outstanding_amount | DECIMAL(14,2) | 未收金额 | 计算得出 |
| due_date | DATE | 应收日期 | |
| received_date | DATE | 实收日期 | |
| payment_method | VARCHAR(30) | 收款方式 | |
| status | VARCHAR(20) | 状态 | 待收款/部分收款/已结清 |
| invoice_no | VARCHAR(50) | 发票号 | |
| handler | VARCHAR(50) | 经办人 | |
| remark | TEXT | 备注 | |
| created_by | INTEGER | 创建人 | FK → users(id) |
| created_at | DATETIME | 创建时间 | |
| updated_at | DATETIME | 更新时间 | |

---

## 14. finance_payables（应付账款表）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| payable_no | VARCHAR(50) | 单据编号 | UNIQUE, NOT NULL |
| payable_type | VARCHAR(30) | 类型 | 如：purchase/install/expense |
| source_id | INTEGER | 来源ID | 采购单或安装单 |
| source_no | VARCHAR(50) | 来源单号 | |
| supplier_id | INTEGER | 供应商 FK | FK → suppliers(id) |
| installer_id | INTEGER | 安装工 FK | FK → installers(id) |
| team_id | INTEGER | 安装队 FK | FK → install_teams(id) |
| amount | DECIMAL(14,2) | 应付金额 | NOT NULL |
| paid_amount | DECIMAL(14,2) | 已付金额 | DEFAULT 0 |
| outstanding_amount | DECIMAL(14,2) | 未付金额 | 计算得出 |
| due_date | DATE | 应付日期 | |
| paid_date | DATE | 实付日期 | |
| payment_method | VARCHAR(30) | 付款方式 | |
| status | VARCHAR(20) | 状态 | 待付款/部分付款/已结清 |
| invoice_no | VARCHAR(50) | 发票号 | |
| handler | VARCHAR(50) | 经办人 | |
| remark | TEXT | 备注 | |
| created_by | INTEGER | 创建人 | FK → users(id) |
| created_at | DATETIME | 创建时间 | |

---

## 15. finance_expenses（日常费用表）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| expense_no | VARCHAR(50) | 单据编号 | UNIQUE, NOT NULL |
| expense_type | VARCHAR(50) | 费用类型 | 如：房租/工资/水电/推广/其他 |
| amount | DECIMAL(14,2) | 金额 | NOT NULL |
| expense_date | DATE | 费用日期 | |
| department | VARCHAR(50) | 部门 | |
| payee | VARCHAR(100) | 收款方 | |
| payment_method | VARCHAR(30) | 付款方式 | |
| status | VARCHAR(20) | 状态 | 待审批/已审批/已支付/已作废 |
| approver | VARCHAR(50) | 审批人 | |
| handler | VARCHAR(50) | 经办人 | |
| receipt_photos | VARCHAR(500) | 凭证照片 | 多个用逗号分隔 |
| remark | TEXT | 备注 | |
| created_by | INTEGER | 创建人 | FK → users(id) |
| created_at | DATETIME | 创建时间 | |

---

## 16. production_feedback（生产反馈表）

记录窗帘布料的加工生产进度。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| order_id | INTEGER | 订单 FK | FK → orders(id) |
| order_item_id | INTEGER | 订单明细 FK | FK → order_items(id) |
| product_id | INTEGER | 产品 FK | FK → products(id) |
| process_step | VARCHAR(50) | 工序名称 | 如：裁剪/缝制/打孔/整烫 |
| status | VARCHAR(20) | 状态 | 待加工/加工中/已完成 |
| worker | VARCHAR(50) | 加工人员 | |
| scheduled_date | DATE | 计划完成日期 | |
| actual_date | DATE | 实际完成日期 | |
| output_quantity | DECIMAL(12,2) | 产出数量 | |
| defect_quantity | DECIMAL(12,2) | 次品数量 | |
| remark | TEXT | 备注 | |
| created_at | DATETIME | 创建时间 | |
| updated_at | DATETIME | 更新时间 | |

---

## 17. followup_records（跟进记录表）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| customer_id | INTEGER | 客户 FK | FK → customers(id), NOT NULL |
| followup_type | VARCHAR(50) | 跟进方式 | 如：电话/微信/上门/短信 |
| followup_date | DATE | 跟进日期 | |
| next_followup_date | DATE | 下次跟进日期 | |
| content | TEXT | 跟进内容 | |
| intent_level | VARCHAR(20) | 意向等级 | 高/中/低/无意向 |
| status | VARCHAR(20) | 客户状态 | 潜在/意向/成交/流失 |
| handler | VARCHAR(50) | 经办人 | |
| created_by | INTEGER | 创建人 | FK → users(id) |
| created_at | DATETIME | 创建时间 | |

---

## 18. operation_logs（操作日志表）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| operator | VARCHAR(50) | 操作人 | |
| user_id | INTEGER | 用户ID | FK → users(id) |
| module | VARCHAR(50) | 模块 | 如：orders/customers |
| action | VARCHAR(50) | 操作类型 | 如：create/update/delete |
| target_type | VARCHAR(50) | 目标类型 | 表名 |
| target_id | INTEGER | 目标ID | |
| target_no | VARCHAR(50) | 目标编号 | 单号等 |
| detail | TEXT | 变更详情 | JSON 格式 |
| ip_address | VARCHAR(50) | IP 地址 | |
| user_agent | VARCHAR(500) | 浏览器信息 | |
| created_at | DATETIME | 操作时间 | |

---

## 19. suppliers（供应商表）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| code | VARCHAR(30) | 供应商编码 | UNIQUE |
| name | VARCHAR(100) | 供应商名称 | NOT NULL |
| contact | VARCHAR(50) | 联系人 | |
| phone | VARCHAR(20) | 联系电话 | |
| address | VARCHAR(500) | 地址 | |
| bank | VARCHAR(100) | 开户行 | |
| account_no | VARCHAR(50) | 银行账号 | |
| tax_no | VARCHAR(50) | 税号 | |
| payment_days | INTEGER | 账期（天） | |
| status | VARCHAR(20) | 状态 | 正常/停止合作 |
| remark | TEXT | 备注 | |
| created_at | DATETIME | 创建时间 | |

---

## 20. users（用户表）

系统登录用户。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键 | PK, AUTO |
| username | VARCHAR(50) | 用户名 | UNIQUE, NOT NULL |
| password_hash | VARCHAR(200) | 密码哈希 | NOT NULL |
| real_name | VARCHAR(50) | 真实姓名 | |
| phone | VARCHAR(20) | 手机号 | |
| email | VARCHAR(100) | 邮箱 | |
| role | VARCHAR(30) | 角色 | admin/manager/staff |
| department | VARCHAR(50) | 部门 | |
| status | VARCHAR(20) | 状态 | active/inactive |
| last_login | DATETIME | 最后登录时间 | |
| created_at | DATETIME | 创建时间 | |

---

## ER 关系摘要

```
customers 1 ──N orders
customers 1 ──N followup_records
orders 1 ──N order_items
orders 1 ──N installation_orders
orders 1 ──N finance_receivables
orders 1 ──N production_feedback

products 1 ──N order_items
products 1 ──N inventory
products 1 ──N inventory_flow
products 1 ──N purchase_items

install_teams 1 ──N installers
install_teams 1 ──N installation_orders
installers 1 ──N installation_orders
installers 1 ──N finance_payables

suppliers 1 ──N products
suppliers 1 ──N purchase_orders
suppliers 1 ──N finance_payables
suppliers 1 ──N inventory

warehouse 1 ──N inventory
warehouse 1 ──N inventory_flow
warehouse 1 ──N purchase_orders

purchase_orders 1 ──N purchase_items
purchase_orders 1 ──N finance_payables
```
