# V3.0 系统性问题修复 - 文档任务

## 文档更新要求

开发每修复一个模块，文档同步更新 API 字段说明。

## 当前文档状况

docs/V3.0_API文档.md 可能与实际 API 不一致，需要核对更新。

## 任务清单

### 1. 核对并更新 API 文档

逐个 API 核对实际返回值，更新 docs/V3.0_API文档.md：

| API 路径 | 说明 |
|---------|------|
| POST /api/auth/login | 已核对 ✅ |
| GET /api/dashboard | 待核对 |
| GET /api/orders | 待核对 |
| POST /api/orders | 待核对 |
| GET /api/products/suppliers | 已核对（payment/address 字段已补）✅ |
| POST /api/products/suppliers | 待核对 |
| PUT /api/products/suppliers/:id | 待核对 |
| GET /api/products | 待核对 |
| POST /api/products | 待核对 |
| GET /api/customers | 待核对 |
| POST /api/customers | 待核对 |
| GET /api/employees | 待核对 |
| POST /api/employees | 待核对 |
| GET /api/dicts | 待核对 |
| POST /api/dicts | 待核对 |
| GET /api/purchase | 待核对 |
| POST /api/purchase | 待核对 |
| GET /api/warehouse | 待核对 |
| POST /api/warehouse/in | 待核对 |
| POST /api/warehouse/out | 待核对 |
| GET /api/finance | 待核对 |
| POST /api/finance | 待核对 |
| GET /api/reports | 待核对 |

### 2. 更新 BUG-MEMO.md

将本次修复过程中发现的所有问题及根因记录到 docs/BUG-MEMO.md，包括：
- 问题描述
- 根因分析
- 修复方案
- 预防措施

### 3. 更新 CHANGELOG.md

记录 V3.0 的版本历史和修复内容。

## 执行要求

1. 每更新一个 API 文档，在群里通知
2. 保持文档格式一致
3. 字段说明要包含类型和说明
