# V3.0 系统性问题修复 - 开发任务

## 已知问题模式

### 1. Vue ref 访问路径错误 ⚠️ 已修复登录模块
**模式**：`moduleForm.value.xxx` 应改为 `moduleForm.xxx`（因为 setup 返回时 Vue 自动解包 ref）
**影响范围**：所有模块的 dialog/form 操作

### 2. 字段名不一致（后端 snake_case vs 前端 camelCase）⚠️ 部分修复
**模式**：`delivery_days` vs `deliveryDays`、`payment` 字段丢失
**影响**：供应商管理（已修复）、其他模块待查

### 3. API 响应格式不一致
**模式**：
- 有的返回 `{success: true, data: {...}}`
- 有的直接返回 `{...}`
- api.js 对 `d.success === undefined` 做了兼容

## 开发任务清单

### Phase 1: 全面排查并修复字段名问题

请逐个检查以下文件，修复所有 `snake_case` vs `camelCase` 不一致：

| 模块 | 前端文件 | 后端API | 检查重点 |
|------|---------|---------|---------|
| 供应商 | 14-dialogs.js | products.py | delivery_days/payment/address |
| 产品资料 | 05-product.js, 13-order-form.js | products.py | 所有产品字段 |
| 客户资料 | 06-customer.js | customers.py | 所有客户字段 |
| 员工资料 | 07-employee.js | employees.py | 所有员工字段 |
| 码表管理 | 12-dict.js | dicts.py | type/value 结构 |
| 订单管理 | 03-orders.js, 13-order-form.js | orders.py | 所有订单字段 |
| 采购管理 | 04-purchase.js | purchase.py, purchase_orders.py | 采购相关字段 |
| 仓库管理 | 10-warehouse.js | warehouse.py | 入库/出库字段 |
| 安装管理 | 11-install.js | installation_orders.py | 安装单字段 |
| 财务结算 | 09-report.js | finance.py | 收付款字段 |
| 统计报表 | 09-report.js | reports.py | 报表字段 |

### Phase 2: 检查 dialog/form 操作的 ref 访问问题

所有 dialog 保存函数，检查：
1. 读取表单值：`form.xxx` 而非 `form.value.xxx`
2. 提交到 API 的字段名与 API 文档一致
3. 保存成功后正确更新列表

### Phase 3: 确保 API 文档与实现一致

检查 `docs/V3.0_API文档.md` 是否与实际 API 返回值匹配。

## 修复标准

1. 所有 dialog 打开/关闭正常
2. 所有列表加载正常
3. 所有新增/编辑/删除操作正常
4. 无 Vue warning（控制台无 prop type 错误）
5. 无 JS 报错

## 执行要求

1. 每次修复后提交，commit message 清晰说明修复了什么
2. 确保 git push
3. 如遇不确定的问题，先在群里问
