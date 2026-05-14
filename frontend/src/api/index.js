import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// 请求拦截 - 添加 token
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截 - 统一错误处理
http.interceptors.response.use(
  (response) => {
    const data = response.data
    if (data.success === false) {
      ElMessage.error(data.error || '请求失败')
      return Promise.reject(new Error(data.error))
    }
    return data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/#/login'
        ElMessage.error('登录已过期，请重新登录')
      } else if (status === 403) {
        ElMessage.error('权限不足')
      } else if (status === 404) {
        ElMessage.error('资源不存在')
      } else {
        ElMessage.error(data?.error || `请求失败(${status})`)
      }
    } else {
      ElMessage.error('网络连接失败')
    }
    return Promise.reject(error)
  }
)

// ── API 方法 ──────────────────────────────────────────────────

export const authApi = {
  login: (data) => http.post('/auth/login', data),
  me: () => http.get('/auth/me'),
  permissions: () => http.get('/auth/permissions'),
  listUsers: () => http.get('/auth/users'),
  createUser: (data) => http.post('/auth/users', data),
  updateUser: (id, data) => http.put(`/auth/users/${id}`, data),
  deleteUser: (id) => http.delete(`/auth/users/${id}`),
}

export const customerApi = {
  list: (params) => http.get('/customers', { params }),
  search: (keyword) => http.get(`/customers/search?keyword=${encodeURIComponent(keyword)}`),
  get: (id) => http.get(`/customers/${id}`),
  create: (data) => http.post('/customers', data),
  update: (id, data) => http.put(`/customers/${id}`, data),
  delete: (id) => http.delete(`/customers/${id}`),
  followups: (id) => http.get(`/customers/${id}/followups`),
  createFollowup: (id, data) => http.post(`/customers/${id}/followups`, data),
  updateFollowup: (customerId, recordId, data) => http.put(`/customers/${customerId}/followups/${recordId}`, data),
}

export const productApi = {
  list: (params) => http.get('/products', { params }),
  get: (id) => http.get(`/products/${id}`),
  create: (data) => http.post('/products', data),
  update: (id, data) => http.put(`/products/${id}`, data),
  search: (keyword) => http.get(`/products/search?keyword=${encodeURIComponent(keyword)}`),
  categories: () => http.get('/products/categories'),
  createCategory: (data) => http.post('/products/categories', data),
  updateCategory: (id, data) => http.put(`/products/categories/${id}`, data),
  deleteCategory: (id) => http.delete(`/products/categories/${id}`),
  listSuppliers: (params) => http.get('/products/suppliers', { params }),
  listAllSuppliers: () => http.get('/products/suppliers/all'),
  createSupplier: (data) => http.post('/products/suppliers', data),
  updateSupplier: (id, data) => http.put(`/products/suppliers/${id}`, data),
  deleteSupplier: (id) => http.delete(`/products/suppliers/${id}`),
  listSeries: (params) => http.get('/products/series', { params }),
  createSeries: (data) => http.post('/products/series', data),
  updateSeries: (id, data) => http.put(`/products/series/${id}`, data),
  deleteSeries: (id) => http.delete(`/products/series/${id}`),
}

export const processingApi = {
  listTypes: () => http.get('/processing/types'),
  getType: (id) => http.get(`/processing/types/${id}`),
  createType: (data) => http.post('/processing/types', data),
  updateType: (id, data) => http.put(`/processing/types/${id}`, data),
  deleteType: (id) => http.delete(`/processing/types/${id}`),
}

export const orderApi = {
  list: (params) => http.get('/orders', { params }),
  get: (id) => http.get(`/orders/${id}`),
  create: (data) => http.post('/orders', data),
  update: (id, data) => http.put(`/orders/${id}`, data),
  delete: (id) => http.delete(`/orders/${id}`),
  advance: (id) => http.post(`/orders/${id}/advance`),
  split: (id) => http.post(`/orders/${id}/split`),
  splitPreview: () => http.get('/orders/split-preview'),
  confirmSplit: () => http.post('/orders/confirm-split'),
  updateStatus: (id, status_key) => http.put(`/orders/${id}/status`, null, { params: { status_key } }),
  rollbackOptions: (id) => http.get(`/orders/${id}/rollback-options`),
  rollbackStatus: (id, data) => http.post(`/orders/${id}/rollback`, data),
  statusOptions: () => http.get('/orders/meta/status-options'),
  // 补单
  createSupplementary: (id) => http.post(`/orders/${id}/create-supplementary`),
  listSupplementary: (id) => http.get(`/orders/${id}/supplementary-orders`),
  // 订单费用
  listFees: (id) => http.get(`/orders/${id}/fees`),
  createFee: (id, data) => http.post(`/orders/${id}/fees`, data),
  updateFee: (id, feeId, data) => http.put(`/orders/${id}/fees/${feeId}`, data),
  deleteFee: (id, feeId) => http.delete(`/orders/${id}/fees/${feeId}`),
}

