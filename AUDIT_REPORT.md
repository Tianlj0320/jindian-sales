# 金典软装窗帘销售系统 V3.0 全面审计报告

**审计时间：** 2026-05-05  
**项目路径：** `/home/tianlj0320/sales-system-dev/`  
**Git分支：** v3.0-dev  
**最新Commit：** 8195ab4 (fix: 订单创建防御性校验 + 状态更新逻辑修复)  
**技术栈：** FastAPI + SQLite + 原生JS (Element Plus UI)

---

## 📊 执行摘要

| 维度 | 评分 | 说明 |
|------|------|------|
| 代码质量 | ⚠️ 中等 | models.py 与 DB schema 严重脱节；两套状态引擎并存 |
| 功能完整性 | ⚠️ 中等 | 核心CRUD完整，但量尺/测量流程/派工等 V4.0 状态缺失 |
| 前端完整性 | ⚠️ 中等 | 三大页面齐全；部分模块仍依赖 localStorage 持久化 |
| 数据库健康 | ⚠️ 中等 | 11张表未映射到 models.py；废弃表未清理 |
| 测试覆盖 | ❌ 薄弱 | 仅覆盖订单创建+流转+删除，无采购/财务/安装单测试 |

---

## 🔴 严重问题（必须修复）

### 1. 【高危】models.py 与数据库 schema 严重不一致

**位置：** `app/models.py` vs `sales.db`

数据库 `orders` 表比 models.py 多出以下字段（全部缺失）：

| 数据库字段 | 类型 | 说明 |
|-----------|------|------|
| `salesperson_id` | INTEGER FK | 关联员工ID（models.py 只有 salesperson 名字段） |
| `creator_id` | INTEGER | 创建人ID |
| `reviewer_id` | INTEGER | 审核人ID |
| `remark` | VARCHAR(500) | 订单备注 |
| `deleted_at` | DATETIME | 软删除时间戳 |
| `order_type_ext` | VARCHAR(20) | 订单类型扩展（retail/project） |
| `price_locked_at` | VARCHAR(30) | 价格锁定时间 |
| `discount_reason` | VARCHAR(200) | 折扣原因 |
| `install_slot` | VARCHAR(10) | 安装时段 |
| `paid_amount` | DECIMAL(12,2) | 已付款金额（与 received 重复） |
| `after_sale_reason` | VARCHAR(500) | 售后原因 |
| `after_sale_status` | VARCHAR(30) | 售后状态 |
| `last_contact_at` | VARCHAR(30) | 最近联系时间 |
| `measure_width/height` | DECIMAL(8,2) | 量尺宽高 |
| `window_width/height` | DECIMAL(8,2) | 窗户宽高 |
| `measure_datetime` | VARCHAR(30) | 量尺时间 |
| `measure_operator_id` | INTEGER | 量尺操作员 |

`customers` 表同样缺失：`salesperson_id`, `deleted_at`, `total_orders`, `total_amount`。

**风险：** ORM 查询时这些字段被忽略，数据库实际有值但 API 不返回；前端无法使用这些字段。

---

### 2. 【高危】两套状态引擎并存，V4.0 引擎未被调用

**文件：**
- `app/core/status_engine.py` — 定义 V4.0 状态机（initial→measured→confirmed→split...→accepted）
- `app/api/orders.py` — 自己 inline 定义 V3.0 状态（created→confirmed→split...→accepted）

`advance` 端点和状态更新逻辑**完全不使用** `status_engine.py`，两个文件各自为政。

`status_engine.py` 中的以下 V4.0 状态在 `ORDER_STATUS_MAP` 中**完全没有**：
- `initial`（待量尺）
- `measured`（已量尺）
- `partial_in`（部分到货）
- `install_scheduled`（已派工）
- `after_sale`（售后中）

**后果：** V4.0 新状态系统是"死代码"，量尺流程（initial→measured→confirmed）无法通过 `advance` 接口推进。

---

### 3. 【高危】11张数据库表未映射到 models.py

以下表存在于 `sales.db` 但 `app/models.py` 中**完全没有定义**：

| 表名 | 用途 |
|------|------|
| `dict_categories` | 码表分类 |
| `dict_items` | 码表明细（已通过 raw SQL 访问，但未 ORM 化） |
| `login_attempts` | 登录尝试日志（未使用） |
| `operational_logs` | 操作日志 |
| `order_fees` | 订单费用明细 |
| `receipts` | 收据 |
| `styles` | 款式/样式表 |
| `system_settings` | 系统配置 |
| `tenants` | 租户（未使用） |
| `wechat_notify_records` | 微信通知记录 |
| `category_accessories` | 配件分类 |

