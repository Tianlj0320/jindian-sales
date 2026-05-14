<template>
  <el-card shadow="never">
    <div class="page-header">
      <h3>操作日志</h3>
    </div>

    <el-form :inline="true" style="margin-bottom:16px">
      <el-form-item label="资源">
        <el-select v-model="filterResource" clearable style="width:130px" @change="loadData">
          <el-option label="订单" value="order" />
          <el-option label="客户" value="customer" />
          <el-option label="产品" value="product" />
          <el-option label="采购" value="purchase" />
          <el-option label="安装" value="installation" />
          <el-option label="财务" value="finance" />
          <el-option label="用户" value="user" />
        </el-select>
      </el-form-item>
      <el-form-item label="操作">
        <el-select v-model="filterAction" clearable style="width:120px" @change="loadData">
          <el-option label="创建" value="CREATE" />
          <el-option label="更新" value="UPDATE" />
          <el-option label="删除" value="DELETE" />
        </el-select>
      </el-form-item>
      <el-form-item label="操作人"><el-input v-model="filterKeyword" placeholder="搜索姓名" clearable style="width:150px" @keyup.enter="loadData" /></el-form-item>
      <el-form-item><el-button type="primary" @click="loadData">查询</el-button></el-form-item>
    </el-form>

    <el-table :data="list" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="created_at" label="时间" width="170">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column prop="operator_name" label="操作人" width="100" />
      <el-table-column label="操作" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="actionType(row.action)" size="small">{{ row.action }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="resource" label="资源" width="90" />
      <el-table-column label="资源ID" width="80" align="center">
        <template #default="{ row }">{{ row.resource_id || '-' }}</template>
      </el-table-column>
      <el-table-column prop="detail" label="详情" min-width="300" show-overflow-tooltip />
      <el-table-column prop="ip_address" label="IP" width="140" />
    </el-table>

    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadData"
      />
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { systemApi } from '@/api'

const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterResource = ref('')
const filterAction = ref('')
const filterKeyword = ref('')

function actionType(action) {
  const map = { CREATE: 'success', UPDATE: 'primary', DELETE: 'danger' }
  return map[action] || 'info'
}

function formatTime(t) {
  if (!t) return '-'
  const d = new Date(t)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterResource.value) params.resource = filterResource.value
    if (filterAction.value) params.action = filterAction.value
    if (filterKeyword.value) params.keyword = filterKeyword.value
    const res = await systemApi.listLogs(params)
    list.value = res.data?.items || res.items || res || []
    total.value = res.data?.total || res.total || 0
  } catch {} finally { loading.value = false }
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h3 { font-size: 18px; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
