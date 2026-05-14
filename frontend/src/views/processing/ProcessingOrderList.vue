<template>
  <el-card shadow="never">
    <div class="page-header">
      <h3>加工单管理</h3>
      <div>
        <el-button type="primary" size="small" @click="openGenerateDialog">生成加工单</el-button>
        <el-button size="small" @click="loadData">刷新</el-button>
      </div>
    </div>

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
          <p style="margin:0;font-size:12px;color:#bbb">订单采购收货完成后，系统会自动生成加工单</p>
          <p style="margin:0;font-size:12px;color:#bbb">也可点击上方「生成加工单」按钮手动从订单创建</p>
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
  </el-card>

  <!-- 生成加工单对话框 -->
  <el-dialog v-model="showGenerateDialog" title="生成加工单" width="800px" top="5vh" :close-on-click-modal="false" @closed="resetGenerateDialog">
    <el-form :inline="true" size="small" style="margin-bottom:12px">
      <el-form-item label="订单号">
        <el-input v-model="searchOrderNo" placeholder="输入订单号搜索" style="width:200px" @keyup.enter="handleSearchOrder" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearchOrder" :loading="searchingOrder">搜索</el-button>
        <el-button @click="resetGenerateDialog">清空</el-button>
      </el-form-item>
    </el-form>

    <template v-if="foundOrder">
      <el-alert :closable="false" type="success" style="margin-bottom:12px">
        <template #title>
          已找到订单 <strong>{{ foundOrder.order_no }}</strong>
          <span v-if="foundOrder.customer_name"> — {{ foundOrder.customer_name }}</span>
          <el-tag :color="foundOrder.status_color" style="color:#fff;border:0;margin-left:8px" size="small">{{ foundOrder.status_label }}</el-tag>
        </template>
      </el-alert>

      <div class="generate-section-title">
        <span>可生成的物料明细（{{ generateItems.length }} 项）</span>
        <span v-if="generateItems.length === 0" style="color:#909399;font-size:12px">该订单没有物料类型的明细</span>
      </div>
      <el-table v-if="generateItems.length > 0" :data="generateItems" size="small" stripe style="width:100%" class="compact-table">
        <el-table-column type="index" label="序号" width="45" />
        <el-table-column prop="product_code" label="编码" width="100" />
        <el-table-column prop="product_name" label="产品名称" width="130" show-overflow-tooltip />
        <el-table-column label="规格" width="90">
          <template #default="{ row }">
            {{ row.width ? row.width : '-' }}×{{ row.height ? row.height : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="qty" label="数量" width="60" align="center" />
        <el-table-column prop="unit" label="单位" width="50" align="center" />
        <el-table-column prop="process_desc" label="工艺描述" width="120" show-overflow-tooltip />
        <el-table-column prop="remark" label="备注" width="100" show-overflow-tooltip />
      </el-table>
    </template>

    <div v-if="searchNoResult" style="text-align:center;padding:32px;color:#909399;font-size:13px">
      未找到匹配的订单，请确认订单号是否正确
    </div>

    <template #footer>
      <el-button @click="showGenerateDialog = false">取消</el-button>
      <el-button type="primary" :loading="generating" :disabled="!foundOrder || generateItems.length === 0" @click="handleConfirmGenerate">
        确认生成
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { orderApi, processingOrderApi } from '@/api'
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

// ── 生成加工单对话框 ──
const showGenerateDialog = ref(false)
const searchOrderNo = ref('')
const searchingOrder = ref(false)
const foundOrder = ref(null)
const generateItems = ref([])
const searchNoResult = ref(false)
const generating = ref(false)

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
// 生成加工单
// =============================================================================

function openGenerateDialog() {
  showGenerateDialog.value = true
  searchOrderNo.value = ''
  foundOrder.value = null
  generateItems.value = []
  searchNoResult.value = false
}

function resetGenerateDialog() {
  searchOrderNo.value = ''
  foundOrder.value = null
  generateItems.value = []
  searchNoResult.value = false
}

async function handleSearchOrder() {
  const keyword = searchOrderNo.value.trim()
  if (!keyword) { ElMessage.warning('请输入订单号'); return }

  searchingOrder.value = true
  searchNoResult.value = false
  foundOrder.value = null
  generateItems.value = []
  try {
    const res = await orderApi.list({ keyword, page_size: 10 })
    const orders = res.items || []
    // 精确匹配优先，否则取第一条
    const match = orders.find(o => o.order_no === keyword) || orders[0]

    if (!match) {
      searchNoResult.value = true
      return
    }

    const detail = await orderApi.get(match.id)
    const orderDetail = detail.data || detail
    foundOrder.value = orderDetail
    generateItems.value = (orderDetail.items || []).filter(
      i => i.procurement_type === '物料'
    )
    if (generateItems.value.length === 0) {
      ElMessage.warning('该订单没有物料类型的明细，无法生成加工单')
    }
  } catch {
    searchNoResult.value = true
  } finally {
    searchingOrder.value = false
  }
}

async function handleConfirmGenerate() {
  if (!foundOrder.value) return
  if (generateItems.value.length === 0) { ElMessage.warning('该订单没有可生成的物料明细'); return }

  generating.value = true
  try {
    const res = await processingOrderApi.generateFromOrder(foundOrder.value.id)
    ElMessage.success(`加工单已生成${res.data?.po_no ? '：' + res.data.po_no : ''}`)
    showGenerateDialog.value = false
    await loadData()
  } catch {
    ElMessage.error('生成加工单失败')
  } finally {
    generating.value = false
  }
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

onMounted(loadData)
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
