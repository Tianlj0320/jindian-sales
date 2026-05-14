<template>
  <div>
    <el-button text @click="$router.back()" style="margin-bottom:8px">← 返回</el-button>

    <el-card shadow="never">
      <template #header>
        <h3 style="font-size:15px;margin:0">{{ isEdit ? '编辑订单' : '新建订单' }}</h3>
      </template>

      <el-form :model="form" label-width="80px">
        <!-- 客户信息 -->
        <el-divider content-position="left">客户信息</el-divider>
        <el-row :gutter="10">
          <el-col :span="8">
            <el-form-item label="客户姓名">
              <el-autocomplete
                v-model="form.customer_name"
                :fetch-suggestions="searchCustomers"
                :trigger-on-focus="true"
                placeholder="输入姓名或手机号搜索"
                clearable
                value-key="name"
                @select="handleCustomerSelect"
                @clear="handleCustomerClear"
                style="width:100%"
              >
                <template #default="{ item }">
                  <div style="display:flex;justify-content:space-between;align-items:center;padding:2px 0">
                    <div>
                      <strong>{{ item.name }}</strong>
                      <span style="color:#909399;margin-left:10px">{{ item.phone }}</span>
                    </div>
                    <span style="color:#c0c4cc;font-size:12px">
                      {{ item.level ? item.level + '级' : '' }}
                      {{ item.address ? '| ' + item.address : '' }}
                    </span>
                  </div>
                </template>
              </el-autocomplete>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="联系电话">
              <el-input v-model="form.customer_phone" placeholder="自动带出" :disabled="!!form.customer_id" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="业务员">
              <el-input v-model="form.salesperson_name" placeholder="自动获取" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 订单信息 -->
        <el-divider content-position="left">订单信息</el-divider>
        <el-row :gutter="10">
          <el-col :span="8">
            <el-form-item label="订单类型">
              <el-select v-model="form.order_type" style="width:100%">
                <el-option label="窗帘" value="窗帘" />
                <el-option label="成品帘" value="成品帘" />
                <el-option label="软包" value="软包" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="下单日期">
              <el-date-picker v-model="form.order_date" type="date" value-format="YYYY-MM-DD" style="width:100%" @change="onOrderDateChange" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="交货日期">
              <el-date-picker v-model="form.delivery_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="交货方式">
              <el-select v-model="form.delivery_method" style="width:100%">
                <el-option label="上门安装" value="上门安装" />
                <el-option label="自提" value="自提" />
                <el-option label="发货" value="发货" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="安装地址">
              <el-input v-model="form.install_address" placeholder="安装地址" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="安装日期">
              <el-date-picker v-model="form.install_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="安装时段">
              <el-select v-model="form.install_time_slot" style="width:100%" clearable>
                <el-option label="上午(8-12点)" value="上午" />
                <el-option label="下午(12-18点)" value="下午" />
                <el-option label="全天" value="全天" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- ============= 主料明细 ============= -->
        <el-divider content-position="left">主料明细</el-divider>
        <el-table :data="mainItems" stripe style="width:100%" size="small" class="compact-table">
          <el-table-column label="空间" width="70">
            <template #default="{ $index }">
              <el-select v-model="mainItems[$index].room" placeholder="空间" style="width:60px" size="small">
                <el-option label="客厅" value="客厅" />
                <el-option label="主卧" value="主卧" />
                <el-option label="次卧" value="次卧" />
                <el-option label="书房" value="书房" />
                <el-option label="餐厅" value="餐厅" />
                <el-option label="阳台" value="阳台" />
                <el-option label="厨房" value="厨房" />
                <el-option label="卫生间" value="卫生间" />
                <el-option label="其他" value="其他" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="产品编码" width="130">
            <template #default="{ $index }">
              <el-autocomplete
                v-model="mainItems[$index].product_code"
                :fetch-suggestions="(q, cb) => searchProducts(q, cb, $index)"
                :trigger-on-focus="true"
                placeholder="编码/名称搜索"
                clearable
                value-key="code"
                @select="(item) => handleProductSelect(item, $index)"
                @clear="handleProductClear($index)"
                style="width:100%"
                size="small"
              >
                <template #default="{ item }">
                  <div style="display:flex;justify-content:space-between;align-items:center;padding:1px 0;font-size:12px">
                    <span><strong>{{ item.code }}</strong> - {{ item.name }}</span>
                    <span style="color:#909399">¥{{ item.selling_price }}</span>
                  </div>
                </template>
              </el-autocomplete>
            </template>
          </el-table-column>
          <el-table-column label="产品名称" width="90">
            <template #default="{ $index }">
              <el-input v-model="mainItems[$index].product_name" placeholder="自动带出" size="small" disabled />
            </template>
          </el-table-column>
          <el-table-column label="宽(m)" width="65">
            <template #default="{ $index }">
              <el-input v-model.number="mainItems[$index].width" placeholder="0" size="small" @input="onMainItemInput($index)" />
            </template>
          </el-table-column>
          <el-table-column label="高(m)" width="65">
            <template #default="{ $index }">
              <el-input v-model.number="mainItems[$index].height" placeholder="0" size="small" @input="onMainItemInput($index)" />
            </template>
          </el-table-column>
          <el-table-column label="倍率" width="55">
            <template #default="{ $index }">
              <el-input v-model.number="mainItems[$index].fold_ratio" placeholder="2.0" size="small" @input="onMainItemInput($index)" />
            </template>
          </el-table-column>
          <el-table-column label="数量" width="65">
            <template #default="{ $index }">
              <el-input v-model.number="mainItems[$index].qty" placeholder="自动" size="small" @input="onMainItemInput($index)" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="80">
            <template #default="{ $index }">
              <el-input v-model.number="mainItems[$index].unit_price" placeholder="0" size="small" @input="onMainItemInput($index)" />
            </template>
          </el-table-column>
          <el-table-column label="折率" width="55">
            <template #default="{ $index }">
              <el-input v-model.number="mainItems[$index].discount" placeholder="1.0" size="small" @input="onMainItemInput($index)" />
            </template>
          </el-table-column>
          <el-table-column label="金额" width="90" align="right">
            <template #default="{ $index }">
              ¥{{ (mainItems[$index].amount || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="采购类型" width="80">
            <template #default="{ $index }">
              <el-select v-model="mainItems[$index].procurement_type" size="small" style="width:68px" @change="onMainItemInput($index)">
                <el-option label="物料" value="物料" />
                <el-option label="成品" value="成品" />
                <el-option label="辅料" value="辅料" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="采购" width="55" align="center">
            <template #default="{ $index }">
              <el-tag :type="mainItems[$index].is_purchase === false ? 'warning' : 'success'" size="small">
                {{ mainItems[$index].is_purchase === false ? '外加工' : '需采购' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="工艺" min-width="80">
            <template #default="{ $index }">
              <el-input v-model="mainItems[$index].process_desc" placeholder="工艺" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="50" fixed="right">
            <template #default="{ $index }">
              <el-button text size="small" type="danger" @click="removeMainItem($index)" :disabled="mainItems.length <= 1">×</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div style="margin:8px 0">
          <el-button size="small" @click="addMainItem">+ 添加主料</el-button>
        </div>
        <!-- 主料小计 -->
        <div style="text-align:right;margin:4px 16px;padding:4px 12px;background:#f5f7fa;border-radius:4px">
          <strong>主料小计：¥{{ mainSubtotal.toFixed(2) }}</strong>
        </div>

        <!-- ============= 辅料明细 ============= -->
        <el-divider content-position="left">辅料明细</el-divider>
        <el-table :data="auxItems" stripe style="width:100%" size="small" class="compact-table">
          <el-table-column label="产品编码" width="130">
            <template #default="{ $index }">
              <el-autocomplete
                v-model="auxItems[$index].product_code"
                :fetch-suggestions="(q, cb) => searchAuxProducts(q, cb, $index)"
                :trigger-on-focus="true"
                placeholder="编码/名称搜索"
                clearable
                value-key="code"
                @select="(item) => handleAuxProductSelect(item, $index)"
                @clear="handleAuxProductClear($index)"
                style="width:100%"
                size="small"
              >
                <template #default="{ item }">
                  <div style="display:flex;justify-content:space-between;align-items:center;padding:1px 0;font-size:12px">
                    <span><strong>{{ item.code }}</strong> - {{ item.name }}</span>
                    <span style="color:#909399">¥{{ item.selling_price }}</span>
                  </div>
                </template>
              </el-autocomplete>
            </template>
          </el-table-column>
          <el-table-column label="产品名称" width="120">
            <template #default="{ $index }">
              <el-input v-model="auxItems[$index].product_name" placeholder="自动带出" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="单位" width="60">
            <template #default="{ $index }">
              <el-input v-model="auxItems[$index].unit" size="small" placeholder="自动" disabled />
            </template>
          </el-table-column>
          <el-table-column label="数量" width="65">
            <template #default="{ $index }">
              <el-input v-model.number="auxItems[$index].qty" placeholder="1" size="small" @input="calcTotal" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="80">
            <template #default="{ $index }">
              <el-input v-model.number="auxItems[$index].unit_price" placeholder="0" size="small" @input="onAuxItemInput($index)" />
            </template>
          </el-table-column>
          <el-table-column label="采购类型" width="80">
            <template #default="{ $index }">
              <el-select v-model="auxItems[$index].procurement_type" size="small" style="width:68px" @change="onAuxItemInput($index)">
                <el-option label="物料" value="物料" />
                <el-option label="成品" value="成品" />
                <el-option label="辅料" value="辅料" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="金额" width="90" align="right">
            <template #default="{ $index }">
              ¥{{ ((auxItems[$index].qty || 0) * (auxItems[$index].unit_price || 0)).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="工艺" min-width="80">
            <template #default="{ $index }">
              <el-input v-model="auxItems[$index].process_desc" placeholder="工艺" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="50">
            <template #default="{ $index }">
              <el-button text size="small" type="danger" @click="removeAuxItem($index)" :disabled="auxItems.length <= 0">×</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div style="margin:8px 0">
          <el-button size="small" @click="addAuxItem">+ 添加辅料</el-button>
        </div>
        <!-- 辅料小计 -->
        <div style="text-align:right;margin:4px 16px;padding:4px 12px;background:#f5f7fa;border-radius:4px">
          <strong>辅料小计：¥{{ auxSubtotal.toFixed(2) }}</strong>
        </div>

        <!-- 金额汇总 -->
        <el-divider content-position="left">金额结算</el-divider>
        <el-row :gutter="10">
          <el-col :span="6">
            <el-form-item label="折前总额">
              <el-input v-model="form.quoteAmount" disabled placeholder="自动计算" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="折扣优惠">
              <el-input v-model.number="form.discount_amount" placeholder="0" @input="onSettlementChange" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="抹零">
              <el-input v-model.number="form.round_amount" placeholder="0" @input="onSettlementChange" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="应收金额">
              <el-input v-model.number="form.amount" disabled placeholder="自动计算" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="10">
          <el-col :span="6">
            <el-form-item label="已收定金">
              <el-input v-model.number="form.received" placeholder="0" @input="onSettlementChange" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="欠款">
              <el-input :model-value="computedDebt" disabled placeholder="自动计算" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="优惠原因">
              <el-input v-model="form.discount_reason" placeholder="选填" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 备注 -->
        <el-divider content-position="left">其他</el-divider>
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="订单备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="备注" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 提交 -->
        <div style="text-align:center;margin-top:24px">
          <el-button @click="$router.back()">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleSubmit">保存订单</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { orderApi, productApi, customerApi, processingApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)

// 加工类型规则缓存
const processingRulesCache = ref({})

// ── 默认空行 ─────────────────────────────────────────────────────

function emptyMainItem() {
  return {
    item_type: '窗帘',
    product_id: null,
    product_name: '',
    product_code: '',
    room: '',
    width: 0,
    height: 0,
    fold_ratio: 2.0,
    unit: '米',
    unit_price: 0,
    qty: 1,
    discount: 1.0,
    amount: 0,
    open_type: '',
    style_code: '',
    process_desc: '',
    classification: '',
    procurement_type: '物料',
    material_type: '主料',
    calc_type: 'per_meter',
    supplier_id: null,
    supplier_name: '',
    is_purchase: true,
    note: '',
  }
}

function emptyAuxItem() {
  return {
    item_type: '辅料',
    product_id: null,
    product_name: '',
    product_code: '',
    room: '',
    width: 0,
    height: 0,
    fold_ratio: 1.0,
    unit: '米',
    unit_price: 0,
    qty: 1,
    discount: 1.0,
    amount: 0,
    open_type: '',
    style_code: '',
    process_desc: '',
    classification: '',
    procurement_type: '辅料',
    material_type: '辅料',
    calc_type: 'per_meter',
    supplier_id: null,
    supplier_name: '',
    is_purchase: true,
    note: '',
  }
}

// ── 计算 2 周后的日期 ──────────────────────────────────────────

function getDateAfterTwoWeeks() {
  const d = new Date()
  d.setDate(d.getDate() + 14)
  return d.toISOString().slice(0, 10)
}

// ── 表单数据 ───────────────────────────────────────────────────

const form = reactive({
  customer_id: null,
  customer_name: '',
  customer_phone: '',
  order_type: '窗帘',
  order_date: new Date().toISOString().slice(0, 10),
  delivery_date: getDateAfterTwoWeeks(),
  delivery_method: '上门安装',
  salesperson_name: auth.userName || '',
  salesperson_id: auth.user?.id || null,
  discount_amount: 0,
  round_amount: 0,
  discount_reason: '',
  received: 0,
  content: '',
  remark: '',
  install_address: '',
  install_date: '',
  install_time_slot: '',
  quoteAmount: 0,
  amount: 0,
})

// 欠款（计算属性）
const computedDebt = computed(() => {
  return Math.max(0, (form.amount || 0) - (form.received || 0)).toFixed(2)
})

// 主料/辅料小计
const mainSubtotal = computed(() => mainItems.reduce((s, i) => s + (i.amount || 0), 0))
const auxSubtotal = computed(() => auxItems.reduce((s, i) => s + (i.qty || 0) * (i.unit_price || 0), 0))

// 主料和辅料分开存储
const mainItems = reactive([emptyMainItem()])
const auxItems = reactive([])

// ── 客户搜索 ──────────────────────────────────────────────────

async function searchCustomers(queryString, cb) {
  try {
    const res = await customerApi.search(queryString || '')
    const items = res.data || []
    cb(items.map(c => ({
      value: c.name,
      ...c,
    })))
  } catch {
    cb([])
  }
}

function handleCustomerSelect(item) {
  form.customer_id = item.id
  form.customer_name = item.name
  form.customer_phone = item.phone
  if (item.address && !form.install_address) {
    form.install_address = item.address
  }
}

function handleCustomerClear() {
  form.customer_id = null
  form.customer_phone = ''
}

// ── 产品搜索（主料）────────────────────────────────────────────

async function searchProducts(queryString, cb, index) {
  try {
    const res = await productApi.search(queryString || '')
    const items = (res.data || []).filter(p => p.product_type === '面料')
    cb(items.map(p => ({
      value: p.code,
      ...p,
    })))
  } catch {
    cb([])
  }
}

async function handleProductSelect(item, index) {
  const it = mainItems[index]
  it.product_id = item.id
  it.product_code = item.code
  it.product_name = item.name
  it.unit_price = item.unit_price || item.selling_price || 0
  it.classification = item.classification || ''
  it.calc_type = item.calc_type || 'per_meter'
  it.fold_ratio = item.fold_ratio || 2.0
  it.unit = item.unit || '米'
  it.supplier_id = item.supplier_id || null
  it.supplier_name = item.supplier_name || ''
  it.is_purchase = item.is_purchase !== undefined ? item.is_purchase : true
  // 根据产品类型自动设置采购类型：面料→物料，成品→成品，辅料→辅料
  const typeMap = { '面料': '物料', '成品': '成品', '辅料': '辅料' }
  it.procurement_type = typeMap[item.product_type] || '物料'

  // 自动生成辅料（如果产品有加工类型）
  if (item.processing_type_id) {
    await autoGenerateAuxItems(item.processing_type_id, it)
  }

  updateMainItemAmount(index)
}

function handleProductClear(index) {
  const it = mainItems[index]
  it.product_id = null
  it.product_name = ''
  it.unit_price = 0
  it.classification = ''
  it.calc_type = 'per_meter'
  updateMainItemAmount(index)
}

// ── 产品搜索（辅料）────────────────────────────────────────────

async function searchAuxProducts(queryString, cb, index) {
  try {
    const res = await productApi.search(queryString || '')
    const items = (res.data || []).filter(p => p.product_type === '辅料' || p.product_type === '成品')
    cb(items.map(p => ({
      value: p.code,
      ...p,
    })))
  } catch {
    cb([])
  }
}

function handleAuxProductSelect(item, index) {
  const it = auxItems[index]
  it.product_id = item.id
  it.product_code = item.code
  it.product_name = item.name
  it.unit_price = item.unit_price || item.selling_price || 0
  it.unit = item.unit || '米'
  it.supplier_id = item.supplier_id || null
  it.supplier_name = item.supplier_name || ''
  it.is_purchase = item.is_purchase !== undefined ? item.is_purchase : true
  const typeMap = { '面料': '物料', '成品': '成品', '辅料': '辅料' }
  it.procurement_type = typeMap[item.product_type] || '辅料'
  updateAuxItemAmount(index)
}

function handleAuxProductClear(index) {
  const it = auxItems[index]
  it.product_id = null
  it.product_name = ''
  it.unit = '米'
  it.unit_price = 0
  updateAuxItemAmount(index)
}

// ── 辅料自动生成 ──────────────────────────────────────────────

async function autoGenerateAuxItems(processingTypeId, mainItem) {
  let rules = processingRulesCache.value[processingTypeId]
  if (!rules) {
    try {
      const res = await processingApi.getType(processingTypeId)
      rules = res.data?.rules || []
      processingRulesCache.value[processingTypeId] = rules
    } catch {
      return
    }
  }

  for (const rule of rules) {
    if (!rule.is_required) continue

    let qty = evalFormula(rule.qty_formula, {
      width: mainItem.width || 0,
      height: mainItem.height || 0,
      qty: mainItem.qty || 1,
      fold_ratio: mainItem.fold_ratio || 2.0,
    })

    // 查找是否已存在同名的辅料（避免重复添加）
    const existing = auxItems.find(a => a.product_name === rule.material_name)
    if (existing) {
      existing.qty = Math.round((existing.qty + qty) * 100) / 100
      updateAuxItemAmount(auxItems.indexOf(existing))
      continue
    }

    const aux = emptyAuxItem()
    aux.product_name = rule.material_name || rule.default_product_name
    aux.product_id = rule.product_id
    aux.unit = rule.unit || '米'
    aux.qty = Math.round(qty * 100) / 100 || 1
    aux.unit_price = rule.unit_price || 0
    aux.is_purchase = mainItem.is_purchase !== undefined ? mainItem.is_purchase : true
    auxItems.push(aux)
  }
  calcTotal()
}

function evalFormula(formula, vars) {
  try {
    const fn = new Function('width', 'height', 'qty', 'fold_ratio', `return ${formula}`)
    const result = fn(vars.width, vars.height, vars.qty, vars.fold_ratio)
    return typeof result === 'number' && !isNaN(result) ? result : 1
  } catch {
    return 1
  }
}

// ── 下单日期变化 → 自动更新交货日期 ─────────────────────────

function onOrderDateChange(val) {
  if (!val) return
  const d = new Date(val)
  d.setDate(d.getDate() + 14)
  form.delivery_date = d.toISOString().slice(0, 10)
}

// ── 金额计算 ──────────────────────────────────────────────────

/**
 * 计算单个主料的折前金额：用量 = 宽×倍率（per_meter）或 宽×高（per_square），金额 = 用量 × 单价
 */
function calcMainItemAmount(item) {
  const w = parseFloat(item.width) || 0
  const h = parseFloat(item.height) || 0
  const fr = parseFloat(item.fold_ratio) || 2.0
  const price = parseFloat(item.unit_price) || 0
  const calcType = item.calc_type || 'per_meter'

  let effectiveQty
  if (calcType === 'per_meter') {
    effectiveQty = w > 0 ? Math.round(w * fr * 100) / 100 : (parseFloat(item.qty) || 1)
  } else if (calcType === 'per_square') {
    effectiveQty = (w > 0 && h > 0) ? Math.round(w * h * 100) / 100 : (parseFloat(item.qty) || 1)
  } else {
    effectiveQty = parseFloat(item.qty) || 1
  }

  const amount = Math.round(effectiveQty * price * 100) / 100
  return { qty: effectiveQty, amount }
}

/**
 * 更新单个主料金额（修改 item 并重算汇总）
 */
function updateMainItemAmount(index) {
  const item = mainItems[index]
  const result = calcMainItemAmount(item)
  item.qty = result.qty
  item.amount = result.amount
  calcTotal()
}

/**
 * 更新单个辅料金额
 */
function updateAuxItemAmount(index) {
  const item = auxItems[index]
  const qty = parseFloat(item.qty) || 0
  const price = parseFloat(item.unit_price) || 0
  item.amount = Math.round(qty * price * 100) / 100
  calcTotal()
}

/**
 * 主料任意字段输入（宽/高/倍率/数量/单价）→ 自动重算金额
 */
function onMainItemInput(index) {
  updateMainItemAmount(index)
}

/**
 * 辅料输入处理
 */
function onAuxItemInput(index) {
  updateAuxItemAmount(index)
}

/**
 * 计算总金额
 */
function calcTotal() {
  let sum = 0
  for (const it of mainItems) {
    sum += (parseFloat(it.amount) || 0)
  }
  for (const it of auxItems) {
    sum += (parseFloat(it.amount) || 0)
  }
  form.quoteAmount = Math.round(sum * 100) / 100
  // 自动计算应收金额
  applySettlementFormula()
}

/**
 * 结算公式：应收 = 报价 - 优惠 - 抹零
 */
function applySettlementFormula() {
  const quote = form.quoteAmount || 0
  const discount = parseFloat(form.discount_amount) || 0
  const roundAmt = parseFloat(form.round_amount) || 0
  form.amount = Math.max(0, Math.round((quote - discount - roundAmt) * 100) / 100)
}

/**
 * 优惠/抹零/已收字段变化
 */
function onSettlementChange() {
  applySettlementFormula()
}

// ── 明细管理 ──────────────────────────────────────────────────

function addMainItem() {
  mainItems.push(emptyMainItem())
}

function removeMainItem(index) {
  mainItems.splice(index, 1)
  calcTotal()
}

function addAuxItem() {
  auxItems.push(emptyAuxItem())
}

function removeAuxItem(index) {
  auxItems.splice(index, 1)
  calcTotal()
}

// ── 提交 ──────────────────────────────────────────────────────

async function handleSubmit() {
  if (!form.customer_name) { ElMessage.warning('请输入客户姓名'); return }
  saving.value = true
  try {
    // 合并主料和辅料到 items
    const allItems = [...mainItems, ...auxItems]

    const payload = {
      ...form,
      customer_id: form.customer_id,
      items: allItems.map(it => ({
        ...it,
        // amount = qty × 单价（折前金额）
        amount: Math.round((parseFloat(it.qty) || 0) * (parseFloat(it.unit_price) || 0) * 100) / 100,
        final_amount: undefined,
      })),
    }
    delete payload.quoteAmount

    if (isEdit.value) {
      await orderApi.update(route.params.id, payload)
      ElMessage.success('更新成功')
    } else {
      await orderApi.create(payload)
      ElMessage.success('创建成功')
    }
    router.push('/orders')
  } catch {} finally { saving.value = false }
}

// ── 初始化 ────────────────────────────────────────────────────

onMounted(async () => {
  if (isEdit.value) {
    try {
      const res = await orderApi.get(route.params.id)
      const data = res.data
      Object.assign(form, {
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
        discount_reason: data.discount_reason || '',
        received: data.received || 0,
        content: data.content || '',
        remark: data.remark || '',
        install_address: data.install_address || '',
        install_date: data.install_date || '',
        install_time_slot: data.install_time_slot || '',
      })

      // 分离主料和辅料
      const items = data.items || []
      mainItems.length = 0
      auxItems.length = 0
      for (const item of items) {
        const clean = { ...item }
        clean.amount = parseFloat(clean.amount) || 0
        if (item.material_type === '辅料') {
          auxItems.push(clean)
        } else {
          mainItems.push(clean)
        }
      }
      if (mainItems.length === 0) mainItems.push(emptyMainItem())
      calcTotal()
    } catch {}
  }
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h3 { font-size: 18px; }

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
:deep(.el-card__header) { padding: 8px 14px; }
h4 { margin: 0 0 4px 0; font-size: 13px; }
:deep(.el-divider) { margin: 6px 0; }
:deep(.el-form-item) { margin-bottom: 4px; }
:deep(.el-form-item__label) { font-size: 12px; line-height: 28px; padding: 0 6px 0 0; }
:deep(.el-form-item__content) { line-height: 28px; }
:deep(.el-row) { margin-bottom: 0 !important; }
:deep(.el-form-item--default) { margin-bottom: 4px; }
:deep(.el-col) { padding-left: 6px !important; padding-right: 6px !important; }
:deep(.el-input__wrapper) { padding: 1px 8px; }
:deep(.el-input__inner) { height: 28px; line-height: 28px; }
:deep(.el-autocomplete) { height: 28px; }
</style>
