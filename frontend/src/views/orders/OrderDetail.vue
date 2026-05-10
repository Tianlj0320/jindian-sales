<template>
  <div>
    <el-button text @click="$router.back()" style="margin-bottom:16px">← 返回</el-button>

    <el-card v-if="order" shadow="never">
      <template #header>
        <div class="page-header">
          <div>
            <h3 style="display:inline;margin-right:12px">{{ order.order_no }}</h3>
            <el-tag :color="order.status_color" style="color:#fff;border:0">{{ order.status_label }}</el-tag>
          </div>
          <div>
            <el-dropdown style="margin-right:8px">
              <el-button>打印 <el-icon><ArrowDown /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="printContract(order)">订货合同</el-dropdown-item>
                  <el-dropdown-item @click="printMeasurement(order)">测量记录单</el-dropdown-item>
                  <el-dropdown-item @click="printProcessing(order)">加工单</el-dropdown-item>
                  <el-dropdown-item @click="printInstallation(order)">安装派工单</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button @click="handleAdvance" :disabled="isTerminal" v-if="order.status_key !== 'accepted'">推进状态</el-button>
            <el-button v-if="order.status_key === 'confirmed' || order.status_key === 'split'" type="warning" @click="handleSplit" :loading="splitting">拆分采购</el-button>
            <el-button type="info" plain @click="handleOpenStatusMgr">状态管理</el-button>
            <el-button @click="$router.push(`/orders/${order.id}/edit`)">编辑</el-button>
          </div>
        </div>
      </template>

      <!-- 客户信息 -->
      <el-descriptions :column="3" border style="margin-bottom:20px">
        <el-descriptions-item label="客户姓名">{{ order.customer_name }}</el-descriptions-item>
        <el-descriptions-item label="电话">{{ order.customer_phone }}</el-descriptions-item>
        <el-descriptions-item label="业务员">{{ order.salesperson_name }}</el-descriptions-item>
        <el-descriptions-item label="订单类型">{{ order.order_type }}</el-descriptions-item>
        <el-descriptions-item label="下单日期">{{ order.order_date }}</el-descriptions-item>
        <el-descriptions-item label="交货日期">{{ order.delivery_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="交货方式">{{ order.delivery_method }}</el-descriptions-item>
        <el-descriptions-item label="安装地址">{{ order.install_address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="安装日期">{{ order.install_date || '-' }} {{ order.install_time_slot || '' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 订单明细 - 主料 -->
      <h4 style="margin-bottom:12px">主料明细</h4>
      <el-table :data="mainItems" stripe size="small" style="width:100%;margin-bottom:20px">
        <el-table-column prop="room" label="空间" width="80" />
        <el-table-column prop="product_code" label="产品编码" width="100" />
        <el-table-column prop="product_name" label="产品名称" width="130" />
        <el-table-column prop="width" label="宽(m)" width="70" align="center" />
        <el-table-column prop="height" label="高(m)" width="70" align="center" />
        <el-table-column prop="fold_ratio" label="倍率" width="60" align="center" />
        <el-table-column prop="qty" label="数量" width="60" align="center" />
        <el-table-column prop="unit_price" label="单价" width="90" align="right">
          <template #default="{ row }">¥{{ row.unit_price?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="discount" label="折率" width="60" align="center" />
        <el-table-column prop="amount" label="金额" width="100" align="right">
          <template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template>
        </el-table-column>
      </el-table>

      <!-- 订单明细 - 辅料 -->
      <h4 style="margin-bottom:12px">辅料明细</h4>
      <el-table :data="auxItems" stripe size="small" style="width:100%;margin-bottom:20px">
        <el-table-column prop="product_name" label="产品名称" width="180" />
        <el-table-column prop="unit" label="单位" width="70" />
        <el-table-column prop="qty" label="数量" width="70" align="center" />
        <el-table-column prop="unit_price" label="单价" width="90" align="right">
          <template #default="{ row }">¥{{ row.unit_price?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="100" align="right">
          <template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template>
        </el-table-column>
      </el-table>

      <!-- 金额汇总 -->
      <el-descriptions :column="4" border style="margin-bottom:20px">
        <el-descriptions-item label="报价金额">¥{{ order.quote_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="优惠金额">¥{{ order.discount_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="抹零">¥{{ order.round_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="应收金额"><strong>¥{{ order.amount?.toFixed(2) }}</strong></el-descriptions-item>
        <el-descriptions-item label="已收金额">¥{{ order.received?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="欠款">
          <span :style="{ color: (order.debt || 0) > 0 ? '#f56c6c' : '#67c23a', fontWeight: 'bold' }">
            ¥{{ (order.debt || 0).toFixed(2) }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="优惠原因" :span="2">{{ order.discount_reason || '-' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 备注 -->
      <el-descriptions :column="1" border style="margin-bottom:20px">
        <el-descriptions-item label="备注">{{ order.remark || '-' }}</el-descriptions-item>
        <el-descriptions-item label="内容">{{ order.content || '-' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 状态变更历史 -->
      <h4 style="margin-bottom:12px">状态历史</h4>
      <el-timeline style="max-width:600px">
        <el-timeline-item
          v-for="(h, i) in history"
          :key="i"
          :timestamp="h.time || h.created_at"
          placement="top"
        >
          <div>
            <el-tag size="small" :color="h.color || '#909399'" style="color:#fff;border:0;margin-right:8px">
              {{ h.to_label || h.s2 || h.status_label }}
            </el-tag>
            <span style="color:#909399;font-size:13px">{{ h.operator ? `操作人: ${h.operator}` : '' }}</span>
          </div>
          <div v-if="h.s" style="color:#666;font-size:13px;margin-top:4px">从: {{ h.s }}</div>
          <div v-if="h.detail" style="color:#409eff;font-size:13px;margin-top:4px">{{ h.detail }}</div>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <!-- 状态管理对话框 -->
    <el-dialog v-model="showStatusMgr" title="订单状态管理" width="580px" top="10vh">
      <template v-if="statusInfo">
        <el-alert :closable="false" type="info" style="margin-bottom:16px">
          <template #title>
            当前状态：<el-tag :color="statusInfo.current_color" style="color:#fff;border:0">{{ statusInfo.current_label }}</el-tag>
          </template>
        </el-alert>

        <h4 style="margin-bottom:12px">可回滚的状态</h4>
        <div v-if="statusInfo.rollback_options && statusInfo.rollback_options.length">
          <div class="rollback-item" v-for="opt in statusInfo.rollback_options" :key="opt.key">
            <div class="rollback-item-left">
              <el-tag :color="opt.color" style="color:#fff;border:0;width:80px;text-align:center">{{ opt.label }}</el-tag>
            </div>
            <div class="rollback-item-right">
              <el-button
                size="small"
                type="warning"
                plain
                :loading="rollingBack === opt.key"
                @click="handleRollback(opt)"
              >回滚到此状态</el-button>
            </div>
          </div>
          <div v-if="!statusInfo.rollback_options.length" style="color:#999;padding:16px;text-align:center">
            没有可回滚的状态
          </div>
        </div>
        <div v-else style="text-align:center;padding:32px;color:#999">
          该订单尚未经过其他状态，无法回滚
        </div>

        <!-- 异常处理 -->
        <div v-if="statusInfo.exception_options && statusInfo.exception_options.length">
          <el-divider />
          <h4 style="margin-bottom:12px;color:#e6a23c">异常处理</h4>
          <el-alert type="warning" :closable="false" style="margin-bottom:12px">
            <template #title>
              以下操作将强制将订单转入异常状态。请填写原因说明后再操作。
            </template>
          </el-alert>
          <el-input
            v-model="exceptionRemark"
            type="textarea"
            :rows="2"
            placeholder="请填写异常处理原因（必填），如：客户投诉质量、客户要求退款等"
            style="margin-bottom:12px"
          />
          <div class="rollback-item" v-for="opt in statusInfo.exception_options" :key="opt.key">
            <div class="rollback-item-left">
              <el-tag :color="opt.color" style="color:#fff;border:0;width:80px;text-align:center">{{ opt.label }}</el-tag>
              <span style="color:#999;font-size:13px">{{ opt.description }}</span>
            </div>
            <div class="rollback-item-right">
              <el-button
                size="small"
                :type="opt.key === 'after_sale' ? 'danger' : 'info'"
                :loading="rollingBack === opt.key"
                @click="handleExceptionRollback(opt)"
              >{{ opt.key === 'after_sale' ? '转入售后' : '取消订单' }}</el-button>
            </div>
          </div>
        </div>

        <el-divider />
        <p style="color:#999;font-size:13px">
          提示：异常处理需填写原因说明，操作后关联的采购单和安装单将被清除。
        </p>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { orderApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { printContract, printMeasurement, printProcessing, printInstallation } from '@/utils/print'

const route = useRoute()
const order = ref(null)
const showStatusMgr = ref(false)
const statusInfo = ref(null)
const rollingBack = ref('')
const exceptionRemark = ref('')

const history = computed(() => {
  const h = order.value?.history || []
  return Array.isArray(h) ? h : []
})

const mainItems = computed(() => (order.value?.items || []).filter(i => i.material_type !== '辅料'))
const auxItems = computed(() => (order.value?.items || []).filter(i => i.material_type === '辅料'))

const splitting = ref(false)

const isTerminal = computed(() => {
  const k = order.value?.status_key
  return ['accepted', 'cancelled', 'after_sale'].includes(k)
})

async function load() {
  try {
    const res = await orderApi.get(route.params.id)
    order.value = res.data
  } catch {}
}

async function handleAdvance() {
  try {
    const res = await orderApi.advance(route.params.id)
    if (res.data && res.data.need_preview) {
      ElMessage.info('请先确认拆分方案')
      showStatusMgr.value = false
      return
    }
    ElMessage.success(res.message || '状态已推进')
    load()
  } catch {}
}

async function handleSplit() {
  splitting.value = true
  try {
    const res = await orderApi.split(route.params.id)
    const poNos = res?.data?.po_nos || []
    ElMessage.success(`已拆分为 ${poNos.length} 张采购单`)
    load()
  } catch {} finally { splitting.value = false }
}

// 状态管理
function handleOpenStatusMgr() {
  showStatusMgr.value = true
  exceptionRemark.value = ''
  loadStatusOptions()
}

async function loadStatusOptions() {
  try {
    const res = await orderApi.rollbackOptions(route.params.id)
    statusInfo.value = res.data
  } catch (e) {
    ElMessage.warning(e.message || '无法加载状态信息')
    showStatusMgr.value = false
  }
}

async function handleRollback(opt) {
  try {
    await ElMessageBox.confirm(
      `确定将订单回滚到「${opt.label}」状态？\n此操作用于异常处理，请谨慎操作。`,
      '确认回滚',
      { type: 'warning', confirmButtonText: '确认回滚', cancelButtonText: '取消' }
    )
  } catch {
    return // 用户取消
  }

  rollingBack.value = opt.key
  try {
    const res = await orderApi.rollbackStatus(route.params.id, { status_key: opt.key })
    ElMessage.success(res.message || `已回滚到「${opt.label}」`)
    showStatusMgr.value = false
    load()
  } catch (e) {
    ElMessage.error(e.message || '回滚失败')
  } finally {
    rollingBack.value = ''
  }
}

async function handleExceptionRollback(opt) {
  if (!exceptionRemark.value.trim()) {
    ElMessage.warning('请填写异常处理原因说明')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定将订单强制转入「${opt.label}」？\n原因: ${exceptionRemark.value}\n\n该操作不可逆，关联的采购单和安装单将被清除。`,
      '确认异常处理',
      { type: 'warning', confirmButtonText: '确认处理', cancelButtonText: '取消' }
    )
  } catch {
    return
  }

  rollingBack.value = opt.key
  try {
    const res = await orderApi.rollbackStatus(route.params.id, {
      status_key: opt.key,
      remark: exceptionRemark.value,
    })
    ElMessage.success(res.message || `状态已跳转至「${opt.label}」`)
    showStatusMgr.value = false
    exceptionRemark.value = ''
    load()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    rollingBack.value = ''
  }
}

onMounted(load)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h3 { font-size: 18px; }
.rollback-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}
.rollback-item:last-child { border-bottom: none; }
.rollback-item-left { display: flex; align-items: center; gap: 8px; }
</style>
