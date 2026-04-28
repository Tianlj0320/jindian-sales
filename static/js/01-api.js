/**
 * 金典软装销售系统 · API 调用层
 * 
 * 所有后端接口统一入口。
 * 规则：
 *   1. 所有路径使用 ${API} 前缀（相对路径）—— 对应 docs/API-FORMAT.md
 *   2. 统一错误处理：失败 throw Error(msg)
 *   3. 响应格式统一：返回 data 字段，详见 docs/API-FORMAT.md
 */

const api = async (u, m = 'GET', b = null) => {
  const headers = { 'Content-Type': 'application/json' };
  // 优先从 cookie 读 token（后端 HttpOnly cookie），fallback 到 localStorage
  let _tok = localStorage.getItem('authToken') || '';
  if (!_tok) {
    // 兼容两种 cookie 格式：authToken=xxx 或直接存 token 值
    const cookieStr = document.cookie;
    if (cookieStr.startsWith('eyJ')) {
      _tok = cookieStr;  // cookie 直接是 token 值
    } else {
      const cookies = Object.fromEntries(
        cookieStr.split('; ').map(c => {
          const eqIdx = c.indexOf('=');
          return eqIdx >= 0 ? [c.slice(0, eqIdx), c.slice(eqIdx+1)] : [c, ''];
        })
      );
      _tok = cookies.authToken || cookies.token || '';
    }
  }
  if (_tok) headers['Authorization'] = 'Bearer ' + _tok;
  const r = await fetch(API + u, { method: m, headers, body: b ? JSON.stringify(b) : null });
  if (!r.ok) throw new Error(u + ' → HTTP ' + r.status);
  const d = await r.json();
  // 兼容直接返回数据（无 success 包装）的格式，如 /api/dicts
  if (d.success === undefined) return d;  // 直接返回
  if (!d.success) throw new Error(d.error || 'API 错误');
  return d.data ?? d;
};

// ── 认证 ────────────────────────────────────────────────
window.apiAuth = {
  login: (phone, password) =>
    api('/api/auth/login', 'POST', { phone, password }),
};

// ── 首页仪表盘 ────────────────────────────────────────────
window.apiDashboard = {
  getSummary: () => api('/api/dashboard'),
};

// ── 订单 ──────────────────────────────────────────────────
window.apiOrders = {
  list: (params = {}) => {
    // params: page, page_size, status_key, year, month
    const q = new URLSearchParams(params).toString();
    return api('/api/orders' + (q ? '?' + q : ''));
  },
  create: (payload) => api('/api/orders', 'POST', payload),
  update: (id, payload) => api(`/api/orders/${id}`, 'PUT', payload),
  updateStatus: (id, new_status_key) =>
    api(`/api/orders/${id}/status`, 'PUT', { new_status_key }),
  delete: (id) => api(`/api/orders/${id}`, 'DELETE'),
};

// ── 采购 ──────────────────────────────────────────────────
window.apiPurchase = {
  list: () => api('/api/purchase-orders'),
  create: (payload) => api('/api/purchase-orders', 'POST', payload),
  updateStatus: (id, status) =>
    api(`/api/purchase-orders/${id}`, 'PATCH', { status }),
  delete: (id) => api(`/api/purchase-orders/${id}`, 'DELETE'),
  batchSplit: (orderIds) =>
    api('/api/purchase-orders/batch-split', 'POST', orderIds),
};

// ── 产品 ──────────────────────────────────────────────────
window.apiProducts = {
  suppliers: () => api('/api/products/suppliers'),
  createSupplier: (payload) =>
    api('/api/products/suppliers', 'POST', payload),
  updateSupplier: (id, payload) =>
    api(`/api/products/suppliers/${id}`, 'PUT', payload),
  deleteSupplier: (id) => api(`/api/products/suppliers/${id}`, 'DELETE'),

  categories: () => api('/api/products/categories'),
  createCategory: (payload) =>
    api('/api/products/categories', 'POST', payload),
  updateCategory: (id, payload) =>
    api(`/api/products/categories/${id}`, 'PUT', payload),

  list: () => api('/api/products'),
  create: (payload) => api('/api/products', 'POST', payload),
  update: (id, payload) => api(`/api/products/${id}`, 'PUT', payload),
  delete: (id) => api(`/api/products/${id}`, 'DELETE'),
};

// ── 客户 ──────────────────────────────────────────────────
window.apiCustomers = {
  list: () => api('/api/customers'),
  create: (payload) => api('/api/customers', 'POST', payload),
  update: (id, payload) => api(`/api/customers/${id}`, 'PUT', payload),
  delete: (id) => api(`/api/customers/${id}`, 'DELETE'),
};

// ── 员工 ──────────────────────────────────────────────────
window.apiEmployees = {
  list: () => api('/api/employees'),
  create: (payload) => api('/api/employees', 'POST', payload),
  update: (id, payload) => api(`/api/employees/${id}`, 'PUT', payload),
};

// ── 仓库 ──────────────────────────────────────────────────
window.apiWarehouse = {
  records: () => api('/api/warehouse/records'),
  createRecord: (payload) =>
    api('/api/warehouse/records', 'POST', payload),
  deleteRecord: (id) => api(`/api/warehouse/records/${id}`, 'DELETE'),
};

// ── 安装 ──────────────────────────────────────────────────
window.apiInstall = {
  list: () => api('/api/installation-orders'),
  listInstallers: () => api('/api/installer/list'),
  complete: (taskId, payload) =>
    api(`/api/installer/tasks/${taskId}/complete`, 'POST', payload),
};

// ── 财务 ──────────────────────────────────────────────────
window.apiFinance = {
  summary: () => api('/api/finance/summary'),
  receive: (payload) => api('/api/finance/receive', 'POST', payload),
  pay: (payload) => api('/api/finance/pay', 'POST', payload),
  expense: (payload) => api('/api/finance/expense', 'POST', payload),
};

// ── 报表 ──────────────────────────────────────────────────
window.apiReports = {
  trend: (year, month) =>
    api(`/api/reports/trend?year=${year}&month=${month}`),
  employeePerformance: (year, month) =>
    api(`/api/reports/employee-performance?year=${year}&month=${month}`),
  productRank: (year, month) =>
    api(`/api/reports/product-rank?year=${year}&month=${month}`),
};

// ── 码表 ──────────────────────────────────────────────────
window.apiDicts = {
  list: () => api('/api/dicts'),
};

// ── 生产反馈 ───────────────────────────────────────────────
window.apiProductionFeedback = {
  list: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return api('/api/production-feedback' + (q ? '?' + q : ''));
  },
  create: (payload) => api('/api/production-feedback', 'POST', payload),
  get: (id) => api(`/api/production-feedback/${id}`),
  update: (id, payload) => api(`/api/production-feedback/${id}`, 'PATCH', payload),
};
