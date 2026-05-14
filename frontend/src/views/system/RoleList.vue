<template>
  <el-card shadow="never">
    <div class="page-header">
      <h3>角色权限管理</h3>
      <el-button type="primary" @click="showDialog = true; dialogMode = 'create'; resetForm()">添加角色</el-button>
    </div>

    <el-table :data="list" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="name" label="角色名称" width="140" />
      <el-table-column prop="code" label="编码" width="120" />
      <el-table-column prop="description" label="描述" min-width="200" />
      <el-table-column prop="sort_order" label="排序" width="60" align="center" />
      <el-table-column label="权限数" width="80" align="center">
        <template #default="{ row }">
          <el-tag size="small">{{ (row.permissions || []).length }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active !== false ? 'success' : 'info'" size="small">
            {{ row.is_active !== false ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button text size="small" type="primary" @click="handleEditPermissions(row)">权限</el-button>
          <el-popconfirm
            :title="row.is_active !== false ? '确认禁用？' : '确认启用？'"
            @confirm="handleToggleActive(row)"
          >
            <template #reference>
              <el-button text size="small" :type="row.is_active !== false ? 'warning' : 'success'">
                {{ row.is_active !== false ? '禁用' : '启用' }}
              </el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 角色编辑对话框 -->
    <el-dialog v-model="showDialog" :title="dialogMode === 'create' ? '添加角色' : '编辑角色'" width="480px">
      <el-form :model="form" label-width="80px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="角色名称"><el-input v-model="form.name" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="编码"><el-input v-model="form.code" :disabled="dialogMode === 'edit'" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort_order" :min="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 权限编辑对话框 -->
    <el-dialog v-model="showPermDialog" title="权限配置" width="500px">
      <el-checkbox-group v-model="permForm.permissions">
        <el-row :gutter="16">
          <el-col v-for="perm in allPermissions" :key="perm.key" :span="12">
            <el-checkbox :label="perm.key" :key="perm.key" style="margin-bottom:10px">
              {{ perm.label }}
            </el-checkbox>
          </el-col>
        </el-row>
      </el-checkbox-group>
      <div style="margin-top:12px">
        <el-button size="small" @click="selectAllPerms">全选</el-button>
        <el-button size="small" @click="clearAllPerms">全不选</el-button>
      </div>
      <template #footer>
        <el-button @click="showPermDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingPerm" @click="handleSavePermissions">保存权限</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { roleApi } from '@/api'
import { ElMessage } from 'element-plus'

const list = ref([])
const loading = ref(false)
const saving = ref(false)
const savingPerm = ref(false)
const showDialog = ref(false)
const showPermDialog = ref(false)
const dialogMode = ref('create')
const form = ref({ name: '', code: '', description: '', sort_order: 0 })
const permForm = ref({ role_id: null, permissions: [] })

const allPermissions = [
  { key: 'dashboard', label: '工作台' },
  { key: 'orders', label: '订单管理' },
  { key: 'customers', label: '客户管理' },
  { key: 'products', label: '产品管理' },
  { key: 'purchases', label: '采购管理' },
  { key: 'warehouse', label: '仓库管理' },
  { key: 'installations', label: '安装管理' },
  { key: 'production', label: '生产反馈' },
  { key: 'finance', label: '财务管理' },
  { key: 'reports', label: '报表统计' },
  { key: 'system', label: '系统设置' },
  { key: 'admin', label: '管理员' },
]

function resetForm() {
  form.value = { name: '', code: '', description: '', sort_order: 0 }
}

async function loadData() {
  loading.value = true
  try {
    const res = await roleApi.list()
    list.value = res.data || res.items || res || []
  } catch {} finally { loading.value = false }
}

function handleEdit(row) {
  dialogMode.value = 'edit'
  form.value = { id: row.id, name: row.name, code: row.code, description: row.description, sort_order: row.sort_order }
  showDialog.value = true
}

function handleEditPermissions(row) {
  permForm.value = { role_id: row.id, permissions: [...(row.permissions || [])] }
  showPermDialog.value = true
}

function selectAllPerms() {
  permForm.value.permissions = allPermissions.map(p => p.key)
}

function clearAllPerms() {
  permForm.value.permissions = []
}

async function handleSave() {
  saving.value = true
  try {
    if (dialogMode.value === 'create') {
      await roleApi.create(form.value)
      ElMessage.success('角色已添加')
    } else {
      const payload = { ...form.value }
      delete payload.id
      await roleApi.update(form.value.id, payload)
      ElMessage.success('角色已更新')
    }
    showDialog.value = false
    loadData()
  } catch {} finally { saving.value = false }
}

async function handleSavePermissions() {
  savingPerm.value = true
  try {
    await roleApi.updatePermissions(permForm.value.role_id, { permissions: permForm.value.permissions })
    ElMessage.success('权限已更新')
    showPermDialog.value = false
    loadData()
  } catch {} finally { savingPerm.value = false }
}

async function handleToggleActive(row) {
  try {
    await roleApi.update(row.id, { is_active: row.is_active !== false ? false : true })
    ElMessage.success(row.is_active !== false ? '已禁用' : '已启用')
    loadData()
  } catch {}
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h3 { font-size: 18px; }
</style>
