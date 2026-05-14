<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <h3>财务管理</h3>
          <div>
            <el-button :type="tab === 'receivable' ? 'primary' : 'default'" size="small" @click="tab = 'receivable'; if (!receivables.length) loadReceivables()">收款管理</el-button>
            <el-button :type="tab === 'payable' ? 'primary' : 'default'" size="small" @click="tab = 'payable'">应付款</el-button>
            <el-button :type="tab === 'expense' ? 'primary' : 'default'" size="small" @click="tab = 'expense'">费用</el-button>
            <el-button :type="tab === 'summary' ? 'primary' : 'default'" size="small" @click="tab = 'summary'">汇总</el-button>
            <el-button :type="tab === 'monthly' ? 'primary' : 'default'" size="small" @click="tab = 'monthly'; loadMonthlyReport()">月度报表</el-button>
            <el-divider direction="vertical" />
            <el-button :type="tab === 'deposit' ? 'primary' : 'default'" size="small" @click="tab = 'deposit'">定金管理</el-button>
          </div>
        </div>
      </template>

      <!-- 收款管理（按订单分组） -->
      <div v-show="tab === 'receivable'">
        <!-- 筛选 -->
        <el-form :inline="true" style="margin-bottom:16px">
          <el-form-item label="搜索">
            <el-input v-model="recQuery.keyword" placeholder="订单号/客户" clearable style="width:180px" @clear="loadReceivables" @keyup.enter="loadReceivables" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="recQuery.status" clearable style="width:120px" @change="loadReceivables">
              <el-option label="待收款" value="待收款" />
              <el-option label="部分收款" value="部分收款" />
              <el-option label="已结清" value="已结清" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadReceivables">查询</el-button>
            <el-button @click="recQuery.keyword=''; recQuery.status=''; recQuery.page=1; loadReceivables()">重置</el-button>
          </el-form-item>
        </el-form>

        <!-- 订单分组列表 -->
        <div v-loading="loadingRec">
          <div v-for="ord in receivables" :key="ord.id" class="order-card">
            <div class="order-card-header" @click="toggleOrder(ord)">
              <div class="order-info">
                <el-icon style="margin-right:6px">
                  <component :is="ord._expanded ? 'ArrowDown' : 'ArrowRight'" />
                </el-icon>
                <strong>{{ ord.order_no || '#' + ord.order_id }}</strong>
                <span style="margin-left:8px;color:#666">{{ ord.customer_name }}</span>
                <el-tag :type="recvStatusTag(ord.status)" size="small" style="margin-left:8px">{{ recvStatusLabel(ord.status) }}</el-tag>
              </div>
              <div class="order-amounts">
                <span>总额: <b>¥{{ ord.total_amount?.toFixed(2) }}</b></span>
                <span style="margin-left:16px;color:#67c23a">已收: <b>¥{{ ord.received_amount?.toFixed(2) }}</b></span>
                <span v-if="ord.unpaid_amount > 0" style="margin-left:16px;color:#f56c6c">欠款: <b>¥{{ ord.unpaid_amount?.toFixed(2) }}</b></span>
                <el-button v-if="ord.unpaid_amount > 0" size="small" type="primary" text style="margin-left:12px" @click.stop="showReceiveDialog(ord)">收款</el-button>
              </div>
            </div>

            <!-- 展开明细 -->
            <div v-if="ord._expanded" class="order-detail">
              <div v-if="ord._loadingPayments" style="text-align:center;padding:12px;color:#999">加载中...</div>
              <template v-else-if="ord._paymentList && ord._paymentList.length > 0">
                <el-table :data="ord._paymentList" stripe size="small" style="width:100%" :show-header="false">
                  <el-table-column width="60">
                    <template #default>
                      <span style="color:#999;font-size:12px">●</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="类型" width="100">
                    <template #default="{ row }">
                      <el-tag v-if="row.source === 'deposit'" type="warning" size="small">定金</el-tag>
                      <el-tag v-else type="success" size="small">{{ row.type }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="金额" width="120" align="right">
                    <template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template>
                  </el-table-column>
                  <el-table-column label="方式" width="80">
                    <template #default="{ row }">{{ row.method || '-' }}</template>
                  </el-table-column>
                  <el-table-column label="日期" width="100">
                    <template #default="{ row }">{{ row.date ? row.date.slice(0,10) : '-' }}</template>
                  </el-table-column>
                  <el-table-column label="备注" min-width="120" show-overflow-tooltip>
                    <template #default="{ row }">{{ row.remark || '-' }}</template>
                  </el-table-column>
                </el-table>
              </template>
              <div v-else style="padding:12px;color:#999;text-align:center">暂无收款明细</div>

              <!-- 内联收款 -->
              <div v-if="ord.unpaid_amount > 0" class="inline-receive">
                <el-select v-model="ord._paymentType" size="small" style="width:90px">
                  <el-option label="定金" value="定金" />
                  <el-option label="进度款" value="进度款" />
                  <el-option label="尾款" value="尾款" />
                  <el-option label="其他" value="其他" />
                </el-select>
                <el-input-number v-model="ord._receiveAmount" :precision="2" :min="0.01" :max="ord.unpaid_amount" size="small" style="width:130px;margin-left:8px" />
                <el-select v-model="ord._receiveMethod" size="small" style="width:90px;margin-left:8px">
                  <el-option label="转账" value="转账" />
                  <el-option label="现金" value="现金" />
                  <el-option label="微信" value="微信" />
                  <el-option label="支付宝" value="支付宝" />
                  <el-option label="刷卡" value="刷卡" />
                </el-select>
                <el-button size="small" type="primary" style="margin-left:8px" :loading="ord._receiving" @click="handleInlineReceive(ord)">确认收款</el-button>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <el-empty v-if="receivables.length === 0" description="没有匹配的收款记录" />
        </div>

        <!-- 分页 -->
        <div style="margin-top:12px;text-align:right">
          <el-pagination
            v-model:current-page="recQuery.page"
            :page-size="20"
            :total="recTotal"
            layout="total, prev, pager, next"
            size="small"
            @current-change="loadReceivables"
          />
        </div>
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
              <el-tag :type="payStatusTag(row.status)" size="small">{{ payStatusLabel(row.status) }}</el-tag>
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
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
          <el-form :inline="true" style="margin-bottom:0">
            <el-form-item label="类别">
              <el-select v-model="expQuery.category" clearable style="width:110px" @change="loadExpenses">
                <el-option label="房租" value="房租" />
                <el-option label="水电" value="水电" />
                <el-option label="工资" value="工资" />
                <el-option label="交通" value="交通" />
                <el-option label="餐饮" value="餐饮" />
                <el-option label="办公" value="办公" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
            <el-form-item label="日期起">
              <el-date-picker v-model="expQuery.start_date" type="date" placeholder="起" value-format="YYYY-MM-DD" style="width:130px" @change="loadExpenses" />
            </el-form-item>
            <el-form-item label="日期止">
              <el-date-picker v-model="expQuery.end_date" type="date" placeholder="止" value-format="YYYY-MM-DD" style="width:130px" @change="loadExpenses" />
            </el-form-item>
            <el-form-item label="关键词">
              <el-input v-model="expQuery.keyword" placeholder="备注搜索" clearable style="width:150px" @keyup.enter="loadExpenses" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadExpenses">查询</el-button>
              <el-button @click="expQuery.category='';expQuery.start_date='';expQuery.end_date='';expQuery.keyword='';expQuery.page=1;loadExpenses()">重置</el-button>
            </el-form-item>
          </el-form>
          <el-button @click="showExpenseDialog = true">新增费用</el-button>
        </div>
        <el-table :data="expenses" v-loading="loadingExp" stripe style="width:100%">
          <el-table-column prop="expense_date" label="日期" width="110" />
          <el-table-column prop="category" label="费用类型" width="120" />
          <el-table-column prop="amount" label="金额" width="120" align="right">
            <template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
          <el-table-column prop="created_at" label="创建时间" width="160" />
        </el-table>
        <div style="margin-top:12px;text-align:right">
          <el-pagination
            v-model:current-page="expQuery.page"
            :page-size="20"
            :total="expTotal"
            layout="total, prev, pager, next"
            size="small"
            @current-change="loadExpenses"
          />
        </div>
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

      <!-- 月度报表 -->
      <div v-show="tab === 'monthly'">
        <el-form :inline="true" style="margin-bottom:16px">
          <el-form-item label="年份">
            <el-date-picker v-model="reportYear" type="year" placeholder="选择年份" value-format="YYYY" style="width:140px" @change="loadMonthlyReport" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadMonthlyReport">查询</el-button>
          </el-form-item>
        </el-form>

        <el-table :data="monthlyReport?.months" v-loading="loadingReport" stripe style="width:100%">
          <el-table-column label="月份" width="120">
            <template #default="{ row }">{{ row.month }}</template>
          </el-table-column>
          <el-table-column label="收入" width="160" align="right">
            <template #default="{ row }">
              <span style="color:#67c23a">¥{{ row.revenue?.toFixed(2) }}</span>
              <span style="color:#999;font-size:12px;margin-left:4px">({{ row.revenue_count }}笔)</span>
            </template>
          </el-table-column>
          <el-table-column label="支出" width="160" align="right">
            <template #default="{ row }">
              <span style="color:#f56c6c">¥{{ row.expense?.toFixed(2) }}</span>
              <span style="color:#999;font-size:12px;margin-left:4px">({{ row.expense_count }}笔)</span>
            </template>
          </el-table-column>
          <el-table-column label="净利润" width="160" align="right">
            <template #default="{ row }">
              <span :style="{ color: row.net_profit >= 0 ? '#67c23a' : '#f56c6c', fontWeight: 'bold' }">
                ¥{{ row.net_profit?.toFixed(2) }}
              </span>
            </template>
          </el-table-column>
        </el-table>

        <el-card v-if="monthlyReport" shadow="never" style="margin-top:16px">
          <el-row :gutter="24">
            <el-col :span="8" style="text-align:center">
              <div style="color:#999;font-size:13px">年度总收入</div>
              <div style="font-size:22px;font-weight:bold;color:#67c23a">¥{{ monthlyReport.total_revenue?.toFixed(2) }}</div>
            </el-col>
            <el-col :span="8" style="text-align:center">
              <div style="color:#999;font-size:13px">年度总支出</div>
              <div style="font-size:22px;font-weight:bold;color:#f56c6c">¥{{ monthlyReport.total_expense?.toFixed(2) }}</div>
            </el-col>
            <el-col :span="8" style="text-align:center">
              <div style="color:#999;font-size:13px">年度净利润</div>
              <div :style="{ fontSize: '22px', fontWeight: 'bold', color: monthlyReport.total_net_profit >= 0 ? '#67c23a' : '#f56c6c' }">
                ¥{{ monthlyReport.total_net_profit?.toFixed(2) }}
              </div>
            </el-col>
          </el-row>
        </el-card>
      </div>
    </el-card>

    <!-- 定金管理 -->
    <DepositPanel v-show="tab === 'deposit'" />

    <!-- 收款对话框（已内联到订单卡片中，保留做备选） -->
    <el-dialog v-model="showReceive" title="收款确认" width="450px">
      <template v-if="receiveTarget">
        <p style="margin-bottom:12px">订单：{{ receiveTarget.order_no }} — {{ receiveTarget.customer_name }}</p>
        <p style="margin-bottom:12px">未收金额：<span style="color:#f56c6c;font-weight:bold">¥{{ receiveTarget.unpaid_amount?.toFixed(2) }}</span></p>
        <el-form :model="receiveForm" label-width="80px">
          <el-form-item label="收款类型">
            <el-select v-model="receiveForm.payment_type" style="width:100%">
              <el-option label="定金" value="定金" />
              <el-option label="进度款" value="进度款" />
              <el-option label="尾款" value="尾款" />
              <el-option label="其他" value="其他" />
            </el-select>
          </el-form-item>
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
import { financeApi, depositApi } from '@/api'
import { ElMessage } from 'element-plus'
import DepositPanel from './DepositPanel.vue'

const tab = ref('receivable')
const receivables = ref([])
const recTotal = ref(0)
const payables = ref([])
const expenses = ref([])
const expTotal = ref(0)
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

// 月度报表
const monthlyReport = ref(null)
const loadingReport = ref(false)
const reportYear = ref(new Date().getFullYear().toString())

const recQuery = reactive({ keyword: '', status: '', page: 1, page_size: 20 })
const payQuery = reactive({ keyword: '', status: '', page: 1, page_size: 100 })
const expQuery = reactive({ category: '', start_date: '', end_date: '', keyword: '', page: 1, page_size: 20 })
const receiveForm = reactive({ order_id: null, amount: 0, method: '转账', payment_type: '其他', remark: '' })
const payForm = reactive({ ref_type: '', ref_id: null, amount: 0, method: '转账', remark: '' })
const expenseForm = reactive({ category: '其他', amount: 0, expense_date: new Date().toISOString().slice(0, 10), remark: '' })

function recvStatusTag(status) {
  const map = { '待收款': 'danger', '部分收款': 'warning', '已结清': 'success' }
  return map[status] || 'info'
}
function recvStatusLabel(status) {
  const map = { '待收款': '待收款', '部分收款': '部分收款', '已结清': '已结清' }
  return map[status] || status || '未收款'
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
    const params = { page: recQuery.page, page_size: recQuery.page_size }
    if (recQuery.keyword) params.keyword = recQuery.keyword
    if (recQuery.status) params.status = recQuery.status
    const res = await financeApi.listReceivables(params)

    // 如果没传状态筛选，默认排除已结清
    const items = (res.items || []).filter(i => {
      if (recQuery.status) return true
      return i.unpaid_amount > 0
    })

    receivables.value = items.map(i => ({
      ...i,
      _expanded: false,
      _loadingPayments: false,
      _paymentList: [],
      _receiveAmount: i.unpaid_amount || 0,
      _receiveMethod: '转账',
      _paymentType: '其他',
      _receiving: false,
    }))
    recTotal.value = res.total || 0
  } catch {} finally { loadingRec.value = false }
}

