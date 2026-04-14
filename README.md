# 金典软装销售系统 V2.2 — 本地开发环境

> 面向：金典软装管理团队
> 版本：V2.2（第三阶段完成：手机适配 + 报表升级 + 登录认证 + 首页工作台）
> 日期：2026-04-14

---

## 🚀 快速启动

```bash
cd /home/tianlj0320/sales-system-dev

# 启动服务
./venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

服务地址：`http://localhost:8000`
API 文档：`http://localhost:8000/docs`

---

## 📱 访问页面

| 页面 | 地址 | 说明 |
|------|------|------|
| 管理端 | `http://localhost:8000/static/index.html` | 电脑+手机双端自适应 |
| 客户查进度 | `http://localhost:8000/static/track.html` | 手机扫码查订单进度 |
| 安装工端 | `http://localhost:8000/static/installer.html` | 手机端安装任务操作 |

---

## 🔑 演示账号

| 角色 | 手机号 | 密码 | 说明 |
|------|--------|------|------|
| 老板/管理员 | `13900000001` | `jd8888` | 韩霜 |
| 导购 | `13900001111` | `jd8888` | 小王 |
| 安装工 | `13800001111` | `888888` | 张师傅（验证码） |

> 客户查进度用订单号 `20260411002` + 手机末4位 `3333`

---

## 📊 V2.2 新功能（第三阶段）

### 🆕 手机端适配
- 管理端全响应式布局（手机/平板/桌面自适应）
- 左侧导航 → 手机端抽屉式菜单（☰ 按钮）
- 表格/卡片自动适配小屏

### 📊 报表升级
- 月份选择器（年/月下拉切换）
- 4个标签页：月报总览 / 员工业绩 / 产品排行 / 订单明细
- 支持历史月份查询

### 🔐 登录认证
- 员工登录（手机号+密码）
- JWT Token 认证（72小时有效）
- 顶部右上角显示当前用户

### 🔔 首页工作台
- 今日日期显示
- 警报横幅（逾期订单/库存不足/到期交期）
- KPI 统计卡片

---

## 📁 项目结构

```
sales-system-dev/
├── main.py              # FastAPI 入口
├── requirements.txt     # Python 依赖
├── sales.db            # SQLite 数据库
├── seed_data.py       # 初始化演示数据
├── README.md
├── app/
│   ├── models.py       # 数据模型（12张表）
│   ├── schemas.py      # Pydantic 模型
│   ├── database.py     # 数据库连接
│   └── api/
│       ├── auth.py         # 员工登录认证 (JWT)
│       ├── dashboard.py    # 首页统计
│       ├── orders.py       # 订单管理（CRUD+8态）
│       ├── customers.py    # 客户管理
│       ├── products.py     # 产品/供应商/布版
│       ├── employees.py    # 员工管理
│       ├── purchase.py     # 采购管理
│       ├── warehouse.py    # 仓库管理
│       ├── finance.py      # 财务结算
│       ├── reports.py      # 统计报表
│       ├── track.py        # 客户查进度
│       ├── installer.py    # 安装工 API
│       └── sms.py          # 短信验证码
└── static/
    ├── index.html      # 管理端（V2.2 手机适配+报表升级）
    ├── installer.html  # 安装工手机端
    └── track.html      # 客户查进度
```

---

## 🔌 API 接口（35个）

| 接口 | 方法 | 说明 |
|------|------|------|
| `GET /health` | GET | 健康检查 |
| `POST /api/auth/login` | POST | 员工登录 |
| `GET /api/auth/me` | GET | 当前用户信息 |
| `GET /api/dashboard` | GET | 首页统计数据 |
| `GET /api/orders` | GET | 订单列表（支持筛选+分页+年月）|
| `POST /api/orders` | POST | 新建订单 |
| `PUT /api/orders/{id}` | PUT | 编辑订单 |
| `PUT /api/orders/{id}/status` | PUT | 变更订单状态 |
| `GET /api/orders/{id}` | GET | 订单详情 |
| `GET /api/customers` | GET | 客户列表 |
| `POST /api/customers` | POST | 新建客户 |
| `PUT /api/customers/{id}` | PUT | 编辑客户 |
| `DELETE /api/customers/{id}` | DELETE | 删除客户 |
| `GET /api/products` | GET | 产品列表 |
| `POST /api/products` | POST | 新建产品 |
| `GET /api/products/suppliers` | GET | 供应商列表 |
| `POST /api/products/suppliers` | POST | 新建供应商 |
| `GET /api/products/categories` | GET | 布版分类 |
| `POST /api/products/categories` | POST | 新建布版 |
| `GET /api/employees` | GET | 员工列表 |
| `POST /api/employees` | POST | 新建员工 |
| `PUT /api/employees/{id}` | PUT | 编辑员工 |
| `GET /api/purchase` | GET | 采购列表 |
| `POST /api/purchase` | POST | 新建采购单 |
| `PUT /api/purchase/{id}/status` | PUT | 变更采购状态 |
| `GET /api/warehouse/stock` | GET | 库存查询 |
| `POST /api/warehouse/in` | POST | 采购入库 |
| `POST /api/warehouse/out` | POST | 领料出库 |
| `GET /api/warehouse/records` | GET | 仓库流水 |
| `GET /api/finance/records` | GET | 财务流水 |
| `GET /api/finance/summary` | GET | 财务摘要 |
| `POST /api/finance/receive` | POST | 收款登记 |
| `POST /api/finance/pay` | POST | 付款登记 |
| `POST /api/finance/expense` | POST | 费用登记 |
| `GET /api/reports/sales` | GET | 月度销售报表 |
| `GET /api/reports/trend` | GET | 销售趋势 |
| `GET /api/reports/employee-performance` | GET | 员工业绩 |
| `GET /api/reports/product-rank` | GET | 产品销售排行 |
| `GET /api/track` | GET | 客户扫码查进度 |
| `POST /api/sms/send` | POST | 发送验证码 |
| `POST /api/installer/login` | POST | 安装工登录 |
| `GET /api/installer/tasks` | GET | 安装任务列表 |
| `POST /api/installer/tasks/{id}/complete` | POST | 确认安装完成 |

---

## ⚠️ 注意事项

1. **后端必须先启动**，前端页面才能正常加载数据
2. 手机端访问时，确保手机和电脑在同一局域网（WSL 端口 8000 需映射或手机连同局域网）
3. 演示验证码固定为 `888888`，不需要真实发短信
4. 这是**本地开发环境**，正式上线需要部署到阿里云 ECS
