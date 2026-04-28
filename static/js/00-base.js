/**
 * 金典软装销售系统 · JS 模块化基础
 * 
 * 模块说明：
 *   00-base  → API配置 + localStorage工具 + 全局常量
 *   01-api   → 所有后端 API 调用（基于 fetch）
 *   02-state → 所有 data() 变量清单（文档，注明类型和用途）
 *   03-orders → 销售订单
 *   04-purchase → 采购管理
 *   05-product  → 产品/供应商/布版
 *   06-customer → 客户管理
 *   07-employee → 员工管理
 *   08-home     → 首页仪表盘
 *   09-report   → 统计报表/财务
 *   10-warehouse → 仓库管理
 *   11-install  → 安装管理
 *   12-dict      → 码表管理
 *   13-order-form → 新建订单表单
 *   14-dialogs   → 所有弹窗（open/save/delete）
 *   15-init      → initAll() 初始化
 *   app.js       → Vue 应用挂载
 *
 * ──────────────────────────────────────
 * 所有 API 返回格式参见 docs/API-FORMAT.md
 * 严禁在页面模板中直接写 API 路径，统一用 ${API} 变量
 * ──────────────────────────────────────
 */

// ── API 基础配置 ──────────────────────────────────────────
window.API = '';   // 本地开发：空字符串（相对路径）；部署时改实际域名
window.AUTH_TOKEN_KEY = 'authToken';
window.AUTH_TOKEN = localStorage.getItem(window.AUTH_TOKEN_KEY) || '';

// ── localStorage 工具 ─────────────────────────────────────
window.LS = key => {
  try { return JSON.parse(localStorage.getItem(key)); } catch { return null; }
};
window.SLS = (k, v) => localStorage.setItem(k, JSON.stringify(v));

// ?clear=1 强制清除缓存（URL 参数绕过）
if (new URLSearchParams(location.search).get('clear') === '1') {
  localStorage.clear();
  location.replace(location.pathname);
}

