# 金典软装ERP V4.0 — 全链路整合测试计划

## 概述

本文档定义全链路整合测试的范围、数据准备方案、执行步骤和验收标准。
目标是通过模拟真实业务操作，验证系统各模块间的数据流转和业务联动正确性。

---

## 1. 测试范围

### 覆盖模块

| # | 模块 | 端点前缀 | 覆盖程度 |
|---|------|---------|---------|
| 1 | 基础资料 - 客户 | `/api/v1/customers` | 创建/查询 |
| 2 | 基础资料 - 产品 | `/api/v1/products` | 创建/查询/搜索/分类 |
| 3 | 基础资料 - 供应商 | `/api/v1/suppliers` | 创建/列表 |
| 4 | 订单管理 | `/api/v1/orders` | 创建/详情/列表/状态推进/回滚 |
| 5 | 采购管理 | `/api/v1/purchases` | 拆分预览/生成/列表/详情/收货 |
| 6 | 仓库管理 | `/api/v1/warehouses` | 库存查询/流水 |
| 7 | 安装管理 | `/api/v1/installations` | 安装队/安装单创建/状态推进 |
| 8 | 财务管理 | `/api/v1/finance` | 应收款/收款确认/应付款 |
| 9 | 仪表盘 | `/api/v1/dashboard` | KPI 数据验证 |

### 不覆盖（需人工或前端测试）

- 主题切换（纯前端功能）
- 打印模块（需浏览器渲染）
- E2E 浏览器交互测试

---

## 2. 测试数据

### 2.1 基础资料种子

部署一个标准测试数据集，包含：

```
客户：         2 个（普通客户 + VIP 客户）
产品分类：     3 个（布艺窗帘、窗纱、辅料）
供应商：       2 个（杭州布艺供应商、广州辅料批发）
产品：         6 个（3 个主料 + 2 个辅料 + 1 个配件）
仓库：         1 个（主仓库）
安装队：       1 个（含 2 名安装工）
```

### 2.2 业务数据

全链路测试模拟一个完整的业务场景：

```
场景：杭州客户王先生订购客厅窗帘 + 阳台窗纱
- 订单金额：客厅窗帘 2 幅 × 1,200 元 = 2,400 元
             阳台窗纱 1 幅 × 500 元 = 500 元
             合计 2,900 元
- 涉及供应商：杭州布艺（供面料）、广州辅料（供配件）
- 流程：量尺 → 确认 → 分单 → 采购 → 入库 → 加工 → 安装 → 验收 → 收款
```

---

## 3. 测试执行流程

### Phase 1 — 基础资料准备

```
1. POST /api/v1/products/categories    创建 3 个产品分类
2. POST /api/v1/products/suppliers     创建 2 个供应商（含完整银行信息）
3. POST /api/v1/products               创建 6 个产品（关联供应商和分类）
4. POST /api/v1/customers              创建 2 个客户
5. POST /api/v1/installations/teams    创建 1 个安装队
6. POST /api/v1/installations/installers 创建 2 个安装工
```

验收标准：所有基础资料可通过 GET 列表接口查看到。

### Phase 2 — 订单创建与推进

```
7.  POST /api/v1/orders                创建订单（含 2 个物料行）
8.  GET  /api/v1/orders/{id}           验证订单详情（含物料、总金额）
9.  POST /api/v1/orders/{id}/advance   推进: initial → measured
10. POST /api/v1/orders/{id}/advance   推进: measured → confirmed
```

验收标准：订单创建成功，状态按预期流转，金额计算正确。

### Phase 3 — 采购拆分与收货

```
11. POST /api/v1/purchases/preview     获取采购拆分预览（按供应商分组）
12. POST /api/v1/purchases/generate    确认生成采购单
13. GET  /api/v1/purchases             验证采购单列表含供应商信息
14. POST /api/v1/purchases/{id}/receive 采购收货（验证库存更新）
15. POST /api/v1/orders/{id}/advance   推进: purchasing → stocked
```

验收标准：采购单按供应商正确拆分，供应商资料自动关联，收货后库存增加。

### Phase 4 — 安装与验收

```
16. POST /api/v1/installations/orders  创建安装单（关联订单）
17. POST /api/v1/installations/orders/{id}/status 推进安装状态
18. POST /api/v1/orders/{id}/advance   推进: install_scheduled → installed → accepted
```

验收标准：安装单关联正确订单，安装状态推进正常。

### Phase 5 — 财务确认

```
19. POST /api/v1/finance/receive       收款确认
20. GET  /api/v1/finance/receivables   验证应收款状态更新
```

验收标准：收款后应收款状态变为"已收"。

### Phase 6 — 仪表盘验证

```
21. GET  /api/v1/dashboard             验证 KPI 数据正确
```

验收标准：仪表盘显示正确的当月销售数据、订单数量。

---

## 4. 验收标准

| 检查点 | 预期结果 |
|--------|---------|
| 全部 API 返回 200 | 所有端点返回 HTTP 200，success=true |
| 数据一致性 | 订单总金额 = 物料金额之和 |
| 关联正确性 | 采购单供应商信息 = 供应商资料信息 |
| 状态机完整性 | 订单状态严格按 initial → ... → accepted 推进 |
| 库存准确性 | 收货后库存数量 = 原有库存 + 收货数量 |
| 财务准确性 | 收款后应收款余额归零 |

---

## 5. 失败处理

| 失败场景 | 处理策略 |
|---------|---------|
| API 返回 422/400 | 打印请求体和错误详情，分析字段校验规则 |
| N+1 查询超时 | 添加批量查询优化，标记为性能回归 |
| 状态推进非法 | 检查状态机配置，确认 `can_transition()` 逻辑 |
| 依赖数据不存在 | 检查 fixture 加载顺序和 scope |
