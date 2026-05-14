<template>
  <div class="product-manager">
    <!-- 顶部标题栏 -->
    <div class="pm-header">
      <h3>产品管理</h3>
      <div>
        <el-button @click="showCategoryDialog = true">分类管理</el-button>
      </div>
    </div>

    <!-- 三栏主体 -->
    <div class="pm-body">
      <!-- 左侧：供应商列表 -->
      <div class="pm-panel pm-panel-suppliers">
        <div class="panel-title">
          <span>供应商</span>
          <el-button text size="small" @click="openAddSupplier" :icon="Plus" />
        </div>
        <div class="panel-search">
          <el-input v-model="supplierKeyword" placeholder="搜索供应商" size="small" clearable />
        </div>
        <div class="panel-items">
          <div
            v-for="s in filteredSuppliers"
            :key="s.id"
            class="panel-item"
            :class="{ active: selectedSupplier?.id === s.id }"
            @click="selectSupplier(s)"
          >
            <span class="item-name">{{ s.name }}</span>
            <span class="item-code">{{ s.code }}</span>
          </div>
          <div v-if="filteredSuppliers.length === 0" class="panel-empty">暂无供应商</div>
        </div>
      </div>

      <!-- 中间：系列/木板列表 -->
      <div class="pm-panel pm-panel-series">
        <div class="panel-title">
          <span>系列/木板</span>
          <el-button
            text size="small"
            :disabled="!selectedSupplier"
            @click="openAddSeries"
            :icon="Plus"
          />
        </div>
        <div class="panel-items">
          <div
            v-for="s in seriesList"
            :key="s.id"
            class="panel-item"
            :class="{ active: selectedSeries?.id === s.id }"
            @click="selectSeries(s)"
          >
            <span class="item-name">{{ s.name }}</span>
            <el-button text size="small" @click.stop="handleEditSeries(s)" style="margin-left:auto">编辑</el-button>
          </div>
          <div v-if="!selectedSupplier" class="panel-empty">请先选择供应商</div>
          <div v-else-if="seriesList.length === 0" class="panel-empty">暂无系列，点击 + 添加</div>
        </div>
      </div>

      <!-- 右侧：产品列表 -->
      <div class="pm-panel pm-panel-products">
        <div class="panel-title">
          <span>产品列表</span>
          <el-button size="small" type="primary" @click="openAddProduct">新建产品</el-button>
        </div>
        <div class="panel-toolbar">
          <el-input
            v-model="productKeyword" placeholder="名称/编码" size="small" style="width:150px"
            clearable @keyup.enter="loadProducts"
          />
          <el-select v-model="productTypeFilter" size="small" clearable placeholder="类型" style="width:90px" @change="loadProducts">
            <el-option label="面料" value="面料" />
            <el-option label="辅料" value="辅料" />
            <el-option label="成品" value="成品" />
          </el-select>
          <el-button size="small" type="primary" @click="loadProducts">查询</el-button>
        </div>
        <el-table
          :data="productList" v-loading="productLoading" stripe size="small"
          style="width:100%" height="calc(100vh - 320px)" highlight-current-row
          @row-dblclick="handleEditProduct"
        >
          <el-table-column type="index" label="序号" width="45" />
          <el-table-column prop="code" label="编码" width="100" />
          <el-table-column prop="name" label="名称" min-width="130" />
          <el-table-column prop="product_type" label="类型" width="60" />
          <el-table-column label="颜色/花型" width="100">
            <template #default="{ row }">{{ row.color || '-' }} / {{ row.pattern || '-' }}</template>
          </el-table-column>
          <el-table-column label="门幅" width="60" align="center">
            <template #default="{ row }">{{ row.standard_width || '-' }}</template>
          </el-table-column>
          <el-table-column prop="cost_price" label="进价" width="80" align="right">
            <template #default="{ row }">¥{{ row.cost_price?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="selling_price" label="售价" width="80" align="right">
            <template #default="{ row }">¥{{ row.selling_price?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="stock" label="库存" width="60" align="center">
            <template #default="{ row }">
              <span :style="{ color: row.stock <= row.safety_stock ? '#f56c6c' : '#67c23a' }">{{ row.stock }}</span>
            </template>
          </el-table-column>
          <el-table-column label="采购" width="60" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_purchase === false ? 'warning' : 'success'" size="small">
                {{ row.is_purchase === false ? '外加工' : '采购' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="60" fixed="right">
            <template #default="{ row }">
              <el-button text size="small" @click="handleEditProduct(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="panel-footer">
          <span class="footer-info">双击产品行编辑</span>
          <el-pagination
            v-model:current-page="productPage" :page-size="20"
            :total="productTotal" layout="prev, pager, next" size="small"
            @current-change="loadProducts"
          />
          <span class="footer-total">共 {{ productTotal }} 条</span>
        </div>
      </div>
    </div>

    <!-- ─── 产品新建/编辑对话框 ─── -->
    <el-dialog v-model="showProductDialog" :title="productMode === 'edit' ? '编辑产品' : '新建产品'" width="700px" @closed="resetProductForm">
      <el-form :model="productForm" label-width="80px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="名称"><el-input v-model="productForm.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="编码"><el-input v-model="productForm.code" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="类型">
              <el-select v-model="productForm.product_type" style="width:100%">
                <el-option label="面料" value="面料" />
                <el-option label="辅料" value="辅料" />
                <el-option label="成品" value="成品" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="供应商">
              <el-select v-model="productForm.supplier_id" style="width:100%" clearable filterable @change="onSupplierChange">
                <el-option v-for="s in allSuppliers" :key="s.id" :label="(s.code || '') + ' - ' + s.name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="系列">
              <el-select v-model="productForm.series_id" style="width:100%" clearable>
                <el-option v-for="s in seriesForSupplier(productForm.supplier_id)" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="分类">
              <el-select v-model="productForm.category_id" style="width:100%" clearable>
                <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8"><el-form-item label="加工类型">
            <el-select v-model="productForm.processing_type_id" style="width:100%" clearable>
              <el-option v-for="t in processingTypes" :key="t.id" :label="t.name" :value="t.id" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="8"><el-form-item label="单位"><el-input v-model="productForm.unit" placeholder="米" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8"><el-form-item label="售价(元)"><el-input v-model="productForm.selling_price" placeholder="0.00" @blur="productForm.selling_price = validatePrice(productForm.selling_price)" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="进价(元)"><el-input v-model="productForm.cost_price" placeholder="0.00" @blur="productForm.cost_price = validatePrice(productForm.cost_price)" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="最低价(元)"><el-input v-model="productForm.min_price" placeholder="0.00" @blur="productForm.min_price = validatePrice(productForm.min_price)" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8"><el-form-item label="颜色"><el-input v-model="productForm.color" placeholder="如: 灰色" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="花型"><el-input v-model="productForm.pattern" placeholder="如: 提花" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="门幅(m)"><el-input-number v-model="productForm.standard_width" :precision="2" :min="0" :step="0.1" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8"><el-form-item label="库存"><el-input-number v-model="productForm.stock" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="安全库存"><el-input-number v-model="productForm.safety_stock" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
          <el-col :span="8">
            <el-form-item label="采购控制">
              <el-checkbox v-model="productForm.is_purchase" :true-value="true" :false-value="false">需采购</el-checkbox>
              <el-tag v-if="!productForm.is_purchase" type="warning" size="small" style="margin-left:6px">外加工</el-tag>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8"><el-form-item label="计价方式">
            <el-select v-model="productForm.calc_type" style="width:100%">
              <el-option label="按米" value="per_meter" />
              <el-option label="按平方" value="per_square" />
              <el-option label="按窗" value="per_window" />
              <el-option label="固定价" value="fixed" />
            </el-select>
          </el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showProductDialog = false">取消</el-button>
        <el-button type="primary" :loading="productSaving" @click="handleSaveProduct">保存</el-button>
      </template>
    </el-dialog>

    <!-- ─── 供应商快速新建对话框 ─── -->
    <el-dialog v-model="showSupplierDialog" title="新建供应商" width="500px">
      <el-form :model="supplierForm" label-width="80px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="名称"><el-input v-model="supplierForm.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="编码"><el-input v-model="supplierForm.code" placeholder="选填" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="类型">
              <el-select v-model="supplierForm.type" style="width:100%">
                <el-option label="布艺" value="布艺" />
                <el-option label="成品" value="成品" />
                <el-option label="配件" value="配件" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8"><el-form-item label="联系人"><el-input v-model="supplierForm.contact" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="电话"><el-input v-model="supplierForm.phone" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showSupplierDialog = false">取消</el-button>
        <el-button type="primary" :loading="supplierSaving" @click="handleSaveSupplier">保存</el-button>
      </template>
    </el-dialog>

    <!-- ─── 系列新建/编辑对话框 ─── -->
    <el-dialog v-model="showSeriesDialog" :title="seriesMode === 'edit' ? '编辑系列' : '新建系列'" width="400px">
      <el-form :model="seriesForm" label-width="70px">
        <el-form-item label="名称"><el-input v-model="seriesForm.name" /></el-form-item>
        <el-form-item label="编码"><el-input v-model="seriesForm.code" placeholder="选填" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSeriesDialog = false">取消</el-button>
        <el-button type="primary" :loading="seriesSaving" @click="handleSaveSeries">保存</el-button>
      </template>
    </el-dialog>

    <!-- ─── 分类管理对话框 ─── -->
    <el-dialog v-model="showCategoryDialog" title="产品分类管理" width="450px">
      <div style="margin-bottom:12px">
        <el-input v-model="catForm.name" placeholder="分类名称" style="width:200px;margin-right:8px" />
        <el-input v-model="catForm.code" placeholder="编码" style="width:100px;margin-right:8px" />
        <el-button type="primary" size="default" @click="handleCreateCategory">添加</el-button>
      </div>
      <el-table :data="categories" stripe size="small" style="width:100%">
        <el-table-column prop="name" label="分类名称" min-width="140" />
        <el-table-column prop="code" label="编码" width="100" />
        <el-table-column label="子分类" width="120">
          <template #default="{ row }">
            <span v-if="row.children?.length">{{ row.children.map(c => c.name).join(', ') }}</span>
            <span v-else style="color:#909399">-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { productApi, processingApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

// ── 供应商面板 ──
const allSuppliers = ref([])
const supplierKeyword = ref('')
const selectedSupplier = ref(null)

const filteredSuppliers = computed(() => {
  const kw = supplierKeyword.value.trim().toLowerCase()
  if (!kw) return allSuppliers.value
  return allSuppliers.value.filter(s =>
    s.name.toLowerCase().includes(kw) || s.code.toLowerCase().includes(kw)
  )
})

function selectSupplier(s) {
  selectedSupplier.value = s
  selectedSeries.value = null
  loadSeries()
  loadProducts()
}

// ── 系列面板 ──
const seriesList = ref([])
const selectedSeries = ref(null)

function selectSeries(s) {
  selectedSeries.value = s
  productPage.value = 1
  loadProducts()
}

// ── 产品列表 ──
const productList = ref([])
const productTotal = ref(0)
const productLoading = ref(false)
const productPage = ref(1)
const productKeyword = ref('')
const productTypeFilter = ref('')

// ── 所有系列（完整列表，用于产品对话框下拉） ──
const allSeries = ref([])

// ── 产品对话框 ──
const showProductDialog = ref(false)
const productMode = ref('create')
const productSaving = ref(false)
const productForm = reactive({
  name: '', code: '', product_type: '面料', category_id: null,
  supplier_id: null, series_id: null, processing_type_id: null,
  selling_price: '', cost_price: '', min_price: '',
  unit: '米', color: '', pattern: '', standard_width: 0,
  stock: 0, safety_stock: 0, is_purchase: true, calc_type: 'per_meter',
})

// ── 供应商对话框 ──
const showSupplierDialog = ref(false)
const supplierSaving = ref(false)
const supplierForm = reactive({ name: '', code: '', type: '布艺', contact: '', phone: '' })

// ── 系列对话框 ──
const showSeriesDialog = ref(false)
const seriesMode = ref('create')
const seriesSaving = ref(false)
const seriesForm = reactive({ name: '', code: '' })
const editingSeriesId = ref(null)

// ── 分类对话框 ──
const showCategoryDialog = ref(false)
const categories = ref([])
const catForm = reactive({ name: '', code: '' })

// ── 加工类型 ──
const processingTypes = ref([])

// ── 通用 ──
function validatePrice(val) {
  if (val === '' || val === null || val === undefined) return 0
  const num = parseFloat(String(val).replace(/[^\d.]/g, ''))
  return isNaN(num) ? 0 : Math.round(num * 100) / 100
}

function seriesForSupplier(supplierId) {
  if (!supplierId) return []
  return allSeries.value.filter(s => s.supplier_id === supplierId)
}

// ── 数据加载 ──
async function loadSuppliers() {
  try {
    const res = await productApi.listAllSuppliers()
    allSuppliers.value = res.data || []
  } catch {}
}

async function loadSeries() {
  // 加载当前供应商的系列（中间面板）
  try {
    const params = {}
    if (selectedSupplier.value) {
      params.supplier_id = selectedSupplier.value.id
    }
    const res = await productApi.listSeries(params)
    seriesList.value = res.data || []
  } catch {}
}

async function loadAllSeries() {
  // 加载所有系列（用于产品对话框下拉）
  try {
    const res = await productApi.listSeries({})
    allSeries.value = res.data || []
  } catch {}
}

async function loadProducts() {
  productLoading.value = true
  try {
    const params = { page: productPage.value, page_size: 20 }
    if (productKeyword.value) params.keyword = productKeyword.value
    if (productTypeFilter.value) params.product_type = productTypeFilter.value
    if (selectedSupplier.value) params.supplier_id = selectedSupplier.value.id
    if (selectedSeries.value) params.series_id = selectedSeries.value.id
    const res = await productApi.list(params)
    productList.value = res.items || []
    productTotal.value = res.total || 0
  } catch {} finally { productLoading.value = false }
}

async function loadCategories() {
  try {
    const res = await productApi.categories()
    categories.value = res.data || res.items || res || []
  } catch {}
}

async function loadProcessingTypes() {
  try {
    const res = await processingApi.listTypes()
    processingTypes.value = res.data || []
  } catch {}
}

// ── 供应商操作 ──
function openAddSupplier() {
  Object.assign(supplierForm, { name: '', code: '', type: '布艺', contact: '', phone: '' })
  showSupplierDialog.value = true
}

async function handleSaveSupplier() {
  if (!supplierForm.name) { ElMessage.warning('请输入供应商名称'); return }
  supplierSaving.value = true
  try {
    await productApi.createSupplier({ ...supplierForm })
    ElMessage.success('供应商已创建')
    showSupplierDialog.value = false
    await loadSuppliers()
    // 自动选中新建的供应商
    if (allSuppliers.value.length > 0) {
      selectSupplier(allSuppliers.value[allSuppliers.value.length - 1])
    }
  } catch {} finally { supplierSaving.value = false }
}

// ── 系列操作 ──
function openAddSeries() {
  seriesMode.value = 'create'
  editingSeriesId.value = null
  seriesForm.name = ''
  seriesForm.code = ''
  showSeriesDialog.value = true
}

function handleEditSeries(s) {
  seriesMode.value = 'edit'
  editingSeriesId.value = s.id
  seriesForm.name = s.name
  seriesForm.code = s.code || ''
  showSeriesDialog.value = true
}

async function handleSaveSeries() {
  if (!seriesForm.name) { ElMessage.warning('请输入系列名称'); return }
  seriesSaving.value = true
  try {
    if (seriesMode.value === 'edit') {
      await productApi.updateSeries(editingSeriesId.value, { name: seriesForm.name, code: seriesForm.code })
      ElMessage.success('系列已更新')
    } else {
      await productApi.createSeries({
        name: seriesForm.name,
        code: seriesForm.code,
        supplier_id: selectedSupplier.value.id,
        sort_order: 0,
      })
      ElMessage.success('系列已创建')
    }
    showSeriesDialog.value = false
    await loadSeries()
    await loadAllSeries()
  } catch {} finally { seriesSaving.value = false }
}

// ── 产品操作 ──
function openAddProduct() {
  productMode.value = 'create'
  resetProductForm()
  // 自动填充当前选中的供应商和系列
  if (selectedSupplier.value) productForm.supplier_id = selectedSupplier.value.id
  if (selectedSeries.value) productForm.series_id = selectedSeries.value.id
  showProductDialog.value = true
}

function handleEditProduct(row) {
  productMode.value = 'edit'
  Object.assign(productForm, {
    id: row.id, name: row.name, code: row.code,
    product_type: row.product_type || '面料',
    category_id: row.category_id || null,
    supplier_id: row.supplier_id || null,
    series_id: row.series_id || null,
    processing_type_id: row.processing_type_id || null,
    selling_price: row.selling_price || '',
    cost_price: row.cost_price || '',
    min_price: row.min_price || '',
    unit: row.unit || '米',
    color: row.color || '',
    pattern: row.pattern || '',
    standard_width: row.standard_width || 0,
    stock: row.stock || 0,
    safety_stock: row.safety_stock || 0,
    is_purchase: row.is_purchase !== undefined ? row.is_purchase : true,
    calc_type: row.calc_type || 'per_meter',
  })
  showProductDialog.value = true
}

function resetProductForm() {
  Object.assign(productForm, {
    id: undefined,
    name: '', code: '', product_type: '面料', category_id: null,
    supplier_id: null, series_id: null, processing_type_id: null,
    selling_price: '', cost_price: '', min_price: '',
    unit: '米', color: '', pattern: '', standard_width: 0,
    stock: 0, safety_stock: 0, is_purchase: true, calc_type: 'per_meter',
  })
}

function onSupplierChange(supplierId) {
  // 如果切换了供应商，清空系列选择
  productForm.series_id = null
}

async function handleSaveProduct() {
  productSaving.value = true
  try {
    const payload = {
      ...productForm,
      selling_price: validatePrice(productForm.selling_price),
      cost_price: validatePrice(productForm.cost_price),
      min_price: validatePrice(productForm.min_price),
    }
    if (productMode.value === 'create') {
      await productApi.create(payload)
      ElMessage.success('产品已创建')
    } else {
      const updateData = { ...payload }
      delete updateData.id
      await productApi.update(productForm.id, updateData)
      ElMessage.success('产品已更新')
    }
    showProductDialog.value = false
    await loadProducts()
  } catch {} finally { productSaving.value = false }
}

// ── 分类操作 ──
async function handleCreateCategory() {
  if (!catForm.name) { ElMessage.warning('请输入分类名称'); return }
  try {
    await productApi.createCategory({ name: catForm.name, code: catForm.code, parent_id: null, sort_order: 0 })
    ElMessage.success('分类已添加')
    catForm.name = ''; catForm.code = ''
    await loadCategories()
  } catch {}
}

// ── 初始化 ──
onMounted(async () => {
  await loadSuppliers()
  await loadAllSeries()
  await loadCategories()
  await loadProcessingTypes()
  // 默认选中第一个供应商
  if (allSuppliers.value.length > 0) {
    selectSupplier(allSuppliers.value[0])
  }
})
</script>

<style scoped>
.product-manager {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.pm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.pm-header h3 { font-size: 18px; margin: 0; }

.pm-body {
  display: flex;
  gap: 10px;
  flex: 1;
  min-height: 0;
}

/* 三个面板通用样式 */
.pm-panel {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
}

.pm-panel-suppliers {
  width: 200px;
  flex-shrink: 0;
}

.pm-panel-series {
  width: 200px;
  flex-shrink: 0;
}

.pm-panel-products {
  flex: 1;
  min-width: 0;
}

/* 面板标题 */
.panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-bottom: 1px solid #e4e7ed;
  font-weight: 600;
  font-size: 13px;
  background: #fafafa;
}

/* 搜索栏 */
.panel-search {
  padding: 6px 8px;
  border-bottom: 1px solid #e4e7ed;
}

/* 列表区域（可滚动） */
.panel-items {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

/* 列表项 */
.panel-item {
  display: flex;
  align-items: center;
  padding: 7px 12px;
  cursor: pointer;
  font-size: 13px;
  border-left: 3px solid transparent;
  gap: 6px;
}
.panel-item:hover {
  background: #f5f7fa;
}
.panel-item.active {
  background: #ecf5ff;
  border-left-color: #409eff;
  color: #409eff;
  font-weight: 500;
}
.item-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-code {
  font-size: 11px;
  color: #909399;
  flex-shrink: 0;
}

/* 空状态 */
.panel-empty {
  padding: 20px 12px;
  color: #c0c4cc;
  font-size: 12px;
  text-align: center;
}

/* 工具栏 */
.panel-toolbar {
  display: flex;
  gap: 6px;
  padding: 6px 8px;
  border-bottom: 1px solid #e4e7ed;
  flex-wrap: wrap;
}

/* 底部 */
.panel-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  border-top: 1px solid #e4e7ed;
  font-size: 12px;
}
.footer-info { color: #909399; }
.footer-total { color: #909399; }
</style>
