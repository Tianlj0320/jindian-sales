<template>
  <el-card shadow="never">
    <div class="page-header">
      <h3>生产反馈</h3>
      <div>
        <el-tag v-if="stats" type="warning" style="margin-right:8px">待处理：{{ stats.pending }}</el-tag>
        <el-tag v-if="stats" type="primary" style="margin-right:8px">处理中：{{ stats.processing }}</el-tag>
        <el-button type="primary" @click="showDialog = true; resetFeedbackForm()">提交反馈</el-button>
      </div>
    </div>

    <!-- 搜索/筛选 -->
    <el-form :inline="true" style="margin-bottom:16px">
      <el-form-item label="订单ID">
        <el-input-number v-model="query.order_id" :min="0" style="width:120px" controls-position="right" />
      </el-form-item>
      <el-form-item label="类型">
        <el-select v-model="query.feedback_type" clearable style="width:110px" @change="loadData">
          <el-option label="质量问题" value="quality" />
          <el-option label="面料残次" value="defect" />
          <el-option label="米数不足" value="shortage" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="query.status" clearable style="width:100px" @change="loadData">
          <el-option label="待处理" value="待处理" />
          <el-option label="处理中" value="处理中" />
          <el-option label="已解决" value="已解决" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadData">查询</el-button>
        <el-button @click="query = { page: 1, page_size: 20 }; loadData()">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 反馈列表 -->
    <el-table :data="list" v-loading="loading" stripe style="width:100%">
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
      <el-pagination v-model:current-page="query.page" :page-size="query.page_size" :total="total" layout="total, prev, pager, next" @current-change="loadData" />
    </div>

    <!-- 新建反馈对话框 -->
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

    <!-- 处理对话框 -->
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
        <el-button type="primary" :loading="processing" @click="handleProcessSubmit">确认</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { productionApi } from '@/api'
import { ElMessage } from 'element-plus'

const list = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const processing = ref(false)
const showDialog = ref(false)
const showProcessDialog = ref(false)
const currentFeedback = ref(null)
const stats = ref(null)

const query = reactive({ order_id: null, feedback_type: '', status: '', page: 1, page_size: 20 })
const fbForm = reactive({ order_id: 1, order_no: '', feedback_type: 'quality', description: '' })
const processForm = reactive({ resolver: '', resolution: '' })

function resetFeedbackForm() {
  fbForm.order_id = 1
  fbForm.order_no = ''
  fbForm.feedback_type = 'quality'
  fbForm.description = ''
}

async function loadData() {
  loading.value = true
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
  } catch {} finally { loading.value = false }
}

async function loadStats() {
  try {
    const res = await productionApi.stats()
    stats.value = res.data
  } catch {}
}

async function handleCreateFeedback() {
  if (!fbForm.order_id) { ElMessage.warning('请输入关联订单ID'); return }
  if (!fbForm.description) { ElMessage.warning('请描述问题'); return }
  saving.value = true
  try {
    await productionApi.createFeedback({ ...fbForm })
    ElMessage.success('反馈已提交')
    showDialog.value = false
    loadData()
    loadStats()
  } catch {} finally { saving.value = false }
}

function handleProcess(row) {
  currentFeedback.value = row
  processForm.resolver = ''
  processForm.resolution = ''
  showProcessDialog.value = true
}

async function handleProcessSubmit() {
  if (!processForm.resolver) { ElMessage.warning('请输入处理人'); return }
  processing.value = true
  try {
    await productionApi.updateFeedback(currentFeedback.value.id, {
      status: '处理中',
      resolver: processForm.resolver,
      resolution: processForm.resolution,
    })
    ElMessage.success('已标记为处理中')
    showProcessDialog.value = false
    loadData()
  } catch {} finally { processing.value = false }
}

function handleResolve(row) {
  currentFeedback.value = row
  processForm.resolver = row.resolver || ''
  processForm.resolution = row.resolution || ''
  showProcessDialog.value = true
}

onMounted(() => {
  loadData()
  loadStats()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h3 { font-size: 18px; }
</style>
