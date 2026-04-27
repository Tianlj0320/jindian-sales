# 金典软装销售系统 V3.0 — 3天冲刺计划

> **目标**：系统性修复所有已知 bug，完善缺失功能，文档同步更新  
> **团队**：dev-swarm（小开）/ qa-swarm（小测）/ doc-swarm（小档）  
> **时间**：每天 ≥10 小时投入  
> **分支**：v3.0-dev  

---

## 📅 Day 1（4月28日）— 扫雷日：修完所有 Bug

### 08:00 - 09:00 **晨会 + 部署验证**
- 确认服务运行正常：`curl http://localhost:8000/health`
- 拉取最新代码：`git pull origin v3.0-dev`
- 执行数据库迁移（如未执行）：
  ```bash
  sqlite3 sales.db "ALTER TABLE products ADD COLUMN remark VARCHAR(500) DEFAULT '';"
  ```

### 09:00 - 12:00 **上午：API 全面审计 + 修复**

**dev-swarm 任务**：

#### 1. 审计所有前端 API 调用方法 vs 后端实际路由
逐个检查 `01-api.js` 中每个 `apiXxx` 方法：

| 模块 | API方法 | 后端方法 | 状态 |
|------|---------|---------|------|
| 供应商 | updateSupplier | PUT ✅ | 已修复 |
| 供应商 | deleteSupplier | DELETE | ✅ |
| 分类 | updateCategory | PUT | ✅ 已修复 |
| 产品 | update | PUT | ✅ 已修复 |
| 产品 | create | POST | ✅ |
| 客户 | update | PUT | ✅ 已修复 |
| 客户 | create | POST | ✅ |
| 员工 | update | PUT | ✅ 已修复 |
| 员工 | create | POST | ✅ |
| 订单 | create | POST | ✅ |
| 订单 | update | PUT | ✅ |
| 订单 | updateStatus | PUT | ✅ |
| 订单 | delete | DELETE | ✅ |
| 采购 | create | POST | ✅ |
| 采购 | updateStatus | PUT | ✅ |
| 仓库 | createRecord | POST | 待查 |
| 财务 | (各方法) | POST | 待查 |

#### 2. 字段名 snake_case vs camelCase 全面检查
- `delivery_days` / `deliveryDays`
- `order_ids` / `orderIds`
- `expected_date` / `expectedDate`
- `supplier_id` / `supplierId`
- `category_id` / `categoryId`
- `unit_price` / `unitPrice`
- `salesperson_id` / `salespersonId`
- `install_address` / `installAddress`
- `install_date` / `installDate`
- `received_amount` / `received`
- `debt_amount` / `debt`
- `customer_name` / `customerName`

#### 3. 检查并修复 dialog 保存后的列表刷新问题

**具体问题**：
- 客户保存后不刷新列表 → `saveCustomer` 中调用 `loadCustomers()`
- 员工保存后不刷新列表 → `saveEmployee` 中调用 `loadEmployees()`
- 供应商保存后不刷新列表 → `saveSupplier` 中已有 ✅

### 12:00 - 13:00 午饭休息

### 13:00 - 18:00 **下午：前端交互问题修复**

#### 4. 修复 Vue ref/getter/setter 残留问题
- 检查 `index.html` 中所有 `computed` 用法，确保没有只读的 computed 被用于 `v-model`
- 检查 getter/setter 对象传递问题（特别是 `dictCat`、`suppSearch`、`suppTypeF`）

#### 5. 完善缺失的编辑功能
- **员工资料**：无编辑功能 → 参照 `saveSupplier` 实现 `saveEmployee`
- **订单编辑**：无编辑功能 → 评估优先级，低则记录待办

#### 6. 修复订单状态流转
- 检查订单状态8态流转是否完整
- 检查各状态下可执行的操作按钮

### 18:00 - 19:00 **日报 + 代码提交**
- 所有修复 commit + push
- 更新 BUG-MEMO.md
- QA 开始准备测试用例

---

## 📅 Day 2（4月29日）— 完善日：补全功能 + 全流程测试

### 08:00 - 09:00 **晨会 + 代码审查**
- 审查 Day 1 所有提交
- QA 开始执行测试

### 09:00 - 12:00 **上午：完善缺失功能**

#### 7. 员工管理模块完善
- `07-employee.js` 添加 `loadEmployees` 后的重载逻辑
- `saveEmployee` 参照 `saveCustomer` 修复

#### 8. 订单模块完善
- 检查订单详情弹窗
- 检查订单明细（items）的增删改
- 检查订单关联的安装单生成

#### 9. 财务结算模块
- 检查收款/付款/费用记录的 CRUD
- 检查与订单的关联