async function loadOrderPayments(ord) {
  if (ord._paymentList && ord._paymentList.length > 0) return
  ord._loadingPayments = true
  try {
    const res = await financeApi.getOrderPayments(ord.order_id)
    const data = res.data || {}
    ord._paymentList = data.payments || []
  } catch {
    ord._paymentList = []
  } finally {
    ord._loadingPayments = false
  }
}

function toggleOrder(ord) {
  ord._expanded = !ord._expanded
  if (ord._expanded) {
    loadOrderPayments(ord)
  }
}

async function handleInlineReceive(ord) {
  ord._receiving = true
  try {
    const msg = await financeApi.receive({
      order_id: ord.order_id,
      amount: ord._receiveAmount,
      method: ord._receiveMethod,
      payment_type: ord._paymentType,
      remark: '',
    })
    ElMessage.success(`${ord._paymentType} ¥${ord._receiveAmount.toFixed(2)} 成功`)
    await loadReceivables()
    loadSummary()
  } catch {
    ElMessage.error('收款失败')
  } finally {
    ord._receiving = false
  }
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
    const params = { page: expQuery.page, page_size: expQuery.page_size }
    if (expQuery.category) params.category = expQuery.category
    if (expQuery.start_date) params.start_date = expQuery.start_date
    if (expQuery.end_date) params.end_date = expQuery.end_date
    // keyword filtering done client-side
    const res = await financeApi.listExpenses(params)
    let items = res.items || []
    if (expQuery.keyword) {
      items = items.filter(i => (i.remark || '').includes(expQuery.keyword))
    }
    expenses.value = items
    expTotal.value = res.total || 0
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
  receiveForm.payment_type = '其他'
  receiveForm.remark = ''
  showReceive.value = true
}

