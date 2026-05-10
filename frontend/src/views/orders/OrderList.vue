<template>
  <el-card shadow="never">
    <div class="page-header">
      <h3>订单管理</h3>
      <el-button type="primary" @click="$router.push('/orders/new')">新建订单</el-button>
    </div>

    <el-form :inline="true" style="margin-bottom:16px">
      <el-form-item label="搜索">
        <el-input v-model="query.keyword" placeholder="订单号/客户" clearable @clear="loadData" @keyup.enter="loadData" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="query.status_key" clearable style="width:130px" @change="loadData">
          <el-option v-for="s in statusOptions" :key="s.key" :label="s.label" :value="s.key">
            <span :style="{ color: s.color }">{{ s.label }}</span>
          </el-option>
        </el-select>
      </el-form-item>
      <el-form-item label="日期">
        <el-date-picker v-model="query.date_from" type="date" placeholder="开始" value-format="YYYY-MM-DD" @change="loadData" />
        <span style="margin:0 8px">至</span>
        <el-date-picker v-model="query.date_to" type="date" placeholder="结束" value-format="YYYY-MM-DD" @change="loadData" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadData">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="list" v-loading="loading" stripe style="width:100%" @row-click="(r) => $router.push(`/orders/${r.id}`)">
      <el-table-column prop="order_no" label="订单号" width="160" />
      <el-table-column prop="customer_name" label="客户" width="120" />
      <el-table-column prop="customer_phone" label="电话" width="130" />
      <el-table-column prop="order_type" label="类型" width="70" />
      <el-table-column prop="content" label="内容" min-width="160" />
      <el-table-column prop="amount" label="金额" width="110" align="right">
        <template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column prop="received" label="已收" width="100" align="right">
        <template #default="{ row }">¥{{ row.received?.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column prop="debt" label="欠款" width="100" align="right">
        <template #default="{ row }">
          <span :style="{ color: row.debt > 0 ? '#f56c6c' : '#67c23a' }">
            ¥{{ row.debt?.toFixed(2) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :color="row.status_color" style="color:#fff;border:0">{{ row.status_label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="order_date" label="下单日期" width="110" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" @click.stop="$router.push(`/orders/${row.id}`)">详情</el-button>
          <el-button text size="small" type="primary" @click.stop="handleAdvance(row)" :disabled="isTerminal(row.status_key)">推进</el-button>
          <el-button v-if="row.status_key === 'confirmed'" text size="small" type="warning" @click.stop="handleShowSplitPreview(row)">拆分</el-button>
          <el-popconfirm v-if="row.status_key === 'initial'" title="确认删除？" @confirm="handleDelete(row.id)">
            <template #reference><el-button text size="small" type="danger" @click.stop>删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <div style="margin-top:16px;text-align:right">
      <el-pagination v-model:current-page="query.page" :page-size="query.page_size" :total="total" layout="total, prev, pager, next" @current-change="loadData" />
    </div>
  </el-card>

  <!-- 采购拆分预览对话框 -->
  <el-dialog v-model="showPreview" title="采购拆分预览" width="800px" top="5vh" :close-on-click-modal="false">
    <template v-if="previewData">
      <el-alert :closable="false" type="info" style="margin-bottom:16px">
        <template #title>
          待拆分订单共 <strong>{{ previewData.order_count }}</strong> 单：
          <strong>{{ (previewData.order_nos || []).join('、') }}</strong>
        </template>
      </el-alert>

      <!-- 主料采购单 -->
      <template v-if="previewData.main_orders && previewData.main_orders.length">
        <h4 style="margin:0 0 8px;color:#409eff">主料采购单 ({{ previewData.main_orders.length }} 张)</h4>
        <el-card v-for="(po, pi) in previewData.main_orders" :key="'m'+pi" shadow="hover" style="margin-bottom:12px">
          <div class="po-header">
            <strong>{{ po.supplier_name }}</strong>
            <span class="po-header-info">联系人: {{ po.contact || '-' }} / {{ po.phone || '-' }}</span>
          </div>
          <div v-if="po.bank_account" class="po-header-info" style="font-size:12px;color:#999;margin-bottom:4px">
            收款: {{ po.bank_name || '-' }} {{ po.bank_account || '-' }} {{ po.payee || '-' }}
          </div>
          <el-table :data="po.items" size="small" stripe style="width:100%">
            <el-table-column prop="product_name" label="产品" min-width="120" />
            <el-table-column label="规格" min-width="130">
              <template #default="{ row }">{{ (row.specs || []).join('；') || '-' }}</template>
            </el-table-column>
            <el-table-column prop="qty" label="数量" width="70" align="center" />
            <el-table-column prop="unit_price" label="单价" width="80" align="right">
              <template #default="{ row }">¥{{ row.unit_price?.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="amount" label="小计" width="90" align="right">
              <template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template>
            </el-table-column>
          </el-table>
          <div style="text-align:right;margin-top:4px;font-weight:bold;color:#f56c6c">
            小计: ¥{{ po.total_amount?.toFixed(2) }} ({{ po.item_count }} 项)
          </div>
        </el-card>
      </template>

      <!-- 辅料采购单 -->
      <template v-if="previewData.aux_orders && previewData.aux_orders.length">
        <h4 style="margin:12px 0 8px;color:#f59e0b">辅料集中采购单 ({{ previewData.aux_orders.length }} 张)</h4>
        <el-card v-for="(po, pi) in previewData.aux_orders" :key="'a'+pi" shadow="hover" style="margin-bottom:12px">
          <div class="po-header">
            <strong>{{ po.supplier_name }}</strong>
            <span class="po-header-info">联系人: {{ po.contact || '-' }} / {{ po.phone || '-' }}</span>
          </div>
          <el-table :data="po.items" size="small" stripe style="width:100%">
            <el-table-column prop="product_name" label="产品" min-width="120" />
            <el-table-column prop="qty" label="数量" width="70" align="center" />
            <el-table-column prop="unit_price" label="单价" width="80" align="right">
              <template #default="{ row }">¥{{ row.unit_price?.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="amount" label="小计" width="90" align="right">
              <template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template>
            </el-table-column>
          </el-table>
          <div style="text-align:right;margin-top:4px;font-weight:bold;color:#f56c6c">
            小计: ¥{{ po.total_amount?.toFixed(2) }} ({{ po.item_count }} 项)
          </div>
        </el-card>
      </template>

      <div v-if="!previewData.main_orders?.length && !previewData.aux_orders?.length" style="text-align:center;padding:32px;color:#999">
        没有需要拆分采购的订单明细
      </div>
    </template>
    <template #footer>
      <el-button @click="showPreview = false">取消</el-button>
      <el-button type="primary" :loading="splitting" @click="handleConfirmSplit">
        确认拆分
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { orderApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const list = ref([])
const total = ref(0)
const loading = ref(false)
const splitting = ref(false)
const statusOptions = ref([])

const query = reactive({ keyword: '', status_key: '', date_from: '', date_to: '', page: 1, page_size: 20 })

// 拆分预览
const showPreview = ref(false)
const previewData = ref(null)

async function loadData() {
  loading.value = true
  try {
    const params = { ...query }
    if (!params.date_from) delete params.date_from
    if (!params.date_to) delete params.date_to
    const res = await orderApi.list(params)
    list.value = res.items
    total.value = res.total
  } catch {} finally { loading.value = false }
}

async function handleAdvance(row) {
  try {
    const res = await orderApi.advance(row.id)
    // 如果返回 need_preview，需要操作员确认拆分方案
    if (res.data && res.data.need_preview) {
      previewData.value = res.data.preview
      showPreview.value = true
      return
    }
    ElMessage.success('订单已推进')
    loadData()
  } catch {}
}

async function handleShowSplitPreview(row) {
  try {
    const res = await orderApi.splitPreview()
    previewData.value = res.data
    showPreview.value = true
  } catch (e) {
    ElMessage.warning(e.message || '没有已确认的订单可拆分')
  }
}

async function handleConfirmSplit() {
  splitting.value = true
  try {
    const res = await orderApi.confirmSplit()
    ElMessage.success(res.message || '拆分成功')
    showPreview.value = false
    previewData.value = null
    loadData()
  } catch (e) {
    ElMessage.error(e.message || '拆分失败')
  } finally {
    splitting.value = false
  }
}

async function handleDelete(id) {
  await orderApi.delete(id)
  ElMessage.success('已删除')
  loadData()
}

function isTerminal(key) {
  return ['accepted', 'cancelled', 'after_sale'].includes(key)
}

onMounted(async () => {
  try {
    const res = await orderApi.statusOptions()
    statusOptions.value = res.items || res.data || res || []
  } catch {}
  loadData()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h3 { font-size: 18px; }
.po-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 14px; }
.po-header-info { font-size: 12px; color: #666; }
</style>
