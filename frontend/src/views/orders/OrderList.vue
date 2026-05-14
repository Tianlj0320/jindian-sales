<template>
  <el-card shadow="never">
    <div class="page-header">
      <h3>订单管理</h3>
      <div>
        <el-button type="primary" size="small" @click="openNewOrder">+ 新增</el-button>
        <el-button size="small" @click="loadData">刷新</el-button>
      </div>
    </div>

    <!-- 查询条件 -->
    <el-form :inline="true" size="small" style="margin-bottom:8px">
      <el-form-item label="搜索">
        <el-input v-model="query.keyword" placeholder="订单号/客户" clearable style="width:160px" @clear="loadData" @keyup.enter="loadData" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="query.status_key" clearable style="width:120px" @change="loadData">
          <el-option v-for="s in statusOptions" :key="s.key" :label="s.label" :value="s.key">
            <span :style="{ color: s.color }">{{ s.label }}</span>
          </el-option>
        </el-select>
      </el-form-item>
      <el-form-item label="日期">
        <el-date-picker v-model="query.date_from" type="date" placeholder="开始" value-format="YYYY-MM-DD" style="width:130px" @change="loadData" />
        <span style="margin:0 6px">至</span>
        <el-date-picker v-model="query.date_to" type="date" placeholder="结束" value-format="YYYY-MM-DD" style="width:130px" @change="loadData" />
      </el-form-item>
      <el-form-item label="业务员">
        <el-input v-model="query.salesperson" placeholder="业务员" style="width:100px" clearable @clear="loadData" @keyup.enter="loadData" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadData">查询</el-button>
        <el-button @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 移动端卡片列表 -->
    <div v-if="isMobile" class="mobile-order-list">
      <div v-for="row in list" :key="row.id" class="mobile-order-card" @click="handleRowClick(row)">
        <div class="mobile-card-header">
          <span class="mobile-order-no">{{ row.order_no }}</span>
          <el-tag :color="row.status_color" style="color:#fff;border:0" size="small">{{ row.status_label }}</el-tag>
        </div>
        <div class="mobile-card-body">
          <div class="mobile-card-row"><label>客户</label><span>{{ row.customer_name }}</span></div>
          <div class="mobile-card-row"><label>金额</label><span>¥{{ row.amount?.toFixed(2) }}</span></div>
          <div class="mobile-card-row"><label>定金</label><span>¥{{ (row.deposit || 0).toFixed(2) }}</span></div>
          <div class="mobile-card-row"><label>欠款</label><span :style="{color: row.debt > 0 ? '#f56c6c' : '#67c23a'}">¥{{ row.debt?.toFixed(2) }}</span></div>
          <div class="mobile-card-row"><label>日期</label><span>{{ row.order_date }}</span></div>
        </div>
        <div class="mobile-card-actions" @click.stop>
          <el-button size="small" text type="primary" @click.stop="openEditOrder(row)">编辑</el-button>
          <el-button size="small" text @click.stop="handleAdvance(row)" :disabled="isTerminal(row.status_key)">推进</el-button>
          <el-button v-if="canRollback(row)" size="small" text type="warning" @click.stop="handleRollback(row)">回退</el-button>
          <el-button v-if="row.status_key === 'confirmed'" size="small" text type="warning" @click.stop="handleShowSplitPreview(row)">拆分</el-button>
          <el-popconfirm v-if="row.status_key === 'initial'" title="确认删除？" @confirm="handleDelete(row.id)">
            <template #reference><el-button text size="small" type="danger" @click.stop>删除</el-button></template>
          </el-popconfirm>
        </div>
      </div>
      <div v-if="list.length === 0 && !loading" class="mobile-empty">暂无订单数据</div>
    </div>

    <!-- 主表：订单列表（桌面端） -->
    <el-table
      v-show="!isMobile"
      :data="list"
      v-loading="loading"
      stripe
      style="width:100%"
      size="small"
      class="compact-table"
      highlight-current-row
      @row-click="handleRowClick"
      @row-dblclick="handleRowDblClick"
    >
      <el-table-column type="index" label="序号" width="50" />
      <el-table-column prop="order_no" label="订单号" width="155" />
      <el-table-column prop="customer_name" label="客户" width="100" />
      <el-table-column prop="customer_phone" label="电话" width="120" />
      <el-table-column prop="order_type" label="类型" width="60" />
      <el-table-column prop="content" label="内容" min-width="150" show-overflow-tooltip />
      <el-table-column prop="amount" label="金额" width="100" align="right">
        <template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column prop="received" label="已收" width="90" align="right">
        <template #default="{ row }">¥{{ row.received?.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column prop="deposit" label="定金" width="90" align="right">
        <template #default="{ row }">¥{{ (row.deposit || 0).toFixed(2) }}</template>
      </el-table-column>
      <el-table-column prop="debt" label="欠款" width="90" align="right">
        <template #default="{ row }">
          <span :style="{ color: row.debt > 0 ? '#f56c6c' : '#67c23a' }">¥{{ row.debt?.toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :color="row.status_color" style="color:#fff;border:0;font-size:11px">{{ row.status_label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="order_date" label="日期" width="95" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" type="primary" @click.stop="openEditOrder(row)">编辑</el-button>
          <el-button text size="small" @click.stop="handleAdvance(row)" :disabled="isTerminal(row.status_key)">推进</el-button>
          <el-button v-if="canRollback(row)" text size="small" type="warning" @click.stop="handleRollback(row)">回退</el-button>
          <el-button v-if="row.status_key === 'confirmed'" text size="small" type="warning" @click.stop="handleShowSplitPreview(row)">拆分</el-button>
          <el-popconfirm v-if="row.status_key === 'initial'" title="确认删除？" @confirm="handleDelete(row.id)">
            <template #reference><el-button text size="small" type="danger" @click.stop>删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div style="margin-top:8px;text-align:right">
      <el-pagination
        v-model:current-page="query.page"
        :page-size="query.page_size"
        :total="total"
        layout="total, prev, pager, next"
        size="small"
        @current-change="loadData"
      />
    </div>

    <!-- 从表：选中订单的明细 -->
    <div v-if="selectedOrder" class="detail-panel">
      <div class="detail-header">
        <span>
          订单 <strong>{{ selectedOrder.order_no }}</strong>
          <el-tag :color="selectedOrder.status_color" style="color:#fff;border:0;margin-left:8px" size="small">{{ selectedOrder.status_label }}</el-tag>
        </span>
        <span>
          客户: {{ selectedOrder.customer_name }}
          <span v-if="selectedOrder.amount"> | 金额: ¥{{ selectedOrder.amount?.toFixed(2) }}</span>
        </span>
        <span class="detail-actions">
          <el-button text size="small" type="primary" @click="openEditOrder(selectedOrder)">编辑</el-button>
          <el-button text size="small" @click="handleAdvance(selectedOrder)" :disabled="isTerminal(selectedOrder.status_key)">推进</el-button>
          <el-button v-if="canRollback(selectedOrder)" text size="small" type="warning" @click="handleRollback(selectedOrder)">回退</el-button>
        </span>
      </div>

      <el-table :data="orderItems" v-loading="itemsLoading" stripe style="width:100%" size="small" class="compact-detail-table">
        <el-table-column type="index" label="序号" width="45" />
        <el-table-column prop="room" label="空间" width="60" />
        <el-table-column prop="product_code" label="编码" width="100" />
        <el-table-column prop="product_name" label="产品名称" width="120" show-overflow-tooltip />
        <el-table-column label="采购类型" width="70">
          <template #default="{ row }">
            <el-tag :type="row.procurement_type === '物料' ? 'primary' : row.procurement_type === '成品' ? 'success' : 'warning'" size="small">
              {{ row.procurement_type || '物料' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="规格" width="100">
          <template #default="{ row }">{{ formatSpec(row) }}</template>
        </el-table-column>
        <el-table-column prop="qty" label="数量" width="55" align="center" />
        <el-table-column label="单价" width="70" align="right">
          <template #default="{ row }">¥{{ (row.unit_price || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="金额" width="80" align="right">
          <template #default="{ row }">¥{{ (row.amount || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="process_desc" label="工艺" width="90" show-overflow-tooltip />
      </el-table>

      <!-- 分类汇总 -->
      <div v-if="selectedItemsByCategory.length > 0" class="category-summary">
        <span v-for="cat in selectedItemsByCategory" :key="cat.name" :class="'cat-' + cat.name">
          <strong>{{ cat.name }}：</strong>¥{{ cat.total.toFixed(2) }} ({{ cat.count }} 项)
        </span>
        <span class="cat-total">
          <strong>合计：</strong>¥{{ orderTotal.toFixed(2) }}
        </span>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading && list.length > 0" class="detail-panel empty-detail">
      点击上方订单行查看明细
    </div>
  </el-card>

  <!-- 订单编辑弹窗 -->
  <OrderEditDialog
    v-model="showEditDialog"
    :order-id="editOrderId"
    :order-ids="allOrderIds"
    @saved="onOrderSaved"
  />

  <!-- 采购拆分预览对话框（保持原有功能） -->
  <el-dialog v-model="showPreview" title="采购拆分预览" :width="isMobile ? '95vw' : '800px'" top="5vh" :close-on-click-modal="false">
    <template v-if="previewData">
      <el-alert :closable="false" type="info" style="margin-bottom:16px">
        <template #title>
          待拆分订单共 <strong>{{ previewData.order_count }}</strong> 单：
          <strong>{{ (previewData.order_nos || []).join('、') }}</strong>
        </template>
      </el-alert>
      <template v-if="previewData.main_orders && previewData.main_orders.length">
        <h4 style="margin:0 0 8px;color:#409eff">主料采购单 ({{ previewData.main_orders.length }} 张)</h4>
        <el-card v-for="(po, pi) in previewData.main_orders" :key="'m'+pi" shadow="hover" style="margin-bottom:12px">
          <div class="po-header"><strong>{{ po.supplier_name }}</strong><span class="po-header-info">联系人: {{ po.contact || '-' }} / {{ po.phone || '-' }}</span></div>
          <el-table :data="po.items" size="small" stripe style="width:100%">
            <el-table-column prop="product_name" label="产品" min-width="120" />
            <el-table-column label="规格" min-width="130"><template #default="{ row }">{{ (row.specs || []).join('；') || '-' }}</template></el-table-column>
            <el-table-column prop="qty" label="数量" width="70" align="center" />
            <el-table-column prop="unit_price" label="单价" width="80" align="right"><template #default="{ row }">¥{{ row.unit_price?.toFixed(2) }}</template></el-table-column>
            <el-table-column prop="amount" label="小计" width="90" align="right"><template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template></el-table-column>
          </el-table>
          <div style="text-align:right;margin-top:4px;font-weight:bold;color:#f56c6c">小计: ¥{{ po.total_amount?.toFixed(2) }} ({{ po.item_count }} 项)</div>
        </el-card>
      </template>
      <template v-if="previewData.aux_orders && previewData.aux_orders.length">
        <h4 style="margin:12px 0 8px;color:#f59e0b">辅料集中采购单 ({{ previewData.aux_orders.length }} 张)</h4>
        <el-card v-for="(po, pi) in previewData.aux_orders" :key="'a'+pi" shadow="hover" style="margin-bottom:12px">
          <div class="po-header"><strong>{{ po.supplier_name }}</strong><span class="po-header-info">联系人: {{ po.contact || '-' }} / {{ po.phone || '-' }}</span></div>
          <el-table :data="po.items" size="small" stripe style="width:100%">
            <el-table-column prop="product_name" label="产品" min-width="120" />
            <el-table-column prop="qty" label="数量" width="70" align="center" />
            <el-table-column prop="unit_price" label="单价" width="80" align="right"><template #default="{ row }">¥{{ row.unit_price?.toFixed(2) }}</template></el-table-column>
            <el-table-column prop="amount" label="小计" width="90" align="right"><template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template></el-table-column>
          </el-table>
          <div style="text-align:right;margin-top:4px;font-weight:bold;color:#f56c6c">小计: ¥{{ po.total_amount?.toFixed(2) }} ({{ po.item_count }} 项)</div>
        </el-card>
      </template>
      <div v-if="!previewData.main_orders?.length && !previewData.aux_orders?.length" style="text-align:center;padding:32px;color:#999">没有需要拆分采购的订单明细</div>
    </template>
    <template #footer>
      <el-button @click="showPreview = false">取消</el-button>
      <el-button type="primary" :loading="splitting" @click="handleConfirmSplit">确认拆分</el-button>
    </template>
  </el-dialog>

  <!-- 状态回退对话框 -->
  <el-dialog v-model="showRollbackDialog" title="状态回退" width="450px" :close-on-click-modal="false">
    <template v-if="rollbackData">
      <el-alert type="warning" :closable="false" style="margin-bottom:16px">
        <template #title>
          当前状态：<el-tag :color="rollbackData.current_color" style="color:#fff;border:0">{{ rollbackData.current_label }}</el-tag>
        </template>
      </el-alert>
      <template v-if="rollbackData.po_statuses?.length">
        <el-alert type="info" :closable="false" style="margin-bottom:12px">
          <template #title>关联采购单状态：{{ rollbackData.po_statuses.map(p => `${p.po_no}(${p.status})`).join('、') }}</template>
        </el-alert>
      </template>
      <div v-if="!rollbackRolling" style="margin-bottom:8px;font-size:13px;color:#606266">选择要回退到的状态：</div>
      <el-radio-group v-model="rollbackTarget" v-if="!rollbackRolling">
        <div v-for="opt in rollbackData.rollback_options" :key="opt.key" style="margin-bottom:8px">
          <el-radio :value="opt.key" :disabled="!opt.allowed">
            <span :style="{ color: opt.color, fontWeight:'bold' }">{{ opt.label }}</span>
            <span v-if="!opt.allowed" style="margin-left:8px;font-size:12px;color:#f56c6c">({{ opt.block_reason }})</span>
          </el-radio>
        </div>
      </el-radio-group>
      <div v-if="rollbackTarget" style="margin-top:12px">
        <el-input v-model="rollbackRemark" placeholder="回退原因说明（选填）" />
      </div>
    </template>
    <template #footer>
      <el-button @click="showRollbackDialog = false">取消</el-button>
      <el-button type="warning" :loading="rollbackRolling" :disabled="!rollbackTarget" @click="handleConfirmRollback">确认回退</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { orderApi } from '@/api'
import { ElMessage } from 'element-plus'
import OrderEditDialog from '@/components/OrderEditDialog.vue'

const list = ref([])
const total = ref(0)
const loading = ref(false)
const splitting = ref(false)
const statusOptions = ref([])
const allOrderIds = ref([])

function getDefaultDateRange() {
  const now = new Date()
  const to = now.toISOString().slice(0, 10)
  const from = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate()).toISOString().slice(0, 10)
  return { from, to }
}
const defaultRange = getDefaultDateRange()
const query = reactive({ keyword: '', status_key: '', date_from: defaultRange.from, date_to: defaultRange.to, salesperson: '', page: 1, page_size: 20 })

// 选中订单
const selectedOrder = ref(null)
const orderItems = ref([])
const itemsLoading = ref(false)

// 编辑弹窗
const showEditDialog = ref(false)
const editOrderId = ref(null)

// 拆分预览
const showPreview = ref(false)
const previewData = ref(null)

// 回退
const showRollbackDialog = ref(false)
const rollbackData = ref(null)
const rollbackTarget = ref('')
const rollbackRemark = ref('')
const rollbackRolling = ref(false)
const rollbackOrderId = ref(null)

// ── 移动端适配 ──
const isMobile = ref(window.innerWidth < 768)
function onResize() { isMobile.value = window.innerWidth < 768 }

// ── 数据加载 ──
async function loadData() {
  loading.value = true
  try {
    const params = { ...query }
    if (!params.salesperson) delete params.salesperson
    const res = await orderApi.list(params)
    list.value = res.items
    total.value = res.total
    allOrderIds.value = (res.items || []).map(i => i.id)
    // 如果之前选中的行还在列表中，保持选中
    if (selectedOrder.value) {
      const stillExists = list.value.find(i => i.id === selectedOrder.value.id)
      if (stillExists) {
        loadOrderItems(selectedOrder.value.id)
      } else {
        selectedOrder.value = null
        orderItems.value = []
      }
    }
  } catch {} finally { loading.value = false }
}

// ── 行操作 ──
function handleRowClick(row) {
  selectedOrder.value = row
  loadOrderItems(row.id)
}

function handleRowDblClick(row) {
  openEditOrder(row)
}

function openNewOrder() {
  editOrderId.value = null
  showEditDialog.value = true
}

function openEditOrder(row) {
  editOrderId.value = row.id
  showEditDialog.value = true
}

function onOrderSaved() {
  loadData()
}

// ── 加载选中订单的明细 ──
async function loadOrderItems(orderId) {
  itemsLoading.value = true
  try {
    const res = await orderApi.get(orderId)
    orderItems.value = (res.data?.items || []).map(i => ({
      ...i,
      procurement_type: i.procurement_type || (i.material_type === '辅料' ? '辅料' : '物料'),
      amount: parseFloat(i.amount) || 0,
    }))
  } catch {
    orderItems.value = []
  } finally {
    itemsLoading.value = false
  }
}

// ── 从表分类汇总 ──
const selectedItemsByCategory = computed(() => {
  const cats = {}
  for (const item of orderItems.value) {
    const cat = item.procurement_type || '物料'
    if (!cats[cat]) cats[cat] = { name: cat, total: 0, count: 0 }
    cats[cat].total += parseFloat(item.amount) || 0
    cats[cat].count += 1
  }
  return Object.values(cats)
})

const orderTotal = computed(() => orderItems.value.reduce((s, i) => s + (parseFloat(i.amount) || 0), 0))

function formatSpec(row) {
  const parts = []
  if (row.width) parts.push(`${row.width}m`)
  if (row.height) parts.push(`${row.height}m`)
  if (row.fold_ratio) parts.push(`×${row.fold_ratio}`)
  return parts.join('×') || '-'
}

// ── 推进 ──
async function handleAdvance(row) {
  try {
    const res = await orderApi.advance(row.id)
    if (res.data && res.data.need_preview) {
      previewData.value = res.data.preview
      showPreview.value = true
      return
    }
    ElMessage.success('订单已推进')
    loadData()
  } catch {}
}

async function handleShowSplitPreview(row) {
  try {
    const res = await orderApi.splitPreview()
    previewData.value = res.data
    showPreview.value = true
  } catch (e) {
    ElMessage.warning(e.message || '没有已确认的订单可拆分')
  }
}

async function handleConfirmSplit() {
  splitting.value = true
  try {
    const res = await orderApi.confirmSplit()
    ElMessage.success(res.message || '拆分成功')
    showPreview.value = false
    previewData.value = null
    loadData()
  } catch (e) {
    ElMessage.error(e.message || '拆分失败')
  } finally { splitting.value = false }
}

async function handleDelete(id) {
  await orderApi.delete(id)
  ElMessage.success('已删除')
  if (selectedOrder.value?.id === id) {
    selectedOrder.value = null
    orderItems.value = []
  }
  loadData()
}

function isTerminal(key) {
  return ['accepted', 'cancelled', 'after_sale'].includes(key)
}

/** 是否可以回退：不是初始态、不是终态 */
function canRollback(row) {
  return row.status_key !== 'initial' && !isTerminal(row.status_key)
}

/** 打开回退对话框，获取可选状态 */
async function handleRollback(row) {
  try {
    const res = await orderApi.rollbackOptions(row.id)
    rollbackData.value = res.data
    rollbackTarget.value = ''
    rollbackRemark.value = ''
    rollbackOrderId.value = row.id
    showRollbackDialog.value = true
  } catch (e) {
    ElMessage.error(e.message || '获取回退选项失败')
  }
}

/** 确认回退 */
async function handleConfirmRollback() {
  if (!rollbackTarget.value) { ElMessage.warning('请选择要回退到的状态'); return }
  if (!rollbackOrderId.value) { ElMessage.error('订单ID丢失，请重新打开'); return }
  rollbackRolling.value = true
  try {
    const res = await orderApi.rollbackStatus(rollbackOrderId.value, {
      status_key: rollbackTarget.value,
      remark: rollbackRemark.value || '',
    })
    ElMessage.success(res.message || '回退成功')
    showRollbackDialog.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.message || '回退失败')
  } finally { rollbackRolling.value = false }
}

function resetQuery() {
  const range = getDefaultDateRange()
  query.keyword = ''
  query.status_key = ''
  query.date_from = range.from
  query.date_to = range.to
  query.salesperson = ''
  query.page = 1
  loadData()
}

onMounted(async () => {
  window.addEventListener('resize', onResize)
  try {
    const res = await orderApi.statusOptions()
    statusOptions.value = res.items || res.data || res || []
  } catch {}
  loadData()
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.page-header h3 { font-size: 15px; margin: 0; }

.compact-table { font-size: 13px; }
.compact-table :deep(.el-table__header th) { padding: 3px 0; font-size: 13px; line-height: 1.5; }
.compact-table :deep(.el-table__cell) { padding: 3px 6px; }
.compact-table :deep(.el-table__body td) { padding: 3px 6px; line-height: 1.5; }

:deep(.el-card__body) { padding: 12px 16px; }

/* 从表明细面板 */
.detail-panel {
  margin-top: 12px;
  border-top: 2px solid #409eff;
  padding-top: 10px;
}
.empty-detail {
  text-align: center;
  color: #c0c4cc;
  font-size: 14px;
  padding: 30px 0;
}
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 14px;
  flex-wrap: wrap;
  gap: 4px;
}
.detail-actions { margin-left: auto; }

.compact-detail-table { font-size: 13px; }
.compact-detail-table :deep(.el-table__header th) { padding: 3px 0; font-size: 13px; }
.compact-detail-table :deep(.el-table__cell) { padding: 3px 4px; }
.compact-detail-table :deep(.el-table__body td) { padding: 3px 4px; }

.category-summary {
  display: flex;
  gap: 16px;
  margin-top: 6px;
  padding: 6px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
}
.cat-total { margin-left: auto; font-weight: bold; }
.cat-物料 { color: #409eff; }
.cat-成品 { color: #67c23a; }
.cat-辅料 { color: #e6a23c; }

.po-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; font-size: 13px; }
.po-header-info { font-size: 11px; color: #666; }

/* ── 移动端卡片布局 ── */
.mobile-order-list { padding: 0; }
.mobile-order-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 10px;
  padding: 12px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.mobile-order-card:active { box-shadow: 0 2px 8px rgba(0,0,0,0.12); }
.mobile-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  padding-bottom: 6px;
  border-bottom: 1px solid #f0f0f0;
}
.mobile-order-no { font-weight: bold; font-size: 14px; }
.mobile-card-body { margin-bottom: 6px; }
.mobile-card-row {
  display: flex;
  justify-content: space-between;
  padding: 2px 0;
  font-size: 13px;
}
.mobile-card-row label { color: #909399; min-width: 50px; }
.mobile-card-row span { text-align: right; }
.mobile-card-actions {
  display: flex;
  gap: 4px;
  padding-top: 6px;
  border-top: 1px dashed #eee;
  flex-wrap: wrap;
}
.mobile-empty { text-align: center; padding: 40px 0; color: #c0c4cc; }

/* ── 移动端响应式：搜索表单 ── */
@media (max-width: 768px) {
  .el-form--inline { display: flex; flex-direction: column; gap: 8px; }
  .el-form--inline .el-form-item { width: 100%; margin-right: 0; }
  .el-form--inline .el-input { width: 100% !important; }
  .el-form--inline .el-select { width: 100% !important; }
  .el-form--inline .el-date-editor { width: 100% !important; }
  .el-dialog { width: 95vw !important; margin: 5vh auto !important; }
}
</style>
