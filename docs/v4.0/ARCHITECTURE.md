# 金典软装ERP V4.0 — 系统架构

## 1. 整体架构

```
┌──────────────────────────────────────────────────────────────┐
│                        客户端层                               │
│              浏览器 (Vue 3 + Element Plus)                   │
│              Postman / cURL (API 调试)                       │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTP/REST (JSON)
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                      API 服务层 (FastAPI)                     │
│                                                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│  │CORS中间件│ │异常处理  │ │请求日志  │ │JWT认证   │            │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   路由层 (12 个 Router)               │   │
│  │  /api/v1/auth  /api/v1/orders  /api/v1/customers ... │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   服务/业务逻辑                        │   │
│  │  状态引擎  |  采购分单  |  计算引擎  |  库存联动       │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┬─────────────────────────────────┘
                             │ SQLAlchemy 2.0 Async
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                       数据存储层                              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   SQLite (开发)                       │   │
│  │         ~/data/jindian.db (单文件)                    │   │
│  │                   PostgreSQL (生产)                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   文件存储                            │   │
│  │  安装照片  |  产品图片  |  客户签名                   │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 目录结构

```
D:\project\
├── backend/                          # 后端服务
│   ├── main.py                       # FastAPI 入口 + 启动事件 + 种子数据
│   ├── data/                         # SQLite 数据库文件
│   │   └── jindian.db
│   ├── app/
│   │   ├── core/                     # 核心基础设施
│   │   │   ├── config.py            # 应用配置 (Pydantic Settings)
│   │   │   ├── security.py          # JWT 签发/验证 + 密码哈希
│   │   │   ├── response.py          # 统一响应格式 (success/error/paginated)
│   │   │   ├── exceptions.py        # 自定义异常类
│   │   │   ├── middleware.py        # CORS + 异常处理 + 请求日志
│   │   │   └── logging.py           # 日志配置
│   │   ├── domain/                   # SQLAlchemy ORM 模型 (28 表)
│   │   │   ├── base.py              # Base + TimestampMixin + SoftDeleteMixin
│   │   │   ├── auth.py              # User
│   │   │   ├── customer.py          # Customer + FollowupRecord
│   │   │   ├── product.py           # Product + ProductCategory + Supplier
│   │   │   ├── order.py             # Order + OrderItem
│   │   │   ├── purchase.py          # PurchaseOrder + PurchaseOrderItem
│   │   │   ├── warehouse.py         # Warehouse + Inventory + InventoryFlow
│   │   │   ├── installation.py      # InstallTeam + Installer + InstallTeamMember + InstallationOrder
│   │   │   ├── finance.py           # FinanceReceivable + FinancePayable + FinanceExpense
│   │   │   ├── production.py        # ProductionFeedback
│   │   │   ├── system.py            # StoreConfig + DictType + DictItem
│   │   │   ├── role.py              # Role
│   │   │   ├── processing.py        # ProcessingType + ProcessingMaterialRule
│   │   │   ├── log.py               # OperationalLog
│   │   │   ├── base.py              # 基类
│   │   │   └── __init__.py          # 全量导出
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── auth.py          # 认证 + 用户管理
│   │   │   │   ├── orders.py        # 订单管理 (含状态机、采购分单)
│   │   │   │   ├── customers.py     # 客户管理
│   │   │   │   ├── products.py      # 产品管理 (含分类、供应商)
│   │   │   │   ├── purchases.py     # 采购管理
│   │   │   │   ├── warehouses.py    # 仓库管理
│   │   │   │   ├── installations.py # 安装管理
│   │   │   │   ├── finance.py       # 财务管理
│   │   │   │   ├── production.py    # 生产反馈
│   │   │   │   ├── dashboard.py     # 仪表盘
│   │   │   │   ├── system.py        # 系统设置 (字典、日志、店铺)
│   │   │   │   ├── roles.py         # 角色权限
│   │   │   │   └── processing.py    # 加工类型
│   │   │   └── deps.py              # 公共依赖 (SessionDep, CurrentUserDep, PageDep)
│   │   ├── services/
│   │   │   └── status_engine.py     # 订单状态机引擎
│   │   └── database.py              # 异步数据库引擎与会话工厂
│   └── requirements.txt
│
├── frontend/                         # 前端 Vue 3 应用
│   ├── src/
│   │   ├── App.vue                  # 根组件
│   │   ├── main.js                  # 入口
│   │   ├── api/
│   │   │   └── index.js             # Axios 封装 + 全量 API 方法
│   │   ├── stores/
│   │   │   └── auth.js              # Pinia 认证状态管理
│   │   ├── router/
│   │   │   └── index.js             # Vue Router 配置
│   │   ├── views/
│   │   │   ├── Login.vue            # 登录页
│   │   │   ├── Dashboard.vue        # 工作台
│   │   │   ├── layout/
│   │   │   │   └── MainLayout.vue   # 主布局 (侧边栏 + 顶部导航)
│   │   │   ├── orders/
│   │   │   │   ├── OrderList.vue    # 订单列表
│   │   │   │   ├── OrderForm.vue    # 订单创建/编辑
│   │   │   │   └── OrderDetail.vue  # 订单详情
│   │   │   ├── customers/
│   │   │   │   ├── CustomerList.vue # 客户列表
│   │   │   │   └── CustomerDetail.vue # 客户详情
│   │   │   ├── products/
│   │   │   │   ├── ProductList.vue  # 产品列表
│   │   │   │   └── SupplierList.vue # 供应商列表
│   │   │   ├── purchases/
│   │   │   │   └── PurchaseList.vue # 采购列表
│   │   │   ├── warehouse/
│   │   │   │   └── InventoryView.vue # 库存/流水
│   │   │   ├── installation/
│   │   │   │   └── InstallationView.vue # 安装管理
│   │   │   ├── production/
│   │   │   │   └── ProductionFeedback.vue # 生产反馈
│   │   │   ├── finance/
│   │   │   │   └── FinanceView.vue  # 财务总览
│   │   │   ├── processing/
│   │   │   │   └── ProcessingTypeList.vue # 加工类型
│   │   │   └── system/
│   │   │       ├── StaffList.vue    # 员工管理
│   │   │       ├── RoleList.vue     # 角色权限
│   │   │       ├── StoreInfoForm.vue # 店铺信息
│   │   │       ├── DictList.vue     # 字典管理
│   │   │       └── OperationLog.vue # 操作日志
│   │   └── styles/
│   └── dist/                         # 构建产物
│
├── docs/                             # 项目文档
│   ├── v4.0/                        # V4.0 文档
│   │   ├── OVERVIEW.md              # 系统概述
│   │   ├── ARCHITECTURE.md          # 系统架构 (本文档)
│   │   ├── DATABASE.md              # 数据库设计
│   │   ├── API_DESIGN.md            # 接口设计
│   │   ├── FRONTEND.md              # 前端说明
│   │   └── DEPLOY.md                # 部署指南
│   └── v3.0/                        # (V3 遗留文档)
│
└── README.md
```

---

## 3. 核心设计模式

### 3.1 响应格式统一

所有 API 响应使用三个标准函数：

```python
# 成功响应（带数据）
{"success": true, "data": {...}, "message": null}

