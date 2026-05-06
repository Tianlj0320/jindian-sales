# 金典软装销售系统 V4.0 — 系统架构

## 1. 整体架构图（文字版）

```
┌──────────────────────────────────────────────────────────────┐
│                        客户端层                               │
│                   (浏览器 / Postman)                         │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                       API 网关层                              │
│                   (FastAPI / Nginx)                          │
│                                                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐             │
│  │认证中间件│ │日志中间件│ │权限中间件│ │异常处理  │             │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘             │
└────────────────────────────┬─────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    路由模块      │ │    服务层        │ │    数据层        │
│   /api/xxx      │ │   CRUD + 业务逻辑 │ │   SQLAlchemy    │
│                 │ │                 │ │   Models        │
└─────────────────┘ └─────────────────┘ └─────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                       数据存储层                              │
│                   (SQLite / PostgreSQL)                      │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 模块关系说明

### 核心模块

| 模块 | 英文名 | 职责 | 依赖模块 |
|------|--------|------|----------|
| 客户管理 | customers | 客户信息建档、跟进记录 | 无 |
| 产品管理 | products | 产品目录、规格、价格 | 无 |
| 销售订单 | orders | 订单创建、状态流转、明细管理 | customers, products |
| 安装管理 | installation | 安装单分配、安装队/安装工管理 | orders |
| 采购管理 | purchase | 采购单、入库联动 | warehouse, products |
| 仓库管理 | warehouse | 多仓库、库存、批次、流转记录 | products |
| 财务管理 | finance | 应收、应付、费用、凭证 | orders, installation, purchase |
| 数据报表 | reports | 经营分析、统计图表 | 全模块 |
| 系统设置 | system | 用户、角色、权限、日志 | 无 |

### 模块依赖图

```
customers ─────┬──▶ orders ─────┬──▶ finance_receivables
               │                 │
               │                 ├──▶ installation_orders ──▶ installers/install_teams
               │                 │
               │                 ├──▶ purchase_orders ──▶ warehouse/inventory
               │                 │
               │                 └──▶ reports（汇总所有模块数据）
               │
               └──▶ followup_records
```

---

## 3. 数据流向

### 订单全流程数据流

```
① 客户建档（customers）
       │
       ▼
② 创建销售订单（orders + order_items）
  - 关联客户
  - 关联产品明细（数量、单价、尺寸）
  - 计算订单总价
       │
       ▼
③ 订单状态流转
  待确认 → 已确认 → 生产中 → 已完成/已取消
       │
       ├──▶ 生产反馈（production_feedback）
       │
       ▼
④ 安装单生成（installation_orders）
  - 关联订单
  - 分配安装队/安装工
  - 记录预约/实际时间
       │
       ▼
⑤ 采购单（如需备料）（purchase_orders + purchase_items）
  - 关联仓库（入库）
       │
       ▼
⑥ 仓库进出库（inventory_flow）
  - 订单用料出库 / 采购入库
       │
       ▼
⑦ 财务结算（finance_receivables / finance_payables）
  - 应收：订单总价
  - 应付：安装费 + 采购成本
       │
       ▼
⑧ 报表分析（reports）
  - 订单统计 / 收入支出 / 库存预警
```

---

## 4. 分层说明

### API 层（路由 + 中间件）

- FastAPI 路由定义在 `app/routers/`
- 中间件：JWT 认证、CORS、日志、异常捕获
- 请求校验：Pydantic 模型

### 服务层（业务逻辑）

- 封装在 `app/services/`
- 每个模块对应一个服务文件（如 `order_service.py`）
- 负责：参数校验、状态机流转、关联操作

### 数据层（ORM + 模型）

- SQLAlchemy 模型定义在 `app/models/`
- 每个表一个模型文件
- 支持迁移： Alembic

---

## 5. 目录结构（规划）

```
sales-system-dev/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置
│   ├── database.py          # 数据库连接
│   ├── models/              # ORM 模型
│   │   ├── __init__.py
│   │   ├── customer.py
│   │   ├── product.py
│   │   ├── order.py
│   │   ├── order_item.py
│   │   ├── installation.py
│   │   ├── purchase.py
│   │   ├── warehouse.py
│   │   ├── finance.py
│   │   └── system.py
│   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── __init__.py
│   │   └── ...
│   ├── routers/             # API 路由
│   │   ├── __init__.py
│   │   ├── customers.py
│   │   ├── orders.py
│   │   └── ...
│   └── services/             # 业务逻辑
│       ├── __init__.py
│       └── ...
├── tests/
├── docs/
│   ├── v3.0/                 # 现有 v3.0 文档（保留不动）
│   └── v4.0/                 # V4.0 文档（本文档所在）
└── requirements.txt
```
