<template>
  <div class="dict-container">
    <!-- 左侧：字典类型列表 -->
    <div class="dict-sidebar">
      <div class="sidebar-header">
        <h3>字典类型</h3>
        <el-button size="small" type="primary" @click="showTypeDialog = true; typeMode = 'create'; resetTypeForm()">新建</el-button>
      </div>
      <div class="type-list">
        <div
          v-for="t in dictTypes"
          :key="t.id"
          class="type-item"
          :class="{ active: activeType?.dict_type === t.dict_type }"
          @click="selectType(t)"
        >
          <div class="type-name">{{ t.dict_name }}</div>
          <div class="type-code">{{ t.dict_type }}</div>
        </div>
        <div v-if="!dictTypes.length" class="empty-tip">暂无字典类型</div>
      </div>
    </div>

    <!-- 右侧：字典项列表 -->
    <div class="dict-main">
      <template v-if="activeType">
        <div class="main-header">
          <div>
            <h3 style="display:inline;margin-right:8px">{{ activeType.dict_name }}</h3>
            <el-tag size="small">{{ activeType.dict_type }}</el-tag>
            <span v-if="activeType.description" style="color:#999;font-size:13px;margin-left:8px">{{ activeType.description }}</span>
          </div>
          <div>
            <el-button size="small" @click="showTypeDialog = true; typeMode = 'edit'; fillTypeForm(activeType)">编辑类型</el-button>
            <el-button size="small" type="danger" plain @click="handleDeleteType(activeType)">删除类型</el-button>
            <el-button size="small" type="primary" @click="showItemDialog = true; itemMode = 'create'; resetItemForm()">添加项</el-button>
          </div>
        </div>

        <el-table :data="items" v-loading="loading" stripe size="small" style="width:100%">
          <el-table-column prop="dict_code" label="编码" width="120" />
          <el-table-column prop="dict_label" label="名称" min-width="140" />
          <el-table-column prop="sort_order" label="排序" width="70" align="center" />
          <el-table-column label="状态" width="70" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active !== false ? 'success' : 'info'" size="small">
                {{ row.is_active !== false ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="140" />
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button text size="small" @click="handleEditItem(row)">编辑</el-button>
              <el-popconfirm title="确认删除？" @confirm="handleDeleteItem(row)">
                <template #reference>
                  <el-button text size="small" type="danger">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </template>
      <div v-else class="empty-main">
        <p>请从左侧选择一个字典类型</p>
      </div>
    </div>

    <!-- 字典类型对话框 -->
    <el-dialog v-model="showTypeDialog" :title="typeMode === 'create' ? '新建字典类型' : '编辑字典类型'" width="450px">
      <el-form :model="typeForm" label-width="90px">
        <el-form-item label="类型编码"><el-input v-model="typeForm.dict_type" :disabled="typeMode === 'edit'" placeholder="如 order_type" /></el-form-item>
        <el-form-item label="类型名称"><el-input v-model="typeForm.dict_name" placeholder="如 订单类型" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="typeForm.sort_order" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="说明"><el-input v-model="typeForm.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTypeDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingType" @click="handleSaveType">保存</el-button>
      </template>
    </el-dialog>

    <!-- 字典项对话框 -->
    <el-dialog v-model="showItemDialog" :title="itemMode === 'create' ? '添加字典项' : '编辑字典项'" width="450px">
      <el-form :model="itemForm" label-width="70px">
        <el-form-item label="编码"><el-input v-model="itemForm.dict_code" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="itemForm.dict_label" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="itemForm.sort_order" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="itemForm.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showItemDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingItem" @click="handleSaveItem">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { systemApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

// 字典类型
const dictTypes = ref([])
const activeType = ref(null)
const showTypeDialog = ref(false)
const typeMode = ref('create')
const savingType = ref(false)
const typeForm = ref({ dict_type: '', dict_name: '', sort_order: 0, description: '' })

// 字典项
const items = ref([])
const loading = ref(false)
const showItemDialog = ref(false)
const itemMode = ref('create')
const savingItem = ref(false)
const itemForm = ref({ dict_code: '', dict_label: '', sort_order: 0, remark: '' })

function resetTypeForm() {
  typeForm.value = { dict_type: '', dict_name: '', sort_order: 0, description: '' }
}

function fillTypeForm(t) {
  typeForm.value = { id: t.id, dict_type: t.dict_type, dict_name: t.dict_name, sort_order: t.sort_order, description: t.description || '' }
}

function resetItemForm() {
  itemForm.value = { dict_code: '', dict_label: '', sort_order: 0, remark: '' }
}

async function loadTypes() {
  try {
    const res = await systemApi.listDictTypes()
    dictTypes.value = res.data || []
    // 如果有激活的类型但不在列表中，清除选择
    if (activeType.value && !dictTypes.value.find(t => t.dict_type === activeType.value.dict_type)) {
      activeType.value = null
    }
  } catch {}
}

async function selectType(t) {
  activeType.value = t
  await loadItems()
}

async function loadItems() {
  if (!activeType.value) return
  loading.value = true
  try {
    const params = { page: 1, page_size: 200, dict_type: activeType.value.dict_type }
    const res = await systemApi.listDictItems(params)
    items.value = res.items || res.data?.items || []
  } catch {} finally { loading.value = false }
}

// 类型 CRUD
async function handleSaveType() {
  if (!typeForm.value.dict_type || !typeForm.value.dict_name) {
    ElMessage.warning('请填写编码和名称')
    return
  }
  savingType.value = true
  try {
    if (typeMode.value === 'create') {
      await systemApi.createDictType(typeForm.value)
      ElMessage.success('字典类型已创建')
    } else {
      const payload = { ...typeForm.value }
      delete payload.id
      delete payload.dict_type
      await systemApi.updateDictType(typeForm.value.id, payload)
      ElMessage.success('字典类型已更新')
    }
    showTypeDialog.value = false
    await loadTypes()
    // 如果当前选中的类型被编辑，刷新选中状态
    if (activeType.value) {
      const updated = dictTypes.value.find(t => t.dict_type === activeType.value.dict_type)
      if (updated) activeType.value = updated
    }
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally { savingType.value = false }
}

async function handleDeleteType(t) {
  try {
    await ElMessageBox.confirm(`确定删除字典类型「${t.dict_name}」？该类型下所有字典项将被禁用。`, '确认', { type: 'warning' })
    await systemApi.deleteDictType(t.id)
    ElMessage.success('已删除')
    if (activeType.value?.id === t.id) activeType.value = null
    await loadTypes()
  } catch {}
}

// 项 CRUD
function handleEditItem(row) {
  itemMode.value = 'edit'
  itemForm.value = { id: row.id, dict_code: row.dict_code, dict_label: row.dict_label, sort_order: row.sort_order, remark: row.remark || '' }
  showItemDialog.value = true
}

async function handleSaveItem() {
  if (!itemForm.value.dict_code || !itemForm.value.dict_label) {
    ElMessage.warning('请填写编码和名称')
    return
  }
  savingItem.value = true
  try {
    if (itemMode.value === 'create') {
      await systemApi.createDictItem({ ...itemForm.value, dict_type: activeType.value.dict_type })
      ElMessage.success('字典项已添加')
    } else {
      const payload = { ...itemForm.value }
      delete payload.id
      await systemApi.updateDictItem(itemForm.value.id, payload)
      ElMessage.success('字典项已更新')
    }
    showItemDialog.value = false
    await loadItems()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally { savingItem.value = false }
}

async function handleDeleteItem(row) {
  try {
    await systemApi.deleteDictItem(row.id)
    ElMessage.success('已删除')
    await loadItems()
  } catch {}
}

onMounted(loadTypes)
</script>

<style scoped>
.dict-container {
  display: flex;
  gap: 16px;
  height: calc(100vh - 120px);
}
.dict-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
}
.sidebar-header h3 { font-size: 15px; margin: 0; }
.type-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}
.type-item {
  padding: 10px 16px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: all 0.15s;
}
.type-item:hover { background: #f5f7fa; }
.type-item.active {
  background: #ecf5ff;
  border-left-color: #409eff;
}
.type-name { font-size: 14px; font-weight: 500; }
.type-code { font-size: 12px; color: #999; margin-top: 2px; }
.empty-tip { text-align: center; padding: 32px; color: #999; }

.dict-main {
  flex: 1;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #ebeef5;
  padding: 16px;
  overflow-y: auto;
}
.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.empty-main {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-size: 15px;
}
</style>
