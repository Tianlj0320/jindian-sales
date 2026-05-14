<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <h3>日报</h3>
          <div>
            <el-date-picker v-model="reportDate" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width:140px" size="small" @change="loadReport" />
            <el-button size="small" style="margin-left:8px" @click="loadReport">刷新</el-button>
          </div>
        </div>
      </template>

      <!-- 2x2 卡片网格 -->
      <el-row :gutter="12">
        <el-col :span="12">
          <el-card shadow="hover" class="report-card">
            <template #header>
              <div class="card-header-wrap">
                <span class="card-title card-title-green">今日收款</span>
                <span v-if="report" class="card-subtitle">{{ report.deposit_count || 0 }} 笔</span>
              </div>
            </template>
            <div v-if="report">
              <div class="stat-row">
                <span class="stat-label">总额</span>
                <span class="stat-value stat-green">¥{{ (report.total_deposits || 0).toFixed(2) }}</span>
              </div>
              <el-divider style="margin:8px 0" />
              <div v-if="report.recent_deposits?.length" class="mini-list">
                <div v-for="d in report.recent_deposits" :key="d.id" class="mini-row">
                  <span class="mini-name">{{ d.customer_name }}</span>
                  <span class="mini-amount stat-green">¥{{ (d.amount || 0).toFixed(2) }}</span>
                  <el-tag :type="d.is_linked ? 'success' : 'warning'" size="small" effect="plain">
                    {{ d.is_linked ? '已关联' : '未关联' }}
                  </el-tag>
                </div>
              </div>
              <div v-else class="no-data">今日暂无收款</div>
            </div>
            <div v-else-if="!reportLoading" class="no-data">暂无数据</div>
            <div v-else class="no-data"><el-icon class="is-loading"><Loading /></el-icon> 加载中</div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover" class="report-card">
            <template #header>
              <div class="card-header-wrap">
                <span class="card-title card-title-blue">今日新订单</span>
                <span v-if="report" class="card-subtitle">{{ report.new_orders_count || 0 }} 单</span>
              </div>
            </template>
            <div v-if="report">
              <div class="stat-row">
                <span class="stat-label">总额</span>
                <span class="stat-value stat-blue">¥{{ (report.new_orders_total || 0).toFixed(2) }}</span>
              </div>
              <el-divider style="margin:8px 0" />
              <div v-if="report.new_orders?.length" class="mini-list">
                <div v-for="o in report.new_orders" :key="o.id" class="mini-row">
                  <span class="mini-name">{{ o.order_no }}</span>
                  <span class="mini-sub">{{ o.customer_name }}</span>
                  <span class="mini-amount stat-blue">¥{{ (o.amount || 0).toFixed(2) }}</span>
                </div>
              </div>
              <div v-else class="no-data">今日暂无新订单</div>
            </div>
            <div v-else-if="!reportLoading" class="no-data">暂无数据</div>
            <div v-else class="no-data"><el-icon class="is-loading"><Loading /></el-icon> 加载中</div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="12" style="margin-top:12px">
        <el-col :span="12">
          <el-card shadow="hover" class="report-card">
            <template #header>
              <div class="card-header-wrap">
                <span class="card-title card-title-orange">待采购</span>
                <span v-if="report" class="card-subtitle">{{ report.pending_purchases_count || 0 }} 单</span>
              </div>
            </template>
            <div v-if="report">
              <div v-if="report.pending_purchases?.length" class="mini-list">
                <div v-for="p in report.pending_purchases" :key="p.id" class="mini-row">
                  <span class="mini-name">{{ p.order_no || p.purchase_no }}</span>
                  <span class="mini-sub">{{ p.supplier_name }}</span>
                  <span class="mini-amount stat-orange">¥{{ (p.amount || 0).toFixed(2) }}</span>
                </div>
              </div>
              <div v-else class="no-data">暂无待采购项</div>
            </div>
            <div v-else-if="!reportLoading" class="no-data">暂无数据</div>
            <div v-else class="no-data"><el-icon class="is-loading"><Loading /></el-icon> 加载中</div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover" class="report-card">
            <template #header>
              <div class="card-header-wrap">
                <span class="card-title card-title-orange">待安装</span>
                <span v-if="report" class="card-subtitle">{{ report.pending_installations_count || 0 }} 单</span>
              </div>
            </template>
            <div v-if="report">
              <div v-if="report.pending_installations?.length" class="mini-list">
                <div v-for="i in report.pending_installations" :key="i.id" class="mini-row">
                  <span class="mini-name">{{ i.order_no }}</span>
                  <span class="mini-sub">{{ i.customer_name }}</span>
                  <el-tag v-if="i.team_name" size="small" effect="plain">{{ i.team_name }}</el-tag>
                </div>
              </div>
              <div v-else class="no-data">暂无待安装项</div>
            </div>
            <div v-else-if="!reportLoading" class="no-data">暂无数据</div>
            <div v-else class="no-data"><el-icon class="is-loading"><Loading /></el-icon> 加载中</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 历史日报表 -->
      <el-card shadow="never" style="margin-top:12px">
        <template #header>
          <div class="section-header">
            <span>历史日报</span>
            <div class="filter-group">
              <el-date-picker v-model="historyQuery.date_from" type="date" placeholder="开始日期" value-format="YYYY-MM-DD" style="width:135px" size="small" @change="loadHistory" />
              <el-date-picker v-model="historyQuery.date_to" type="date" placeholder="结束日期" value-format="YYYY-MM-DD" style="width:135px" size="small" @change="loadHistory" />
              <el-button type="primary" size="small" @click="loadHistory">查询</el-button>
            </div>
          </div>
        </template>
        <el-table :data="history" v-loading="historyLoading" stripe style="width:100%" size="small" class="compact-table">
          <el-table-column prop="report_date" label="日期" width="100" />
          <el-table-column label="收款总额" width="130" align="right">
            <template #default="{ row }">
              <span style="color:#3C6E47;font-weight:600">¥{{ (row.total_deposits || 0).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="deposit_count" label="收款笔数" width="80" align="center" />
          <el-table-column label="订单总额" width="130" align="right">
            <template #default="{ row }">
              <span style="color:#409eff;font-weight:600">¥{{ (row.new_orders_total || 0).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="new_orders_count" label="新订单数" width="80" align="center" />
          <el-table-column prop="pending_purchases_count" label="待采购" width="70" align="center" />
          <el-table-column prop="pending_installations_count" label="待安装" width="70" align="center" />
        </el-table>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { dailyReportApi } from '@/api'

const report = ref(null)
const reportLoading = ref(false)
const reportDate = ref(new Date().toISOString().slice(0, 10))

const history = ref([])
const historyLoading = ref(false)
const historyQuery = reactive({
  date_from: new Date(Date.now() - 7 * 86400000).toISOString().slice(0, 10),
  date_to: new Date().toISOString().slice(0, 10),
})

// ── 加载日报 ──
async function loadReport() {
  reportLoading.value = true
  report.value = null
  try {
    const res = await dailyReportApi.getToday()
    report.value = res.data || res
  } catch {} finally {
    reportLoading.value = false
  }
}

// ── 加载历史 ──
async function loadHistory() {
  historyLoading.value = true
  try {
    const params = { ...historyQuery }
    if (!params.date_from) delete params.date_from
    if (!params.date_to) delete params.date_to
    const res = await dailyReportApi.getHistory(params)
    history.value = res.items || res.data || res || []
  } catch {} finally {
    historyLoading.value = false
  }
}

onMounted(() => {
  loadReport()
  loadHistory()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.page-header h3 { font-size: 15px; margin: 0; }

.section-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.section-header > span { font-weight: 600; font-size: 14px; }
.filter-group { display: flex; align-items: center; gap: 6px; }

/* 统计卡片 */
.report-card { margin-bottom: 0; }
.report-card :deep(.el-card__body) { padding: 12px 16px; }
.report-card :deep(.el-card__header) { padding: 8px 16px; border-bottom: 1px solid #ebeef5; }

.card-header-wrap { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-size: 14px; font-weight: 700; }
.card-title-green { color: #3C6E47; }
.card-title-blue { color: #409eff; }
.card-title-orange { color: #e6a23c; }
.card-subtitle { font-size: 12px; color: #909399; }

.stat-row { display: flex; justify-content: space-between; align-items: center; padding: 2px 0; }
.stat-label { font-size: 13px; color: #606266; }
.stat-value { font-size: 20px; font-weight: bold; }
.stat-green { color: #3C6E47; }
.stat-blue { color: #409eff; }
.stat-orange { color: #e6a23c; }

.mini-list { display: flex; flex-direction: column; gap: 4px; max-height: 200px; overflow-y: auto; }
.mini-row { display: flex; align-items: center; gap: 8px; font-size: 12px; padding: 2px 0; }
.mini-name { min-width: 0; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mini-sub { color: #909399; font-size: 11px; white-space: nowrap; }
.mini-amount { font-weight: 600; white-space: nowrap; min-width: 80px; text-align: right; }

.no-data { text-align: center; color: #c0c4cc; font-size: 13px; padding: 20px 0; }

.compact-table { font-size: 12px; }
.compact-table :deep(.el-table__header th) { padding: 2px 0; font-size: 12px; line-height: 1.4; }
.compact-table :deep(.el-table__cell) { padding: 2px 4px; }
.compact-table :deep(.el-table__body td) { padding: 2px 4px; line-height: 1.4; }
:deep(.el-card__body) { padding: 10px 14px; }
</style>