---

### 4. 【高危】码表(dict) API 鉴权路径不一致

**文件：** `app/middleware.py`

`is_public_path()` 中 `/api/dicts` 是公开的，但 `/api/dicts/items`（POST/PUT/DELETE）也是同样前缀，也无需认证即可写入。这允许任意未登录用户**增删改**码表数据。

```python
if path == "/api/dicts":  # ← 只匹配精确路径，不包括 /api/dicts/items
    return True
```

**对比：** `/api/track` 和 `/api/installer` 使用 `startswith()` 前缀匹配更安全。

---

## 🟡 中等问题（应该修复）

### 5. 【中】schemas.py 字段严重不完整

`OrderDetailData` 和 `OrderListItem` 返回的字段远少于数据库实际存在的字段。例如：

```python
# schemas.py 缺少：
# salesperson_id, creator_id, review_status, remark, order_type_ext,
# price_locked_at, discount_reason, after_sale_reason, after_sale_status,
# measure_width, measure_height, window_width, window_height, measure_datetime
```

前端如果依赖 API 返回值来做逻辑，很多数据根本拿不到。

---

### 6. 【中】finance API 使用 `dict` 而非正式 Pydantic Schema

**文件：** `app/api/finance.py`

所有端点 `response_model=dict`，没有使用 Pydantic model 校验。应该抽取 `FinanceRecordSchema` 等正式 schema。

---

### 7. 【中】安装单派工功能前端部分已实现但依赖字段不完整

**文件：** `app/api/installations_v4.py`

派工端点 `dispatch_installation` 需要 `installer_id` 和 `scheduled_date`，但：
- `InstallationOrder` 模型中 `installer_id` 是 Integer，但 `installer_name` 需要手动填充（无关联查询）
- 前端 `installer.html` 调用安装工列表 API，但字段映射不完整
- 安装单生成后不会自动推送到安装工 App 端（需手动派工）

---

### 8. 【中】采购汇总（多订单合并）功能部分实现

**文件：** `app/api/purchase_orders.py`

存在 `POST /api/purchase-orders/merge`（合并采购单），但：
- 合并后的 `po_no` 没有在 `make_po_no()` 中补全序号（返回 `PO20260505` 而非 `PO20260505001`）
- 合并后状态更新逻辑未在 `advance` 流程中体现

---

### 9. 【中】废弃表未清理，数据无法利用

`login_attempts`、`operational_logs`、`tenants`、`wechat_notify_records` 等表存在但：
- 没有任何 API 操作这些表
- `login_attempts` 表实际有数据（审计日志），但无人使用
- 应决定是迁移数据还是删除

---

### 10. 【中】OrderItem 关系表未被充分使用

`OrderItem` 表（order_items）虽然有 256 条记录，但：
- 采购单拆分 (`split/{order_id}`) 时直接用 `Order.items` JSON 字段，没有利用 `order_items` 表的规范化数据
- `update_order` 中会重建 `OrderItem` 记录，但查询时从不读 `order_items` 表（只读 `Order.items` JSON）

---

## 🟢 轻微问题（建议修复）

### 11. `status_key` 字段长度只有 30 字符

**文件：** `app/models.py`

```python
status_key = Column(String(30), default="created")
```

`status_engine.py` 中的 `after_sale`（7字符）、`install_scheduled`（17字符）都在限制内，但 `install_order_generated`（22字符）已是极限。建议扩充到 50 字符以备扩展。

---

### 12. 测试覆盖仅限订单基本流程

| 测试文件 | 覆盖内容 |
|---------|---------|
| `test_orders.py` | 订单列表/创建/流转/删除/详情 |
| `test_auth.py` | 登录/Token 校验 |
| `test_customers.py` | 客户 CRUD |
| `test_installation.py` | 安装单列表/生成/状态 |
| `test_api.py` | 通用 API 检查 |

**完全缺失：**
- 采购单全流程测试（split → purchasing → stocked）
- 财务收付款测试
- 生产反馈测试
- 多订单合并采购测试
- 安装单派工测试

---

### 13. 前端仍部分依赖 localStorage

**文件：** `static/js/12-dict.js` 注释明确写道：

> "原来 saveDictItem / delDictItem 只写 localStorage，现在改为：先调后端 API 持久化，再更新本地状态并同步 localStorage"

虽然已改为 API 优先，但**降级策略**是"API 失败仍保留本地"，这意味着：
- 多人协作时可能看到不同步的码表
- localStorage 数据过期不会被清理

---

### 14. `track.html`（客户查进度）前端模块

**文件：** `static/track.html`（234KB）

