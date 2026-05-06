# V4.0 审计报告

**审计时间**：2026-05-05
**审计范围**：V4.0 本地未提交代码 vs V3.0 已上线代码
**项目路径**：`/home/tianlj0320/sales-system-dev/`

---

## 一、模块对比总览

| V4 模块 | 对应 V3 | V4 行数 | 实质新增 vs 复制改名 |
|---------|---------|---------|----------------------|
| `customers_v4.py` | `customers.py` | 415 | 部分实质新增 |
| `installations_v4.py` | `installation_orders.py` | 329 | 实质重写 |
| `inventory_v4.py` | `warehouse.py` | 280 | 部分实质新增 |
| `products_v4.py` | `products.py` | 335 | 部分实质新增 |
| `purchases_v4.py` | `purchase.py` | 368 | 实质重写 |
| `reports_v4.py` | `reports.py` | 223 | 部分实质新增 |
| `warehouses_v4.py` | `warehouse.py` | 88 | 明显缩减 |
| `status_engine.py` | orders.py 状态机 | 169 | 全新（未集成） |

**V4 在 main.py 已注册 ✅**，但 `status_engine.py` **未被任何模块引用**。

---

## 二、逐模块详细对比

### 2.1 客户管理：`customers_v4.py` vs `customers.py`

#### V3 功能
- 客户 CRUD（列表/详情/创建/更新/软删除）
- 按姓名/电话搜索，按类型筛选
- 手机号查重 + 自动生成客户编号

#### V4 新增内容
- **沉睡客户**检测（按跟进间隔 `days` 参数，默认30天）
- **跟进记录**独立表（`followup_records`）+ 列表接口 + 添加接口
- **客户等级**筛选（A/B/C）
- **标签**支持（JSON数组，like 模糊查询）
- `customer_type` 字段（retail/project/designer）
- `next_followup_date` 字段 + 自动写入
- `followup_history` JSON 摘要（最近20条）
- `credit_limit` 赊账额度
- `measure_status` 量尺状态
- `salesperson_id` 字段

#### 复制改名 / 删减
- V3 的**客户编号自动生成**逻辑（`CU{today}{seq:03d}`）被移除
- V3 列表接口返回 schema（Pydantic 模型）改为直接 dict 返回（代码更简洁但类型安全降低）

#### 骨架 / 占位
- ✅ 完成度约 **85%**
- 无删除接口（客户软删除未迁移到 V4）
- 跟进记录添加后**未更新 `last_contact_at`**（代码有写，但 `last_contact_at` 字段未出现在 customers 表扩展中，migrations/v4_phase1.py 也未添加）

---

### 2.2 安装单：`installations_v4.py` vs `installation_orders.py`

#### V3 功能（`installation_orders.py`）
- 安装单列表（含按订单/状态/日期筛选）
- 安装单详情
- 更新安装单（联系人/地址/时间）
- 状态更新
- 派工（installer_id + scheduled_date）
- 安装排班视图

#### V4 重写内容（实质新增）
- 完全重写，使用独立的 `InstallationOrder` 模型（注意：V3 用的是 `InstallationOrder`，V4 用的是**另一个同名的 `InstallationOrder`**）
- **排班日历视图**（`/schedule`，按日期分组）
- **派工接口**（`/dispatch`）
- **状态更新接口**（`/status`，含签收时间自动记录 `confirmed_at`）
- 独立安装单创建（V3 安装单随订单自动生成）

#### 问题
- V4 的 `InstallationOrder` 表（migrations/v4_phase1.py）**缺少关键字段**：`customer_name`、`customer_phone`、`address`（这三个字段在 V4 API 的列表/详情中直接返回，但表 schema 中只有 `address`/`contact_phone`，缺少 `customer_name` 和 `customer_phone` 列）
- ✅ 完成度约 **75%**（骨架完整，细节有遗漏）

---

### 2.3 库存管理：`inventory_v4.py` vs `warehouse.py`

#### V3 功能
- 仓库流水记录（入/出）
- 库存查看
- 入库/出库操作（更新库存）

#### V4 新增内容
- **库存流水表**（`inventory_flow`）独立追踪
- **库存预警**（`/warnings`，低于安全库存）
- **库存调整**（盘盈盘亏，`/adjust`）
- **库存调拨**（跨仓库，`/transfer`）
- **库存汇总**（`/summary`）
- **库存流水**接口（支持 product/warehouse/type/日期筛选）

