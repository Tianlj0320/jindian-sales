<template>
  <div>
    <!-- 登记定金 -->
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <h3>定金管理</h3>
        </div>
      </template>
      <el-form :inline="true" size="small" class="deposit-form">
        <el-form-item label="客户" required>
          <el-autocomplete
            v-model="createForm.customer_name"
            :fetch-suggestions="searchCustomers"
            placeholder="输入客户名称搜索"
            style="width:180px"
            :trigger-on-focus="false"
            clearable
            @select="handleCustomerSelect"
          />
        </el-form-item>
        <el-form-item label="金额" required>
          <el-input-number v-model="createForm.amount" :precision="2" :min="0.01" :step="100" :max="9999999" style="width:140px" />
        </el-form-item>
        <el-form-item label="方式" required>
          <el-select v-model="createForm.payment_method" placeholder="选择方式" style="width:105px">
            <el-option label="微信" value="微信" />
            <el-option label="支付宝" value="支付宝" />
            <el-option label="现金" value="现金" />
            <el-option label="银行转账" value="银行转账" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="createForm.received_at" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width:135px" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.remark" placeholder="备注" style="width:140px" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="creating" @click="handleCreateDeposit">登记定金</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 客户余额卡片 -->
    <el-card v-if="balanceData" shadow="never" style="margin-top:12px">
      <div class="balance-card">
        <span class="balance-label">{{ balanceData.customer_name }}</span>
        <span class="balance-sub-label">定金余额</span>
        <span class="balance-value" :style="{ color: balanceData.balance >= 0 ? '#3C6E47' : '#f56c6c' }">
          ¥{{ (balanceData.balance || 0).toFixed(2) }}
        </span>
      </div>
    </el-card>

    <!-- 定金记录列表 -->
    <el-card shadow="never" style="margin-top:12px">
      <template #header>
        <div class="section-header">
          <span>定金记录</span>
          <div class="filter-group">
            <el-input v-model="query.keyword" placeholder="搜索客户" clearable style="width:150px" size="small" @clear="loadList" @keyup.enter="loadList" />
            <el-date-picker v-model="query.date_from" type="date" placeholder="开始日期" value-format="YYYY-MM-DD" style="width:135px" size="small" @change="loadList" />
            <el-date-picker v-model="query.date_to" type="date" placeholder="结束日期" value-format="YYYY-MM-DD" style="width:135px" size="small" @change="loadList" />
            <el-button type="primary" size="small" @click="loadList">查询</el-button>
          </div>
        </div>
      </template>
      <el-table :data="list" v-loading="loading" stripe style="width:100%" size="small" class="compact-table">
        <el-table-column type="index" label="序号" width="50" />
        <el-table-column prop="received_at" label="日期" width="100" />
        <el-table-column prop="customer_name" label="客户" width="120" show-overflow-tooltip />
        <el-table-column prop="amount" label="金额" width="110" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.amount >= 0 ? '#3C6E47' : '#f56c6c', fontWeight: 'bold' }">
              ¥{{ (row.amount || 0).toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="余额" width="110" align="right">
          <template #default="{ row }">¥{{ (row.balance_after || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="payment_method" label="方式" width="80" align="center" />
        <el-table-column prop="remark" label="备注" min-width="140" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="160" />
      </el-table>
      <div style="margin-top:8px;text-align:right">
        <el-pagination
          v-model:current-page="query.page"
          :page-size="query.page_size"
          :total="total"
          layout="total, prev, pager, next"
          small
          @current-change="loadList"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { depositApi, customerApi } from '@/api'
import { ElMessage } from 'element-plus'

const list = ref([])
const total = ref(0)
const loading = ref(false)
const creating = ref(false)
const balanceData = ref(null)
const selectedCustomerId = ref(null)

const query = reactive({ keyword: '', date_from: '', date_to: '', page: 1, page_size: 20 })

const createForm = reactive({
  customer_name: '',
  customer_id: null,
  amount: 100,
  payment_method: '微信',
  received_at: new Date().toISOString().slice(0, 10),
  remark: '',
})

// ── 客户搜索 ──
async function searchCustomers(queryString, cb) {
  if (!queryString || queryString.length < 1) { cb([]); return }
  try {
    const res = await customerApi.search(queryString)
    const customers = res.items || res.data || res || []
    const suggestions = customers.map(c => ({ value: c.name, customer_id: c.id, ...c }))
    cb(suggestions)
  } catch {
    cb([])
  }
}

function handleCustomerSelect(item) {
  selectedCustomerId.value = item.customer_id
  createForm.customer_id = item.customer_id
  createForm.customer_name = item.value || item.name
  loadBalance(item.customer_id)
}

// ── 余额查询 ──
async function loadBalance(customerId) {
  try {
    const res = await depositApi.customerBalance(customerId)
    balanceData.value = res.data || res
  } catch {
    balanceData.value = null
  }
}

// ── 创建定金 ──
async function handleCreateDeposit() {
  if (!createForm.customer_id) { ElMessage.warning('请选择客户'); return }
  if (!createForm.amount || createForm.amount <= 0) { ElMessage.warning('请输入有效金额'); return }
  creating.value = true
  try {
    await depositApi.create({
      customer_id: createForm.customer_id,
      amount: createForm.amount,
      payment_method: createForm.payment_method,
      received_at: createForm.received_at,
      remark: createForm.remark,
    })
    ElMessage.success('定金登记成功')
    // 重置表单
    createForm.amount = 100
    createForm.payment_method = '微信'
    createForm.received_at = new Date().toISOString().slice(0, 10)
    createForm.remark = ''
    // 刷新余额和列表
    if (selectedCustomerId.value) loadBalance(selectedCustomerId.value)
    loadList()
  } catch {} finally { creating.value = false }
}

// ── 定金记录列表 ──
async function loadList() {
  loading.value = true
  try {
    const params = { ...query }
    if (!params.date_from) delete params.date_from
    if (!params.date_to) delete params.date_to
    if (!params.keyword) delete params.keyword
    const res = await depositApi.list(params)
    list.value = res.items || []
    total.value = res.total || 0
  } catch {} finally { loading.value = false }
}

onMounted(() => {
  loadList()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.page-header h3 { font-size: 15px; margin: 0; }

.section-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.section-header > span { font-weight: 600; font-size: 14px; }
.filter-group { display: flex; align-items: center; gap: 8px; }

.deposit-form { margin-bottom: -12px; }
.deposit-form :deep(.el-form-item) { margin-bottom: 8px; }

.compact-table { font-size: 12px; }
.compact-table :deep(.el-table__header th) { padding: 2px 0; font-size: 12px; line-height: 1.4; }
.compact-table :deep(.el-table__cell) { padding: 2px 4px; }
.compact-table :deep(.el-table__body td) { padding: 2px 4px; line-height: 1.4; }
:deep(.el-card__body) { padding: 10px 14px; }

.balance-card {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 4px 0;
}
.balance-label { font-size: 15px; font-weight: 600; color: #1E3525; }
.balance-sub-label { font-size: 13px; color: #909399; }
.balance-value { font-size: 28px; font-weight: bold; margin-left: auto; }
</style>
