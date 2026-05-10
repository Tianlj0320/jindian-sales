<template>
  <el-card shadow="never">
    <div class="page-header">
      <h3>产品管理</h3>
      <div>
        <el-button @click="showCategoryDialog = true">分类管理</el-button>
        <el-button type="primary" @click="showDialog = true; dialogMode = 'create'; resetForm()">新建产品</el-button>
      </div>
    </div>

    <el-form :inline="true" style="margin-bottom:16px">
      <el-form-item label="搜索"><el-input v-model="query.keyword" placeholder="名称/编码" clearable @keyup.enter="loadData" /></el-form-item>
      <el-form-item label="类型">
        <el-select v-model="query.product_type" clearable style="width:120px" @change="loadData">
          <el-option label="面料" value="面料" />
          <el-option label="辅料" value="辅料" />
          <el-option label="成品" value="成品" />
        </el-select>
      </el-form-item>
      <el-form-item label="分类">
        <el-select v-model="query.category" clearable style="width:130px" @change="loadData">
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.name" />
        </el-select>
      </el-form-item>
      <el-form-item><el-button type="primary" @click="loadData">查询</el-button></el-form-item>
    </el-form>

    <el-table :data="list" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="code" label="编码" width="110" />
      <el-table-column prop="name" label="名称" min-width="150" />
      <el-table-column prop="product_type" label="类型" width="70" />
      <el-table-column prop="category_name" label="分类" width="80" />
      <el-table-column prop="supplier_name" label="供应商" width="120" />
      <el-table-column label="颜色/花型" width="110">
        <template #default="{ row }">{{ row.color || '-' }} / {{ row.pattern || '-' }}</template>
      </el-table-column>
      <el-table-column label="门幅" width="70" align="center">
        <template #default="{ row }">{{ row.standard_width || '-' }}</template>
      </el-table-column>
      <el-table-column prop="cost_price" label="进价" width="90" align="right">
        <template #default="{ row }">¥{{ row.cost_price?.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column prop="selling_price" label="售价" width="90" align="right">
        <template #default="{ row }">¥{{ row.selling_price?.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column prop="min_price" label="最低价" width="90" align="right">
        <template #default="{ row }">¥{{ row.min_price?.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column prop="stock" label="库存" width="70" align="center">
        <template #default="{ row }">
          <span :style="{ color: row.stock <= row.safety_stock ? '#f56c6c' : '#67c23a' }">{{ row.stock }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="unit" label="单位" width="60" />
      <el-table-column label="计价方式" width="80" align="center">
        <template #default="{ row }">{{ { per_meter: '按米', per_square: '按平方', per_window: '按窗', fixed: '固定价' }[row.calc_type] || '按米' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" @click="handleEdit(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="margin-top:16px;text-align:right">
      <el-pagination v-model:current-page="query.page" :page-size="query.page_size" :total="total" layout="total, prev, pager, next" @current-change="loadData" />
    </div>
  </el-card>

  <!-- 产品新建/编辑对话框 -->
  <el-dialog v-model="showDialog" :title="dialogMode === 'edit' ? '编辑产品' : '新建产品'" width="700px" @closed="resetForm">
    <el-form :model="form" label-width="80px">
      <el-row :gutter="16">
        <el-col :span="12"><el-form-item label="名称"><el-input v-model="form.name" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="编码"><el-input v-model="form.code" /></el-form-item></el-col>
      </el-row>
      <el-row :gutter="16">
        <el-col :span="8">
          <el-form-item label="类型">
            <el-select v-model="form.product_type" style="width:100%">
              <el-option label="面料" value="面料" />
              <el-option label="辅料" value="辅料" />
              <el-option label="成品" value="成品" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="分类">
            <el-select v-model="form.category_id" style="width:100%" clearable value-key="id">
              <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="供应商">
            <el-select v-model="form.supplier_id" style="width:100%" clearable filterable>
              <el-option v-for="s in suppliers" :key="s.id" :label="s.name" :value="s.id" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="16">
        <el-col :span="8"><el-form-item label="加工类型">
          <el-select v-model="form.processing_type_id" style="width:100%" clearable>
            <el-option v-for="t in processingTypes" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item></el-col>
        <el-col :span="8"><el-form-item label="售价(元)"><el-input v-model="form.selling_price" placeholder="0.00" @blur="form.selling_price = validatePrice(form.selling_price)" /></el-form-item></el-col>
        <el-col :span="8"><el-form-item label="进价(元)"><el-input v-model="form.cost_price" placeholder="0.00" @blur="form.cost_price = validatePrice(form.cost_price)" /></el-form-item></el-col>
      </el-row>
      <el-row :gutter="16">
        <el-col :span="8"><el-form-item label="最低价(元)"><el-input v-model="form.min_price" placeholder="0.00" @blur="form.min_price = validatePrice(form.min_price)" /></el-form-item></el-col>
        <el-col :span="8"><el-form-item label="单位"><el-input v-model="form.unit" placeholder="米" /></el-form-item></el-col>
      </el-row>
      <el-row :gutter="16">
        <el-col :span="8"><el-form-item label="颜色"><el-input v-model="form.color" placeholder="如: 灰色" /></el-form-item></el-col>
        <el-col :span="8"><el-form-item label="花型"><el-input v-model="form.pattern" placeholder="如: 提花" /></el-form-item></el-col>
        <el-col :span="8"><el-form-item label="门幅(m)"><el-input-number v-model="form.standard_width" :precision="2" :min="0" :step="0.1" style="width:100%" /></el-form-item></el-col>
      </el-row>
      <el-row :gutter="16">
        <el-col :span="8"><el-form-item label="库存"><el-input-number v-model="form.stock" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
        <el-col :span="8"><el-form-item label="安全库存"><el-input-number v-model="form.safety_stock" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
        <el-col :span="8"><el-form-item label="计价方式">
          <el-select v-model="form.calc_type" style="width:100%">
            <el-option label="按米" value="per_meter" />
            <el-option label="按平方" value="per_square" />
            <el-option label="按窗" value="per_window" />
            <el-option label="固定价" value="fixed" />
          </el-select>
        </el-form-item></el-col>
      </el-row>
    </el-form>
    <template #footer>
      <el-button @click="showDialog = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>

  <!-- 分类管理对话框 -->
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
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { productApi, processingApi } from '@/api'
import { ElMessage } from 'element-plus'

const list = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const showCategoryDialog = ref(false)
const dialogMode = ref('create')
const categories = ref([])
const suppliers = ref([])
const processingTypes = ref([])

const query = reactive({ keyword: '', product_type: '', category: '', page: 1, page_size: 20 })
const form = reactive({
  name: '', code: '', product_type: '面料', category_id: null,
  supplier_id: null, processing_type_id: null,
  selling_price: '', cost_price: '', min_price: '',
  unit: '米', color: '', pattern: '', standard_width: 0,
  stock: 0, safety_stock: 0, calc_type: 'per_meter',
})
const catForm = reactive({ name: '', code: '' })

function validatePrice(val) {
  if (val === '' || val === null || val === undefined) return 0
  const num = parseFloat(String(val).replace(/[^\d.]/g, ''))
  return isNaN(num) ? 0 : Math.round(num * 100) / 100
}

function resetForm() {
  Object.assign(form, {
    name: '', code: '', product_type: '面料', category_id: null,
    supplier_id: null, processing_type_id: null,
    selling_price: '', cost_price: '', min_price: '',
    unit: '米', color: '', pattern: '', standard_width: 0,
    stock: 0, safety_stock: 0, calc_type: 'per_meter',
  })
}

async function loadData() {
  loading.value = true
  try {
    const params = { ...query }
    const res = await productApi.list(params)
    list.value = res.items
    total.value = res.total
  } catch {} finally { loading.value = false }
}

async function loadCategories() {
  try {
    const res = await productApi.categories()
    categories.value = res.data || res.items || res || []
  } catch {}
}

async function loadSuppliers() {
  try {
    const res = await productApi.listSuppliers({ page: 1, page_size: 200 })
    suppliers.value = res.items || []
  } catch {}
}

async function loadProcessingTypes() {
  try {
    const res = await processingApi.listTypes()
    processingTypes.value = res.data || []
  } catch {}
}

function handleEdit(row) {
  dialogMode.value = 'edit'
  Object.assign(form, {
    id: row.id, name: row.name, code: row.code,
    product_type: row.product_type || '面料',
    category_id: row.category_id || null,
    supplier_id: row.supplier_id || null,
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
    calc_type: row.calc_type || 'per_meter',
  })
  showDialog.value = true
}

async function handleSave() {
  saving.value = true
  try {
    // 构建提交数据，将价格转为数字
    const payload = {
      ...form,
      selling_price: validatePrice(form.selling_price),
      cost_price: validatePrice(form.cost_price),
      min_price: validatePrice(form.min_price),
    }
    if (dialogMode.value === 'create') {
      await productApi.create(payload)
      ElMessage.success('产品已创建')
    } else {
      const updateData = { ...payload }
      delete updateData.id
      await productApi.update(form.id, updateData)
      ElMessage.success('产品已更新')
    }
    showDialog.value = false
    loadData()
  } catch {} finally { saving.value = false }
}

async function handleCreateCategory() {
  if (!catForm.name) { ElMessage.warning('请输入分类名称'); return }
  try {
    await productApi.createCategory({ name: catForm.name, code: catForm.code, parent_id: null, sort_order: 0 })
    ElMessage.success('分类已添加')
    catForm.name = ''; catForm.code = ''
    loadCategories()
  } catch {}
}

onMounted(() => {
  loadData()
  loadCategories()
  loadSuppliers()
  loadProcessingTypes()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h3 { font-size: 18px; }
</style>