async function loadMonthlyReport() {
  loadingReport.value = true
  try {
    const res = await financeApi.monthlyReport({ year: reportYear.value || undefined })
    monthlyReport.value = res.data
  } catch {} finally { loadingReport.value = false }
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
  if (!expenseForm.amount) {
    ElMessage.warning('请输入金额')
    return
  }
  saving.value = true
  try {
    await financeApi.createExpense(expenseForm)
    ElMessage.success('费用记录创建成功')
    showExpenseDialog.value = false
    loadExpenses()
    loadSummary()
  } catch {} finally { saving.value = false }
}

onMounted(() => {
  loadReceivables()
  loadPayables()
  loadExpenses()
  loadSummary()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.page-header h3 { margin: 0; }
.summary-card { padding: 4px 0; }
.summary-label { font-size: 13px; color: #999; margin-bottom: 4px; }
.summary-value { font-size: 20px; font-weight: bold; }

/* 订单卡片 */
.order-card {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 8px;
  overflow: hidden;
}
.order-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  cursor: pointer;
  background: #fafafa;
  transition: background 0.2s;
}
.order-card-header:hover { background: #f0f5f0; }
.order-info { display: flex; align-items: center; }
.order-amounts { display: flex; align-items: center; font-size: 13px; }
.order-detail {
  padding: 8px 14px 12px;
  border-top: 1px solid #ebeef5;
  background: #fff;
}
.inline-receive {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #e8e8e8;
  display: flex;
  align-items: center;
}
</style>