# 成功响应（分页）
{"success": true, "total": 100, "page": 1, "page_size": 20, "items": [...]}

# 错误响应
{"success": false, "error": "错误描述", "message": "ERROR_CODE"}
```

### 3.2 状态机模式

订单采用状态机驱动，定义在 `app/services/status_engine.py`：

- **11 个状态**：initial → measured → confirmed → split → purchasing → stocked → processing → completed → install_scheduled → installed → accepted
- **状态配置**：每个状态定义可流转的下一个状态列表、标签、颜色
- **回滚支持**：可回退到任意前置状态（admin/manager 权限）
- **自动联动**：状态到达某些节点时自动触发操作（如 completed 自动创建安装单）

### 3.3 依赖注入

FastAPI 依赖注入系统提供三个公共依赖：

```python
SessionDep    # AsyncSession 数据库会话
CurrentUserDep # User 当前登录用户
PageDep       # PageParams 分页参数 (page, page_size)
```

### 3.4 热拷贝模式

为了减少 JOIN 查询，关键关联表的数据以冗余字段形式拷贝到子表：

- Order 中存储 `customer_name`、`customer_phone`
- PurchaseOrder 中存储 `supplier_name`、`contact`、`phone`、银行信息
- InstallationOrder 中存储 `customer_name`、`customer_phone`

### 3.5 字典系统

通用字典系统支持运行时动态配置：

- **DictType**：定义字典类型（如订单类型、客户来源）
- **DictItem**：定义字典项（类型下的具体选项）
- 接口：`/api/v1/system/dict/{dict_type}` 获取指定类型的所有项
- 配置型数据（如店铺信息）也通过字典管理

---

## 4. 模块关系图

```
┌──────────────┐
│   认证模块    │ ← JWT Token
│   Auth       │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌────────────────┐
│   客户管理    │────▶│   订单管理      │
│   Customers  │     │   Orders       │
└──────────────┘     └───┬───┬───┬────┘
                         │   │   │
          ┌──────────────┘   │   └──────────────┐
          ▼                  ▼                  ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │   采购管理    │   │   生产反馈    │   │   安装管理    │
   │   Purchases  │   │  Production  │   │ Installations│
   └──────┬───────┘   └──────────────┘   └──────┬───────┘
          │                                     │
          ▼                                     ▼
   ┌──────────────┐                     ┌──────────────┐
   │   仓库管理    │                     │   财务管理    │
   │  Warehouse   │                     │   Finance    │
   └──────────────┘                     └──────────────┘

   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │   角色权限    │   │   产品管理    │   │   系统设置    │
   │    Roles     │   │   Products   │   │    System    │
   └──────────────┘   └──────────────┘   └──────────────┘
```

---

## 5. 数据流向

### 5.1 订单主流程

```
客户建档 → 创建订单 → 量尺确认 → 采购分单 → 采购入库
    → 加工完成 → 排安装 → 安装完成 → 验收结款
```

### 5.2 财务联动

```
订单确认 → 自动生成应收款记录
采购入库 → 自动生成应付款记录
收款确认 → 更新订单已收/欠款金额 + 更新应收款状态
付款确认 → 更新采购单已付/欠款金额 + 更新应付款状态
```

### 5.3 库存联动

```
采购入库 → 增加库存量 → 写入库存流水 (purchase_in)
订单出库 → 减少库存量 → 写入库存流水 (sale_out)
```

---

## 6. 异常处理体系

| 异常 | HTTP 状态码 | 说明 |
|------|-------------|------|
| NotFoundError | 404 | 资源不存在 |
| UnauthorizedError | 401 | 未登录/Token 失效 |
| ForbiddenError | 403 | 无权限 |
| BusinessError | 400 | 业务逻辑错误 |
| ConflictError | 409 | 数据冲突 |
| ValidationError | 422 | 参数校验失败 |
| AppException | 500 | 通用应用异常 |