// ── 共享状态容器（模块间通信用）────────────────────────────
// 所有模块把自己的 ref 挂在这里，其他模块可读取
// 注意：用 Vue.reactive 包装成响应式，这样修改属性 Vue 能自动追踪变化
window.__STATE__ = Vue.reactive({
  // ── 核心认证 ──
  authToken: window.AUTH_TOKEN,
  currentUser: window.LS('currentUser') || null,
  isLoggedIn: false,   // initAll 后根据 currentUser 重算
  loginLoading: false,
  loginForm: { phone: '', password: '' },
  showLogin: false,    // 未登录时强制弹登录页
  drawerVisible: false,

  // ── 页面路由 ──
  page: 'home',
  activeMenu: 'home',
  pageTitle: '',

  // ── 首页 ──
  stats: { todayOrders: 0, monthSales: 0, pendingInstall: 0, overdueOrders: 0, pendingPayment: 0, totalCustomers: 0 },
  alerts: [
    { msg: '逾期订单 1 单，请尽快处理', icon: '⚠️', color: '#f56c6c' },
    { msg: '本周到期交期 3 单', icon: '📅', color: '#e6a23c' },
    { msg: '库存不足：婴儿绒雪尼尔 剩 5 米', icon: '📦', color: '#909399' },
  ],

  // ── 供应商 ──
  suppliers: [],
  suppSearch: '',
  suppTypeF: '',

  // ── 布版分类 ──
  categories: [],

  // ── 产品 ──
  products: [],
  prodSearch: '',
  prodSupplierF: '',
  prodCatF: '',

  // ── 客户 ──
  customers: [],
  customerSearch: '',
  customerTypeF: '',

  // ── 员工 ──
  employees: [],
  empSearch: '',
  empPositionF: '',

  // ── 码表 ──
  dictCats: [
    { k: 'orderStatus', l: '订单状态' },
    { k: 'orderType', l: '订单类型' },
    { k: 'deliveryMethod', l: '提货方式' },
    { k: 'supplierType', l: '供应商类型' },
    { k: 'productType', l: '产品分类' },
    { k: 'customerType', l: '客户类型' },
    { k: 'installPosition', l: '安装位置' },
    { k: 'finishType', l: '成品类型' },
    { k: 'style', l: '款式' },
    { k: 'process', l: '工艺' },
    { k: 'paymentType', l: '收款类型' },
    { k: 'orderExpenseType', l: '订单费用类型' },
    { k: 'warehouseType', l: '仓库分类' },
    { k: 'department', l: '部门' },
    { k: 'position', l: '职务' },
  ],
  dictCat: 'orderStatus',
  dictMap: window.LS('dictMap') || {
    orderStatus: [
      { k: 'created', v: '已创建', c: '#909399' },
      { k: 'confirmed', v: '已确认', c: '#409eff' },
      { k: 'split', v: '已拆分', c: '#7c3aed' },
      { k: 'purchasing', v: '采购中', c: '#f59e0b' },
      { k: 'stocked', v: '已到货', c: '#10b981' },
      { k: 'processing', v: '生产中', c: '#f97316' },
      { k: 'production_exception', v: '生产异常', c: '#ef4444' },
      { k: 'install_order_generated', v: '安装单已生成', c: '#8b5cf6' },
      { k: 'shipped', v: '已发货', c: '#06b6d4' },
      { k: 'installed', v: '已安装', c: '#1a3a5c' },
      { k: 'accepted', v: '已验收', c: '#059669' },
      { k: 'completed', v: '已完成', c: '#6366f1' },
      { k: 'cancelled', v: '已取消', c: '#d9d9d9' },
    ],
    orderType: [
      { k: 'curtain', v: '窗帘' },
      { k: 'wallpaper', v: '墙布' },
      { k: 'hardsheet', v: '硬包' },
      { k: 'rockboard', v: '岩板' },
      { k: 'wholehouse', v: '全屋' },
    ],
    deliveryMethod: [
      { k: 'install', v: '上门安装' },
      { k: 'pickup', v: '自提' },
    ],
  },

  // ── 订单 ──
  orders: [],
  filteredOrders: [],
  selOrder: {},            // { id, orderNo, customerName, orderType, salesperson, orderDate, deliveryDate, deliveryMethod, amount, received, debt, roundAmount, status, statusKey, statusColor, statusColorKey, history, items }
  orderSearch: '',
  orderStatusF: '',
  orderTypeF: '',
  showNewOrder: false,

  // ── 采购 ──
  purchases: [],
  filteredPurchase: [],
  purchaseSearch: '',
  purchaseStatusF: '',
  purchaseOrdersForSplit: [],   // 待采购订单列表（勾选生成采购单）
  selectedSplitOrders: [],       // 已选中的订单ID

  // ── 生产 ──
  productionSteps: ['订单接单审核', '用料核定', '报货', '下料汇总', '加工', '完成审核'],
  productionOrders: [],
  filteredProduction: [],
  prodStep: 1,
  prodSearch: '',
  prodStepF: '',

  // ── 安装 ──
  installOrders: [],
  filteredInstall: [],
  installSearch: '',
  installStatusF: '',

  // ── 仓库 ──
  warehouses: [],           // [{ name: '成品库', items: [{ name, stock, unit, recordId }] }]
  warehouseRecords: [],

  // ── 财务 ──
  financeData: { monthRevenue: 0, monthCost: 0, monthProfit: 0, totalDebt: 0, pendingCommission: 0 },
  costBreakdown: [],

  // ── 报表 ──
  salesTrend: [],
  staffRank: [],
  topProducts: [],
  reportOrders: [],
  rptYear: new Date().getFullYear(),
  rptMonth: new Date().getMonth() + 1,
  rptTab: 'overview',

  // ── 新建订单表单 ──
  orderF: {
    customerId: null,
    orderType: '窗帘',
    orderDate: '',
    deliveryDate: '',
    deliveryMethod: '上门安装',
    salespersonId: '',
    items: [],         // [{ productType, location, style, itemName, productId, size, qty, discount, price, amount }]
    materials: [],     // [{ category, productId, model, qty, unit, price, amount }]
    quoteAmount: 0,
    discountAmount: 0,
    roundAmount: 0,
    amount: 0,
    received: 0,
    itemsTotal: 0,
    materialsTotal: 0,
  },

  // ── 订单编辑 ──
  showEditOrder: false,
  editingOrderId: null,
  editOrderF: {},

  // ── 弹窗状态（dialogs）─────────────────────────
  // 供应商
  dlgSupplier: false,
  editingSupplier: null,
  sForm: { type: '', contact: '', phone: '', deliveryDays: 3, address: '', payment: '' },
  // 布版
  dlgCategory: false,
  editingCategory: null,
  cForm: { code: '', name: '', supplierId: '', desc: '' },
  // 产品
  dlgProduct: false,
  editingProduct: null,
  pForm: { code: '', name: '', supplierId: '', categoryId: '', category: '窗帘', classification: '', model: '', material: '', width: 280, weight: 0, cf: 0, price: 0, stock: 0, unit: '米', remark: '' },
  // 客户
  dlgCustomer: false,
  editingCustomer: null,
  cuForm: { name: '', type: '零售', contact: '', phone: '', community: '', address: '', salespersonId: '', source: '', debtLimit: 0, remark: '' },
  // 员工
  dlgEmployee: false,
  editingEmp: null,
  empForm: { name: '', position: '', phone: '', idCard: '', joinDate: '', status: '在职', remark: '' },
  // 码表条目
  dlgDictItem: false,
  editingDictItem: null,
  diForm: { k: '', v: '', c: '#409eff' },
  // 采购单
  dlgPurchase: false,
  editingPurchase: null,
  purchaseForm: { supplierId: '', orderIds: '', expectedDate: '', status: '待采购', remark: '' },
  // 仓库记录
  dlgWarehouseRecord: false,
  warehouseForm: { recordType: 'in', productName: '', quantity: 1, unit: '米', remark: '' },
});