export const purchaseApi = {
  list: (params) => http.get('/purchases', { params }),
  get: (id) => http.get(`/purchases/${id}`),
  create: (data) => http.post('/purchases', data),
  delete: (id) => http.delete(`/purchases/${id}`),
  receive: (id, data) => http.post(`/purchases/${id}/receive`, data),
  updateStatus: (id, status) => http.put(`/purchases/${id}/status`, null, { params: { status } }),
  // 采购拆分新流程
  pendingOrders: (params) => http.get('/purchases/pending-orders', { params }),
  preview: (data) => http.post('/purchases/preview', data),
  generate: (data) => http.post('/purchases/generate', data),
  tracking: (params) => http.get('/purchases/tracking', { params }),
  // 新增 - 发送采购单给供应商
  share: (id) => http.post(`/purchases/${id}/share`),
  // 新增 - 供应商列表（采购中用）
  suppliers: () => http.get('/purchases/suppliers/list'),
  // 新增 - 合并生成采购单
  generateMerged: (data) => http.post('/purchases/generate-merged', data),
  // 收货回退
  receiveRollback: (id, data) => http.post(`/purchases/${id}/receive-rollback`, data),
  batchReceive: (data) => http.post('/purchases/batch-receive', data),
  // QR码 & 扫码
  qrcode: (id) => http.get(`/purchases/${id}/qrcode`, { responseType: 'blob' }),
  scan: (code) => http.get(`/purchases/scan/${encodeURIComponent(code)}`),
}

export const warehouseApi = {
  list: (params) => http.get('/warehouses', { params }),
  create: (data) => http.post('/warehouses', data),
  update: (id, data) => http.put(`/warehouses/${id}`, data),
  delete: (id) => http.delete(`/warehouses/${id}`),
  inventory: (params) => http.get('/warehouses/inventory', { params }),
  flows: (params) => http.get('/warehouses/flows', { params }),
  adjustInventory: (data) => http.post('/warehouses/inventory/adjust', data),
  // 三级分类管理
  listStorage: (params) => http.get('/warehouses/storage', { params }),
  createStorage: (data) => http.post('/warehouses/storage', data),
  updateStorage: (id, data) => http.put(`/warehouses/storage/${id}`, data),
  deleteStorage: (id) => http.delete(`/warehouses/storage/${id}`),
  // 库存位置设置
  setLocation: (productId, warehouseId, data) => http.put(`/warehouses/inventory/${productId}/location`, data, { params: { warehouse_id: warehouseId } }),
}

export const installationApi = {
  listTeams: () => http.get('/installations/teams'),
  createTeam: (data) => http.post('/installations/teams', data),
  updateTeam: (id, data) => http.put(`/installations/teams/${id}`, data),
  deleteTeam: (id) => http.delete(`/installations/teams/${id}`),
  listInstallers: () => http.get('/installations/installers'),
  createInstaller: (data) => http.post('/installations/installers', data),
  updateInstaller: (id, data) => http.put(`/installations/installers/${id}`, data),
  deleteInstaller: (id) => http.delete(`/installations/installers/${id}`),
  listOrders: (params) => http.get('/installations/orders', { params }),
  getOrder: (id) => http.get(`/installations/orders/${id}`),
  createOrder: (data) => http.post('/installations/orders', data),
  updateStatus: (id, status, extraParams = {}) => http.put(`/installations/orders/${id}/status`, null, { params: { status, ...extraParams } }),
  stats: () => http.get('/installations/stats'),
}

