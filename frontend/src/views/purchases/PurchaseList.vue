<template>
  <div>
    <el-card shadow="never">
      <!-- 标签页导航 -->
      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <el-tab-pane label="待采购订单" name="pending">
          <div class="tab-toolbar">
            <el-input v-model="pendingQuery.keyword" placeholder="搜索订单号/客户" clearable style="width:240px" @clear="loadPending" @keyup.enter="loadPending" />
            <div>
              <el-button :disabled="selectedIds.length === 0" type="primary" @click="handlePreview">生成采购单 ({{ selectedIds.length }})</el-button>
            </div>
          </div>
          <el-table :data="pendingOrders" v-loading="pendingLoading" stripe style="width:100%" @selection-change="(rows) => selectedIds = rows.map(r => r.id)">
            <el-table-column type="selection" width="44" />
            <el-table-column prop="order_no" label="订单号" width="150" />
            <el-table-column prop="customer_name" label="客户" width="120" />
            <el-table-column prop="customer_phone" label="电话" width="130" />
            <el-table-column prop="order_date" label="下单日期" width="110" />
            <el-table-column prop="content" label="内容" min-width="160" show-overflow-tooltip />
            <el-table-column label="商品数" width="80" align="center">
              <template #default="{ row }">{{ row.item_count }}</template>
            </el-table-column>
            <el-table-column label="物料" width="160">
              <template #default="{ row }">
                <el-tag v-for="m in getMaterialTypes(row.items)" :key="m" size="small" style="margin-right:4px">{{ m }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ row }">
                <el-button text size="small" @click="toggleExpand(row)">{{ expandedRows.has(row.id) ? '收起' : '明细' }}</el-button>
              </template>
            </el-table-column>
            <!-- 展开行: 显示该订单的明细 -->
            <el-table-column type="expand" width="1">
              <template #default="{ row }">
                <el-table :data="row.items" size="small" stripe style="width:100%">
                  <el-table-column prop="product_name" label="产品" width="160" />
                  <el-table-column prop="product_code" label="编码" width="110" />
                  <el-table-column prop="qty" label="数量" width="70" align="center" />
                  <el-table-column prop="unit" label="单位" width="60" />
                  <el-table-column prop="material_type" label="物料类型" width="80">
                    <template #default="{ row: it }">
                      <el-tag :type="it.material_type === '主料' ? 'primary' : 'warning'" size="small">{{ it.material_type }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="unit_price" label="单价" width="90" align="right">
                    <template #default="{ row: it }">¥{{ it.unit_price?.toFixed(2) }}</template>
                  </el-table-column>
                  <el-table-column prop="amount" label="金额" width="100" align="right">
                    <template #default="{ row: it }">¥{{ it.amount?.toFixed(2) }}</template>
                  </el-table-column>
                </el-table>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="pendingOrders.length === 0 && !pendingLoading" style="text-align:center;padding:40px 0;color:#999">暂无待采购订单（已确认的订单将显示在这里）</div>
        </el-tab-pane>

        <el-tab-pane label="采购单管理" name="list">
          <div class="tab-toolbar">
            <el-input v-model="listQuery.keyword" placeholder="采购单号/供应商" clearable style="width:200px" @clear="loadPurchaseList" @keyup.enter="loadPurchaseList" />
            <el-select v-model="listQuery.status" clearable style="width:120px" placeholder="状态筛选" @change="loadPurchaseList">
              <el-option label="待采购" value="待采购" />
              <el-option label="已下单" value="已下单" />
              <el-option label="部分到货" value="部分到货" />
              <el-option label="全部到货" value="全部到货" />
              <el-option label="已结算" value="已结算" />
            </el-select>
            <el-button type="primary" @click="goToPending">生成采购单</el-button>
          </div>
          <el-table :data="purchaseList" v-loading="listLoading" stripe style="width:100%">
            <el-table-column prop="po_no" label="采购单号" width="150" />
            <el-table-column prop="supplier_name" label="供应商" width="150" />
            <el-table-column prop="total_amount" label="金额" width="110" align="right">
              <template #default="{ row }">¥{{ row.total_amount?.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column label="已付/欠款" width="140" align="center">
              <template #default="{ row }">
                <span>¥{{ (row.paid_amount || 0).toFixed(2) }}</span>
                <span v-if="row.debt_amount > 0" style="color:#f56c6c;margin-left:4px">/ ¥{{ row.debt_amount?.toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="order_date" label="下单日期" width="100" />
            <el-table-column prop="expected_date" label="预计到货" width="100" />
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button text size="small" @click="showDetail(row)">详情</el-button>
                <el-button text size="small" type="primary" @click="showReceive(row)" :disabled="row.status === '全部到货' || row.status === '已结算'">收货</el-button>
                <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
                  <template #reference><el-button text size="small" type="danger">删除</el-button></template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top:16px;text-align:right">
            <el-pagination v-model:current-page="listQuery.page" :page-size="listQuery.page_size" :total="listTotal" layout="total, prev, pager, next" @current-change="loadPurchaseList" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="采购跟踪" name="tracking">
          <div class="tab-toolbar">
            <el-input v-model="trackQuery.keyword" placeholder="搜索订单号/客户" clearable style="width:240px" @clear="loadTracking" @keyup.enter="loadTracking" />
          </div>
          <template v-if="trackingList.length > 0">
            <el-card v-for="item in trackingList" :key="item.order_id" shadow="never" style="margin-bottom:12px">
              <div class="track-header">
                <div>
                  <strong>{{ item.order_no }}</strong>
                  <span style="margin-left:12px;color:#666">{{ item.customer_name }}</span>
                  <el-tag :type="item.all_arrived ? 'success' : 'warning'" size="small" style="margin-left:12px">
                    {{ item.all_arrived ? '已全部到货' : '采购中' }}
                  </el-tag>
                </div>
                <span style="color:#999;font-size:13px">关联 {{ item.po_count }} 张采购单</span>
              </div>
              <el-table :data="item.purchase_orders" size="small" stripe style="width:100%;margin-top:8px">
                <el-table-column prop="po_no" label="采购单号" width="150" />
                <el-table-column prop="supplier_name" label="供应商" width="140" />
                <el-table-column prop="total_amount" label="金额" width="100" align="right">
                  <template #default="{ row: po }">¥{{ po.total_amount?.toFixed(2) }}</template>
                </el-table-column>
                <el-table-column label="状态" width="90" align="center">
                  <template #default="{ row: po }">
                    <el-tag :type="po.arrived ? 'success' : po.status === '待采购' ? 'info' : 'primary'" size="small">{{ po.status }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80">
                  <template #default="{ row: po }">
                    <el-button text size="small" @click="showPurchaseOrders(po)">查看</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </template>
          <div v-else style="text-align:center;padding:40px 0;color:#999">暂无采购跟踪数据</div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 采购拆分预览对话框 -->
    <el-dialog v-model="showPreviewDialog" title="采购拆分预览" width="800px" @closed="previewData = null">
      <template v-if="previewData">
        <div style="margin-bottom:12px">
          涉及 {{ previewData.order_count }} 个订单: {{ previewData.order_nos?.join(', ') }}
        </div>
        <el-card v-for="(g, gi) in previewData.groups" :key="gi" shadow="never" style="margin-bottom:12px">
          <template #header>
            <div class="preview-group-header">
              <div>
                <el-tag :type="g.material_type === '主料' ? 'primary' : 'warning'" size="small" style="margin-right:8px">{{ g.material_type }}</el-tag>
                <strong>{{ g.supplier_name }}</strong>
                <span style="margin-left:12px;color:#666">{{ g.contact }} {{ g.phone }}</span>
              </div>
              <span style="font-size:15px;font-weight:bold">¥{{ g.total_amount?.toFixed(2) }}</span>
            </div>
          </template>
          <el-table :data="g.items" size="small" stripe style="width:100%">
            <el-table-column prop="product_name" label="产品" width="150" />
            <el-table-column prop="product_code" label="编码" width="100" />
            <el-table-column prop="qty" label="数量" width="70" align="center" />
            <el-table-column prop="unit" label="单位" width="60" />
            <el-table-column prop="unit_price" label="单价" width="90" align="right">
              <template #default="{ row: it }">¥{{ it.unit_price?.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="amount" label="金额" width="100" align="right">
              <template #default="{ row: it }">¥{{ it.amount?.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column label="规格" min-width="140" show-overflow-tooltip>
              <template #default="{ row: it }">{{ it.specs?.join('；') || '-' }}</template>
            </el-table-column>
          </el-table>
          <div v-if="g.qq || g.wechat || g.bank_account" style="margin-top:8px;font-size:13px;color:#999">
            <span v-if="g.qq">QQ: {{ g.qq }}</span>
            <span v-if="g.wechat" style="margin-left:12px">微信: {{ g.wechat }}</span>
            <span v-if="g.bank_account" style="margin-left:12px">账号: {{ g.bank_account }}</span>
            <span v-if="g.bank_name" style="margin-left:4px">({{ g.bank_name }})</span>
          </div>
        </el-card>
      </template>
      <template #footer>
        <el-button @click="showPreviewDialog = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="handleConfirmGenerate">确认生成采购单</el-button>
      </template>
    </el-dialog>

    <!-- 采购单详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="采购单详情" width="700px">
      <template v-if="detailOrder">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="采购单号">{{ detailOrder.po_no }}</el-descriptions-item>
          <el-descriptions-item label="供应商">{{ detailOrder.supplier_name }}</el-descriptions-item>
          <el-descriptions-item label="联系人">{{ detailOrder.contact || '-' }}</el-descriptions-item>
          <el-descriptions-item label="电话">{{ detailOrder.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="下单日期">{{ detailOrder.order_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="预计到货">{{ detailOrder.expected_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="总金额">¥{{ detailOrder.total_amount?.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTag(detailOrder.status)" size="small">{{ detailOrder.status }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:16px 0 8px">明细</h4>
        <el-table :data="detailOrder.po_items || []" size="small" stripe style="width:100%">
          <el-table-column prop="product_name" label="产品" width="140" />
          <el-table-column prop="spec" label="规格" width="100" />
          <el-table-column prop="quantity" label="数量" width="70" align="center" />
          <el-table-column prop="unit_price" label="单价" width="90" align="right">
            <template #default="{ row }">¥{{ row.unit_price?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="subtotal" label="小计" width="100" align="right">
            <template #default="{ row }">¥{{ row.subtotal?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="已到货" width="70" align="center">
            <template #default="{ row }">{{ row.arrived_qty || 0 }}</template>
          </el-table-column>
        </el-table>
        <div v-if="detailOrder.remark" style="margin-top:12px"><strong>备注：</strong>{{ detailOrder.remark }}</div>
      </template>
    </el-dialog>

    <!-- 收货对话框 -->
    <el-dialog v-model="showReceiveDialog" title="收货" width="500px">
      <template v-if="receiveOrder">
        <p style="margin-bottom:12px;color:#666">采购单：{{ receiveOrder.po_no }} — {{ receiveOrder.supplier_name }}</p>
        <el-table :data="receiveOrder.po_items || []" size="small" style="width:100%">
          <el-table-column prop="product_name" label="产品" width="140" />
          <el-table-column prop="quantity" label="采购数量" width="80" align="center" />
          <el-table-column label="已到货" width="70" align="center">
            <template #default="{ row }">{{ row.arrived_qty || 0 }}</template>
          </el-table-column>
          <el-table-column label="本次收货" width="100">
            <template #default="{ $index }">
              <el-input-number v-model="receiveItems[$index].qty" :min="0" :max="Math.max(0, (receiveOrder.po_items?.[$index]?.quantity || 0) - (receiveOrder.po_items?.[$index]?.arrived_qty || 0))" size="small" style="width:90px" controls-position="right" />
            </template>
          </el-table-column>
        </el-table>
      </template>
      <template #footer>
        <el-button @click="showReceiveDialog = false">取消</el-button>
        <el-button type="primary" :loading="receiving" @click="handleReceive">确认收货</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { purchaseApi } from '@/api'
import { ElMessage } from 'element-plus'

const activeTab = ref('pending')

// ── 待采购订单 ──────────────────────────────────────────────
const pendingOrders = ref([])
const pendingLoading = ref(false)
const pendingQuery = reactive({ keyword: '' })
const selectedIds = ref([])
const expandedRows = ref(new Set())

function toggleExpand(row) {
  if (expandedRows.value.has(row.id)) {
    expandedRows.value.delete(row.id)
  } else {
    expandedRows.value.add(row.id)
  }
}

function getMaterialTypes(items) {
  const types = new Set()
  items.forEach(it => types.add(it.material_type))
  return [...types]
}

async function loadPending() {
  pendingLoading.value = true
  try {
    const res = await purchaseApi.pendingOrders(pendingQuery)
    pendingOrders.value = res.data || []
  } catch {} finally { pendingLoading.value = false }
}

// ── 采购拆分预览 ────────────────────────────────────────────
const showPreviewDialog = ref(false)
const previewData = ref(null)
const generating = ref(false)

async function handlePreview() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请选择至少一个订单')
    return
  }
  try {
    const res = await purchaseApi.preview({ order_ids: selectedIds.value })
    previewData.value = res.data
    showPreviewDialog.value = true
  } catch {}
}

async function handleConfirmGenerate() {
  generating.value = true
  try {
    const res = await purchaseApi.generate({ order_ids: selectedIds.value })
    ElMessage.success(res.message || '采购单已生成')
    showPreviewDialog.value = false
    previewData.value = null
    selectedIds.value = []
    loadPending()
  } finally { generating.value = false }
}

// ── 采购单列表 ──────────────────────────────────────────────
const purchaseList = ref([])
const listTotal = ref(0)
const listLoading = ref(false)
const listQuery = reactive({ keyword: '', status: '', page: 1, page_size: 20 })

async function loadPurchaseList() {
  listLoading.value = true
  try {
    const res = await purchaseApi.list(listQuery)
    purchaseList.value = res.items
    listTotal.value = res.total
  } catch {} finally { listLoading.value = false }
}

function goToPending() {
  activeTab.value = 'pending'
}

// ── 采购跟踪 ────────────────────────────────────────────────
const trackingList = ref([])
const trackQuery = reactive({ keyword: '' })

async function loadTracking() {
  try {
    const res = await purchaseApi.tracking(trackQuery)
    trackingList.value = res.data || []
  } catch {}
}

// ── 采购单详情 ──────────────────────────────────────────────
const showDetailDialog = ref(false)
const detailOrder = ref(null)

function showDetail(row) {
  purchaseApi.get(row.id).then(res => { detailOrder.value = res.data || res; showDetailDialog.value = true }).catch(() => {})
}

function showPurchaseOrders(po) {
  purchaseApi.get(po.po_id).then(res => { detailOrder.value = res.data || res; showDetailDialog.value = true }).catch(() => {})
}

// ── 收货 ────────────────────────────────────────────────────
const showReceiveDialog = ref(false)
const receiveOrder = ref(null)
const receiveItems = ref([])
const receiving = ref(false)

function showReceive(row) {
  purchaseApi.get(row.id).then(res => {
    receiveOrder.value = res.data || res
    const items = receiveOrder.value.po_items || []
    receiveItems.value = items.map(i => ({ product_id: i.product_id || i.id, qty: 0, unit: i.unit || '米', product_name: i.product_name }))
    showReceiveDialog.value = true
  }).catch(() => {})
}

async function handleReceive() {
  receiving.value = true
  try {
    await purchaseApi.receive(receiveOrder.value.id, { items: receiveItems.value.filter(i => i.qty > 0) })
    ElMessage.success('收货成功')
    showReceiveDialog.value = false
    loadPurchaseList()
  } catch {} finally { receiving.value = false }
}

// ── 删除 ────────────────────────────────────────────────────
async function handleDelete(id) {
  await purchaseApi.delete(id)
  ElMessage.success('已删除')
  loadPurchaseList()
}

// ── 工具 ────────────────────────────────────────────────────
function statusTag(status) {
  const map = { '待采购': 'info', '已下单': 'primary', '部分到货': 'warning', '全部到货': 'success', '已结算': 'success' }
  return map[status] || 'info'
}

function onTabChange(tab) {
  if (tab === 'list') loadPurchaseList()
  else if (tab === 'tracking') loadTracking()
}

onMounted(async () => {
  await loadPending()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h3 { font-size: 18px; }
.tab-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px; }
.track-header { display: flex; justify-content: space-between; align-items: center; }
.preview-group-header { display: flex; justify-content: space-between; align-items: center; }
:deep(.el-table__expanded-cell) { padding: 8px 8px 8px 48px; }
</style>
