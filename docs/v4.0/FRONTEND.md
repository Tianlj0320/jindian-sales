# 金典软装ERP V4.0 — 前端说明

> 框架：Vue 3 (Composition API) + Vite
> UI 组件库：Element Plus
> 路由：Vue Router 4 (Hash History)
> 状态管理：Pinia
> HTTP 客户端：Axios

---

## 1. 路由结构

基础路径使用 Hash 模式：`/#/...`

### 路由表

| 路径 | 页面 | 说明 |
|------|------|------|
| /login | 登录页 | 公开页面，无需认证 |
| /dashboard | 工作台 | 仪表盘 |
| /orders | 订单列表 | 订单管理主页 |
| /orders/new | 新建订单 | 订单创建表单 |
| /orders/:id | 订单详情 | 查看订单完整信息 |
| /orders/:id/edit | 编辑订单 | 修改订单（仅初始状态） |
| /products | 产品列表 | 产品管理 |
| /customers | 客户列表 | 客户管理 |
| /customers/:id | 客户详情 | 查看客户信息+跟进记录 |
| /suppliers | 供应商列表 | 供应商管理 |
| /staff | 员工管理 | 系统用户管理 |
| /roles | 角色权限 | 角色 CRUD |
| /processing-types | 加工类型 | 加工类型+辅料规则 |
| /purchases | 采购管理 | 采购单列表+详情 |
| /warehouse | 仓库管理 | 库存查询+流水 |
| /installations | 安装管理 | 安装单+安装队+安装工 |
| /production | 生产反馈 | 品质问题反馈 |
| /finance | 财务管理 | 应收/应付/费用 |
| /store-settings | 店铺信息 | 店铺配置表单 |
| /dicts | 字典管理 | 字典类型+项 CRUD |
| /logs | 操作日志 | 操作日志查询 |
| /* | → 重定向至 /dashboard | 通配路由 |

### 路由守卫

在 `router/index.js` 中定义全局 `beforeEach` 导航守卫：

- 访问公开路由（`meta.public = true`）直接放行
- 其他路由检查 `useAuthStore().isLoggedIn`
- 未登录统一重定向至 `/login`

---

## 2. 菜单结构

侧边栏菜单定义在 `MainLayout.vue` 中，使用 Element Plus `<el-menu>`，采用深色主题。

```
金典软装ERP
├── 🏠 工作台         → /dashboard
├── 📄 订单管理       → /orders
├── ▸ 基础资料
│   ├── 📦 产品管理   → /products
│   ├── 👤 客户管理   → /customers
│   ├── 🚚 供应商管理 → /suppliers
│   ├── 👥 员工管理   → /staff
│   ├── 🔑 角色权限   → /roles
│   └── ⚙️ 加工类型   → /processing-types
├── 🛒 采购管理       → /purchases
├── 🏪 仓库管理       → /warehouse
├── 🔧 安装管理       → /installations
├── ⚠️ 生产反馈       → /production
├── 💰 财务管理       → /finance
└── ▸ 系统设置
    ├── 🏬 店铺信息   → /store-settings
    ├── 📋 字典管理   → /dicts
    └── 🎫 操作日志   → /logs
```

---

## 3. 页面功能说明

### 3.1 登录页 (Login.vue)
- 用户名+密码登录
- 调用 `POST /api/v1/auth/login`
- 成功后存储 Token 到 Pinia store 和 localStorage
- 跳转至 Dashboard

### 3.2 工作台 (Dashboard.vue)
- 今日订单数、月度销售额、待办安装数
- 逾期应收款、低库存预警、待处理采购
- 月度销售报表（柱状图/折线图）
- 产品销售排行（Top 10）

### 3.3 订单管理 (OrderList.vue / OrderForm.vue / OrderDetail.vue)

**订单列表：**
- 多条件筛选：关键字、状态、年份/月份、业务员
- 分页表格展示
- 点击行进入详情

**订单表单：**
- 客户选择（带搜索自动补全）
- 明细行管理（增删改行）
- 自动计算：面料用量 = (窗宽 × 褶皱系数) × 数量
- 报价/折扣/抹零/实收联动计算
- 支持多类型订单（窗帘/墙布/硬包等）

**订单详情：**
- 基本信息 + 明细表格
- 状态流转操作（推进/跳转/回滚）
- 关联采购单、安装单、财务信息
- 状态变更历史时间线

### 3.4 客户管理 (CustomerList.vue / CustomerDetail.vue)
- 客户列表（搜索+分页）
- 客户详情（信息+跟进记录）
- 跟进记录展示

### 3.5 产品管理 (ProductList.vue)
- 产品列表（分类筛选+搜索）
- 产品分类树
- 产品创建/编辑弹窗

### 3.6 供应商管理 (SupplierList.vue)
- 供应商列表（搜索+分页）
- 供应商创建/编辑弹窗
- 付款信息字段（银行账号/开户行/收款人）

### 3.7 采购管理 (PurchaseList.vue)
- 采购单列表（按年份/月份/状态筛选）
- 采购单详情（明细+入库操作）
- 采购入库确认弹窗

### 3.8 仓库管理 (InventoryView.vue)
- 库存查询（搜索+低库存筛选）
- 库存流水追溯

### 3.9 安装管理 (InstallationView.vue)
- 安装队管理（创建/编辑）
- 安装工管理（创建/编辑）
- 安装单列表（筛选+分页）
- 安装单详情（状态更新）

### 3.10 生产反馈 (ProductionFeedback.vue)
- 反馈列表（按状态/类型筛选）
- 反馈处理（处理人+处理结果）

### 3.11 财务管理 (FinanceView.vue)
- 应收款列表 + 收款确认
- 应付款列表 + 付款确认
- 费用记录 + 月度费用汇总
- 经营概况总览

### 3.12 加工类型 (ProcessingTypeList.vue)
- 加工类型 CRUD
- 辅料规则管理（增删改辅料）

### 3.13 系统设置

**员工管理 (StaffList.vue)：** 用户 CRUD
**角色权限 (RoleList.vue)：** 角色 CRUD + 权限配置
**店铺信息 (StoreInfoForm.vue)：** 店铺配置表单 + 全部配置项表格 CRUD
**字典管理 (DictList.vue)：** 字典类型（左侧列表）+ 字典项（右侧表格）CRUD
**操作日志 (OperationLog.vue)：** 分页查询操作日志

---

## 4. API 请求封装

所有 API 调用通过 `frontend/src/api/index.js` 中的 Axios 实例封装：

```javascript
import axios from 'axios'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 30000,
})

// 请求拦截器：自动注入 Token
http.interceptors.request.use(config => {
  const token = useAuthStore().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截器：统一错误处理
http.interceptors.response.use(
  res => res.data,
  err => {
    // Token 过期 → 跳转登录
    // 业务错误 → 显示 ElMessage
  }
)
```

---

## 5. 状态管理

使用 Pinia 管理认证状态：

```javascript
// stores/auth.js
export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
  },
  actions: {
    setToken(token) { ... },
    setUser(user) { ... },
    logout() { ... },
  },
})
```

---

## 6. 构建与运行

```bash
# 安装依赖
cd frontend
npm install

# 开发模式（热重载）
npm run dev

# 生产构建
npm run build

# 构建产物输出至 dist/
# 后端自动挂载 dist/ 目录作为静态文件服务
```
