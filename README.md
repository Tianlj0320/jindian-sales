# 金典软装ERP V4.0

> 面向：金典软装管理团队
> 架构：Vue 3 + Element Plus 前端 / FastAPI + SQLAlchemy 后端
> 日期：2026-05-09

---

## 系统架构

```
project/
├── frontend/                # Vue 3 + Element Plus 前端
│   ├── src/
│   │   ├── api/             # Axios API 封装
│   │   ├── router/          # Vue Router 路由
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── utils/           # 工具函数（打印、主题等）
│   │   ├── views/           # 页面组件
│   │   │   ├── layout/      # 主布局（侧边栏+顶栏）
│   │   │   ├── orders/      # 订单管理
│   │   │   ├── products/    # 产品管理
│   │   │   ├── customers/   # 客户管理
│   │   │   ├── purchases/   # 采购管理
│   │   │   ├── warehouse/   # 仓库管理
│   │   │   ├── installation/# 安装管理
│   │   │   ├── production/  # 生产反馈
│   │   │   ├── finance/     # 财务管理
│   │   │   └── system/      # 系统设置
│   │   └── assets/          # 静态资源
│   ├── public/
│   │   └── themes/          # 主题 CSS（7套配色 + 基底样式）
│   └── package.json
│
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/             # API 路由
│   │   │   └── v1/          # API v1 版本
│   │   ├── core/            # 核心配置（异常、响应、安全）
│   │   ├── domain/          # SQLAlchemy 数据模型
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   └── services/        # 业务逻辑（状态机等）
│   ├── migrations/          # 数据库迁移
│   ├── alembic.ini
│   └── requirements.txt
│
├── .gitignore
└── README.md
```

## 功能模块

| 模块 | 功能 |
|------|------|
| 工作台 | KPI 统计、逾期预警、快捷操作 |
| 订单管理 | 订单创建/编辑/详情、状态机推进、异常回滚、采购拆分 |
| 基础资料 | 产品管理、供应商管理、客户管理、员工管理、角色权限、加工类型 |
| 采购管理 | 待采购订单预览、按供应商分组拆分、采购单列表、采购跟踪 |
| 仓库管理 | 库存查询、出入库流水 |
| 安装管理 | 安装队管理、安装派工单、状态跟踪 |
| 生产反馈 | 生产问题记录与跟踪 |
| 财务管理 | 应收/应付、收支登记、费用管理 |
| 系统设置 | 店铺信息、字典管理、操作日志、主题切换 |

## 快速启动

### 后端

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API 文档：`http://localhost:8000/docs`

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问地址：`http://localhost:5173`

### 演示账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |

---

## 开发工具链（Harness）

本系统集成了完整的 4 层开发工具链，覆盖测试、代码规范、Git 提交规范和 CI/CD。

### 第 1 层：后端 — 测试 & 代码规范

```bash
cd backend

# 安装测试依赖
pip install -r requirements-test.txt --break-system-packages

# 运行测试
make test              # pytest + 覆盖率
make test-coverage     # 带详细覆盖率报告
make lint              # Ruff 静态检查
make lint-fix          # Ruff 自动修复
make format            # Ruff 格式化
make format-check      # 检查格式
make check             # lint + format-check + test 一站式检查
```

### 第 2 层：前端 — 测试 & 代码规范

```bash
cd frontend

# 安装依赖（含所有测试/规范工具）
npm install

# 运行测试
make test              # Vitest 单元测试
make test-coverage     # 带覆盖率报告
make test-e2e          # Playwright E2E 测试
make lint              # ESLint 检查
make lint-fix          # ESLint 自动修复
make format            # Prettier 格式化
make format-check      # 检查格式
make check             # lint + format-check + test 一站式检查

# E2E 首次运行需安装浏览器
make e2e-install
```

### 第 3 层：Git 提交规范（Husky + Commitlint）

提交信息格式：`type(scope): subject`

**示例：**
```
feat(orders): 添加异常回滚功能
fix(purchase): 修复 422 分页错误
style(theme): 更新墨绿配色
```

**初始化 Git Hooks（首次运行）：**
```bash
cd frontend
npx husky init
npm install --save-dev @commitlint/cli @commitlint/config-conventional
```

然后将以下内容分别写入 `.husky/pre-commit` 和 `.husky/commit-msg`：

**pre-commit** — 提交前自动 lint 暂存文件：
```bash
npx --no-install lint-staged || { echo '检查失败'; exit 1; }
```

**commit-msg** — 校验提交信息格式：
```bash
npx --no-install commitlint --edit "$1" || { echo '格式错误'; exit 1; }
```

> `lint-staged` 配置已在 `frontend/package.json` 中预设，对 `src/**/*.{vue,js}` 自动执行 ESLint 修复 + Prettier 格式化。

### 第 4 层：CI/CD — GitHub Actions

配置文件：`.github/workflows/ci.yml`

每次推送到 `main/master/develop` 分支或创建 PR 时自动触发：

| Job | 内容 | 并行/串行 |
|-----|------|-----------|
| `backend`   | Ruff lint → format-check → Pyright 类型检查 → pytest + 覆盖率 | 与前端并行 |
| `frontend`  | ESLint → Prettier check → Vitest + 覆盖率 → Vite 构建 | 与后端并行 |
| `e2e`       | Playwright E2E 测试 | 依赖前端构建完成 |

### 一站式检查

```bash
# 后端全部检查
cd backend && make check

# 前端全部检查
cd frontend && make check

# 提交代码（自动触发 pre-commit 检查）
git add .
git commit -m "feat(scope): 本次变更说明"
```

---

## 版本控制

```bash
git init
git add .
git commit -m "V4.0: 金典软装ERP 完整系统"
```
