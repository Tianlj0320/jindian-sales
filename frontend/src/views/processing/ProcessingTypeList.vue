<template>
  <el-card shadow="never">
    <div class="page-header">
      <h3>加工类型管理</h3>
      <el-button type="primary" @click="showDialog = true; dialogMode = 'create'; resetForm()">新建加工类型</el-button>
    </div>

    <el-table :data="list" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="code" label="编码" width="100" />
      <el-table-column prop="name" label="名称" width="150" />
      <el-table-column prop="description" label="描述" min-width="200" />
      <el-table-column label="辅料规则" width="250">
        <template #default="{ row }">
          <span v-if="row.rules?.length">{{ row.rules.map(r => r.material_name).join('、') }}</span>
          <span v-else style="color:#909399">无</span>
        </template>
      </el-table-column>
      <el-table-column label="启用" width="70" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button text size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="dialogMode === 'edit' ? '编辑加工类型' : '新建加工类型'" width="700px" @closed="resetForm">
      <el-form :model="form" label-width="80px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="名称"><el-input v-model="form.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="编码"><el-input v-model="form.code" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>

        <el-divider content-position="left">辅料规则</el-divider>
        <div v-for="(rule, idx) in form.rules" :key="idx" style="border:1px solid #ebeef5;padding:12px;border-radius:4px;margin-bottom:8px">
          <el-row :gutter="8">
            <el-col :span="6"><el-form-item label="辅料名" :label-width="60"><el-input v-model="rule.material_name" size="small" /></el-form-item></el-col>
            <el-col :span="4"><el-form-item label="单位" :label-width="40"><el-input v-model="rule.unit" size="small" placeholder="米" /></el-form-item></el-col>
            <el-col :span="5"><el-form-item label="公式" :label-width="40"><el-input v-model="rule.qty_formula" size="small" placeholder="如: width" /></el-form-item></el-col>
            <el-col :span="4"><el-form-item label="单价" :label-width="40"><el-input v-model.number="rule.unit_price" size="small" /></el-form-item></el-col>
            <el-col :span="3">
              <el-form-item label="必选" :label-width="40">
                <el-switch v-model="rule.is_required" size="small" />
              </el-form-item>
            </el-col>
            <el-col :span="2">
              <el-button text size="small" type="danger" @click="form.rules.splice(idx, 1)">×</el-button>
            </el-col>
          </el-row>
          <div style="color:#909399;font-size:12px">可用变量: width(宽), height(高), qty(数量), fold_ratio(倍率)。示例: "width * 1.1 + 0.2"</div>
        </div>
        <el-button size="small" @click="form.rules.push({ material_name: '', unit: '米', qty_formula: '1', unit_price: 0, is_required: true, sort_order: 0 })">+ 添加辅料规则</el-button>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { processingApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const list = ref([])
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const dialogMode = ref('create')

const form = reactive({
  name: '', code: '', description: '',
  rules: [],
})

function resetForm() {
  Object.assign(form, { name: '', code: '', description: '', rules: [] })
}

async function loadData() {
  loading.value = true
  try {
    const res = await processingApi.listTypes()
    list.value = res.data || []
  } catch {} finally { loading.value = false }
}

function handleEdit(row) {
  dialogMode.value = 'edit'
  form.id = row.id
  form.name = row.name
  form.code = row.code
  form.description = row.description || ''
  form.rules = (row.rules || []).map(r => ({
    material_name: r.material_name,
    unit: r.unit || '米',
    qty_formula: r.qty_formula || '1',
    unit_price: r.unit_price || 0,
    is_required: r.is_required !== false,
    sort_order: r.sort_order || 0,
  }))
  showDialog.value = true
}

async function handleSave() {
  if (!form.name || !form.code) { ElMessage.warning('请填写名称和编码'); return }
  saving.value = true
  try {
    if (dialogMode.value === 'create') {
      await processingApi.createType({
        name: form.name,
        code: form.code,
        description: form.description,
        sort_order: 0,
        is_active: true,
        rules: form.rules,
      })
      ElMessage.success('加工类型已创建')
    } else {
      await processingApi.updateType(form.id, { name: form.name, code: form.code, description: form.description })
      // 批量删除旧规则再添加新规则不在本次实现范围内，简化处理
      ElMessage.success('加工类型已更新（辅料规则请分别管理）')
    }
    showDialog.value = false
    loadData()
  } catch {} finally { saving.value = false }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除加工类型「${row.name}」吗？`, '确认', { type: 'warning' })
    await processingApi.deleteType(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch {}
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h3 { font-size: 18px; }
</style>
