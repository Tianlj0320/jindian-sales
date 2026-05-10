<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <h3>财务管理</h3>
          <div>
            <el-button :type="tab === 'receivable' ? 'primary' : 'default'" size="small" @click="tab = 'receivable'">应收款</el-button>
            <el-button :type="tab === 'payable' ? 'primary' : 'default'" size="small" @click="tab = 'payable'">应付款</el-button>
            <el-button :type="tab === 'expense' ? 'primary' : 'default'" size="small" @click="tab = 'expense'">费用</el-button>
            <el-button :type="tab === 'summary' ? 'primary' : 'default'" size="small" @click="tab = 'summary'">汇总</el-button>
          </div>
        </div>
      </template>

      <!-- 应收款 -->
      <div v-show="tab === 'receivable'">
        <el-form :inline="true" style="margin-bottom:16px">
          <el-form-item label="搜索">
            <el-input v-model="recQuery.keyword" placeholder="订单号/客户" clearable @clear="loadReceivables" @keyup.enter="loadReceivables" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="recQuery.status" clearable style="width:100px" @change="loadReceivables">
              <el-option label="未收" value="unpaid" />
              <el-option label="部分" value="partial" />
              <el-option label="已收" value="paid" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadReceivables">查询</el-button>
          </el-form-item>
        </el-form>
        <el-table :data="receivables" v-loading="loadingRec" stripe style="width:100%">
          <el-table-column prop="order_no" label="订单号" width="150" />
          <el-table-column prop="customer_name" label="客户" width="120" />
          <el-table-column prop="total_amount" label="应收总额" width="120" align="right">
            <template #default="{ row }">¥{{ row.total_amount?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="received_amount" label="已收金额" width="120" align="right">
            <template #default="{ row }">¥{{ row.received_amount?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="unpaid_amount" label="未收金额" width="120" align="right">
            <template #default="{ row }">
              <span :style="{ color: row.unpaid_amount > 0 ? '#f56c6c' : '#67c23a', fontWeight: 'bold' }">
                ¥{{ row.unpaid_amount?.toFixed(2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="recStatusTag(row.status)" size="small">{{ recStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.unpaid_amount > 0" text size="small" type="primary" @click="showReceiveDialog(row)">收款</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 应付款 -->
      <div v-show="tab === 'payable'">
        <el-form :inline="true" style="margin-bottom:16px">
          <el-form-item label="搜索">
            <el-input v-model="payQuery.keyword" placeholder="供应商" clearable @clear="loadPayables" @keyup.enter="loadPayables" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="payQuery.status" clearable style="width:100px" @change="loadPayables">
              <el-option label="未付" value="unpaid" />
              <el-option label="部分" value="partial" />
              <el-option label="已付" value="paid" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadPayables">查询</el-button>
          </el-form-item>
        </el-form>
        <el-table :data="payables" v-loading="loadingPay" stripe style="width:100%">
          <el-table-column prop="ref_type" label="类型" width="100" />
          <el-table-column prop="supplier_name" label="供应商" min-width="160" />
          <el-table-column prop="total_amount" label="应付总额" width="120" align="right">
            <template #default="{ row }">¥{{ row.total_amount?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="paid_amount" label="已付金额" width="120" align="right">
            <template #default="{ row }">¥{{ row.paid_amount?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="unpaid_amount" label="未付金额" width="120" align="right">
            <template #default="{ row }">
              <span :style="{ color: row.unpaid_amount > 0 ? '#f56c6c' : '#67c23a', fontWeight: 'bold' }">
                ¥{{ row.unpaid_amount?.toFixed(2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="recStatusTag(row.status)" size="small">{{ recStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.unpaid_amount > 0" text size="small" type="primary" @click="showPayDialog(row)">付款</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 费用 -->
      <div v-show="tab === 'expense'">
        <el-button style="margin-bottom:12px" @click="showExpenseDialog = true">新增费用</el-button>
        <el-table :data="expenses" v-loading="loadingExp" stripe style="width:100%">
          <el-table-column prop="expense_date" label="日期" width="110" />
          <el-table-column prop="category" label="费用类型" width="120" />
          <el-table-column prop="amount" label="金额" width="120" align="right">
            <template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="200" />
          <el-table-column prop="created_at" label="创建时间" width="160" />
        </el-table>
      </div>

      <!-- 汇总 -->
      <div v-show="tab === 'summary'">
        <el-row :gutter="16" v-if="summary">
          <el-col :span="6">
            <el-card shadow="hover">
              <div class="summary-card">
                <div class="summary-label">应收总额</div>
                <div class="summary-value" style="color:#409eff">¥{{ summary.total_receivable?.toFixed(2) }}</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <div class="summary-card">
                <div class="summary-label">已收总额</div>
                <div class="summary-value" style="color:#67c23a">¥{{ summary.total_received?.toFixed(2) }}</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <div class="summary-card">
                <div class="summary-label">未收总额</div>
                <div class="summary-value" style="color:#f56c6c">¥{{ summary.total_unpaid?.toFixed(2) }}</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <div class="summary-card">
                <div class="summary-label">应付总额</div>
                <div class="summary-value" style="color:#e6a23c">¥{{ summary.total_payable?.toFixed(2) }}</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="16" style="margin-top:16px" v-if="summary">
          <el-col :span="6">
            <el-card shadow="hover">
              <div class="summary-card">
                <div class="summary-label">已付总额</div>
                <div class="summary-value" style="color:#67c23a">¥{{ summary.total_paid?.toFixed(2) }}</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <div class="summary-card">
                <div class="summary-label">未付总额</div>
                <div class="summary-value" style="color:#f56c6c">¥{{ summary.total_unpaid_payable?.toFixed(2) }}</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <div class="summary-card">
                <div class="summary-label">本月收款</div>
                <div class="summary-value" style="color:#67c23a">¥{{ summary.month_received?.toFixed(2) }}</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <div class="summary-card">
                <div class="summary-label">本月支出</div>
                <div class="summary-value" style="color:#f56c6c">¥{{ (summary.month_paid + summary.month_expense).toFixed(2) }}</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-empty v-else description="暂无汇总数据" />
      </div>
    </el-card>

    <!-- 收款对话框 -->
    <el-dialog v-model="showReceive" title="收款确认" width="450px">
      <template v-if="receiveTarget">
        <p style="margin-bottom:12px">订单：{{ receiveTarget.order_no }} — {{ receiveTarget.customer_name }}</p>
        <p style="margin-bottom:12px">未收金额：<span style="color:#f56c6c;font-weight:bold">¥{{ receiveTarget.unpaid_amount?.toFixed(2) }}</span></p>
        <el-form :model="receiveForm" label-width="80px">
          <el-form-item label="收款金额">
            <el-input-number v-model="receiveForm.amount" :precision="2" :min="0.01" :max="receiveTarget.unpaid_amount" style="width:100%" />
          </el-form-item>
          <el-form-item label="收款方式">
            <el-select v-model="receiveForm.method" style="width:100%">
              <el-option label="转账" value="转账" />
              <el-option label="现金" value="现金" />
              <el-option label="微信" value="微信" />
              <el-option label="支付宝" value="支付宝" />
              <el-option label="刷卡" value="刷卡" />
            </el-select>
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="receiveForm.remark" type="textarea" :rows="2" />
          </el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="showReceive = false">取消</el-button>
        <el-button type="primary" :loading="receiving" @click="handleReceive">确认收款</el-button>
      </template>
    </el-dialog>

    <!-- 付款对话框 -->
    <el-dialog v-model="showPay" title="付款确认" width="450px">
      <template v-if="payTarget">
        <p style="margin-bottom:12px">{{ payTarget.ref_type }} — {{ payTarget.supplier_name }}</p>
        <p style="margin-bottom:12px">未付金额：<span style="color:#f56c6c;font-weight:bold">¥{{ payTarget.unpaid_amount?.toFixed(2) }}</span></p>
        <el-form :model="payForm" label-width="80px">
          <el-form-item label="付款金额">
            <el-input-number v-model="payForm.amount" :precision="2" :min="0.01" :max="payTarget.unpaid_amount" style="width:100%" />
          </el-form-item>
          <el-form-item label="付款方式">
            <el-select v-model="payForm.method" style="width:100%">
              <el-option label="转账" value="转账" />
              <el-option label="现金" value="现金" />
              <el-option label="微信" value="微信" />
              <el-option label="支付宝" value="支付宝" />
            </el-select>
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="payForm.remark" type="textarea" :rows="2" />
          </el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="showPay = false">取消</el-button>
        <el-button type="primary" :loading="paying" @click="handlePay">确认付款</el-button>
      </template>
    </el-dialog>

    <!-- 新增费用 -->
    <el-dialog v-model="showExpenseDialog" title="新增费用" width="450px">
      <el-form :model="expenseForm" label-width="80px">
        <el-form-item label="费用类型">
          <el-select v-model="expenseForm.category" style="width:100%">
            <el-option label="房租" value="房租" />
            <el-option label="水电" value="水电" />
            <el-option label="工资" value="工资" />
            <el-option label="交通" value="交通" />
            <el-option label="餐饮" value="餐饮" />
            <el-option label="办公" value="办公" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额">
          <el-input-number v-model="expenseForm.amount" :precision="2" :min="0.01" style="width:100%" />
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="expenseForm.expense_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="expenseForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExpenseDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreateExpense">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { financeApi } from '@/api'
import { ElMessage } from 'element-plus'

const tab = ref('receivable')
const receivables = ref([])
const payables = ref([])
const expenses = ref([])
const summary = ref(null)
const loadingRec = ref(false)
const loadingPay = ref(false)
const loadingExp = ref(false)
const saving = ref(false)
const receiving = ref(false)
const paying = ref(false)
const showReceive = ref(false)
const showPay = ref(false)
const showExpenseDialog = ref(false)
const receiveTarget = ref(null)
const payTarget = ref(null)

const recQuery = reactive({ keyword: '', status: '', page: 1, page_size: 100 })
const payQuery = reactive({ keyword: '', status: '', page: 1, page_size: 100 })
const receiveForm = reactive({ order_id: null, amount: 0, method: '转账', remark: '' })
const payForm = reactive({ ref_type: '', ref_id: null, amount: 0, method: '转账', remark: '' })
const expenseForm = reactive({ category: '其他', amount: 0, expense_date: new Date().toISOString().slice(0, 10), remark: '' })

function recStatusTag(status) {
  const map = { unpaid: 'danger', partial: 'warning', paid: 'success' }
  return map[status] || 'info'
}
function recStatusLabel(status) {
  const map = { unpaid: '未收', partial: '部分', paid: '已收' }
  return map[status] || status
}

function payStatusTag(status) {
  const map = { unpaid: 'danger', partial: 'warning', paid: 'success' }
  return map[status] || 'info'
}
function payStatusLabel(status) {
  const map = { unpaid: '未付', partial: '部分', paid: '已付' }
  return map[status] || status
}

async function loadReceivables() {
  loadingRec.value = true
  try {
    const res = await financeApi.listReceivables(recQuery)
    receivables.value = res.items || []
  } catch {} finally { loadingRec.value = false }
}

async function loadPayables() {
  loadingPay.value = true
  try {
    const res = await financeApi.listPayables(payQuery)
    payables.value = res.items || []
  } catch {} finally { loadingPay.value = false }
}

async function loadExpenses() {
  loadingExp.value = true
  try {
    const res = await financeApi.listExpenses({ page: 1, page_size: 100 })
    expenses.value = res.items || []
  } catch {} finally { loadingExp.value = false }
}

async function loadSummary() {
  try {
    const res = await financeApi.summary()
    summary.value = res.data || res
  } catch {}
}

function showReceiveDialog(row) {
  receiveTarget.value = row
  receiveForm.order_id = row.order_id
  receiveForm.amount = row.unpaid_amount
  receiveForm.method = '转账'
  receiveForm.remark = ''
  showReceive.value = true
}

async function handleReceive() {
  receiving.value = true
  try {
    await financeApi.receive(receiveForm)
    ElMessage.success('收款成功')
    showReceive.value = false
    loadReceivables()
    loadSummary()
  } catch {} finally { receiving.value = false }
}

function showPayDialog(row) {
  payTarget.value = row
  payForm.ref_type = row.ref_type
  payForm.ref_id = row.ref_id
  payForm.amount = row.unpaid_amount
  payForm.method = '转账'
  payForm.remark = ''
  showPay.value = true
}

async function handlePay() {
  paying.value = true
  try {
    await financeApi.pay(payForm)
    ElMessage.success('付款成功')
    showPay.value = false
    loadPayables()
    loadSummary()
  } catch {} finally { paying.value = false }
}

async function handleCreateExpense() {
  if (!expenseForm.category || !expenseForm.amount) { ElMessage.warning('请填写完整'); return }
  saving.value = true
  try {
    await financeApi.createExpense(expenseForm)
    ElMessage.success('费用已记录')
    showExpenseDialog.value = false
    expenseForm.category = '其他'; expenseForm.amount = 0; expenseForm.remark = ''
    loadExpenses()
    loadSummary()
  } catch {} finally { saving.value = false }
}

watch(tab, (val) => {
  if (val === 'receivable') loadReceivables()
  else if (val === 'payable') loadPayables()
  else if (val === 'expense') loadExpenses()
  else if (val === 'summary') loadSummary()
})

onMounted(() => {
  loadReceivables()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.page-header h3 { font-size: 18px; }
.summary-card { text-align: center; padding: 8px 0; }
.summary-label { font-size: 14px; color: #909399; margin-bottom: 8px; }
.summary-value { font-size: 24px; font-weight: bold; }
</style>
