<template>
  <el-card shadow="never">
    <div class="page-header">
      <h3>售后管理</h3>
      <div class="header-actions">
        <template v-if="stats">
          <el-tag type="danger" style="margin-right:4px" size="small">待审核：{{ stats.pending_review_count }}</el-tag>
          <el-tag type="warning" style="margin-right:4px" size="small">待处理：{{ stats.pending_count }}</el-tag>
          <el-tag type="warning" style="margin-right:4px" size="small">处理中：{{ stats.processing_count }}</el-tag>
          <el-tag type="success" style="margin-right:4px" size="small">已完成：{{ stats.completed_count }}</el-tag>
          <el-divider direction="vertical" />
          <template v-for="(info, key) in stats.by_type" :key="key">
            <el-tag style="margin-right:4px;margin-bottom:2px" size="small" effect="plain">{{ info.label }} {{ info.count }}</el-tag>
          </template>
          <el-divider direction="vertical" />
        </template>
        <el-button type="primary" @click="handleAdd">新建售后单</el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <el-form :inline="true" style="margin-bottom:16px">
      <el-form-item label="状态">
        <el-select v-model="filters.status" clearable style="width:110px" @change="loadData">
          <el-option label="待审核" value="待审核" />
          <el-option label="待处理" value="待处理" />
          <el-option label="处理中" value="处理中" />
          <el-option label="待客户确认" value="待客户确认" />
          <el-option label="已完成" value="已完成" />
          <el-option label="已关闭" value="已关闭" />
        </el-select>
      </el-form-item>
      <el-form-item label="售后类型">
        <el-select v-model="filters.service_type" clearable style="width:120px" @change="loadData">
          <el-option v-for="item in serviceTypeOptions" :key="item.code" :label="item.label" :value="item.code" />
        </el-select>
      </el-form-item>
      <el-form-item label="优先级">
        <el-select v-model="filters.priority" clearable style="width:100px" @change="loadData">
          <el-option label="紧急" value="urgent" />
          <el-option label="高" value="high" />
          <el-option label="普通" value="normal" />
          <el-option label="低" value="low" />
        </el-select>
      </el-form-item>
      <el-form-item label="订单阻塞">
        <el-select v-model="filters.order_hold" clearable style="width:100px" @change="loadData">
          <el-option label="是" :value="true" />
          <el-option label="否" :value="false" />
        </el-select>
      </el-form-item>
      <el-form-item label="日期起">
        <el-date-picker v-model="filters.start_date" type="date" placeholder="创建日期起" value-format="YYYY-MM-DD" style="width:130px" @change="loadData" />
      </el-form-item>
      <el-form-item label="日期止">
        <el-date-picker v-model="filters.end_date" type="date" placeholder="创建日期止" value-format="YYYY-MM-DD" style="width:130px" @change="loadData" />
      </el-form-item>
      <el-form-item label="关键词">
        <el-input v-model="filters.keyword" placeholder="单号/订单号/客户" clearable style="width:200px" @keyup.enter="loadData" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadData">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 列表 -->
    <el-table :data="list" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="service_no" label="售后单号" width="150">
        <template #default="{ row }">
          <el-link type="primary" @click="handleViewDetail(row)">{{ row.service_no }}</el-link>
        </template>
      </el-table-column>
      <el-table-column prop="order_no" label="订单号" width="120" />
      <el-table-column prop="customer_name" label="客户" width="80" />
      <el-table-column prop="service_type_label" label="类型" width="80" />
      <el-table-column label="优先级" width="55" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.priority === 'urgent'" type="danger" size="small">紧急</el-tag>
          <el-tag v-else-if="row.priority === 'high'" type="warning" size="small">高</el-tag>
          <el-tag v-else size="info" effect="plain" style="font-size:11px">{{ row.priority === 'low' ? '低' : '普通' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="阻塞" width="50" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.order_hold" type="danger" size="small" effect="dark">是</el-tag>
          <span v-else style="color:#ccc">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="问题描述" min-width="140" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="handler_name" label="处理人" width="70" />
      <el-table-column label="创建时间" width="130">
        <template #default="{ row }">{{ row.created_at?.slice(0, 16) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" type="primary" @click="handleViewDetail(row)">详情</el-button>
          <el-button
            v-if="row.status === '待审核'"
            text size="small" type="warning"
            @click="handleReview(row)"
          >审核</el-button>
          <el-button
            v-if="row.status === '待处理'"
            text size="small" type="primary"
            @click="handleProcess(row)"
          >处理</el-button>
          <el-button
            v-if="row.status === '处理中'"
            text size="small" type="success"
            @click="handleResolve(row)"
          >完成</el-button>
          <el-button
            v-if="row.status === '待客户确认'"
            text size="small" type="success"
            @click="handleCustomerConfirm(row)"
          >客户确认</el-button>
          <el-button
            v-if="row.status === '待客户确认'"
            text size="small" type="warning"
            @click="handleRejectResolution(row)"
          >不满意</el-button>
          <el-button
            v-if="row.status !== '已完成' && row.status !== '已关闭'"
            text size="small" type="danger"
            @click="handleClose(row)"
          >关闭</el-button>
          <el-button
            v-if="row.order_id"
            text size="small" type="primary"
            @click="handleCreateSupplementary(row)"
          >补单</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="margin-top:16px;text-align:right">
      <el-pagination
        v-model:current-page="filters.page"
        :page-size="filters.page_size"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadData"
      />
    </div>

    <!-- 新建售后单对话框 -->
    <el-dialog v-model="showFormDialog" title="新建售后单" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="关联订单">
          <el-row :gutter="8">
            <el-col :span="10">
              <el-input-number v-model="form.order_id" :min="0" style="width:100%" controls-position="right" placeholder="订单ID" />
            </el-col>
            <el-col :span="14">
              <el-input v-model="form.order_no" placeholder="订单号(选填)" />
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="客户姓名">
          <el-input v-model="form.customer_name" placeholder="如关联订单，自动填充" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.customer_phone" placeholder="如关联订单，自动填充" />
        </el-form-item>
        <el-form-item label="售后类型" required>
          <el-select v-model="form.service_type" style="width:100%" @change="onServiceTypeChange">
            <el-option v-for="item in serviceTypeOptions" :key="item.code" :label="item.label" :value="item.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority" style="width:100%">
            <el-option label="紧急" value="urgent" />
            <el-option label="高" value="high" />
            <el-option label="普通" value="normal" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="阻塞订单">
          <el-switch v-model="form.order_hold" active-text="阻塞关联订单推进" />
        </el-form-item>
        <el-form-item label="问题描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="详细描述售后问题..." />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="500" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">创建</el-button>
      </template>
    </el-dialog>

    <!-- 审核对话框 -->
    <el-dialog v-model="showReviewDialog" :title="'审核售后 - ' + (currentItem?.service_no || '')" width="500px">
      <el-form :model="reviewForm" label-width="90px">
        <el-form-item label="审核意见">
          <el-input v-model="reviewForm.review_remark" type="textarea" :rows="3" placeholder="审核意见..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReviewDialog = false">取消</el-button>
        <el-button type="danger" :loading="reviewing" @click="handleReviewReject">驳回</el-button>
        <el-button type="primary" :loading="reviewing" @click="handleReviewApprove">审核通过</el-button>
      </template>
    </el-dialog>

    <!-- 处理对话框（处理中→待客户确认） -->
    <el-dialog v-model="showProcessDialog" :title="'处理售后 - ' + (currentItem?.service_no || '')" width="600px">
      <el-form :model="processForm" label-width="100px">
        <el-form-item label="处理人">
          <el-input v-model="processForm.handler_name" placeholder="处理人姓名" />
        </el-form-item>
        <el-form-item label="处理方案">
          <el-select v-model="processForm.resolved_type" style="width:100%">
            <el-option label="退款" value="refund" />
            <el-option label="换货" value="replacement" />
            <el-option label="返工" value="rework" />
            <el-option label="退货" value="return" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理结果">
          <el-input v-model="processForm.resolution" type="textarea" :rows="3" placeholder="描述处理结果..." />
        </el-form-item>
        <el-divider />
        <div style="color:#666;font-size:13px;margin-bottom:8px">财务信息（可填）</div>
        <el-form-item label="退款金额">
          <el-input-number v-model="processForm.refund_amount" :precision="2" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="赔偿金额">
          <el-input-number v-model="processForm.compensation_amount" :precision="2" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="返工费用">
          <el-input-number v-model="processForm.rework_cost" :precision="2" :min="0" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showProcessDialog = false">取消</el-button>
        <el-button type="primary" :loading="processing" @click="handleProcessSubmit">确认完成</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="showDetailDialog" :title="'售后详情 - ' + (detailItem?.service_no || '')" width="750px">
      <template v-if="detailItem">
        <el-descriptions :column="2" border style="margin-bottom:16px">
          <el-descriptions-item label="售后单号" :span="2">{{ detailItem.service_no }}</el-descriptions-item>
          <el-descriptions-item label="订单号">{{ detailItem.order_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTag(detailItem.status)" size="small">{{ detailItem.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="客户姓名">{{ detailItem.customer_name }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ detailItem.customer_phone }}</el-descriptions-item>
          <el-descriptions-item label="售后类型" :span="2">{{ detailItem.service_type_label }}</el-descriptions-item>
          <el-descriptions-item label="优先级">
            <el-tag v-if="detailItem.priority === 'urgent'" type="danger" size="small">紧急</el-tag>
            <el-tag v-else-if="detailItem.priority === 'high'" type="warning" size="small">高</el-tag>
            <span v-else>{{ detailItem.priority === 'low' ? '低' : '普通' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="来源">{{ detailItem.source || 'manual' }}</el-descriptions-item>
          <el-descriptions-item label="阻塞订单">
            <el-tag v-if="detailItem.order_hold" type="danger" size="small">是</el-tag>
            <span v-else>否</span>
          </el-descriptions-item>
          <el-descriptions-item label="问题描述" :span="2">{{ detailItem.description || '-' }}</el-descriptions-item>
        </el-descriptions>

        <el-descriptions v-if="detailItem.status !== '待审核'" :column="2" border style="margin-bottom:16px">
          <template #title>
            <span style="font-weight:bold">审核信息</span>
          </template>
          <el-descriptions-item label="审核人">{{ detailItem.reviewer_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审核时间">{{ detailItem.reviewed_at?.slice(0,16) || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审核意见" :span="2">{{ detailItem.review_remark || '-' }}</el-descriptions-item>
        </el-descriptions>

        <el-descriptions v-if="detailItem.status !== '待审核' && detailItem.status !== '待处理'" :column="2" border style="margin-bottom:16px">
          <template #title>
            <span style="font-weight:bold">处理信息</span>
          </template>
          <el-descriptions-item label="处理人">{{ detailItem.handler_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="处理方案">{{ resolvedTypeLabel(detailItem.resolved_type) }}</el-descriptions-item>
          <el-descriptions-item label="处理时间">{{ detailItem.resolved_at?.slice(0,16) || '-' }}</el-descriptions-item>
          <el-descriptions-item label="处理结果" :span="2">{{ detailItem.resolution || '-' }}</el-descriptions-item>
        </el-descriptions>

        <el-descriptions v-if="detailItem.refund_amount > 0 || detailItem.compensation_amount > 0 || detailItem.rework_cost > 0" :column="3" border style="margin-bottom:16px">
          <template #title>
            <span style="font-weight:bold">财务信息</span>
          </template>
          <el-descriptions-item label="退款金额" v-if="detailItem.refund_amount > 0">
            <span style="color:#f56c6c">¥{{ detailItem.refund_amount.toFixed(2) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="赔偿金额" v-if="detailItem.compensation_amount > 0">
            <span style="color:#e6a23c">¥{{ detailItem.compensation_amount.toFixed(2) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="返工费用" v-if="detailItem.rework_cost > 0">
            <span style="color:#909399">¥{{ detailItem.rework_cost.toFixed(2) }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="客户确认">
            <el-tag v-if="detailItem.customer_confirmed" type="success" size="small">已确认</el-tag>
            <span v-else>未确认</span>
          </el-descriptions-item>
          <el-descriptions-item label="确认时间">{{ detailItem.customer_confirmed_at?.slice(0,16) || '-' }}</el-descriptions-item>
          <el-descriptions-item label="关闭时间">{{ detailItem.closed_at?.slice(0,16) || '-' }}</el-descriptions-item>
          <el-descriptions-item label="驳回时间">{{ detailItem.rejected_at?.slice(0,16) || '-' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detailItem.remark || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ detailItem.created_at?.slice(0,16) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ detailItem.updated_at?.slice(0,16) }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { afterSaleApi, orderApi, systemApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const list = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const processing = ref(false)
const reviewing = ref(false)
const stats = ref(null)
const serviceTypeOptions = ref([])

const filters = reactive({
  status: '', service_type: '', keyword: '',
  start_date: '', end_date: '',
  priority: '', order_hold: null,
  page: 1, page_size: 20,
})

const form = reactive({
  order_id: null, order_no: '', customer_name: '', customer_phone: '',
  service_type: '', service_type_label: '', description: '',
  priority: 'normal', source: 'manual', order_hold: false, remark: '',
})

const processForm = reactive({
  handler_name: '', resolution: '', resolved_type: '',
  refund_amount: 0, compensation_amount: 0, rework_cost: 0,
})

const reviewForm = reactive({
  review_remark: '',
})

const showFormDialog = ref(false)
const showReviewDialog = ref(false)
const showProcessDialog = ref(false)
const showDetailDialog = ref(false)
const currentItem = ref(null)
const detailItem = ref(null)

function statusTag(status) {
  const map = {
    '待审核': 'danger',
    '待处理': 'warning',
    '处理中': '',
    '待客户确认': 'primary',
    '已完成': 'success',
    '已关闭': 'info',
  }
  return map[status] || 'info'
}

function resolvedTypeLabel(type) {
  const map = { refund: '退款', replacement: '换货', rework: '返工', return: '退货', other: '其他' }
  return map[type] || type || '-'
}

async function loadServiceTypeOptions() {
  try {
    const res = await systemApi.getDict('after_sale_category')
    serviceTypeOptions.value = Array.isArray(res.data) ? res.data : []
  } catch {}
}

async function loadData() {
  loading.value = true
  try {
    const params = {}
    if (filters.status) params.status = filters.status
    if (filters.service_type) params.service_type = filters.service_type
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.start_date) params.start_date = filters.start_date
    if (filters.end_date) params.end_date = filters.end_date
    if (filters.priority) params.priority = filters.priority
    if (filters.order_hold !== null && filters.order_hold !== '') params.order_hold = filters.order_hold
    params.page = filters.page
    params.page_size = filters.page_size
    const res = await afterSaleApi.list(params)
    list.value = res.items || []
    total.value = res.total || 0
  } catch {} finally { loading.value = false }
}

async function loadStats() {
  try {
    const res = await afterSaleApi.stats()
    stats.value = res.data
  } catch {}
}

function onServiceTypeChange(code) {
  const opt = serviceTypeOptions.value.find(o => o.code === code)
  form.service_type_label = opt ? opt.label : code
}

function resetForm() {
  form.order_id = null
  form.order_no = ''
  form.customer_name = ''
  form.customer_phone = ''
  form.service_type = ''
  form.service_type_label = ''
  form.description = ''
  form.priority = 'normal'
  form.source = 'manual'
  form.order_hold = false
  form.remark = ''
}

function resetFilters() {
  filters.status = ''
  filters.service_type = ''
  filters.keyword = ''
  filters.start_date = ''
  filters.end_date = ''
  filters.priority = ''
  filters.order_hold = null
  filters.page = 1
  loadData()
}

function handleAdd() {
  resetForm()
  showFormDialog.value = true
}

async function handleSave() {
  if (!form.service_type) {
    ElMessage.warning('请选择售后类型')
    return
  }
  saving.value = true
  try {
    await afterSaleApi.create(form)
    ElMessage.success('售后单创建成功')
    showFormDialog.value = false
    loadData()
    loadStats()
  } catch (e) {
    ElMessage.error(e.message || '创建失败')
  } finally { saving.value = false }
}

function handleViewDetail(row) {
  detailItem.value = row
  showDetailDialog.value = true
}

// ── 审核 ──

function handleReview(row) {
  currentItem.value = row
  reviewForm.review_remark = ''
  showReviewDialog.value = true
}

async function handleReviewApprove() {
  reviewing.value = true
  try {
    await afterSaleApi.update(currentItem.value.id, {
      status: '待处理',
      reviewer_name: reviewForm.review_remark ? undefined : '',
      review_remark: reviewForm.review_remark || undefined,
    })
    ElMessage.success('审核通过，已转为待处理')
    showReviewDialog.value = false
    loadData()
    loadStats()
  } catch (e) {
    ElMessage.error(e.message || '审核失败')
  } finally { reviewing.value = false }
}

async function handleReviewReject() {
  reviewing.value = true
  try {
    await afterSaleApi.update(currentItem.value.id, {
      status: '已关闭',
      review_remark: reviewForm.review_remark || undefined,
    })
    ElMessage.success('已驳回并关闭售后单')
    showReviewDialog.value = false
    loadData()
    loadStats()
  } catch (e) {
    ElMessage.error(e.message || '驳回失败')
  } finally { reviewing.value = false }
}

// ── 处理 ──

function handleProcess(row) {
  currentItem.value = row
  processForm.handler_name = ''
  processForm.resolution = ''
  processForm.resolved_type = ''
  processForm.refund_amount = 0
  processForm.compensation_amount = 0
  processForm.rework_cost = 0
  showProcessDialog.value = true
}

function handleResolve(row) {
  currentItem.value = row
  processForm.handler_name = row.handler_name || ''
  processForm.resolution = row.resolution || ''
  processForm.resolved_type = row.resolved_type || ''
  processForm.refund_amount = row.refund_amount || 0
  processForm.compensation_amount = row.compensation_amount || 0
  processForm.rework_cost = row.rework_cost || 0
  showProcessDialog.value = true
}

async function handleProcessSubmit() {
  if (!processForm.handler_name) {
    ElMessage.warning('请输入处理人')
    return
  }
  processing.value = true
  try {
    const isResolve = currentItem.value.status === '处理中'
    const data = {
      status: isResolve ? '待客户确认' : '处理中',
      handler_name: processForm.handler_name,
      resolution: processForm.resolution || undefined,
      resolved_type: processForm.resolved_type || undefined,
      refund_amount: processForm.refund_amount > 0 ? processForm.refund_amount : undefined,
      compensation_amount: processForm.compensation_amount > 0 ? processForm.compensation_amount : undefined,
      rework_cost: processForm.rework_cost > 0 ? processForm.rework_cost : undefined,
    }
    await afterSaleApi.update(currentItem.value.id, data)
    ElMessage.success(isResolve ? '售后已完成处理，等待客户确认' : '已标记为处理中')
    showProcessDialog.value = false
    loadData()
    loadStats()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally { processing.value = false }
}

// ── 客户确认 ──

async function handleCustomerConfirm(row) {
  try {
    await afterSaleApi.update(row.id, { status: '已完成' })
    ElMessage.success('客户已确认，售后完成')
    loadData()
    loadStats()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

async function handleRejectResolution(row) {
  try {
    await afterSaleApi.update(row.id, { status: '处理中' })
    ElMessage.success('已退回处理环节')
    loadData()
    loadStats()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

// ── 关闭 ──

async function handleClose(row) {
  try {
    await ElMessageBox.confirm(`确定关闭售后单「${row.service_no}」？`, '确认关闭', { type: 'warning' })
    await afterSaleApi.update(row.id, { status: '已关闭' })
    ElMessage.success('售后单已关闭')
    loadData()
    loadStats()
  } catch {}
}

// ── 补单 ──

async function handleCreateSupplementary(row) {
  try {
    await ElMessageBox.confirm(
      `确定为订单 #${row.order_id} 生成售后补单？`,
      '生成补单',
      { type: 'info' }
    )
    const res = await orderApi.createSupplementary(row.order_id)
    ElMessage.success(`补单已生成${res.data?.order_no ? '：' + res.data.order_no : ''}`)
    loadData()
  } catch (e) {
    if (e) ElMessage.error(e.message || '生成补单失败')
  }
}

// ── 加载完成 ──

onMounted(() => {
  loadData()
  loadStats()
  loadServiceTypeOptions()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.page-header h3 { font-size: 18px; }
.header-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }
</style>