#### 关键问题
- `inventory_v4.py` 和 `products_v4.py` **存在重复的 transfer 接口**：
  - `inventory_v4.py` → `POST /api/v4/inventory/transfer`
  - `products_v4.py` → `POST /api/v4/products/transfer`（内部调用同一函数）
  - 两层都存在，造成路由冲突风险（V4 在 main.py 已注册 `inventory_v4` 在前，`products_v4` 在后，后注册的会覆盖前者）
- V3 的 `warehouse_id` 筛选在 V4 中被使用，但**产品表没有 warehouse_id 字段**（只有 `warehouse_id` 在 `InventoryFlow` 表中），多仓库支持是残缺的
- ✅ 完成度约 **70%**（核心功能有，链路有断裂）

---

### 2.4 产品管理：`products_v4.py` vs `products.py`

#### V3 功能
- 产品 CRUD
- 供应商管理（增删改查）
- 布版/系列管理（按供应商筛选）
- 产品列表（按名称/编号/供应商/分类/类型筛选）
- 产品详情（含关联供应商名/分类名）

#### V4 新增内容
- **价格三角校验**（`cost_price ≤ min_price ≤ selling_price`，`PUT /{id}/price`）
- `series` 系列字段支持
- `cf` 褶皱系数
- `model` 型号字段
- `cost_price` / `min_price` / `selling_price` 多价格体系
- 更完整的字段暴露（创建/更新/详情）

#### 删减
- ❌ **供应商 CRUD 未迁移**（`/suppliers` 等接口完全缺失）
- ❌ **布版/系列（FabricCategory）管理未迁移**
- ❌ **产品删除接口未迁移**

#### 问题
- `products_v4.py` 的 `POST /transfer` 和 `inventory_v4.py` 的 `POST /transfer` 重复
- ✅ 完成度约 **70%**（缺失供应商/分类管理是业务断裂点）

---

### 2.5 采购管理：`purchases_v4.py` vs `purchase.py`

#### V3 功能
- 采购单 CRUD（列表/详情/创建/删除）
- 状态更新（到货后自动入库）

#### V4 重写内容（实质新增）
- **采购单列表**（支持 status/supplier/日期/关键词筛选）
- **采购单详情**（含明细 items）
- **部分收货**（`/receive`，分批到货，自动更新状态）
- **待收货统计**（`/pending`）
- **更新采购单**（仅限备注/联系信息，状态不可回退）
- **删除采购单**（仅限待采购状态）
- V4 的 `PurchaseOrder` 模型字段比 V3 丰富（多了 `paid_amount`/`debt_amount`/`arrived_date` 等）

#### 逻辑问题
- `receive_purchase_v4` 中，如果多次到货，状态逻辑写死为"第二次就变全部到货"：
  ```python
  if po.status not in ("部分到货", "全部到货"):
      po.status = "部分到货"
  elif po.status == "部分到货":
      po.status = "全部到货"  # 第二次直接变全部，不计数
  ```
  正确的做法应该计数实际到货品种数 vs 采购品种总数。
- ✅ 完成度约 **80%**（核心逻辑有 bug，但可修复）

---

### 2.6 报表：`reports_v4.py` vs `reports.py`

#### V3 功能
- 月度销售报表（订单数/金额/平均单价/状态分布）
- 产品销量排行
- 员工业绩报表
- 月度趋势（每日累计）

#### V4 新增内容
- **每日销售报表**（`/daily`，独立日期查询）
- **员工业绩**（`/staff-performance`，支持年/月参数）
- **产品销售排行**（`/product-sales`，支持TOP N）

#### 删减
- ❌ **月度趋势**未迁移（`/trend` 接口消失）
- ❌ **状态分布统计**未迁移

#### 逻辑问题
- `staff_performance_report` 中 `install_map` 缺少 `avg_score`（从 `InstallationOrder` 表查询了 `avg_score` 但 SQL 中没有 `avg()` 聚合，查询结果中该字段为空）
- ✅ 完成度约 **75%**（功能比 V3 丰富，但有计算错误）

---

### 2.7 仓库：`warehouses_v4.py` vs `warehouse.py`

#### V3 功能
- 仓库流水记录
- 库存查看
- 入库/出库
- 仓库记录增删改

#### V4 严重缩减
- **仅返回虚拟主仓**（硬编码 `[{id: 1, code: "WH001", name: "主仓库"}]`）
- **库存列表**（`/{warehouse_id}/stock`）
- 所有出入库功能**完全缺失**