### 12:00 - 13:00 午饭休息

### 13:00 - 18:00 **下午：端到端测试**

#### 10. QA 执行完整测试（按模块）
每个模块测试清单：

| 模块 | 测试项 | 结果 |
|------|--------|------|
| 登录 | 正常登录 | |
| 登录 | 错误密码 | |
| 登录 | 自动登录（刷新） | |
| 首页 | 仪表盘数据 | |
| 供应商 | 列表加载 | |
| 供应商 | 新增（所有字段） | |
| 供应商 | 编辑 | |
| 供应商 | 删除 | |
| 供应商 | 筛选+搜索 | |
| 产品 | 列表加载 | |
| 产品 | 新增 | |
| 产品 | 编辑 | |
| 产品 | 删除 | |
| 产品 | 筛选+搜索 | |
| 客户 | 列表加载 | |
| 客户 | 新增 | |
| 客户 | 编辑 | |
| 客户 | 删除 | |
| 员工 | 列表加载 | |
| 员工 | 新增 | |
| 员工 | 编辑 | |
| 员工 | 删除 | |
| 码表 | 分类切换 | |
| 订单 | 新建 | |
| 订单 | 状态流转 | |
| 订单 | 删除 | |
| 采购 | 新建采购单 | |
| 采购 | 更新状态 | |
| 仓库 | 入库 | |
| 仓库 | 出库 | |
| 安装 | 创建安装单 | |
| 财务 | 收款 | |
| 财务 | 付款 | |
| 报表 | 月报 | |

#### 11. 安装工端测试（/static/installer.html）
- 安装工登录
- 查看任务列表
- 更新安装状态

#### 12. 客户查进度测试（/static/track.html）
- 输入订单号查询
- 查看进度条

### 18:00 - 19:00 **日报 + 修复**
- QA 汇总所有问题
- dev-swarm 修复 Day 2 发现的新 bug
- doc-swarm 更新 API 文档

---

## 📅 Day 3（4月30日）— 收尾日：问题收敛 + 上线准备

### 08:00 - 09:00 **晨会**
- 确认剩余问题数量
- 决定哪些必须修，哪些可以延期

### 09:00 - 12:00 **上午：问题修复收尾**

#### 13. 修复 Day 2 QA 发现的所有问题
- 按优先级排序
- 高优先级（影响业务流程）必须修
- 中优先级（非核心）记录待办
- 低优先级（体验类）可延期

#### 14. 特殊问题处理
- **问题#11**：老板账号 `password_hash` 缺失 → 检查登录逻辑是否绕过了 hash 检查
- **问题#12**：truck 图标缺失 → 替换为其他图标或使用文字

### 12:00 - 13:00 午饭休息

### 13:00 - 17:00 **下午：文档 + 上线准备**

#### 15. API 文档全面更新
- doc-swarm 逐个核对 API 返回值
- 更新 `docs/V3.0_API文档.md`
- 确保文档与代码一致

#### 16. CHANGELOG 更新
- 记录 V3.0 版本的完整变更历史

#### 17. 数据库备份
```bash
cp sales.db backups/sales_v3.0_$(date +%Y%m%d).db
```

#### 18. 最终验收
- 所有高优先级问题已修复
- 主要业务流程可正常运行
- 文档已更新
- git tag: `v3.0-20260430`

### 17:00 - 18:00 **收尾会议**
- 汇报完成情况
- 列出遗留问题清单
- 制定下一阶段计划

---

## 📊 交付标准

### 必须完成（Day 3 结束前）
- [ ] 所有已知 bug 已修复或记录
- [ ] 主要业务流程（登录→订单→采购→安装→财务）可跑通
- [ ] API 文档与代码一致
- [ ] 代码已 commit + push
- [ ] 数据库已备份

### 延期可接受
- 体验类小问题（如 truck 图标）
- 低优先级功能优化

---

## 🔧 每日工作记录模板

```markdown
## Day X (4月XX日)

### 完成
- 完成了什么

### 发现的新问题
- 问题描述

### 明日计划
- 要做什么
```

---

## 📞 沟通机制

- **微信群**：问题随时抛出来
- **commit message 规范**：`[模块] 修复内容` 或 `[模块] 新增功能`
- **测试结果**：每模块测完立即在群里发结果
- **阻塞**：遇到阻塞立即上报，不要等

---

**启动命令**
```bash
cd /home/tianlj0320/sales-system-dev
git pull origin v3.0-dev
pkill -f uvicorn
JWT_SECRET=fbb765c8b0c0f4dae3a779acf6e92e8847fdc24352cf49db18c86612afcd41b0 ./venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
```
