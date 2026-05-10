<template>
  <div>
    <el-card shadow="never">
      <div class="page-header">
        <h3>客户管理</h3>
        <el-button type="primary" @click="openCreate">新建客户</el-button>
      </div>

      <!-- 搜索 -->
      <el-form :inline="true" style="margin-bottom:16px">
        <el-form-item label="搜索">
          <el-input v-model="query.keyword" placeholder="姓名/电话" clearable @clear="loadData" @keyup.enter="loadData" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="list" v-loading="loading" stripe style="width:100%" @row-click="(r) => $router.push(`/customers/${r.id}`)">
        <el-table-column prop="name" label="姓名" width="110" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ typeLabels[row.type] || row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="90">
          <template #default="{ row }">{{ sourceLabels[row.source] || row.source }}</template>
        </el-table-column>
        <el-table-column prop="level" label="等级" width="70">
          <template #default="{ row }">
            <el-tag :type="levelType(row.level)" size="small">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="community" label="小区" width="120">
          <template #default="{ row }">{{ row.community || '-' }}</template>
        </el-table-column>
        <el-table-column prop="total_orders" label="订单数" width="70" align="center" />
        <el-table-column prop="total_amount" label="累计金额" width="120" align="right">
          <template #default="{ row }">¥{{ row.total_amount?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="debt" label="欠款" width="110" align="right">
          <template #default="{ row }"><span :style="{ color: row.debt > 0 ? '#f56c6c' : '#67c23a' }">¥{{ row.debt?.toFixed(2) }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" @click.stop="openEdit(row)">编辑</el-button>
            <el-button text size="small" @click.stop="$router.push(`/customers/${row.id}`)">详情</el-button>
            <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
              <template #reference><el-button text size="small" type="danger" @click.stop>删除</el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div style="margin-top:16px;text-align:right">
        <el-pagination v-model:current-page="query.page" :page-size="query.page_size" :total="total" layout="total, prev, pager, next" @current-change="loadData" />
      </div>
    </el-card>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editingId ? '编辑客户' : '新建客户'" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="姓名" prop="name"><el-input v-model="form.name" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话" prop="phone"><el-input v-model="form.phone" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="客户类型">
              <el-select v-model="form.type" style="width:100%">
                <el-option label="零售" value="retail" />
                <el-option label="工程" value="project" />
                <el-option label="设计师" value="designer" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户等级">
              <el-select v-model="form.level" style="width:100%">
                <el-option label="A级" value="A" />
                <el-option label="B级" value="B" />
                <el-option label="C级" value="C" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="客户来源">
              <el-select v-model="form.source" style="width:100%" allow-create filterable>
                <el-option label="自然进店" value="self" />
                <el-option label="老客介绍" value="referral" />
                <el-option label="线上引流" value="online" />
                <el-option label="小区推广" value="community" />
                <el-option label="电话销售" value="telemarketing" />
                <el-option label="展会活动" value="exhibition" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属小区">
              <el-input v-model="form.community" placeholder="如：阳光花园" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="地址">
          <el-input v-model="form.address" />
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="form.tags" multiple filterable allow-create default-first-option style="width:100%" placeholder="输入标签后回车添加">
            <el-option v-for="tag in tagOptions" :key="tag" :label="tag" :value="tag" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { customerApi } from '@/api'
import { ElMessage } from 'element-plus'

const list = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const editingId = ref(null)
const formRef = ref(null)

const query = reactive({ keyword: '', page: 1, page_size: 20 })
const form = reactive({
  name: '', phone: '', type: 'retail', source: '', level: 'C',
  community: '', address: '', tags: [], remark: '',
})
const rules = {
  name: [{ required: true, message: '请输入客户姓名' }],
  phone: [{ required: true, message: '请输入电话' }],
}

const typeLabels = { retail: '零售', project: '工程', designer: '设计师' }
const sourceLabels = {
  self: '自然进店', referral: '老客介绍', online: '线上引流',
  community: '小区推广', telemarketing: '电话销售', exhibition: '展会活动', other: '其他',
}
const tagOptions = ['高意向', '已测量', '已报价', '已成交', '老客户', '需跟进', '犹豫中', '价格敏感']

function levelType(level) {
  if (level === 'A') return 'danger'
  if (level === 'B') return 'warning'
  return 'info'
}

function resetForm() {
  form.name = ''
  form.phone = ''
  form.type = 'retail'
  form.source = ''
  form.level = 'C'
  form.community = ''
  form.address = ''
  form.tags = []
  form.remark = ''
}

function openCreate() {
  editingId.value = null
  resetForm()
  showDialog.value = true
}

function openEdit(row) {
  editingId.value = row.id
  form.name = row.name
  form.phone = row.phone
  form.type = row.type || 'retail'
  form.source = row.source || ''
  form.level = row.level || 'C'
  form.community = row.community || ''
  form.address = row.address || ''
  form.tags = row.tags || []
  form.remark = row.remark || ''
  showDialog.value = true
}

async function loadData() {
  loading.value = true
  try {
    const res = await customerApi.list(query)
    list.value = res.items
    total.value = res.total
  } catch {} finally { loading.value = false }
}

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editingId.value) {
      await customerApi.update(editingId.value, form)
      ElMessage.success('客户已更新')
    } else {
      await customerApi.create(form)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    loadData()
  } finally { saving.value = false }
}

async function handleDelete(id) {
  await customerApi.delete(id)
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h3 { font-size: 18px; }
[class*='el-col'] { margin-bottom: 0; }
</style>
