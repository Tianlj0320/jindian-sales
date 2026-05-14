<template>
  <el-card shadow="never">
    <div class="page-header">
      <h3>供应商管理</h3>
      <div>
        <el-button type="primary" @click="dialogMode = 'create'; resetForm(); showDialog = true">新建供应商</el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <el-form :inline="true" size="small" style="margin-bottom:10px">
      <el-form-item label="搜索">
        <el-input v-model="query.keyword" placeholder="名称/联系人/手机号" clearable style="width:180px" @clear="loadData" @keyup.enter="loadData" />
      </el-form-item>
      <el-form-item label="类型">
        <el-select v-model="query.type" clearable placeholder="全部" style="width:100px" @change="loadData">
          <el-option label="布艺" value="布艺" />
          <el-option label="成品" value="成品" />
          <el-option label="配件" value="配件" />
          <el-option label="其他" value="其他" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadData">查询</el-button>
        <el-button @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="list" v-loading="loading" stripe style="width:100%;cursor:pointer" highlight-current-row @row-dblclick="handleRowDblClick" @row-click="handleRowClick">
      <el-table-column type="index" label="序号" width="50" />
      <el-table-column prop="code" label="编码" width="100" />
      <el-table-column prop="name" label="名称" min-width="140" />
      <el-table-column prop="type" label="类型" width="70" />
      <el-table-column prop="contact" label="联系人" width="90" />
      <el-table-column prop="phone" label="电话" width="110" />
      <el-table-column label="QQ/微信" width="120">
        <template #default="{ row }">{{ row.qq || '-' }} / {{ row.wechat || '-' }}</template>
      </el-table-column>
      <el-table-column label="收款账号" width="130">
        <template #default="{ row }">{{ row.bank_account || '-' }}</template>
      </el-table-column>
      <el-table-column label="开户行" width="120">
        <template #default="{ row }">{{ row.bank_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="收款人" width="80">
        <template #default="{ row }">{{ row.payee || '-' }}</template>
      </el-table-column>
      <el-table-column prop="delivery_days" label="交期" width="60" align="center" />
      <el-table-column prop="address" label="地址" min-width="150" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button text size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="margin-top:8px;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:12px;color:#999">双击供应商行编辑 / 共 {{ total }} 条</span>
      <el-pagination v-model:current-page="query.page" :page-size="query.page_size" :total="total" layout="total, prev, pager, next" size="small" @current-change="loadData" />
    </div>
  </el-card>

  <!-- 新建/编辑对话框 -->
  <el-dialog v-model="showDialog" :title="dialogMode === 'edit' ? '编辑供应商' : '新建供应商'" width="600px">
    <el-form :model="form" label-width="90px">
      <el-row :gutter="16">
        <el-col :span="12"><el-form-item label="名称"><el-input v-model="form.name" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="编码"><el-input v-model="form.code" placeholder="选填" /></el-form-item></el-col>
      </el-row>
      <el-row :gutter="16">
        <el-col :span="8">
          <el-form-item label="类型">
            <el-select v-model="form.type" style="width:100%">
              <el-option label="布艺" value="布艺" />
              <el-option label="成品" value="成品" />
              <el-option label="配件" value="配件" />
              <el-option label="其他" value="其他" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8"><el-form-item label="联系人"><el-input v-model="form.contact" /></el-form-item></el-col>
        <el-col :span="8"><el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item></el-col>
      </el-row>
      <el-row :gutter="16">
        <el-col :span="8"><el-form-item label="QQ"><el-input v-model="form.qq" /></el-form-item></el-col>
        <el-col :span="8"><el-form-item label="微信"><el-input v-model="form.wechat" /></el-form-item></el-col>
        <el-col :span="8"><el-form-item label="交期(天)"><el-input-number v-model="form.delivery_days" :min="0" :max="90" style="width:100%" /></el-form-item></el-col>
      </el-row>
      <el-row :gutter="16">
        <el-col :span="8"><el-form-item label="收款账号"><el-input v-model="form.bank_account" /></el-form-item></el-col>
        <el-col :span="8"><el-form-item label="开户银行"><el-input v-model="form.bank_name" /></el-form-item></el-col>
        <el-col :span="8"><el-form-item label="收款人"><el-input v-model="form.payee" /></el-form-item></el-col>
      </el-row>
      <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showDialog = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { productApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const list = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const dialogMode = ref('create')

const query = reactive({ keyword: '', type: '', page: 1, page_size: 20 })
const form = reactive({
  name: '', code: '', type: '布艺', contact: '', phone: '',
  qq: '', wechat: '', bank_account: '', bank_name: '', payee: '',
  address: '', delivery_days: 7,
})

function resetForm() {
  form.id = undefined
  Object.assign(form, {
    name: '', code: '', type: '布艺', contact: '', phone: '',
    qq: '', wechat: '', bank_account: '', bank_name: '', payee: '',
    address: '', delivery_days: 7,
  })
}

async function loadData() {
  loading.value = true
  try {
    const params = { page: query.page, page_size: query.page_size }
    if (query.keyword) params.keyword = query.keyword
    if (query.type) params.type = query.type
    const res = await productApi.listSuppliers(params)
    list.value = res.items || []
    total.value = res.total || 0
  } catch {} finally { loading.value = false }
}

function resetQuery() {
  query.keyword = ''
  query.type = ''
  query.page = 1
  loadData()
}

function handleRowClick(row) {
  handleEdit(row)
}

function handleRowDblClick(row) {
  handleEdit(row)
}

function handleEdit(row) {
  dialogMode.value = 'edit'
  form.id = row.id
  Object.assign(form, {
    name: row.name, code: row.code || '', type: row.type || '布艺',
    contact: row.contact || '', phone: row.phone || '',
    qq: row.qq || '', wechat: row.wechat || '',
    bank_account: row.bank_account || '', bank_name: row.bank_name || '',
    payee: row.payee || '',
    address: row.address || '', delivery_days: row.delivery_days || 7,
  })
  showDialog.value = true
}

async function handleSave() {
  if (!form.name) { ElMessage.warning('请输入供应商名称'); return }
  saving.value = true
  try {
    const payload = { ...form }
    delete payload.id
    if (dialogMode.value === 'edit') {
      await productApi.updateSupplier(form.id, payload)
      ElMessage.success('供应商已更新')
    } else {
      await productApi.createSupplier(payload)
      ElMessage.success('供应商已创建')
    }
    showDialog.value = false
    loadData()
  } catch {} finally { saving.value = false }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除供应商「${row.name}」吗？`, '确认', { type: 'warning' })
    await productApi.deleteSupplier(row.id)
    ElMessage.success('供应商已删除')
    loadData()
  } catch {}
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h3 { font-size: 18px; }
</style>