#### 问题
- V4 把 V3 的丰富功能缩减成一个占位模块，**实际不可用**（出入库、调拨记录全无）
- ✅ 完成度约 **25%**

---

### 2.8 状态机：`status_engine.py` vs orders.py 内嵌状态机

#### V3 状态机（orders.py）
```
created → confirmed → split → purchasing → stocked
→ processing → completed → install_order_generated
→ shipped → installed → accepted
```
- 内嵌在 orders.py（~50行配置 + 约50行函数）
- `production_exception` 异常状态参与步进数组但被跳过
- `get_next_status()` 手动跳过 SKIP_STATUSES

#### V4 状态机（status_engine.py，169行）
- **配置化 JSON 驱动**（`ORDER_STATUS_CONFIG`）
- 新增 `measured` 状态（量尺完成后确认前）
- `partial_in` 作为正式状态（部分到货）
- `install_scheduled` 替代 `install_order_generated`
- `after_sale` 独立售后状态
- **V3 → V4 兼容映射表**（`V3_TO_V4_STATUS_MAP`）
- 工具函数：`get_status_info` / `get_next_status` / `get_all_next_statuses` / `can_transition` / `is_terminal` / `normalize_status_key`

#### 关键问题
- **未被任何 V4 API 调用**（status_engine.py 纯粹是配置层，没有被 `orders.py` 或任何 V4 模块 import 使用）
- 状态机存在于隔离文件中，但没有集成到实际业务逻辑
- ✅ 配置本身完成度约 **90%**，但**完全未集成**（0%）

---

## 三、核心差异分析

### 3.1 状态机差异

| 维度 | V3 | V4 |
|------|----|----|
| 位置 | orders.py 内嵌 | 独立 `status_engine.py` |
| 状态数量 | 12态（含 shipped） | 12态（用 install_scheduled 替代 shipped，新增 measured/partial_in/after_sale） |
| 特性 | `production_exception` | 14态（含 measured/partial_in/after_sale/created） |
| 配置化 | ❌ 硬编码 | ✅ JSON 驱动 |
| 兼容层 | 无 | V3→V4 映射表 |
| 集成状态 | 已集成 | 未集成（孤立文件） |

### 3.2 数据模型差异

| 操作 | V3 | V4 |
|------|----|----|
| 订单表扩展 | 无迁移 | 21个新字段（measure_*/order_type_ext/price_locked/discount_reason/paid_amount 等） |
| 客户表扩展 | 无迁移 | 12个新字段（customer_type/level/tags/credit_limit/next_followup_date 等） |
| 新表 | InstallationOrder（同一名）| 新增 `inventory_flow`/`followup_records`/`login_attempts` + 新 InstallationOrder |
| 安装单 | V3 使用旧 InstallationOrder | V4 使用新 InstallationOrder（schema 有字段缺失） |
| 库存 | 无独立流水表 | `inventory_flow` 表记录每笔进出 |

### 3.3 API 设计差异

| 维度 | V3 | V4 |
|------|----|----|
| 路由前缀 | `/api/{resource}` | `/api/v4/{resource}` |
| 响应格式 | Pydantic Schema（类型安全） | 直接 dict（灵活但类型不安全） |
| 列表筛选 | 基础筛选 | 多维度筛选（日期范围/关键词/状态/标签） |
| 跟进记录 | 无 | 独立 `followup_records` 表 + API |
| 安装单 | 随订单自动生成 | 可独立创建安装单 |
| 采购到货 | 一次性全到 | 支持部分收货（分批） |
| 库存流水 | 无 | 独立流水表追踪 |
| 报表 | 月维度 | 日维度 + 月维度 |

---

## 四、完成度评估

| 模块 | 完成度 | 核心缺失 / 问题 |
|------|--------|----------------|
| customers_v4 | **85%** | 客户删除接口缺失，last_contact_at 字段 DB 未添加 |
| installations_v4 | **75%** | InstallationOrder 表缺 customer_name/phone 字段 |
| inventory_v4 | **70%** | transfer 接口重复注册（被 products_v4 覆盖）；多仓库支持残缺 |
| products_v4 | **70%** | 供应商 CRUD、FabricCategory CRUD、产品删除全部缺失；transfer 接口重复 |
| purchases_v4 | **80%** | 部分收货计数逻辑错误 |
| reports_v4 | **75%** | 月度趋势缺失；avg_score 计算错误 |
| warehouses_v4 | **25%** | 出入库功能完全缺失，只有壳 |
| status_engine | **90% 配置 / 0% 集成** | 配置完整但无任何模块调用 |

