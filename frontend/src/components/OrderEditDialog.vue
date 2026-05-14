<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑订单' : '新建订单'"
    width="92%"
    top="3vh"
    :close-on-click-modal="false"
    destroy-on-close
    @open="onOpen"
  >
    <el-form :model="form" label-width="80px" size="small" @keydown.enter="handleEnterKey">
      <!-- ===== 第一行：客户 ===== -->
      <el-row :gutter="10">
        <el-col :span="8">
          <el-form-item label="客户">
            <el-input v-model="form.customer_name" placeholder="点击选择客户" readonly style="width:calc(100% - 40px)">
              <template #suffix>
                <el-button link type="primary" @click="showCustomerSelect = true">选择</el-button>
              </template>
            </el-input>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="电话">
            <el-input v-model="form.customer_phone" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="业务员">
            <el-input v-model="form.salesperson_name" disabled />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- ===== 第二行：订单信息 ===== -->
      <el-row :gutter="10">
        <el-col :span="6">
          <el-form-item label="订单类型">
            <el-select v-model="form.order_type" style="width:100%">
              <el-option label="窗帘" value="窗帘" />
              <el-option label="成品帘" value="成品帘" />
              <el-option label="软包" value="软包" />
              <el-option label="其他" value="其他" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="下单日期">
            <el-date-picker v-model="form.order_date" type="date" value-format="YYYY-MM-DD" style="width:100%" @change="onOrderDateChange" />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="交货日期">
            <el-date-picker v-model="form.delivery_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="交货方式">
            <el-select v-model="form.delivery_method" style="width:100%">
              <el-option label="上门安装" value="上门安装" />
              <el-option label="自提" value="自提" />
              <el-option label="发货" value="发货" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <!-- ===== 第三行：安装信息 ===== -->
      <el-row :gutter="10">
        <el-col :span="6">
          <el-form-item label="安装地址">
            <el-input v-model="form.install_address" />
          </el-form-item>
        </el-col>
        <el-col :span="4">
          <el-form-item label="安装日期">
            <el-date-picker v-model="form.install_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item>
        </el-col>
        <el-col :span="4">
          <el-form-item label="安装时段">
            <el-select v-model="form.install_time_slot" style="width:100%" clearable>
              <el-option label="上午(8-12点)" value="上午" />
              <el-option label="下午(12-18点)" value="下午" />
              <el-option label="全天" value="全天" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="5">
          <el-form-item label="订单编号">
            <el-input v-model="form.order_no" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="5" v-if="isEdit">
          <el-form-item label="订单状态">
            <el-tag :color="form.status_color" style="color:#fff;border:0">{{ form.status_label }}</el-tag>
          </el-form-item>
        </el-col>
      </el-row>

      <!-- ===== 订单明细 ===== -->
      <el-divider content-position="left">面料/物料</el-divider>

      <el-table ref="mainTableRef" data-table="main" :data="mainItems" stripe style="width:100%" size="small" class="compact-table">
        <el-table-column type="index" label="序号" width="50" />
        <el-table-column label="空间" width="70">
          <template #default="{ $index }">
            <el-select v-model="mainItems[$index].room" placeholder="空间" style="width:60px" size="small" @change="onRoomChange(true, $index)">
              <el-option label="客厅" value="客厅" />
              <el-option label="主卧" value="主卧" />
              <el-option label="次卧" value="次卧" />
              <el-option label="书房" value="书房" />
              <el-option label="餐厅" value="餐厅" />
              <el-option label="阳台" value="阳台" />
              <el-option label="其他" value="其他" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="产品编码" width="155">
          <template #default="{ $index }">
            <el-autocomplete
              v-model="mainItems[$index].product_code"
              :fetch-suggestions="(q, cb) => searchProducts(q, cb, true, $index)"
              :trigger-on-focus="true"
              placeholder="搜索产品"
              clearable
              value-key="code"
              @select="(item) => { handleProductSelect(item, true, $index); onProductAutoselect(true, $index) }"
              @clear="handleProductClear(true, $index)"
              style="width:100%"
              size="small"
            >
              <template #default="{ item }">
                <div style="display:flex;justify-content:space-between;font-size:12px">
                  <span><strong>{{ item.code }}</strong> - {{ item.name }}</span>
                  <span style="color:#909399">¥{{ item.selling_price }}</span>
                </div>
              </template>
            </el-autocomplete>
          </template>
        </el-table-column>
        <el-table-column label="产品名称" width="200">
          <template #default="{ $index }">
            <el-input v-model="mainItems[$index].product_name" placeholder="自动" size="small" disabled />
          </template>
        </el-table-column>
        <el-table-column label="宽(m)" width="80">
          <template #default="{ $index }">
            <el-input v-model.number="mainItems[$index].width" placeholder="0" size="small" @input="onItemInput(true, $index)" />
          </template>
        </el-table-column>
        <el-table-column label="高(m)" width="80">
          <template #default="{ $index }">
            <el-input v-model.number="mainItems[$index].height" placeholder="0" size="small" @input="onItemInput(true, $index)" />
          </template>
        </el-table-column>
        <!-- 倍率列隐藏，保留默认值用于计算 -->
        <el-table-column v-if="false" label="倍率" width="70">
          <template #default="{ $index }">
            <el-input v-model.number="mainItems[$index].fold_ratio" placeholder="2.0" size="small" @input="onItemInput(true, $index)" />
          </template>
        </el-table-column>
        <el-table-column label="幅数" width="70">
          <template #default="{ $index }">
            <el-input v-model.number="mainItems[$index].panel_count" placeholder="0" size="small" @input="onItemInput(true, $index)" />
          </template>
        </el-table-column>
        <el-table-column label="数量" width="70">
          <template #default="{ $index }">
            <el-input v-model.number="mainItems[$index].qty" placeholder="自动" size="small" @input="onItemInput(true, $index)" />
          </template>
        </el-table-column>
        <el-table-column label="单价" width="90">
          <template #default="{ $index }">
            <el-input v-model.number="mainItems[$index].unit_price" placeholder="0" size="small" @input="onItemInput(true, $index)" />
          </template>
        </el-table-column>
        <el-table-column label="折率" width="70">
          <template #default="{ $index }">
            <el-input v-model.number="mainItems[$index].discount" placeholder="1.0" size="small" @input="onItemInput(true, $index)" />
          </template>
        </el-table-column>
        <el-table-column label="金额" width="90" align="right">
          <template #default="{ $index }">
            ¥{{ (mainItems[$index].amount || 0).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column label="采购类型" width="80">
          <template #default="{ $index }">
            <el-select v-model="mainItems[$index].procurement_type" size="small" style="width:68px" @change="onItemInput(true, $index)">
              <el-option label="物料" value="物料" />
              <el-option label="成品" value="成品" />
              <el-option label="辅料" value="辅料" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="工艺" width="200">
          <template #default="{ $index }">
            <el-input v-model="mainItems[$index].process_desc" placeholder="工艺" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="50" fixed="right">
          <template #default="{ $index }">
            <el-button text size="small" type="danger" @click="removeItem(true, $index)" :disabled="mainItems.length <= 1">×</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin:4px 0">
        <el-button size="small" @click="addItem(true)">+ 添加面料行</el-button>
        <span style="margin-left:12px;font-weight:bold;color:#409eff">面料小计：¥{{ mainSubtotal.toFixed(2) }}</span>
      </div>

      <!-- ===== 辅料 ===== -->
      <el-divider content-position="left">辅料/配件</el-divider>

      <el-table ref="auxTableRef" data-table="aux" :data="auxItems" stripe style="width:100%" size="small" class="compact-table">
        <el-table-column type="index" label="序号" width="50" />
        <el-table-column label="空间" width="70">
          <template #default="{ $index }">
            <el-select v-model="auxItems[$index].room" placeholder="空间" style="width:60px" size="small" @change="onRoomChange(false, $index)">
              <el-option label="客厅" value="客厅" />
              <el-option label="主卧" value="主卧" />
              <el-option label="次卧" value="次卧" />
              <el-option label="书房" value="书房" />
              <el-option label="餐厅" value="餐厅" />
              <el-option label="阳台" value="阳台" />
              <el-option label="其他" value="其他" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="产品编码" width="120">
          <template #default="{ $index }">
            <el-autocomplete
              v-model="auxItems[$index].product_code"
              :fetch-suggestions="(q, cb) => searchProducts(q, cb, false, $index)"
              :trigger-on-focus="true"
              placeholder="搜索产品"
              clearable
              value-key="code"
              @select="(item) => { handleProductSelect(item, false, $index); onProductAutoselect(false, $index) }"
              @clear="handleProductClear(false, $index)"
              style="width:100%"
              size="small"
            >
              <template #default="{ item }">
                <div style="display:flex;justify-content:space-between;font-size:12px">
                  <span><strong>{{ item.code }}</strong> - {{ item.name }}</span>
                  <span style="color:#909399">¥{{ item.selling_price }}</span>
                </div>
              </template>
            </el-autocomplete>
          </template>
        </el-table-column>
        <el-table-column label="产品名称" width="100">
          <template #default="{ $index }">
            <el-input v-model="auxItems[$index].product_name" placeholder="自动" size="small" disabled />
          </template>
        </el-table-column>
        <el-table-column label="数量" width="60">
          <template #default="{ $index }">
            <el-input v-model.number="auxItems[$index].qty" placeholder="1" size="small" @input="onItemInput(false, $index)" />
          </template>
        </el-table-column>
        <el-table-column label="单价" width="75">
          <template #default="{ $index }">
            <el-input v-model.number="auxItems[$index].unit_price" placeholder="0" size="small" @input="onItemInput(false, $index)" />
          </template>
        </el-table-column>
        <el-table-column label="折率" width="55">
          <template #default="{ $index }">
            <el-input v-model.number="auxItems[$index].discount" placeholder="1.0" size="small" @input="onItemInput(false, $index)" />
          </template>
        </el-table-column>
        <el-table-column label="金额" width="85" align="right">
          <template #default="{ $index }">
            ¥{{ (auxItems[$index].amount || 0).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column label="采购类型" width="80">
          <template #default="{ $index }">
            <el-select v-model="auxItems[$index].procurement_type" size="small" style="width:68px" @change="onItemInput(false, $index)">
              <el-option label="物料" value="物料" />
              <el-option label="成品" value="成品" />
              <el-option label="辅料" value="辅料" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="50" fixed="right">
          <template #default="{ $index }">
            <el-button text size="small" type="danger" @click="removeItem(false, $index)" :disabled="auxItems.length <= 1">×</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin:4px 0">
        <el-button size="small" @click="addItem(false)">+ 添加辅料行</el-button>
        <span style="margin-left:12px;font-weight:bold;color:#e6a23c">辅料小计：¥{{ auxSubtotal.toFixed(2) }}</span>
      </div>

      <!-- 合计 -->
      <div style="display:flex;gap:16px;margin:6px 0;padding:6px 12px;background:#f5f7fa;border-radius:4px;font-size:13px">
        <span><strong>面料小计：</strong>¥{{ mainSubtotal.toFixed(2) }}</span>
        <span><strong>辅料小计：</strong>¥{{ auxSubtotal.toFixed(2) }}</span>
        <span style="margin-left:auto"><strong>合计：</strong>¥{{ totalAmount.toFixed(2) }}</span>
      </div>

      <!-- ===== 金额结算 ===== -->
      <el-divider content-position="left">金额结算</el-divider>
      <el-row :gutter="10">
        <el-col :span="5">
          <el-form-item label="折前总额">
            <el-input v-model="form.quoteAmount" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="4">
          <el-form-item label="折扣优惠">
            <el-input v-model.number="form.discount_amount" @input="onSettlementChange" />
          </el-form-item>
        </el-col>
        <el-col :span="4">
          <el-form-item label="抹零">
            <el-input v-model.number="form.round_amount" @input="onSettlementChange" />
          </el-form-item>
        </el-col>
        <el-col :span="4">
          <el-form-item label="定金抵扣">
            <el-input v-model.number="form.deposit_deduction" placeholder="0" @input="onSettlementChange" />
          </el-form-item>
        </el-col>
        <el-col :span="4">
          <el-form-item label="应收金额">
            <el-input v-model.number="form.amount" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="3">
          <el-form-item label="优惠原因">
            <el-input v-model="form.discount_reason" />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- ===== 备注 ===== -->
      <el-divider content-position="left">备注</el-divider>
      <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="备注" />
    </el-form>

    <!-- 客户选择弹窗 -->
    <CustomerSelectDialog v-model="showCustomerSelect" @select="handleCustomerSelect" />

    <template #footer>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <el-button size="small" @click="navPrev" :disabled="!hasPrev">← 上一条</el-button>
          <el-button size="small" @click="navNext" :disabled="!hasNext">下一条 →</el-button>
        </div>
        <div>
          <el-button @click="visible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { orderApi, productApi, customerApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import CustomerSelectDialog from './CustomerSelectDialog.vue'

const props = defineProps({
  modelValue: Boolean,
  orderId: { type: [Number, String], default: null },
  // 用于上一条/下一条导航
  orderIds: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const auth = useAuthStore()
const visible = ref(false)
const saving = ref(false)
const showCustomerSelect = ref(false)
const currentOrderIds = ref([])

const isEdit = computed(() => !!props.orderId)

const mainTableRef = ref(null)
const auxTableRef = ref(null)

watch(() => props.modelValue, (v) => { visible.value = v })
watch(visible, (v) => { emit('update:modelValue', v) })
watch(() => props.orderIds, (v) => { currentOrderIds.value = v || [] }, { immediate: true })

// 上一条/下一条
const currentIdx = computed(() => currentOrderIds.value.indexOf(Number(props.orderId)))
const hasPrev = computed(() => currentIdx.value > 0)
const hasNext = computed(() => currentIdx.value >= 0 && currentIdx.value < currentOrderIds.value.length - 1)

function navPrev() {
  if (hasPrev.value) {
    const prevId = currentOrderIds.value[currentIdx.value - 1]
    emit('saved', prevId)
    loadOrder(prevId)
  }
}

function navNext() {
  if (hasNext.value) {
    const nextId = currentOrderIds.value[currentIdx.value + 1]
    emit('saved', nextId)
    loadOrder(nextId)
  }
}

// ── 表单数据 ──
const form = reactive({
  order_no: '',
  customer_id: null,
  customer_name: '',
  customer_phone: '',
  order_type: '窗帘',
  order_date: new Date().toISOString().slice(0, 10),
  delivery_date: '',
  delivery_method: '上门安装',
  salesperson_name: '',
  salesperson_id: null,
  discount_amount: 0,
  round_amount: 0,
  deposit_deduction: 0,
  discount_reason: '',
  content: '',
  remark: '',
  install_address: '',
  install_date: '',
  install_time_slot: '',
  quoteAmount: 0,
  amount: 0,
  status_key: '',
  status_label: '',
  status_color: '',
})

// ── 回车智能导航 ──
function handleEnterKey(e) {
  const target = e.target
  if (target.tagName === 'TEXTAREA') return
  if (!target.matches('input') || target.disabled || target.readOnly) return

  // 跳过 el-select — 让原生 Enter 打开/关闭下拉
  if (target.closest('.el-select')) return

  // 跳过 el-autocomplete — 让 Enter 选中建议项，Tab 跳转到下一字段
  if (target.closest('.el-autocomplete')) return

  e.preventDefault()

  const formEl = target.closest('.el-form')
  if (!formEl) return

  const inputs = Array.from(formEl.querySelectorAll(
    'input:not([type="hidden"]):not([disabled]):not([readonly])'
  ))

  const idx = inputs.indexOf(target)
  if (idx < 0 || idx >= inputs.length - 1) return

  const next = inputs[idx + 1]
  const curTr = target.closest('tr')
  const nextTr = next.closest('tr')

  // 检测是否在同一行内（同 tr）：正常跳转
  if (curTr && nextTr && curTr === nextTr) {
    next.focus()
    if (next.type === 'text' || next.type === 'search') next.select()
    return
  }

  // 离开当前行的最后一个字段（下一字段在不同行，或已离开表格区域）
  if (curTr && (!nextTr || curTr !== nextTr)) {
    const curTable = target.closest('.el-table')

    if (curTable) {
      const rows = curTable.querySelectorAll('.el-table__body-wrapper tbody tr.el-table__row')
      const rowIdx = Array.from(rows).indexOf(curTr)
      const isMain = isMainTable(curTable)
      const items = isMain ? mainItems : auxItems

      // 离开当前表格区域时清理末尾空白行
      if (!nextTr || (next.closest('.el-table') && next.closest('.el-table') !== curTable)) {
        cleanupTrailingRows(isMain)
      }

      // 最后一行且当前行有数据 → 自动添加空白行
      if (rowIdx >= 0 && rowIdx === rows.length - 1) {
        const currentItem = items[rowIdx]
        if (currentItem && !isRowEmpty(currentItem)) {
          addItem(isMain)
          // 延迟重试设焦新行首字段
          setTimeout(() => focusFirstFieldOfNewRow(isMain), 200)
          return
        }
      }
    }
  }

  // 默认：跳转到下一个输入
  next.focus()
  if (next.type === 'text' || next.type === 'search') next.select()
}

// ── 辅助函数 ──

/** 判断 el-table 是否是主料表 */
function isMainTable(tableEl) {
  return tableEl?.getAttribute('data-table') === 'main'
}

/** 判断行是否为空（无产品、无尺寸、无单价） */
function isRowEmpty(item) {
  return !item.product_code && !item.product_name && item.unit_price === 0
}

/** 清理指定表格末尾的空白行（至少保留 1 行） */
function cleanupTrailingRows(isMain) {
  const items = isMain ? mainItems : auxItems
  while (items.length > 1 && isRowEmpty(items[items.length - 1])) {
    items.pop()
  }
}

/** 通过 data-table 属性获取表格根 DOM 元素 */
function getTableEl(isMain) {
  return document.querySelector(`.el-table[data-table="${isMain ? 'main' : 'aux'}"]`)
}

/** 在新添加的最后一行的首字段设焦（带重试） */
function focusFirstFieldOfNewRow(isMain) {
  const tableEl = getTableEl(isMain)
  if (!tableEl || !tableEl.querySelector('.el-table__body-wrapper tbody .el-table__row')) {
    setTimeout(() => focusFirstFieldOfNewRow(isMain), 100)
    return
  }
  const rows = tableEl.querySelectorAll('.el-table__body-wrapper tbody .el-table__row')
  const newRow = rows[rows.length - 1]
  if (!newRow) return

  // 第一列是 el-select（空间），点击其 wrapper 以打开下拉
  const selectWrapper = newRow.querySelector('.el-select__wrapper')
  if (selectWrapper) {
    selectWrapper.click()
    return
  }
  // 回退：找第一个非只读输入框
  const inp = newRow.querySelector('input:not([readonly])')
  if (inp) {
    inp.focus()
    inp.focus({preventScroll: true})
  }
}

/** 空间选择后自动跳转到产品编码 */
function onRoomChange(isMain, index) {
  nextTick(() => {
    const tableEl = getTableEl(isMain)
    if (!tableEl) return
    const rows = tableEl.querySelectorAll('.el-table__body-wrapper tbody tr.el-table__row')
    const row = rows[index]
    if (!row) return
    const acInput = row.querySelector('.el-autocomplete input')
    if (acInput) {
      acInput.focus()
      acInput.select()
    }
  })
}

/** 产品编码选中后自动跳转到下一字段（主料→宽，辅料→数量） */
function onProductAutoselect(isMain, index) {
  nextTick(() => {
    const tableEl = getTableEl(isMain)
    if (!tableEl) return
    const rows = tableEl.querySelectorAll('.el-table__body-wrapper tbody tr.el-table__row')
    const row = rows[index]
    if (!row) return
    // 找出行内普通输入框（排除 el-select 和 el-autocomplete 内部的输入框）
    const allInputs = Array.from(row.querySelectorAll('input:not([disabled]):not([readonly])'))
    const regularInputs = allInputs.filter(inp =>
      !inp.closest('.el-select') && !inp.closest('.el-autocomplete')
    )
    if (regularInputs.length > 0) {
      regularInputs[0].focus()
      regularInputs[0].select()
    }
  })
}

function emptyItem(isMain = true) {
  return {
    item_type: isMain ? '窗帘' : '辅料',
    product_id: null,
    product_name: '',
    product_code: '',
    procurement_type: isMain ? '物料' : '辅料',
    is_purchase: true,
    material_type: isMain ? '主料' : '辅料',
    room: '',
    width: 0,
    height: 0,
    fold_ratio: isMain ? 2.0 : 1.0,
    unit: isMain ? '米' : '个',
    unit_price: 0,
    qty: 1,
    discount: 1.0,
    amount: 0,
    process_desc: '',
    classification: '',
    calc_type: isMain ? 'per_meter' : 'per_unit',
    panel_count: 0,
    supplier_id: null,
    note: '',
  }
}

const mainItems = reactive([emptyItem(true)])
const auxItems = reactive([emptyItem(false)])

// ── 分类小计 ──
const mainSubtotal = computed(() => mainItems.reduce((s, i) => s + (parseFloat(i.amount) || 0), 0))
const auxSubtotal = computed(() => auxItems.reduce((s, i) => s + (parseFloat(i.amount) || 0), 0))
const totalAmount = computed(() => mainSubtotal.value + auxSubtotal.value)

// ── 客户选择 ──
function handleCustomerSelect(customer) {
  form.customer_id = customer.id
  form.customer_name = customer.name
  form.customer_phone = customer.phone
  if (customer.address && !form.install_address) {
    form.install_address = customer.address
  }
  if (customer.salesperson_name) {
    form.salesperson_name = customer.salesperson_name
    form.salesperson_id = customer.salesperson_id || customer.salesperson_id
  }
}

// ── 产品搜索 ──
async function searchProducts(queryString, cb, isMain, index) {
  try {
    const res = await productApi.search(queryString || '')
    const allowedTypes = isMain ? ['面料'] : ['辅料', '成品']
    const items = (res.data || []).filter(p => allowedTypes.includes(p.product_type))
    cb(items.map(p => ({ value: p.code, ...p })))
  } catch { cb([]) }
}

function handleProductSelect(item, isMain, index) {
  const items = isMain ? mainItems : auxItems
  const it = items[index]
  it.product_id = item.id
  it.product_code = item.code
  it.product_name = item.name
  it.unit_price = item.unit_price || item.selling_price || 0
  it.classification = item.classification || ''
  it.calc_type = item.calc_type || (isMain ? 'per_meter' : 'per_unit')
  it.fold_ratio = item.fold_ratio || (isMain ? 2.0 : 1.0)
  it.unit = item.unit || (isMain ? '米' : '个')
  it.supplier_id = item.supplier_id || null
  it.panel_count = item.panel_count || 0
  const typeMap = { '面料': '物料', '成品': '成品', '辅料': '辅料' }
  it.procurement_type = typeMap[item.product_type] || (isMain ? '物料' : '辅料')
  updateItemAmount(isMain, index)
}

function handleProductClear(isMain, index) {
  const items = isMain ? mainItems : auxItems
  const it = items[index]
  it.product_id = null
  it.product_name = ''
  it.unit_price = 0
  updateItemAmount(isMain, index)
}

// ── 金额计算 ──
function calcItemAmount(item) {
  const w = parseFloat(item.width) || 0
  const h = parseFloat(item.height) || 0
  const fr = parseFloat(item.fold_ratio) || 2.0
  const price = parseFloat(item.unit_price) || 0
  const calcType = item.calc_type || 'per_meter'
  const disc = parseFloat(item.discount) || 1.0
  const classification = item.classification || ''

  let effectiveQty
  if (calcType === 'per_meter') {
    if (classification === '定宽') {
      // 定宽面料: 数量 = 高度 × 倍率
      effectiveQty = h > 0 ? Math.round(h * fr * 100) / 100 : (parseFloat(item.qty) || 1)
    } else {
      // 定高面料（默认）: 数量 = 宽度 × 倍率
      effectiveQty = w > 0 ? Math.round(w * fr * 100) / 100 : (parseFloat(item.qty) || 1)
    }
  } else if (calcType === 'per_square') {
    effectiveQty = (w > 0 && h > 0) ? Math.round(w * h * 100) / 100 : (parseFloat(item.qty) || 1)
  } else {
    effectiveQty = parseFloat(item.qty) || 1
  }

  item.qty = effectiveQty
  return Math.round(effectiveQty * price * disc * 100) / 100
}

function updateItemAmount(isMain, index) {
  const items = isMain ? mainItems : auxItems
  const item = items[index]
  item.amount = calcItemAmount(item)
  calcTotal()
}

function onItemInput(isMain, index) {
  updateItemAmount(isMain, index)
}

function calcTotal() {
  let sumAfterDiscount = 0
  let sumBeforeDiscount = 0
  for (const it of mainItems) {
    const amt = parseFloat(it.amount) || 0
    sumAfterDiscount += amt
    const disc = parseFloat(it.discount) || 1.0
    sumBeforeDiscount += disc > 0 ? amt / disc : amt
  }
  for (const it of auxItems) {
    const amt = parseFloat(it.amount) || 0
    sumAfterDiscount += amt
    const disc = parseFloat(it.discount) || 1.0
    sumBeforeDiscount += disc > 0 ? amt / disc : amt
  }
  sumBeforeDiscount = Math.round(sumBeforeDiscount * 100) / 100
  form.quoteAmount = sumBeforeDiscount
  // 自动计算折扣优惠 = 折前总额 - 折后合计
  form.discount_amount = Math.round((sumBeforeDiscount - sumAfterDiscount) * 100) / 100
  applySettlement()
}

function applySettlement() {
  const quote = form.quoteAmount || 0
  const discount = parseFloat(form.discount_amount) || 0
  const roundAmt = parseFloat(form.round_amount) || 0
  const depositDed = parseFloat(form.deposit_deduction) || 0
  form.amount = Math.max(0, Math.round((quote - discount - roundAmt - depositDed) * 100) / 100)
}

function onSettlementChange() { applySettlement() }

function onOrderDateChange(val) {
  if (!val) return
  const d = new Date(val)
  d.setDate(d.getDate() + 14)
  form.delivery_date = d.toISOString().slice(0, 10)
}

// ── 明细管理 ──
function addItem(isMain) {
  const items = isMain ? mainItems : auxItems
  items.push(emptyItem(isMain))
}
function removeItem(isMain, index) {
  const items = isMain ? mainItems : auxItems
  items.splice(index, 1)
  if (items.length === 0) items.push(emptyItem(isMain))
  calcTotal()
}

function getAllItems() {
  return [...mainItems, ...auxItems]
}

// ── 保存 ──
async function handleSubmit() {
  if (!form.customer_name) { ElMessage.warning('请选择客户'); return }
  // 保存前清理末尾空记录
  cleanupTrailingRows(true)
  cleanupTrailingRows(false)
  saving.value = true
  try {
    const payload = {
      ...form,
      customer_id: form.customer_id,
      items: getAllItems().map(it => ({
        ...it,
        amount: Math.round((parseFloat(it.qty) || 0) * (parseFloat(it.unit_price) || 0) * 100) / 100,
      })),
    }
    delete payload.quoteAmount
    delete payload.status_key
    delete payload.status_label
    delete payload.status_color

    if (isEdit.value) {
      await orderApi.update(props.orderId, payload)
      ElMessage.success('更新成功')
    } else {
      await orderApi.create(payload)
      ElMessage.success('创建成功')
    }
    emit('saved')
    visible.value = false
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

// ── 加载订单 ──
async function loadOrder(id) {
  if (!id) return
  try {
    const res = await orderApi.get(id)
    const data = res.data
    Object.assign(form, {
      order_no: data.order_no || '',
      customer_id: data.customer_id || null,
      customer_name: data.customer_name || '',
      customer_phone: data.customer_phone || '',
      order_type: data.order_type || '窗帘',
      order_date: data.order_date || '',
      delivery_date: data.delivery_date || '',
      delivery_method: data.delivery_method || '上门安装',
      salesperson_name: data.salesperson_name || auth.userName || '',
      salesperson_id: data.salesperson_id || auth.user?.id || null,
      discount_amount: data.discount_amount || 0,
      round_amount: data.round_amount || 0,
      deposit_deduction: data.deposit_deduction || 0,
      discount_reason: data.discount_reason || '',
      content: data.content || '',
      remark: data.remark || '',
      install_address: data.install_address || '',
      install_date: data.install_date || '',
      install_time_slot: data.install_time_slot || '',
      status_key: data.status_key || '',
      status_label: data.status_label || '',
      status_color: data.status_color || '',
    })

    mainItems.length = 0
    auxItems.length = 0
    const items = data.items || []
    for (const item of items) {
      const isMain = item.material_type !== '辅料' && item.procurement_type !== '辅料'
      const target = isMain ? mainItems : auxItems
      target.push({
        ...item,
        procurement_type: item.procurement_type || (isMain ? '物料' : '辅料'),
        is_purchase: item.is_purchase !== undefined ? item.is_purchase : true,
        panel_count: item.panel_count || 0,
        amount: parseFloat(item.amount) || 0,
      })
    }
    if (mainItems.length === 0) mainItems.push(emptyItem(true))
    if (auxItems.length === 0) auxItems.push(emptyItem(false))
    calcTotal()
  } catch {}
}

function resetForm() {
  Object.assign(form, {
    order_no: '',
    customer_id: null,
    customer_name: '',
    customer_phone: '',
    order_type: '窗帘',
    order_date: new Date().toISOString().slice(0, 10),
    delivery_date: '',
    delivery_method: '上门安装',
    salesperson_name: auth.userName || '',
    salesperson_id: auth.user?.id || null,
    discount_amount: 0,
    round_amount: 0,
    deposit_deduction: 0,
    discount_reason: '',
    content: '',
    remark: '',
    install_address: '',
    install_date: '',
    install_time_slot: '',
    status_key: '',
    status_label: '',
    status_color: '',
  })
  mainItems.length = 0
  auxItems.length = 0
  mainItems.push(emptyItem(true))
  auxItems.push(emptyItem(false))
  calcTotal()
}

function onOpen() {
  if (isEdit.value) {
    loadOrder(props.orderId)
  } else {
    resetForm()
  }
}
</script>

<style scoped>
.compact-table { font-size: 13px; }
.compact-table :deep(.el-table__header th) { padding: 3px 4px; font-size: 13px; line-height: 1.5; }
.compact-table :deep(.el-table__cell) { padding: 3px 4px; }
.compact-table :deep(.el-table__body td) { padding: 3px 4px; line-height: 1.5; }
.compact-table :deep(.el-table__inner-wrapper) { border: none; }

:deep(.el-divider) { margin: 8px 0; }
:deep(.el-form-item) { margin-bottom: 6px; }
:deep(.el-form-item__label) { font-size: 13px; line-height: 32px; }
:deep(.el-form-item__content) { line-height: 32px; }
:deep(.el-input__wrapper) { padding: 2px 10px; }
:deep(.el-input__inner) { height: 32px; line-height: 32px; font-size: 13px; }
:deep(.el-select) { height: 32px; }
</style>
