<template>
  <div class="store-page">
    <!-- 上方：表单视图（标准字段） -->
    <el-card shadow="never" class="form-card">
      <template #header>
        <div class="card-header">
          <span><strong>店铺信息配置</strong></span>
          <el-button type="primary" :loading="saving" @click="handleSaveForm">保存表单</el-button>
        </div>
      </template>

      <el-form v-loading="loading" :model="form" label-width="100px" label-position="left">
        <el-divider content-position="left">基本信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="店铺名称">
              <el-input v-model="form.store_name" placeholder="请输入店铺名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="店铺编号">
              <el-input v-model="form.store_code" placeholder="多店运行时区分使用" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="联系电话">
              <el-input v-model="form.phone" placeholder="请输入联系电话" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="店铺地址">
              <el-input v-model="form.address" placeholder="请输入店铺地址" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">订单配置</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="订单抬头">
              <el-input v-model="form.order_header" placeholder="打印订单时显示在顶部" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="订单模板">
              <el-input v-model="form.order_template" placeholder="订单打印模板标识" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="订单提示/声明">
          <el-input v-model="form.order_tips" type="textarea" :rows="2" placeholder="打印订单时显示在底部的声明文字" />
        </el-form-item>

        <el-divider content-position="left">合同配置</el-divider>
        <el-form-item label="合同抬头">
          <el-input v-model="form.contract_header" placeholder="打印合同时显示在顶部" />
        </el-form-item>
        <el-form-item label="合同提示/声明">
          <el-input v-model="form.contract_tips" type="textarea" :rows="2" placeholder="打印合同时显示在底部的声明文字" />
        </el-form-item>

        <div style="text-align:center;margin-top:16px">
          <el-button type="primary" :loading="saving" size="large" @click="handleSaveForm">
            保存店铺信息
          </el-button>
        </div>
      </el-form>
    </el-card>

    <!-- 下方：全部配置项表格（完整 CRUD） -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span><strong>全部配置项</strong></span>
          <el-button size="small" type="primary" @click="openAddDialog">添加配置项</el-button>
        </div>
      </template>

      <el-table :data="allItems" v-loading="loading" stripe size="small" style="width:100%">
        <el-table-column prop="dict_code" label="编码" width="160" />
        <el-table-column label="值" min-width="200">
          <template #default="{ row }">
            <el-input
              v-if="editingId === row.id"
              v-model="editValue"
              size="small"
              @keyup.enter="confirmEdit(row)"
              @blur="confirmEdit(row)"
            />
            <span v-else class="cell-value" @click="startEdit(row)">{{ row.dict_label || '(空)' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="70" align="center" />
        <el-table-column label="状态" width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active !== false ? 'success' : 'info'" size="small">
              {{ row.is_active !== false ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" @click="startEdit(row)">编辑</el-button>
            <el-popconfirm title="确认删除？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button text size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加配置项对话框 -->
    <el-dialog v-model="showAddDialog" title="添加配置项" width="450px">
      <el-form :model="newItem" label-width="80px">
        <el-form-item label="编码">
          <el-input v-model="newItem.dict_code" placeholder="如 wechat_qr" />
        </el-form-item>
        <el-form-item label="值">
          <el-input v-model="newItem.dict_label" placeholder="配置值" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="newItem.sort_order" :min="0" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :loading="addingItem" @click="handleAddItem">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { systemApi } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const saving = ref(false)

// ── 表单 - 标准字段 ──
const form = reactive({
  store_name: '',
  store_code: '',
  phone: '',
  address: '',
  order_header: '',
  order_template: '',
  order_tips: '',
  contract_header: '',
  contract_tips: '',
})

// ── 表格 - 全部配置项（CRUD）──
const allItems = ref([])

// 行内编辑
const editingId = ref(null)
const editValue = ref('')

// 新增项
const showAddDialog = ref(false)
const addingItem = ref(false)
const newItem = reactive({
  dict_code: '',
  dict_label: '',
  sort_order: 0,
})

// ── 加载数据 ──
async function loadAll() {
  loading.value = true
  try {
    // 加载全部配置项（含 id，用于 CRUD）
    const params = { page: 1, page_size: 200, dict_type: 'store_info' }
    const res = await systemApi.listDictItems(params)
    // 响应格式: { success, items, total, page, page_size }
    allItems.value = res.items || []

    // 同步到表单
    for (const item of allItems.value) {
      if (item.dict_code in form) {
        form[item.dict_code] = item.dict_label || ''
      }
    }
  } catch (e) {
    ElMessage.error('加载店铺信息失败')
  } finally {
    loading.value = false
  }
}

// ── 保存表单 ──
async function handleSaveForm() {
  saving.value = true
  try {
    const items = {}
    for (const [key, value] of Object.entries(form)) {
      if (value) items[key] = value
    }
    const res = await systemApi.updateStoreInfo({ items })
    ElMessage.success(res.message || '店铺信息已保存')
    await loadAll()
  } catch (e) {
    // api 已统一处理错误
  } finally {
    saving.value = false
  }
}

// ── 行内编辑 ──
function startEdit(row) {
  editingId.value = row.id
  editValue.value = row.dict_label || ''
}

async function confirmEdit(row) {
  if (editingId.value !== row.id) return
  const newVal = editValue.value
  editingId.value = null
  if (newVal === (row.dict_label || '')) return
  try {
    await systemApi.updateDictItem(row.id, { dict_label: newVal })
    ElMessage.success('已更新')
    await loadAll()
  } catch (e) {
    // 已统一处理
  }
}

// ── 删除配置项 ──
async function handleDelete(row) {
  try {
    await systemApi.deleteDictItem(row.id)
    ElMessage.success('已删除')
    await loadAll()
  } catch (e) {
    // 已统一处理
  }
}

// ── 新增配置项 ──
function openAddDialog() {
  newItem.dict_code = ''
  newItem.dict_label = ''
  newItem.sort_order = 0
  showAddDialog.value = true
}

async function handleAddItem() {
  if (!newItem.dict_code) {
    ElMessage.warning('请输入编码')
    return
  }
  addingItem.value = true
  try {
    await systemApi.createDictItem({
      dict_type: 'store_info',
      dict_code: newItem.dict_code,
      dict_label: newItem.dict_label,
      sort_order: newItem.sort_order,
    })
    ElMessage.success('配置项已添加')
    showAddDialog.value = false
    await loadAll()
  } catch (e) {
    // 已统一处理
  } finally {
    addingItem.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.store-page {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.el-divider { margin-top: 20px; margin-bottom: 20px; }
.cell-value {
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 3px;
  min-height: 22px;
  display: inline-block;
}
.cell-value:hover {
  background: #ecf5ff;
  color: #409eff;
}
</style>
