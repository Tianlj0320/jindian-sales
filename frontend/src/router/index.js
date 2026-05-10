import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/views/layout/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      // ── 工作台 ──
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '工作台' } },

      // ── 订单管理 ──
      { path: 'orders', name: 'Orders', component: () => import('@/views/orders/OrderList.vue'), meta: { title: '订单管理' } },
      { path: 'orders/new', name: 'OrderNew', component: () => import('@/views/orders/OrderForm.vue'), meta: { title: '新建订单' } },
      { path: 'orders/:id', name: 'OrderDetail', component: () => import('@/views/orders/OrderDetail.vue'), meta: { title: '订单详情' } },
      { path: 'orders/:id/edit', name: 'OrderEdit', component: () => import('@/views/orders/OrderForm.vue'), meta: { title: '编辑订单' } },

      // ── 基础资料 ──
      { path: 'products', name: 'Products', component: () => import('@/views/products/ProductList.vue'), meta: { title: '产品管理', module: 'basic' } },
      { path: 'customers', name: 'Customers', component: () => import('@/views/customers/CustomerList.vue'), meta: { title: '客户管理', module: 'basic' } },
      { path: 'customers/:id', name: 'CustomerDetail', component: () => import('@/views/customers/CustomerDetail.vue'), meta: { title: '客户详情', module: 'basic' } },
      { path: 'suppliers', name: 'Suppliers', component: () => import('@/views/products/SupplierList.vue'), meta: { title: '供应商管理', module: 'basic' } },
      { path: 'staff', name: 'Staff', component: () => import('@/views/system/StaffList.vue'), meta: { title: '员工管理', module: 'basic' } },
      { path: 'roles', name: 'Roles', component: () => import('@/views/system/RoleList.vue'), meta: { title: '角色权限', module: 'basic' } },
      { path: 'processing-types', name: 'ProcessingTypes', component: () => import('@/views/processing/ProcessingTypeList.vue'), meta: { title: '加工类型', module: 'basic' } },

      // ── 采购/仓库 ──
      { path: 'purchases', name: 'Purchases', component: () => import('@/views/purchases/PurchaseList.vue'), meta: { title: '采购管理' } },
      { path: 'warehouse', name: 'Warehouse', component: () => import('@/views/warehouse/InventoryView.vue'), meta: { title: '仓库管理' } },

      // ── 安装/生产 ──
      { path: 'installations', name: 'Installations', component: () => import('@/views/installation/InstallationView.vue'), meta: { title: '安装管理' } },
      { path: 'production', name: 'Production', component: () => import('@/views/production/ProductionFeedback.vue'), meta: { title: '生产反馈' } },

      // ── 财务 ──
      { path: 'finance', name: 'Finance', component: () => import('@/views/finance/FinanceView.vue'), meta: { title: '财务管理' } },

      // ── 系统设置 ──
      { path: 'store-settings', name: 'StoreSettings', component: () => import('@/views/system/StoreInfoForm.vue'), meta: { title: '店铺信息', module: 'system' } },
      { path: 'dicts', name: 'Dicts', component: () => import('@/views/system/DictList.vue'), meta: { title: '字典管理', module: 'system' } },
      { path: 'logs', name: 'Logs', component: () => import('@/views/system/OperationLog.vue'), meta: { title: '操作日志', module: 'system' } },
      { path: 'theme-settings', name: 'ThemeSettings', component: () => import('@/views/system/ThemeSettings.vue'), meta: { title: '主题切换', module: 'system' } },

      // ── 通配路由（未匹配到的路径自动跳转工作台）──
      { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router