export const financeApi = {
  listReceivables: (params) => http.get('/finance/receivables', { params }),
  listPayables: (params) => http.get('/finance/payables', { params }),
  receive: (data) => http.post('/finance/receive', data),
  pay: (data) => http.post('/finance/pay', data),
  listExpenses: (params) => http.get('/finance/expenses', { params }),
  createExpense: (data) => http.post('/finance/expenses', data),
  updateExpense: (id, data) => http.put(`/finance/expenses/${id}`, data),
  deleteExpense: (id) => http.delete(`/finance/expenses/${id}`),
  summary: () => http.get('/finance/summary'),
  monthlyReport: (params) => http.get('/finance/monthly-report', { params }),
}

export const productionApi = {
  listFeedbacks: (params) => http.get('/production/feedbacks', { params }),
  getFeedback: (id) => http.get(`/production/feedbacks/${id}`),
  createFeedback: (data) => http.post('/production/feedbacks', data),
  updateFeedback: (id, data) => http.put(`/production/feedbacks/${id}`, data),
  stats: () => http.get('/production/stats'),
  processingOrders: (params) => http.get('/production/processing-orders', { params }),
}

export const dashboardApi = {
  get: () => http.get('/dashboard'),
  salesReport: (params) => http.get('/dashboard/sales-report', { params }),
  productRank: (params) => http.get('/dashboard/product-rank', { params }),
}

export const systemApi = {
  getDict: (type) => http.get(`/system/dict/${type}`),
  getDictTypes: () => http.get('/system/dicts/types'),
  listDictItems: (params) => http.get('/system/dicts', { params }),
  createDictItem: (data) => http.post('/system/dicts', data),
  updateDictItem: (id, data) => http.put(`/system/dicts/${id}`, data),
  deleteDictItem: (id) => http.delete(`/system/dicts/${id}`),
  // 字典类型管理
  listDictTypes: () => http.get('/system/dict-types'),
  createDictType: (data) => http.post('/system/dict-types', data),
  updateDictType: (id, data) => http.put(`/system/dict-types/${id}`, data),
  deleteDictType: (id) => http.delete(`/system/dict-types/${id}`),
  listLogs: (params) => http.get('/system/logs', { params }),
  // 店铺信息
  getStoreInfo: () => http.get('/system/store-info'),
  updateStoreInfo: (data) => http.put('/system/store-info', data),
}

export const afterSaleApi = {
  list: (params) => http.get('/after-sales', { params }),
  get: (id) => http.get(`/after-sales/${id}`),
  create: (data) => http.post('/after-sales', data),
  update: (id, data) => http.put(`/after-sales/${id}`, data),
  delete: (id) => http.delete(`/after-sales/${id}`),
  stats: () => http.get('/after-sales/stats'),
}

export const roleApi = {
  list: () => http.get('/roles'),
  create: (data) => http.post('/roles', data),
  update: (id, data) => http.put(`/roles/${id}`, data),
  delete: (id) => http.delete(`/roles/${id}`),
  updatePermissions: (id, data) => http.put(`/roles/${id}/permissions`, data),
}

export const depositApi = {
  list(params) { return http.get('/deposits', { params }) },
  create(data) { return http.post('/deposits', data) },
  get(id) { return http.get(`/deposits/${id}`) },
  customerBalance(customerId) { return http.get(`/deposits/customer/${customerId}/balance`) },
}

export const processingOrderApi = {
  list(params) { return http.get('/processing', { params }) },
  get(id) { return http.get(`/processing/${id}`) },
  generateFromOrder(orderId) { return http.post(`/processing/generate-from-order/${orderId}`) },
  updateItem(poId, itemId, data) { return http.put(`/processing/${poId}/items/${itemId}`, data) },
  updateStatus(poId, data) { return http.put(`/processing/${poId}/status`, data) },
  markPrinted(poId) { return http.put(`/processing/${poId}/mark-printed`) },
  getPrintData(poId) { return http.get(`/processing/${poId}/print`) },
  settle(poId) { return http.post(`/processing/${poId}/settle`) },
}

export const dailyReportApi = {
  getToday() { return http.get('/daily-report') },
  getHistory(params) { return http.get('/daily-report/history', { params }) },
  getUnlinkedDeposits() { return http.get('/daily-report/deposits/unlinked') },
}

export default http
