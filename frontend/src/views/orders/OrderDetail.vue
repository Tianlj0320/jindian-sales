<template>
  <div>
    <el-button text @click="$router.back()" style="margin-bottom:8px">← 返回</el-button>

    <el-card v-if="order" shadow="never">
      <template #header>
        <div class="page-header">
          <div>
            <span class="order-no">{{ order.order_no }}</span>
            <el-tag :color="order.status_color" style="color:#fff;border:0;font-size:11px;height:22px;line-height:22px;padding:0 8px">{{ order.status_label }}</el-tag>
            <el-tag v-if="order.orig_order_no" type="info" style="margin-left:4px;cursor:pointer;font-size:11px;height:22px;line-height:22px;padding:0 8px" @click="$router.push(`/orders/${order.parent_order_id}`)">
              补单 ← {{ order.orig_order_no }}
            </el-tag>
          </div>
          <div>
            <el-dropdown style="margin-right:4px">
              <el-button size="small">打印 <el-icon><ArrowDown /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="showPreviewContract">订货合同</el-dropdown-item>
                  <el-dropdown-item @click="showPreviewMeasurement">测量记录单</el-dropdown-item>
                  <el-dropdown-item @click="showPreviewProcessing">加工单</el-dropdown-item>
                  <el-dropdown-item @click="showPreviewInstallation">安装派工单</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button size="small" @click="handleAdvance" :disabled="isTerminal" v-if="order.status_key !== 'accepted'">推进状态</el-button>
            <el-button size="small" v-if="order.status_key === 'confirmed' || order.status_key === 'split'" type="warning" @click="handleSplit" :loading="splitting">拆分采购</el-button>
            <el-button size="small" type="info" plain @click="handleOpenStatusMgr">状态管理</el-button>
            <el-button size="small" @click="$router.push(`/orders/${order.id}/edit`)">编辑</el-button>
            <el-button size="small" type="success" plain @click="handleCreateSupplementary" :loading="creatingSup">生成补单</el-button>
          </div>
        </div>
      </template>

      <!-- 客户信息 -->
      <el-descriptions :column="3" border style="margin-bottom:12px">
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
      <el-table :data="mainItems" stripe size="small" style="width:100%;margin-bottom:12px" class="compact-table">
        <el-table-column prop="room" label="空间" width="70" />
        <el-table-column prop="product_code" label="产品编码" width="80" />
        <el-table-column prop="product_name" label="产品名称" width="90" />
        <el-table-column prop="width" label="宽(m)" width="60" align="center" />
        <el-table-column prop="height" label="高(m)" width="60" align="center" />
        <el-table-column prop="fold_ratio" label="倍率" width="55" align="center" />
        <el-table-column prop="qty" label="数量" width="55" align="center" />
        <el-table-column prop="unit_price" label="单价" width="75" align="right">
          <template #default="{ row }">¥{{ row.unit_price?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="discount" label="折率" width="55" align="center" />
        <el-table-column prop="amount" label="金额" width="85" align="right">
          <template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="process_desc" label="工艺" min-width="80" show-overflow-tooltip />
      </el-table>
      <!-- 主料小计 -->
      <div style="text-align:right;margin-top:-12px;margin-bottom:10px;padding:4px 12px;background:#f5f7fa;border-radius:4px">
        <strong>主料小计：¥{{ mainTotal.toFixed(2) }}</strong>
      </div>

      <!-- 订单明细 - 辅料 -->
      <h4 style="margin-bottom:12px">辅料明细</h4>
      <el-table :data="auxItems" stripe size="small" style="width:100%;margin-bottom:12px" class="compact-table">
        <el-table-column prop="product_code" label="型号" width="80" />
        <el-table-column prop="product_name" label="名称" width="120" />
        <el-table-column prop="unit" label="单位" width="60" />
        <el-table-column prop="qty" label="数量" width="60" align="center" />
        <el-table-column prop="unit_price" label="单价" width="75" align="right">
          <template #default="{ row }">¥{{ row.unit_price?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="85" align="right">
          <template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="process_desc" label="工艺" min-width="80" show-overflow-tooltip />
      </el-table>
      <!-- 辅料小计 -->
      <div style="text-align:right;margin-top:-12px;margin-bottom:10px;padding:4px 12px;background:#f5f7fa;border-radius:4px">
        <strong>辅料小计：¥{{ auxTotal.toFixed(2) }}</strong>
      </div>

      <!-- 金额汇总 -->
      <el-descriptions :column="4" border style="margin-bottom:12px">
        <el-descriptions-item label="折前总额">¥{{ order.quote_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="折扣优惠">¥{{ order.discount_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="抹零">¥{{ order.round_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="应收金额"><strong>¥{{ order.amount?.toFixed(2) }}</strong></el-descriptions-item>
        <el-descriptions-item label="已收金额">¥{{ order.received?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="定金">¥{{ (order.deposit || 0).toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="欠款">
          <span :style="{ color: (order.debt || 0) > 0 ? '#f56c6c' : '#67c23a', fontWeight: 'bold' }">
            ¥{{ (order.debt || 0).toFixed(2) }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="优惠原因">{{ order.discount_reason || '-' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 订单费用 -->
      <h4 style="margin-bottom:12px">
        订单费用
        <el-button size="small" type="primary" plain style="margin-left:12px" @click="handleAddFee">添加费用</el-button>
      </h4>
      <el-table :data="orderFees" stripe size="small" style="width:100%;margin-bottom:12px">
        <el-table-column prop="fee_type_label" label="费用类型" width="100" />
        <el-table-column prop="amount" label="金额" width="120" align="right">
          <template #default="{ row }">¥{{ (row.amount || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="160" />
        <el-table-column prop="operator_name" label="操作人" width="80" />
        <el-table-column prop="created_at" label="时间" width="140" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="handleEditFee(row)">编辑</el-button>
            <el-popconfirm title="确认删除该费用？" @confirm="handleDeleteFee(row)">
              <template #reference>
                <el-button size="small" text type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div style="text-align:right;font-size:14px;margin-bottom:20px;color:#606266">
        费用合计：<strong style="color:#f56c6c">¥{{ feeTotal.toFixed(2) }}</strong>
        &nbsp;&nbsp;订单总应收：<strong>¥{{ (order.amount + feeTotal).toFixed(2) }}</strong>
      </div>

      <!-- 备注 -->
      <el-descriptions :column="1" border style="margin-bottom:12px">
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

      <!-- 补单列表 -->
      <template v-if="supplementaryOrders.length">
        <el-divider />
        <h4 style="margin-bottom:12px">关联补单</h4>
        <el-table :data="supplementaryOrders" stripe size="small" style="width:100%">
          <el-table-column prop="order_no" label="补单单号" width="180">
            <template #default="{ row }">
              <el-link type="primary" @click="$router.push(`/orders/${row.id}`)">{{ row.order_no }}</el-link>
            </template>
          </el-table-column>
          <el-table-column prop="status_label" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :color="row.status_color" style="color:#fff;border:0">{{ row.status_label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="金额" width="120" align="right">
            <template #default="{ row }">¥{{ (row.amount || 0).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="order_date" label="下单日期" width="120" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" @click="$router.push(`/orders/${row.id}`)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-card>

    <!-- 订单费用对话框 -->
    <el-dialog v-model="showFeeDialog" :title="feeFormTitle" width="450px" top="25vh">
      <el-form :model="feeForm" label-width="80px">
        <el-form-item label="费用类型" required>
          <el-select v-model="feeForm.fee_type" style="width:100%" @change="onFeeTypeChange">
            <el-option v-for="item in feeTypeOptions" :key="item.code" :label="item.label" :value="item.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额" required>
          <el-input v-model="feeForm.amount" type="number" step="0.01" min="0" placeholder="请输入金额" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="feeForm.remark" type="textarea" :rows="2" maxlength="200" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFeeDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveFee" :loading="savingFee">保存</el-button>
      </template>
    </el-dialog>

    <!-- 状态管理对话框 -->
    <el-dialog v-model="showStatusMgr" title="订单状态管理" width="620px" top="10vh">
      <template v-if="statusInfo">
        <el-alert :closable="false" type="info" style="margin-bottom:16px">
          <template #title>
            当前状态：<el-tag :color="statusInfo.current_color" style="color:#fff;border:0">{{ statusInfo.current_label }}</el-tag>
          </template>
        </el-alert>

        <!-- 关联采购单状态 -->
        <el-alert v-if="statusInfo.po_statuses && statusInfo.po_statuses.length" :closable="false"
          :type="statusInfo.po_statuses.some(p => p.status !== '待采购') ? 'warning' : 'info'"
          style="margin-bottom:12px">
          <template #title>
            <div>关联采购单（{{ statusInfo.po_statuses.length }} 单）</div>
            <div style="font-size:13px;font-weight:normal;margin-top:4px">
              <span v-for="(po, i) in statusInfo.po_statuses" :key="po.po_no">
                {{ po.po_no }}：<el-tag size="small" :type="po.status === '待采购' ? 'info' : 'warning'" style="margin-right:6px">{{ po.status }}</el-tag>
              </span>
            </div>
          </template>
        </el-alert>

        <h4 style="margin-bottom:12px">可回滚的状态</h4>
        <div v-if="statusInfo.rollback_options && statusInfo.rollback_options.length">
          <div class="rollback-item" v-for="opt in statusInfo.rollback_options" :key="opt.key">
            <div class="rollback-item-left">
              <el-tag :color="opt.color" style="color:#fff;border:0;width:80px;text-align:center">{{ opt.label }}</el-tag>
              <span v-if="!opt.allowed && opt.block_reason" style="color:#e6a23c;font-size:12px;max-width:260px">{{ opt.block_reason }}</span>
            </div>
            <div class="rollback-item-right">
              <el-button
                size="small"
                type="warning"
                plain
                :disabled="opt.allowed === false"
                :loading="rollingBack === opt.key"
                @click="handleRollback(opt)"
              >回滚到此状态</el-button>
            </div>
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
              {{ statusInfo.po_statuses && statusInfo.po_statuses.length
                ? '关联采购单尚在处理中，请先联系供应商确认取消后再操作。'
                : '异常处理操作将强制将订单转入异常状态。请填写原因说明后再操作。' }}
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
              <span v-if="opt.allowed === false && opt.block_reason" style="color:#e6a23c;font-size:12px;max-width:200px">{{ opt.block_reason }}</span>
            </div>
            <div class="rollback-item-right">
              <el-button
                size="small"
                :type="opt.key === 'after_sale' ? 'danger' : 'info'"
                :disabled="opt.allowed === false"
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

    <!-- 打印预览对话框 -->
    <el-dialog v-model="showPrintPreview" :title="`打印预览 - ${previewDocType}`" width="95%" top="2vh"
      :close-on-click-modal="false" destroy-on-close>
      <div class="pv-wrap">
        <div class="pv-bar">
          <span class="pv-label">{{ previewDocType }}</span>
          <span class="pv-info">A4 / 纵向</span>
          <div class="pv-spacer"></div>
          <el-button :icon="Printer" type="primary" :disabled="!iframeReady" @click="doPreviewPrint">打印</el-button>
          <el-button @click="showPrintPreview = false">关闭</el-button>
        </div>
        <div class="pv-body">
          <div class="pv-paper">
            <iframe ref="iframeRef" :srcdoc="previewHtml" class="pv-frame"
              @load="iframeReady = true" frameborder="0"></iframe>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { orderApi, systemApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, Printer } from '@element-plus/icons-vue'
import { generateContractHtml, generateMeasurementHtml, generateProcessingHtml, generateInstallationHtml } from '@/utils/print'

const route = useRoute()
const router = useRouter()
const order = ref(null)
const showStatusMgr = ref(false)
const statusInfo = ref(null)
const rollingBack = ref('')
const exceptionRemark = ref('')

// ── 打印预览 ──
const showPrintPreview = ref(false)
const previewHtml = ref('')
const previewDocType = ref('')
const iframeRef = ref(null)
const iframeReady = ref(false)

const history = computed(() => {
  const h = order.value?.history || []
  return Array.isArray(h) ? h : []
})

const mainItems = computed(() => (order.value?.items || []).filter(i => i.material_type !== '辅料'))
const auxItems = computed(() => (order.value?.items || []).filter(i => i.material_type === '辅料'))
const mainTotal = computed(() => mainItems.value.reduce((s, i) => s + (i.amount || 0), 0))
const auxTotal = computed(() => auxItems.value.reduce((s, i) => s + (i.amount || 0), 0))

const splitting = ref(false)
const creatingSup = ref(false)
const supplementaryOrders = ref([])

const isTerminal = computed(() => {
  const k = order.value?.status_key
  return ['accepted', 'cancelled', 'after_sale'].includes(k)
})

// ── 订单费用 ──
const orderFees = ref([])
const showFeeDialog = ref(false)
const savingFee = ref(false)
const editingFeeId = ref(null)
const feeTypeOptions = ref([])
const feeForm = ref({ fee_type: '', fee_type_label: '', amount: null, remark: '' })
const feeFormTitle = computed(() => editingFeeId.value ? '编辑费用' : '添加费用')

const feeTotal = computed(() => {
  return orderFees.value.reduce((sum, f) => sum + (f.amount || 0), 0)
})

async function loadFees() {
  try {
    const res = await orderApi.listFees(route.params.id)
    orderFees.value = Array.isArray(res.data) ? res.data : []
  } catch {}
}

async function loadFeeTypeOptions() {
  try {
    const res = await systemApi.getDict('order_fee_type')
    feeTypeOptions.value = Array.isArray(res.data) ? res.data : []
  } catch {}
}

function onFeeTypeChange(code) {
  const opt = feeTypeOptions.value.find(o => o.code === code)
  feeForm.value.fee_type_label = opt ? opt.label : code
}

function handleAddFee() {
  editingFeeId.value = null
  feeForm.value = { fee_type: '', fee_type_label: '', amount: null, remark: '' }
  showFeeDialog.value = true
}

function handleEditFee(row) {
  editingFeeId.value = row.id
  feeForm.value = {
    fee_type: row.fee_type,
    fee_type_label: row.fee_type_label,
    amount: row.amount,
    remark: row.remark,
  }
  showFeeDialog.value = true
}

async function handleSaveFee() {
  if (!feeForm.value.fee_type) {
    ElMessage.warning('请选择费用类型')
    return
  }
  if (!feeForm.value.amount || feeForm.value.amount <= 0) {
    ElMessage.warning('请输入金额')
    return
  }
  savingFee.value = true
  try {
    if (editingFeeId.value) {
      await orderApi.updateFee(route.params.id, editingFeeId.value, feeForm.value)
      ElMessage.success('费用更新成功')
    } else {
      await orderApi.createFee(route.params.id, feeForm.value)
      ElMessage.success('费用添加成功')
    }
    showFeeDialog.value = false
    await loadFees()
    await load() // refresh order totals
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    savingFee.value = false
  }
}

async function handleDeleteFee(row) {
  try {
    await orderApi.deleteFee(route.params.id, row.id)
    ElMessage.success('费用已删除')
    await loadFees()
  } catch (e) {
    ElMessage.error(e.message || '删除失败')
  }
}

async function load() {
  try {
    const res = await orderApi.get(route.params.id)
    order.value = res.data
    await loadSupplementary()
    await loadFees()
  } catch {}
}

// ── 打印预览 ──
async function showPreviewContract() {
  try {
    const res = await systemApi.getStoreInfo()
    previewHtml.value = generateContractHtml(order.value, res.data)
  } catch {
    previewHtml.value = generateContractHtml(order.value, {})
  }
  previewDocType.value = '订货合同'
  iframeReady.value = false
  showPrintPreview.value = true
}

function showPreviewMeasurement() {
  previewHtml.value = generateMeasurementHtml(order.value)
  previewDocType.value = '测量记录单'
  iframeReady.value = false
  showPrintPreview.value = true
}

function showPreviewProcessing() {
  previewHtml.value = generateProcessingHtml(order.value)
  previewDocType.value = '加工单'
  iframeReady.value = false
  showPrintPreview.value = true
}

function showPreviewInstallation() {
  previewHtml.value = generateInstallationHtml(order.value)
  previewDocType.value = '安装派工单'
  iframeReady.value = false
  showPrintPreview.value = true
}

function doPreviewPrint() {
  const el = iframeRef.value
  if (el && el.contentWindow) {
    el.contentWindow.focus()
    el.contentWindow.print()
  }
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

async function handleCreateSupplementary() {
  creatingSup.value = true
  try {
    const res = await orderApi.createSupplementary(route.params.id)
    ElMessage.success(res.message || '补单创建成功')
    // 跳转到新补单编辑页
    if (res.data && res.data.id) {
      showStatusMgr.value = false
      await load()
      router.push(`/orders/${res.data.id}/edit`)
    }
  } catch (e) {
    ElMessage.error(e.message || '创建补单失败')
  } finally {
    creatingSup.value = false
  }
}

async function loadSupplementary() {
  if (!order.value) return
  try {
    const res = await orderApi.listSupplementary(route.params.id)
    supplementaryOrders.value = Array.isArray(res.data) ? res.data : []
  } catch {}
}

onMounted(() => {
  load()
  loadSupplementary()
  loadFeeTypeOptions()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; }
.order-no { font-size: 15px; font-weight: bold; margin-right: 8px; }

/* 紧凑表格样式 */
.compact-table { font-size: 11px; }
.compact-table :deep(.el-table__header th) { padding: 1px 0; font-size: 11px; line-height: 1.4; }
.compact-table :deep(.el-table__cell) { padding: 1px 2px; }
.compact-table :deep(.el-table__body td) { padding: 1px 2px; line-height: 1.4; }
.compact-table :deep(.el-table__inner-wrapper) { border: none; }
.compact-table :deep(.el-table__border) { display: none; }
.compact-table :deep(table) { border-collapse: collapse; }

/* 页面紧凑 */
:deep(.el-card__body) { padding: 10px 14px; }
h4 { margin: 0 0 4px 0; font-size: 13px; }
.el-descriptions :deep(.el-descriptions__cell) { padding: 4px 6px; }
.el-descriptions :deep(.el-descriptions__label) { font-size: 11px; }
.el-descriptions :deep(.el-descriptions__content) { font-size: 11px; }
.el-card :deep(.el-card__header) { padding: 8px 14px; }
.rollback-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}
.rollback-item:last-child { border-bottom: none; }
.rollback-item-left { display: flex; align-items: center; gap: 8px; }

/* 打印预览 */
.pv-wrap { display: flex; flex-direction: column; }
.pv-bar { display: flex; align-items: center; padding: 0 0 10px 0; gap: 8px; border-bottom: 1px solid #e8e8e8; margin-bottom: 10px; }
.pv-label { font-weight: bold; font-size: 15px; }
.pv-info { color: #999; font-size: 12px; }
.pv-spacer { flex: 1; }
.pv-body { flex: 1; overflow: auto; background: #e8e8e8; display: flex; justify-content: center; padding: 20px; border-radius: 4px; min-height: 65vh; }
.pv-paper { width: 100%; max-width: 210mm; min-height: 297mm; background: #fff; box-shadow: 0 2px 12px rgba(0,0,0,0.12); }
.pv-frame { width: 100%; max-width: 210mm; height: 297mm; border: none; display: block; }
</style>
