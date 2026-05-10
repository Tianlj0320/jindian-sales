<template>
  <div class="dashboard">
    <h2 style="margin-bottom:20px">工作台 <span style="font-size:14px;color:#909399;font-weight:normal">{{ today }}</span></h2>

    <!-- KPI 卡片 -->
    <el-row :gutter="16" style="margin-bottom:20px">
      <el-col :span="6" v-for="card in kpiCards" :key="card.label">
        <el-card shadow="hover" :body-style="{ padding: '20px' }">
          <div class="kpi-item">
            <div class="kpi-value" :style="{ color: card.color }">{{ card.value ?? '-' }}</div>
            <div class="kpi-label">{{ card.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <!-- 快捷操作 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>快捷操作</template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/orders/new')">新建订单</el-button>
            <el-button @click="$router.push('/customers')">客户管理</el-button>
            <el-button @click="$router.push('/orders')">订单列表</el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 销售报表 -->
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>本月销售</template>
          <div class="sales-info">
            <div class="sales-row">
              <span>销售额</span>
              <span class="sales-value">¥{{ (dashboardData?.month_sales || 0).toLocaleString() }}</span>
            </div>
            <div class="sales-row">
              <span>今日订单</span>
              <span class="sales-value">{{ dashboardData?.today_orders || 0 }}</span>
            </div>
            <div class="sales-row">
              <span>待安装</span>
              <span class="sales-value warn">{{ dashboardData?.pending_install || 0 }}</span>
            </div>
            <div class="sales-row">
              <span>逾期订单</span>
              <span class="sales-value danger">{{ dashboardData?.overdue_orders || 0 }}</span>
            </div>
            <div class="sales-row">
              <span>待收款</span>
              <span class="sales-value">{{ dashboardData?.pending_payment || 0 }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { dashboardApi } from '@/api'
import { ElMessage } from 'element-plus'

const today = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
const dashboardData = ref(null)

const kpiCards = computed(() => [
  { label: '今日订单', value: dashboardData.value?.today_orders, color: '#409eff' },
  { label: '本月销售(元)', value: dashboardData.value?.month_sales?.toLocaleString(), color: '#67c23a' },
  { label: '待安装', value: dashboardData.value?.pending_install, color: '#e6a23c' },
  { label: '低库存预警', value: dashboardData.value?.low_stock, color: '#f56c6c' },
])

async function loadDashboard() {
  try {
    dashboardData.value = (await dashboardApi.get()).data
  } catch {}
}

onMounted(loadDashboard)
</script>

<style scoped>
.kpi-item { text-align: center; }
.kpi-value { font-size: 32px; font-weight: bold; line-height: 1.4; }
.kpi-label { font-size: 14px; color: #909399; margin-top: 4px; }
.quick-actions { display: flex; flex-direction: column; gap: 12px; }
.sales-info { display: flex; flex-direction: column; gap: 16px; }
.sales-row { display: flex; justify-content: space-between; font-size: 15px; padding: 0 8px; }
.sales-value { font-weight: bold; color: #67c23a; }
.sales-value.warn { color: #e6a23c; }
.sales-value.danger { color: #f56c6c; }
</style>
