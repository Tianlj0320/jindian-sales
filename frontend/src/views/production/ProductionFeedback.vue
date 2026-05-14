<template>
  <el-card shadow="never">
    <template #header>
      <div class="page-header">
        <h3>生产管理</h3>
        <div class="header-actions">
          <!-- 统计徽章 -->
          <template v-if="stats">
            <el-tag type="danger" style="margin-right:4px" size="small">待处理 {{ stats.pending }}</el-tag>
            <el-tag type="warning" style="margin-right:4px" size="small">处理中 {{ stats.processing }}</el-tag>
            <el-tag type="success" style="margin-right:4px" size="small">已解决 {{ stats.resolved }}</el-tag>
            <el-divider direction="vertical" />
            <el-tag style="margin-right:4px" size="small" type="danger" effect="plain">质量 {{ stats.by_type?.quality || 0 }}</el-tag>
            <el-tag style="margin-right:4px" size="small" type="warning" effect="plain">残次 {{ stats.by_type?.defect || 0 }}</el-tag>
            <el-tag style="margin-right:4px" size="small" type="info" effect="plain">米数不足 {{ stats.by_type?.shortage || 0 }}</el-tag>
            <el-divider direction="vertical" />
          </template>
          <el-button type="primary" @click="showDialog = true; resetFeedbackForm()">提交反馈</el-button>
          <el-button @click="showPrintDialog = true">打印加工单</el-button>
          <el-button :type="tab === 'feedback' ? 'primary' : 'default'" @click="tab = 'feedback'">生产反馈</el-button>
          <el-button :type="tab === 'processing' ? 'primary' : 'default'" @click="tab = 'processing'; loadProcessingOrders()">加工流转</el-button>
        </div>
      </div>
    </template>

    <!-- ═══════════════  生产反馈  ═══════════════ -->
    <div v-show="tab === 'feedback'">
      <!-- 搜索/筛选 -->
      <el-form :inline="true" style="margin-bottom:16px">
        <el-form-item label="订单ID">
          <el-input-number v-model="query.order_id" :min="0" style="width:120px" controls-position="right" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="query.feedback_type" clearable style="width:110px" @change="loadFeedback">
            <el-option label="质量问题" value="quality" />
            <el-option label="面料残次" value="defect" />
            <el-option label="米数不足" value="shortage" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" clearable style="width:100px" @change="loadFeedback">
            <el-option label="待处理" value="待处理" />
            <el-option label="处理中" value="处理中" />
            <el-option label="已解决" value="已解决" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadFeedback">查询</el-button>
          <el-button @click="query = { page: 1, page_size: 20 }; loadFeedback()">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 反馈列表 -->
      <el-table :data="list" v-loading="loadingFeedback" stripe style="width:100%">
        <el-table-column prop="feedback_no" label="编号" width="130" />
        <el-table-column prop="order_no" label="订单号" width="120" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag :type="row.feedback_type === 'quality' ? 'danger' : row.feedback_type === 'defect' ? 'warning' : 'info'" size="small">
              {{ { quality: '质量', defect: '残次', shortage: '米数不足' }[row.feedback_type] || row.feedback_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="问题描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === '待处理' ? 'danger' : row.status === '处理中' ? 'warning' : 'success'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resolver" label="处理人" width="80" />
        <el-table-column prop="resolution" label="处理方案" min-width="160" show-overflow-tooltip />
        <el-table-column label="创建时间" width="150">
          <template #default="{ row }">{{ row.created_at?.slice(0, 16) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === '待处理'" text size="small" type="primary" @click="handleProcess(row)">处理</el-button>
            <el-button v-if="row.status === '处理中'" text size="small" type="success" @click="handleResolve(row)">解决</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top:16px;text-align:right">
        <el-pagination v-model:current-page="query.page" :page-size="query.page_size" :total="total" layout="total, prev, pager, next" @current-change="loadFeedback" />
      </div>
    </div>

    <!-- ═══════════════  加工流转  ═══════════════ -->
    <div v-show="tab === 'processing'">
      <el-form :inline="true" style="margin-bottom:16px">
        <el-form-item label="搜索">
          <el-input v-model="procKeyword" placeholder="订单号/客户" clearable style="width:220px" @clear="loadProcessingOrders" @keyup.enter="loadProcessingOrders" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="procStatusKey" style="width:120px" @change="loadProcessingOrders">
            <el-option label="生产中" value="processing" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadProcessingOrders">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="processingOrders" v-loading="loadingProcessing" stripe style="width:100%">
        <el-table-column prop="order_no" label="订单号" width="140" />
        <el-table-column prop="customer_name" label="客户" width="100" />
        <el-table-column prop="customer_phone" label="电话" width="120" />
        <el-table-column prop="order_date" label="订单日期" width="100">
          <template #default="{ row }">{{ row.order_date?.slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column prop="content" label="产品内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="item_count" label="明细数" width="70" align="center" />
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :color="row.status_color || ''" size="small" effect="dark" style="border:0">
              {{ row.status_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="反馈数" width="70" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.feedback_count > 0" type="danger" size="small" effect="plain">{{ row.feedback_count }}</el-tag>
            <span v-else style="color:#999">0</span>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="100" align="right">
          <template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" type="primary" @click="handlePrintProcessingByOrder(row)">打印加工单</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!processingOrders.length && !loadingProcessing" style="text-align:center;padding:40px 0;color:#999">
        暂无加工流转中的订单
      </div>
    </div>

    <!-- ═══ 新建反馈对话框 ═══ -->
    <el-dialog v-model="showDialog" title="提交生产反馈" width="550px">
      <el-form :model="fbForm" label-width="100px">
        <el-form-item label="关联订单">
          <el-row :gutter="8">
            <el-col :span="10">
              <el-input-number v-model="fbForm.order_id" :min="1" style="width:100%" controls-position="right" placeholder="订单ID" />
            </el-col>
            <el-col :span="14">
              <el-input v-model="fbForm.order_no" placeholder="订单号(选填)" />
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="问题类型">
          <el-select v-model="fbForm.feedback_type" style="width:100%">
            <el-option label="面料质量问题" value="quality" />
            <el-option label="面料残次" value="defect" />
            <el-option label="米数不足" value="shortage" />
          </el-select>
        </el-form-item>
        <el-form-item label="问题描述">
          <el-input v-model="fbForm.description" type="textarea" :rows="3" placeholder="详细描述问题情况..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreateFeedback">提交</el-button>
      </template>
    </el-dialog>

    <!-- ═══ 处理/解决对话框 ═══ -->
    <el-dialog v-model="showProcessDialog" :title="'处理反馈 - ' + (currentFeedback?.feedback_no || '')" width="450px">
      <el-form :model="processForm" label-width="80px">
        <el-form-item label="处理人">
          <el-input v-model="processForm.resolver" placeholder="处理人姓名" />
        </el-form-item>
        <el-form-item label="处理方案">
          <el-input v-model="processForm.resolution" type="textarea" :rows="3" placeholder="描述处理方案..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showProcessDialog = false">取消</el-button>
        <el-button type="primary" :loading="processingSave" @click="handleProcessSubmit">确认</el-button>
      </template>
    </el-dialog>

    <!-- ═══ 打印加工单对话框 ═══ -->
    <el-dialog v-model="showPrintDialog" title="打印加工单" width="400px" top="30vh">
      <el-form label-width="80px">
        <el-form-item label="订单编号" required>
          <el-input v-model="printOrderNo" placeholder="输入订单号" @keyup.enter="handlePrintProcessing" />
        </el-form-item>
        <p style="color:#999;font-size:13px;margin:0">输入订单号后点击确认，预览并打印加工单</p>
      </el-form>
      <template #footer>
        <el-button @click="showPrintDialog = false">取消</el-button>
        <el-button type="primary" :loading="loadingPrintOrder" @click="handlePrintProcessing">确认</el-button>
      </template>
    </el-dialog>

    <!-- ═══ 打印预览 ═══ -->
    <el-dialog v-model="showPrintPreview" :title="`打印预览 - ${printDocType}`" width="95%" top="2vh"
      :close-on-click-modal="false" destroy-on-close>
      <div class="pv-wrap">
        <div class="pv-bar">
          <span class="pv-label">{{ printDocType }}</span>
          <span class="pv-info">A4 / 纵向</span>
          <div class="pv-spacer"></div>
          <el-button type="primary" :disabled="!iframeReady" @click="doPrint">打印</el-button>
          <el-button @click="showPrintPreview = false">关闭</el-button>
        </div>
        <div class="pv-body">
          <div class="pv-paper">
            <iframe ref="iframeRef" :srcdoc="printHtml" class="pv-frame"
              @load="iframeReady = true" frameborder="0"></iframe>
          </div>
        </div>
      </div>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { productionApi, orderApi } from '@/api'
import { ElMessage } from 'element-plus'
import { generateProcessingHtml } from '@/utils/print'

// ── Tab 切换 ──
const tab = ref('feedback')

// ── 反馈列表 ──
const list = ref([])
const total = ref(0)
const loadingFeedback = ref(false)
const stats = ref(null)

const query = reactive({ order_id: null, feedback_type: '', status: '', page: 1, page_size: 20 })

async function loadFeedback() {
  loadingFeedback.value = true
  try {
    const params = {}
    if (query.order_id) params.order_id = query.order_id
    if (query.feedback_type) params.feedback_type = query.feedback_type
    if (query.status) params.status = query.status
    params.page = query.page
    params.page_size = query.page_size
    const res = await productionApi.listFeedbacks(params)
    list.value = res.items || []
    total.value = res.total || 0
  } catch {} finally { loadingFeedback.value = false }
}

async function loadStats() {
  try {
    const res = await productionApi.stats()
    stats.value = res.data
  } catch {}
}

// ── 创建反馈 ──
const showDialog = ref(false)
const saving = ref(false)
const fbForm = reactive({ order_id: 1, order_no: '', feedback_type: 'quality', description: '' })

function resetFeedbackForm() {
  fbForm.order_id = 1
  fbForm.order_no = ''
  fbForm.feedback_type = 'quality'
  fbForm.description = ''
}

async function handleCreateFeedback() {
  if (!fbForm.order_id) { ElMessage.warning('请输入关联订单ID'); return }
  if (!fbForm.description) { ElMessage.warning('请描述问题'); return }
  saving.value = true
  try {
    await productionApi.createFeedback({ ...fbForm })
    ElMessage.success('反馈已提交')
    showDialog.value = false
    loadFeedback()
    loadStats()
  } catch {} finally { saving.value = false }
}

// ── 处理 / 解决 ──
const showProcessDialog = ref(false)
const processingSave = ref(false)
const currentFeedback = ref(null)
const processForm = reactive({ resolver: '', resolution: '' })

function handleProcess(row) {
  currentFeedback.value = row
  processForm.resolver = ''
  processForm.resolution = ''
  showProcessDialog.value = true
}

async function handleProcessSubmit() {
  if (!processForm.resolver) { ElMessage.warning('请输入处理人'); return }
  processingSave.value = true
  try {
    const isResolve = currentFeedback.value.status === '处理中'
    await productionApi.updateFeedback(currentFeedback.value.id, {
      status: isResolve ? '已解决' : '处理中',
      resolver: processForm.resolver,
      resolution: processForm.resolution,
    })
    ElMessage.success(isResolve ? '已标记为已解决' : '已标记为处理中')
    showProcessDialog.value = false
    loadFeedback()
    loadStats()
  } catch {} finally { processingSave.value = false }
}

function handleResolve(row) {
  currentFeedback.value = row
  processForm.resolver = row.resolver || ''
  processForm.resolution = row.resolution || ''
  showProcessDialog.value = true
}

// ── 加工流转 ──
const processingOrders = ref([])
const loadingProcessing = ref(false)
const procKeyword = ref('')
const procStatusKey = ref('processing')

async function loadProcessingOrders() {
  loadingProcessing.value = true
  try {
    const params = { status_key: procStatusKey.value }
    if (procKeyword.value.trim()) params.keyword = procKeyword.value.trim()
    const res = await productionApi.processingOrders(params)
    processingOrders.value = res.data || []
  } catch {} finally { loadingProcessing.value = false }
}

// ── 打印加工单 ──
const showPrintDialog = ref(false)
const showPrintPreview = ref(false)
const printOrderNo = ref('')
const loadingPrintOrder = ref(false)
const printHtml = ref('')
const printDocType = ref('')
const iframeReady = ref(false)
const iframeRef = ref(null)

async function handlePrintProcessing() {
  if (!printOrderNo.value.trim()) {
    ElMessage.warning('请输入订单号')
    return
  }
  loadingPrintOrder.value = true
  try {
    const res = await orderApi.list({ keyword: printOrderNo.value.trim(), page_size: 1 })
    const orders = res.items || []
    if (!orders.length) {
      ElMessage.warning('未找到该订单')
      return
    }
    await doPrintOrder(orders[0].id)
  } catch {
    ElMessage.warning('无法加载订单数据')
  } finally {
    loadingPrintOrder.value = false
  }
}

/** 从加工流转列表点击打印 */
async function handlePrintProcessingByOrder(row) {
  loadingPrintOrder.value = true
  try {
    await doPrintOrder(row.id)
  } catch {
    ElMessage.warning('无法加载订单数据')
  } finally {
    loadingPrintOrder.value = false
  }
}

async function doPrintOrder(orderId) {
  const orderRes = await orderApi.get(orderId)
  const order = orderRes.data
  if (!order) { ElMessage.warning('订单数据不存在'); return }
  printHtml.value = generateProcessingHtml(order)
  printDocType.value = '加工单'
  iframeReady.value = false
  showPrintDialog.value = false
  showPrintPreview.value = true
  printOrderNo.value = ''
}

function doPrint() {
  const el = iframeRef.value
  if (el && el.contentWindow) {
    el.contentWindow.focus()
    el.contentWindow.print()
  }
}

// ── 初始化 ──
onMounted(() => {
  loadFeedback()
  loadStats()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.page-header h3 { font-size: 18px; }
.header-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }
.pv-wrap { display: flex; flex-direction: column; }
.pv-bar { display: flex; align-items: center; padding: 0 0 10px 0; gap: 8px; border-bottom: 1px solid #e8e8e8; margin-bottom: 10px; }
.pv-label { font-weight: bold; font-size: 15px; }
.pv-info { color: #999; font-size: 12px; }
.pv-spacer { flex: 1; }
.pv-body { flex: 1; overflow: auto; background: #e8e8e8; display: flex; justify-content: center; padding: 20px; border-radius: 4px; min-height: 65vh; }
.pv-paper { width: 210mm; min-height: 297mm; background: #fff; box-shadow: 0 2px 12px rgba(0,0,0,0.12); }
.pv-frame { width: 210mm; height: 297mm; border: none; display: block; }
</style>
