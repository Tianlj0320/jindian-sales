<template>
  <div>
    <el-button text @click="$router.back()" style="margin-bottom:16px">← 返回</el-button>

    <el-card v-if="customer" shadow="never" style="margin-bottom:20px">
      <template #header>
        <div class="page-header">
          <h3>{{ customer.name }}</h3>
          <div>
            <el-button @click="startEdit" v-if="!editing">编辑</el-button>
            <template v-if="editing">
              <el-button @click="cancelEdit">取消</el-button>
              <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
            </template>
          </div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="姓名">
          <el-input v-if="editing" v-model="editForm.name" size="small" />
          <span v-else>{{ customer.name }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="电话">
          <el-input v-if="editing" v-model="editForm.phone" size="small" />
          <span v-else>{{ customer.phone }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-select v-if="editing" v-model="editForm.type" size="small" style="width:100%">
            <el-option label="零售" value="retail" />
            <el-option label="工程" value="project" />
            <el-option label="设计师" value="designer" />
          </el-select>
          <span v-else>{{ typeLabels[customer.type] || customer.type }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="来源">
          <el-select v-if="editing" v-model="editForm.source" size="small" style="width:100%" allow-create filterable>
            <el-option label="自然进店" value="self" />
            <el-option label="老客介绍" value="referral" />
            <el-option label="线上引流" value="online" />
            <el-option label="小区推广" value="community" />
            <el-option label="其他" value="other" />
          </el-select>
          <span v-else>{{ sourceLabels[customer.source] || customer.source }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="等级">
          <el-select v-if="editing" v-model="editForm.level" size="small" style="width:100%">
            <el-option label="A级" value="A" />
            <el-option label="B级" value="B" />
            <el-option label="C级" value="C" />
          </el-select>
          <el-tag v-else :type="levelType(customer.level)" size="small">{{ customer.level }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="导购">
          <span>{{ customer.salesperson_name || '-' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="小区">
          <el-input v-if="editing" v-model="editForm.community" size="small" />
          <span v-else>{{ customer.community || '-' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="地址" :span="2">
          <el-input v-if="editing" v-model="editForm.address" size="small" />
          <span v-else>{{ customer.address || '-' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="标签" :span="2">
          <template v-if="editing">
            <el-select v-model="editForm.tags" multiple filterable allow-create default-first-option style="width:100%" placeholder="输入标签后回车添加">
              <el-option v-for="t in commonTags" :key="t" :label="t" :value="t" />
            </el-select>
          </template>
          <template v-else>
            <el-tag v-for="t in (customer.tags || [])" :key="t" size="small" style="margin-right:4px">{{ t }}</el-tag>
            <span v-if="!customer.tags || customer.tags.length === 0">-</span>
          </template>
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          <el-input v-if="editing" v-model="editForm.remark" type="textarea" :rows="2" size="small" />
          <span v-else>{{ customer.remark || '-' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="累计订单">{{ customer.total_orders }}</el-descriptions-item>
        <el-descriptions-item label="累计金额">¥{{ customer.total_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="当前欠款">
          <span :style="{ color: (customer.debt || 0) > 0 ? '#f56c6c' : '#67c23a' }">¥{{ (customer.debt || 0).toFixed(2) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="最后联系">{{ customer.last_contact_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="下次跟进">
          <el-date-picker v-if="editing" v-model="editForm.next_followup_date" type="date" value-format="YYYY-MM-DD" size="small" style="width:100%" placeholder="选择日期" />
          <span v-else>{{ customer.next_followup_date || '-' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ customer.created_at }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 跟进记录 -->
    <el-card shadow="never">
      <template #header>
        <span>跟进记录</span>
      </template>

      <div v-if="followups.length === 0" style="color:#999;padding:20px 0;text-align:center">暂无跟进记录</div>

      <div v-for="(f, idx) in followups" :key="f.id" class="followup-item" :style="{ borderTop: idx > 0 ? '1px solid #eee' : 'none' }">
        <div class="followup-header">
          <el-tag size="small" type="primary">{{ f.type }}</el-tag>
          <span class="followup-time">{{ f.created_at }}</span>
          <span v-if="f.result" class="followup-result">结果: {{ f.result }}</span>
          <span v-if="f.next_date" class="followup-next">下次: {{ f.next_date }}</span>
        </div>
        <div class="followup-content">{{ f.content }}</div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { customerApi } from '@/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const customer = ref(null)
const editing = ref(false)
const saving = ref(false)
const followups = ref([])

const editForm = ref({})

const typeLabels = { retail: '零售', project: '工程', designer: '设计师' }
const sourceLabels = {
  self: '自然进店', referral: '老客介绍', online: '线上引流',
  community: '小区推广', other: '其他',
}
const commonTags = ['高意向', '已测量', '已报价', '已成交', '老客户', '需跟进', '犹豫中', '价格敏感']

function levelType(level) {
  if (level === 'A') return 'danger'
  if (level === 'B') return 'warning'
  return 'info'
}

async function load() {
  const res = await customerApi.get(route.params.id)
  customer.value = res.data
}

async function loadFollowups() {
  try {
    const res = await customerApi.followups(route.params.id)
    followups.value = res.data || []
  } catch {}
}

function startEdit() {
  const c = customer.value
  editForm.value = {
    name: c.name,
    phone: c.phone,
    type: c.type || 'retail',
    source: c.source || '',
    level: c.level || 'C',
    community: c.community || '',
    address: c.address || '',
    tags: c.tags || [],
    remark: c.remark || '',
    next_followup_date: c.next_followup_date || null,
  }
  editing.value = true
}

function cancelEdit() {
  editing.value = false
}

async function handleSave() {
  if (!editForm.value.name || !editForm.value.phone) {
    ElMessage.warning('姓名和电话不能为空')
    return
  }
  saving.value = true
  try {
    const payload = { ...editForm.value }
    // clean up: send only changed fields
    const result = await customerApi.update(route.params.id, payload)
    ElMessage.success('保存成功')
    editing.value = false
    // reload customer data
    await load()
  } catch {} finally {
    saving.value = false
  }
}

onMounted(() => {
  load()
  loadFollowups()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h3 { font-size: 18px; }
.followup-item { padding: 14px 0; }
.followup-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; flex-wrap: wrap; }
.followup-time { color: #999; font-size: 13px; }
.followup-result { color: #409eff; font-size: 13px; }
.followup-next { color: #67c23a; font-size: 13px; }
.followup-content { color: #333; font-size: 14px; line-height: 1.6; white-space: pre-wrap; }
</style>