**整体估算**：V4 代码骨架完整，但各模块均有10~75%功能缺失或链路断裂，综合完成度约 **65~70%**。

---

## 五、是否值得继续 — 投入产出分析

### 5.1 如果继续 V4，需要的工作量

| 工作项 | 估算 |
|--------|------|
| 修复 installations_v4 表结构（补 customer_name/phone） | 0.5天 |
| 解决 transfer 接口重复（合并或删除一个） | 0.5天 |
| 补全 warehouses_v4 出入库功能 | 2天 |
| 补全 products_v4 供应商/分类管理 | 2天 |
| 修复 purchases_v4 部分收货逻辑 | 0.5天 |
| 修复 reports_v4 avg_score + 补 trend 接口 | 1天 |
| 集成 status_engine 到 orders_v4（含 V3 兼容） | 3天 |
| 补全 customers_v4 删除接口 + DB 字段迁移 | 1天 |
| V3→V4 双轨运行测试 + 数据迁移脚本 | 3天 |
| 前端适配（V4 API 对接） | **未知（估计 5~10天）** |
| **合计** | **约 13.5~18.5天**（不含前端） |

### 5.2 如果在 V3 基础上增量开发

| 工作项 | 估算 |
|--------|------|
| V3 客户增加标签/等级/跟进记录 | 2天 |
| V3 采购增加部分收货 + 库存流水表 | 2天 |
| V3 报表增加日粒度 | 1天 |
| V3 状态机配置化（参考 V4 status_engine） | 2天 |
| V3 增加安装单独立创建 | 1天 |
| **合计** | **约 8天**（风险低，渐进增量） |

### 5.3 建议结论

> **建议：在 V3.0 基础上增量开发，不继续 V4 重写路线。**

**理由**：

1. **V4 骨架庞大了 2.7倍**（新增 7个 API 模块），但实际业务价值只比 V3 多了跟进记录、部分收货、库存流水、价格三角校验等有限功能
2. **status_engine 完全未集成**，状态机改造是 V4 的核心价值点，但这个核心价值是"孤立配置"而非"可用代码"
3. **重复的 transfer 接口**说明 V4 开发期间模块设计有混乱（库存和产品的调拨功能重复实现又互相覆盖）
4. **warehouses_v4 只剩 25%**说明 V4 开发者对仓库模块的需求判断有偏差（大面积复制改名后大幅删减功能，这不是正常迭代）
5. **13.5~18.5天**的收尾工作量 vs **8天**的增量改进，前者是后者的 **1.7~2.3倍**，投入产出比明显差于增量路线
6. V3 已稳定运行，V4 的"完整替换"方案风险高（数据迁移、双轨并行）；增量改进可以随时回滚

---

## 六、给老板的摘要（中文）

**V4.0 审计结论：骨架完整但链路断裂，建议走增量路线。**

**进展**：V4 的 7个 API 模块已在 main.py 全部注册，状态机配置完整，代码量达 2038 行。

**实质新增**（相比 V3）：
- 客户跟进记录 + 沉睡客户提醒
- 安装单独立管理（排班/派工/状态）
- 采购分批到货
- 库存流水追踪 + 调拨
- 价格三角校验（成本价 ≤ 最低售价 ≤ 销售价）
- 每日销售报表

**主要问题**：
1. **warehouses_v4 只剩 25%**——仓库核心功能（出入库）完全缺失
2. **transfer 接口重复**——`inventory_v4` 和 `products_v4` 各有一个调拨接口，互相覆盖
3. **status_engine 完全未集成**——状态机是孤立文件，没被任何 API 调用
4. **部分收货计数逻辑有 bug**——第二次到货直接标"全部到货"，不验证是否全部到齐
5. **供应商/分类/产品删除等 V3 基础功能缺失**——这是业务断裂点

**如果继续 V4**：约需 13.5~18.5 天收尾（不含前端），且存在高风险的数据迁移。

**如果走增量路线**：约需 8 天在 V3 基础上增加上述功能，风险更低。

**建议**：取 V4 的状态机设计 + 跟进记录 + 分批收货逻辑，以增量补丁方式融入 V3，不做整体替换。
