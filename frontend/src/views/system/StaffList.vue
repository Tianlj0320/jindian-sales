<template>
  <el-card shadow="never">
    <div class="page-header">
      <h3>员工管理</h3>
      <el-button type="primary" @click="showDialog = true; dialogMode = 'create'; resetForm()">添加员工</el-button>
    </div>

    <el-table :data="list" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="username" label="用户名" width="140" />
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="phone" label="手机号" width="140" />
      <el-table-column prop="role" label="角色" width="80">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" size="small">
            {{ { admin: '管理员', manager: '经理', staff: '员工' }[row.role] || row.role }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="position" label="职务" width="100" />
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active !== false ? 'success' : 'info'" size="small">
            {{ row.is_active !== false ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" @click="handleEdit(row)">编辑</el-button>
          <el-popconfirm
            :title="row.is_active !== false ? '确认禁用该员工？' : '确认启用该员工？'"
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

    <el-dialog v-model="showDialog" :title="dialogMode === 'create' ? '添加员工' : '编辑员工'" width="480px">
      <el-form :model="form" label-width="80px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="用户名"><el-input v-model="form.username" :disabled="dialogMode === 'edit'" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="dialogMode === 'create' ? '密码' : '新密码'">
              <el-input v-model="form.password" type="password" :placeholder="dialogMode === 'edit' ? '留空不修改' : ''" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="姓名"><el-input v-model="form.name" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="角色">
              <el-select v-model="form.role" style="width:100%">
                <el-option label="管理员" value="admin" />
                <el-option label="经理" value="manager" />
                <el-option label="员工" value="staff" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="职务"><el-input v-model="form.position" /></el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { authApi } from '@/api'
import { ElMessage } from 'element-plus'

const list = ref([])
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const dialogMode = ref('create')
const form = ref({ username: '', password: '', name: '', phone: '', role: 'staff', position: '' })

function resetForm() {
  form.value = { username: '', password: '', name: '', phone: '', role: 'staff', position: '' }
}

async function loadData() {
  loading.value = true
  try {
    const res = await authApi.listUsers()
    list.value = res.data || res.items || res || []
  } catch {} finally { loading.value = false }
}

function handleEdit(row) {
  dialogMode.value = 'edit'
  form.value = {
    id: row.id,
    username: row.username,
    password: '',
    name: row.name,
    phone: row.phone,
    role: row.role,
    position: row.position,
  }
  showDialog.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (dialogMode.value === 'create') {
      await authApi.createUser(form.value)
      ElMessage.success('员工已添加')
    } else {
      const payload = { ...form.value }
      delete payload.id
      delete payload.username
      if (!payload.password) delete payload.password
      await authApi.updateUser(form.value.id, payload)
      ElMessage.success('员工已更新')
    }
    showDialog.value = false
    loadData()
  } catch {} finally { saving.value = false }
}

async function handleToggleActive(row) {
  try {
    await authApi.updateUser(row.id, { is_active: row.is_active !== false ? false : true })
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
