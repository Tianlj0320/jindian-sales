<template>
  <el-card shadow="never">
    <div class="page-header">
      <h3>加工单管理</h3>
      <div>
        <el-button size="small" @click="loadData">刷新</el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange" style="margin-top:4px">

      <!-- 待生成加工单 -->
      <el-tab-pane label="待生成加工单" name="pending">
        <el-table :data="pendingList" v-loading="loadingPending" stripe size="small" style="width:100%" class="compact-table" @row-click="handlePendingRowClick">
          <template #empty>
            <div style="padding:30px 0;color:#999;font-size:13px">
              所有已入库订单均已完成加工单生成
            </div>
          </template>
          <el-table-column type="index" label="序号" width="50" />
          <el-table-column prop="order_no" label="订单号" width="160" />
          <el-table-column prop="customer_name" label="客户名" width="120" show-overflow-tooltip />
          <el-table-column prop="material_count" label="物料数量" width="80" align="center" />
          <el-table-column prop="order_date" label="下单日期" width="100" />
          <el-table-column label="操作" width="130" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" :loading="generatingPendingId === row.order_id" @click.stop="generateFromPending(row)">
                生成加工单
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 加工单列表 -->
      <el-tab-pane label="加工单列表" name="list">
        <!-- 筛选栏 -->
        <el-form :inline="true" size="small" style="margin-bottom:8px">
          <el-form-item label="搜索">
            <el-input v-model="query.keyword" placeholder="加工单号/客户" clearable style="width:160px" @clear="loadData" @keyup.enter="loadData" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="query.status" clearable placeholder="加工单状态" style="width:120px" @change="loadData">
              <el-option label="待加工" value="pending" />
              <el-option label="加工中" value="processing" />
              <el-option label="已完成" value="completed" />
            </el-select>
          </el-form-item>
          <el-form-item label="订单状态">
            <el-select v-model="query.order_status" clearable placeholder="订单状态" style="width:130px" @change="loadData">
              <el-option label="已确认" value="confirmed" />
              <el-option label="已分单" value="split" />
              <el-option label="采购中" value="purchasing" />
              <el-option label="已入库" value="stocked" />
              <el-option label="加工中" value="processing" />
              <el-option label="已完成" value="completed" />
              <el-option label="已验收" value="accepted" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadData">查询</el-button>
            <el-button @click="resetQuery">重置</el-button>
          </el-form-item>
        </el-form>

        <!-- 主表：加工单列表 -->
        <el-table
          :data="list"
          v-loading="loading"
          stripe
          style="width:100%"
          size="small"
          class="compact-table"
          highlight-current-row
          @row-click="handleRowClick"
        >
          <template #empty>
            <div style="padding:30px 0;color:#999;font-size:13px">
              <p style="margin:0 0 6px">暂无加工单</p>
              <p style="margin:0;font-size:12px;color:#bbb">订单采购收货完成后，在待生成页面生成加工单</p>
            </div>
          </template>
          <el-table-column type="index" label="序号" width="50" />
          <el-table-column prop="po_no" label="加工单号" width="160" />
          <el-table-column prop="order_no" label="订单号" width="140" />
          <el-table-column prop="customer_name" label="客户名" width="100" show-overflow-tooltip />
          <el-table-column prop="processor_name" label="加工厂" width="120" show-overflow-tooltip />
          <el-table-column prop="item_count" label="明细条数" width="70" align="center" />
          <el-table-column label="加工费总额" width="110" align="right">
            <template #default="{ row }">¥{{ (row.total_process_fee || 0).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :color="statusColorMap[row.status]" style="color:#fff;border:0;font-size:11px">
                {{ statusLabelMap[row.status] }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="打印" width="60" align="center">
            <template #default="{ row }">
              <el-tag :type="row.printed ? 'success' : 'info'" size="small">{{ row.printed ? '是' : '否' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建日期" width="95" />
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

        <!-- 从表：选中加工单明细 -->
        <div v-if="selectedOrder" class="detail-panel">
          <div class="detail-header">
            <span>
              加工单 <strong>{{ selectedOrder.po_no }}</strong>
              <el-tag :color="statusColorMap[selectedOrder.status]" style="color:#fff;border:0;margin-left:8px" size="small">{{ statusLabelMap[selectedOrder.status] }}</el-tag>
              <el-tag v-if="selectedOrder.printed" type="success" size="small" style="margin-left:4px">已打印</el-tag>
            </span>
            <span>
              订单: {{ selectedOrder.order_no }}
              <span v-if="selectedOrder.customer_name"> | 客户: {{ selectedOrder.customer_name }}</span>
              <span v-if="selectedOrder.processor_name"> | 加工厂: {{ selectedOrder.processor_name }}</span>
              <span> | 加工费: ¥{{ (selectedOrder.total_process_fee || 0).toFixed(2) }}</span>
            </span>
            <span class="detail-actions">
              <el-button text size="small" :loading="itemsSaving" :disabled="itemsSaving" @click="handleUpdateItems">更新单价</el-button>
              <el-button text size="small" :disabled="!canAdvance(selectedOrder.status) || advancing" @click="handleAdvanceStatus">
                {{ nextStatusLabel(selectedOrder.status) }}
              </el-button>
              <el-button text size="small" @click="handlePrint(selectedOrder)">打印</el-button>
              <el-button v-if="selectedOrder.status === 'completed'" text size="small" type="warning" @click="handleSettle(selectedOrder)">结算</el-button>
            </span>
          </div>

          <el-table :data="orderItems" v-loading="itemsLoading" stripe style="width:100%" size="small" class="compact-detail-table">
            <el-table-column type="index" label="序号" width="45" />
            <el-table-column prop="product_code" label="产品编码" width="100" />
            <el-table-column prop="product_name" label="产品名称" width="120" show-overflow-tooltip />
            <el-table-column label="宽" width="50" align="center">
              <template #default="{ row }">{{ row.width || '-' }}</template>
            </el-table-column>
            <el-table-column label="高" width="50" align="center">
              <template #default="{ row }">{{ row.height || '-' }}</template>
            </el-table-column>
            <el-table-column prop="qty" label="数量" width="55" align="center" />
            <el-table-column prop="unit" label="单位" width="45" align="center" />
            <el-table-column prop="process_desc" label="工艺描述" width="100" show-overflow-tooltip />
            <el-table-column label="加工单价" width="90" align="right">
              <template #default="{ row }">
                <el-input-number v-model="row._edit_fee" size="small" :min="0" :precision="2" :controls="false" style="width:75px" />
              </template>
            </el-table-column>
            <el-table-column label="加工费小计" width="90" align="right">
              <template #default="{ row }">¥{{ ((row._edit_fee || 0) * (row.qty || 0)).toFixed(2) }}</template>
            </el-table-column>
            <el-table-column label="验收" width="55" align="center">
              <template #default="{ row }">
                <el-checkbox v-model="row._edit_checked" />
              </template>
            </el-table-column>
            <el-table-column prop="remark" label="备注" width="100" show-overflow-tooltip />
          </el-table>
        </div>

        <!-- 空状态提示 -->
        <div v-else-if="!loading && list.length > 0" class="detail-panel empty-detail">
          点击上方加工单行查看明细
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-card>

  <!-- 生成加工单对话框 → 已合并到「待生成加工单」标签页内，每行有生成按钮 -->
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { processingOrderApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

// ── 常量 ──
const statusLabelMap = { pending: '待加工', processing: '加工中', completed: '已完成' }
const statusColorMap = {
  pending: '#909399',
  processing: '#e6a23c',
  completed: '#67c23a',
}
const statusFlow = {
  pending: { next: 'processing', label: '推进加工中' },
  processing: { next: 'completed', label: '标记完成' },
}

// ── 主表数据 ──
const list = ref([])
const total = ref(0)
const loading = ref(false)
const query = reactive({ keyword: '', status: '', order_status: '', page: 1, page_size: 20 })

// ── 选中加工单 ──
const selectedOrder = ref(null)
const orderItems = ref([])
const itemsLoading = ref(false)
const itemsSaving = ref(false)
const advancing = ref(false)

// ── 待生成加工单 ──
const activeTab = ref('pending')
const pendingList = ref([])
const loadingPending = ref(false)
const generatingPendingId = ref(null)

// =============================================================================
// 数据加载
// =============================================================================

async function loadData() {
  loading.value = true
  try {
    const params = { page: query.page, page_size: query.page_size }
    if (query.keyword) params.keyword = query.keyword
    if (query.status) params.status = query.status
    if (query.order_status) params.order_status = query.order_status
    const res = await processingOrderApi.list(params)
    list.value = res.items || []
    total.value = res.total || 0
    // 保持选中行
    if (selectedOrder.value) {
      const exists = list.value.find(i => i.id === selectedOrder.value.id)
      if (exists) {
        loadOrderItems(selectedOrder.value.id)
      } else {
        selectedOrder.value = null
        orderItems.value = []
      }
    }
  } catch {} finally { loading.value = false }
}

// =============================================================================
// 待生成加工单
// =============================================================================

async function loadPendingOrders() {
  loadingPending.value = true
  try {
    const res = await processingOrderApi.pendingOrders()
    pendingList.value = res.data || []
  } catch {} finally { loadingPending.value = false }
}

function handleTabChange(tab) {
  if (tab === 'pending') loadPendingOrders()
  else if (tab === 'list') loadData()
}

// =============================================================================
// 行操作
// =============================================================================

function handleRowClick(row) {
  selectedOrder.value = row
  loadOrderItems(row.id)
}

// =============================================================================
// 加载选中加工单明细
// =============================================================================

async function loadOrderItems(id) {
  itemsLoading.value = true
  try {
    const res = await processingOrderApi.get(id)
    const po = res.data || res
    orderItems.value = (po.items || []).map(i => ({
      ...i,
      _edit_fee: parseFloat(i.process_fee_unit) || 0,
      _edit_checked: !!i.checked,
    }))
    // 同步头部信息
    if (selectedOrder.value) {
      Object.assign(selectedOrder.value, {
        po_no: po.po_no,
        order_no: po.order_no,
        customer_name: po.customer_name,
        processor_name: po.processor_name,
        total_process_fee: parseFloat(po.total_process_fee) || 0,
        status: po.status,
        printed: !!po.printed,
      })
    }
  } catch {
    orderItems.value = []
  } finally {
    itemsLoading.value = false
  }
}

// =============================================================================
// 状态辅助
// =============================================================================

function canAdvance(status) {
  return !!statusFlow[status]
}

function nextStatusLabel(status) {
  return statusFlow[status]?.label || '推进状态'
}

// =============================================================================
// 更新单价/验收
// =============================================================================

async function handleUpdateItems() {
  if (!selectedOrder.value || orderItems.value.length === 0) return
  itemsSaving.value = true
  try {
    const modified = orderItems.value.filter(i => {
      const origFee = parseFloat(i.process_fee_unit) || 0
      const origChecked = !!i.checked
      return origFee !== i._edit_fee || origChecked !== i._edit_checked
    })
    if (modified.length === 0) {
      ElMessage.info('没有需要更新的项目')
      return
    }
    for (const item of modified) {
      await processingOrderApi.updateItem(selectedOrder.value.id, item.id, {
        process_fee_unit: item._edit_fee,
        checked: item._edit_checked,
      })
    }
    ElMessage.success(`已更新 ${modified.length} 项`)
    await loadOrderItems(selectedOrder.value.id)
    await loadData()
  } catch {
    ElMessage.error('更新失败')
  } finally {
    itemsSaving.value = false
  }
}

// =============================================================================
// 推进状态
// =============================================================================

async function handleAdvanceStatus() {
  if (!selectedOrder.value) return
  const next = statusFlow[selectedOrder.value.status]
  if (!next) { return }

  advancing.value = true
  try {
    await processingOrderApi.updateStatus(selectedOrder.value.id, { status: next.next })
    ElMessage.success(`加工单已${next.label}`)
    if (selectedOrder.value) {
      selectedOrder.value.status = next.next
    }
    await loadOrderItems(selectedOrder.value.id)
    await loadData()
  } catch {
    ElMessage.error('状态推进失败')
  } finally {
    advancing.value = false
  }
}

// =============================================================================
// 打印
// =============================================================================

async function handlePrint(po) {
  try {
    await processingOrderApi.markPrinted(po.id)
    const res = await processingOrderApi.getPrintData(po.id)
    if (res.data?.print_url) {
      window.open(res.data.print_url, '_blank')
    } else {
      ElMessage.success('已标记打印')
    }
    if (selectedOrder.value?.id === po.id) {
      selectedOrder.value.printed = true
    }
    await loadData()
  } catch {
    ElMessage.error('打印操作失败')
  }
}

// =============================================================================
// 结算
// =============================================================================

async function handleSettle(po) {
  try {
    await ElMessageBox.confirm(`确认对加工单「${po.po_no}」进行结算？`, '结算确认', { type: 'warning' })
    await processingOrderApi.settle(po.id)
    ElMessage.success('结算成功')
    if (selectedOrder.value?.id === po.id) {
      await loadOrderItems(po.id)
    }
    await loadData()
  } catch {} // cancelled or error
}

// =============================================================================
// 从待生成列表一键生成
// =============================================================================

async function generateFromPending(row) {
  generatingPendingId.value = row.order_id
  try {
    const res = await processingOrderApi.generateFromOrder(row.order_id)
    ElMessage.success(`加工单已生成${res.data?.po_no ? '：' + res.data.po_no : ''}`)
    // 刷新待生成列表和加工单列表
    await Promise.all([loadPendingOrders(), loadData()])
    // 自动切换到加工单列表查看
    activeTab.value = 'list'
  } catch {
    ElMessage.error('生成加工单失败')
  } finally {
    generatingPendingId.value = null
  }
}

function handlePendingRowClick(row) {
  // 点击行跳转到订单详情（可在订单管理页面查看）
  // 当前只做简单交互，无额外操作
}

// =============================================================================
// 重置查询
// =============================================================================

function resetQuery() {
  query.keyword = ''
  query.status = ''
  query.page = 1
  loadData()
}

onMounted(() => {
  loadPendingOrders()
  loadData()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.page-header h3 { font-size: 15px; margin: 0; }

.compact-table { font-size: 12px; }
.compact-table :deep(.el-table__header th) { padding: 2px 0; font-size: 12px; line-height: 1.4; }
.compact-table :deep(.el-table__cell) { padding: 2px 4px; }
.compact-table :deep(.el-table__body td) { padding: 2px 4px; line-height: 1.4; }

:deep(.el-card__body) { padding: 10px 14px; }

/* 从表明细面板 */
.detail-panel {
  margin-top: 12px;
  border-top: 2px solid #3C6E47;
  padding-top: 10px;
}
.empty-detail {
  text-align: center;
  color: #c0c4cc;
  font-size: 13px;
  padding: 30px 0;
}
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 13px;
  flex-wrap: wrap;
  gap: 4px;
}
.detail-actions { margin-left: auto; }

.compact-detail-table { font-size: 12px; }
.compact-detail-table :deep(.el-table__header th) { padding: 2px 0; font-size: 12px; }
.compact-detail-table :deep(.el-table__cell) { padding: 2px 3px; }
.compact-detail-table :deep(.el-table__body td) { padding: 2px 3px; }

.compact-detail-table :deep(.el-input-number--small) { width: 75px; }
.compact-detail-table :deep(.el-input-number--small .el-input__inner) { padding: 0 4px; font-size: 11px; height: 24px; }
.compact-detail-table :deep(.el-checkbox) { vertical-align: middle; }

.generate-section-title {
  font-weight: bold;
  font-size: 13px;
  color: #3C6E47;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