- 调用 `/api/track` 获取进度，依赖 `status_history` 字段
- 若 `Order.history` 为空（历史记录未初始化），返回不友好

---

## 📋 功能缺失清单

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 量尺/测量流程 | P1 | `initial → measured` 状态和对应 UI（量尺App端）缺失 |
| 安装单派工推送 | P1 | 生成安装单后需主动推送到安装工 App，仍需手动派工 |
| 采购汇总单自动序号 | P1 | `merge` 端点的 `po_no` 生成逻辑有 bug |
| 码表持久化 API | P2 | 后端已实现但需要 `dict_categories` ORM model |
| 多客户跟进记录 | P2 | `followup_records` 表存在但无 API |
| 库存预警规则 | P2 | `inventory_flow` 存在但预警规则未实现 |
| 操作日志查询 | P2 | `operational_logs` 表有数据但无 API |
| 订单编辑功能 | P2 | 已有 `PUT /api/orders/{id}` 但前端入口缺失 |
| 收款收据生成 | P3 | `receipts` 表存在但无 API 和 UI |
| 微信通知记录 | P3 | `wechat_notify_records` 表无 API |

---

## ✅ 订单状态流转审计（V3.0 规范 vs 实现）

规范要求：
```
created → confirmed → split → purchasing → stocked → processing → 
completed → install_order_generated → shipped → installed → accepted
```

**审计结果：**

| 流转 | advance端点 | 状态映射 | 备注 |
|------|------------|---------|------|
| created → confirmed | ✅ | ✅ | |
| confirmed → split | ✅ | ✅ | 需手动生成采购单 |
| split → purchasing | ✅ | ✅ | |
| purchasing → stocked | ✅ | ✅ | |
| stocked → processing | ✅ | ✅ | |
| processing → completed | ✅ | ✅ | |
| completed → install_order_generated | ✅ | ✅ | 自动生成安装单 |
| install_order_generated → shipped | ✅ | ✅ | |
| shipped → installed | ✅ | ✅ | |
| installed → accepted | ✅ | ✅ | |

> ⚠️ `production_exception`（生产异常）状态存在于 `ORDER_STATUS_MAP`，但不在 `STATUS_STEPS` 线性步骤中，无法通过 advance 推进，只能通过 `PUT /status` 手动设置。

---

## 🔒 安全审计

| 项目 | 状态 | 说明 |
|------|------|------|
| SQL 注入 | ⚠️ 警告 | `dicts.py` 使用 `text()` 拼接 SQL，但参数化正确；建议迁移到 ORM |
| XSS | ✅ 无直接风险 | API 层无渲染，前端 Vue 自动转义 |
| 权限绕过 | 🔴 码表CRUD | `/api/dicts/items`（POST/DELETE）无需认证 |
| 认证中间件 | ✅ | `AuthMiddleware` 覆盖 `/api/` 路径，公开路径白名单清晰 |
| 敏感信息 | ⚠️ 警告 | `salesperson` 以明文名字存储，应改为 `salesperson_id` FK |
| CORS | ✅ | `ALLOWED_ORIGINS` 读取环境变量，生产需配置具体域名 |

---

## 📁 代码文件健康概览

| 文件 | 行数 | 问题 |
|------|------|------|
| `app/models.py` | ~450 | **models/DB 不一致** |
| `app/schemas.py` | ~420 | 字段不完整 |
| `app/api/orders.py` | ~650 | 状态引擎重复 |
| `app/api/purchase_orders.py` | ~800+ | merge 序号 bug |
| `app/core/status_engine.py` | ~150 | V4.0 引擎死代码 |
| `static/index.html` | 192KB | 大文件，可拆分 |
| `static/js/13-order-form.js` | 415行 | 核心表单逻辑 |

---

## 📌 建议优先级

### 🔴 第一批（立即修复）
1. 补全 `models.py` 中缺失的数据库字段（orders、customers）
2. 修复码表 `/api/dicts/items` 鉴权漏洞
3. 统一状态引擎：删除 `status_engine.py` 或在 orders API 中调用它

### 🟡 第二批（短期修复）
4. 补全 `schemas.py` 字段定义
5. 补充关键流程测试（采购、安装单）
6. 修复 `merge` 端点 `po_no` 序号 bug

### 🟢 第三批（持续优化）
7. ORM 化 `dict_items` 和 `dict_categories`
8. 清理废弃数据库表
9. 前端拆分 `index.html`（按模块懒加载）
10. 实现量尺/测量 V4.0 状态流转

---

*审计报告由 AI 子智能体生成 | 时间：2026-05-05 17:38 GMT+8*
