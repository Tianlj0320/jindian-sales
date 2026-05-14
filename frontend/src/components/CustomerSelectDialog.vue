<template>
  <el-dialog v-model="visible" title="选择客户" width="700px" top="10vh" :close-on-click-modal="false" @open="onOpen">
    <el-form :inline="true" size="small" style="margin-bottom:8px">
      <el-form-item label="搜索">
        <el-input v-model="query.keyword" placeholder="客户名称/电话" style="width:200px" clearable @keyup.enter="search" @clear="search" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="search">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table
      ref="tableRef"
      :data="list"
      v-loading="loading"
      stripe
      size="small"
      style="width:100%;cursor:pointer"
      class="compact-table"
      highlight-current-row
      @row-click="handleCurrentChange"
      @row-dblclick="handleSelect"
    >
      <el-table-column type="index" label="序号" width="55" />
      <el-table-column prop="name" label="客户名称" width="140" />
      <el-table-column prop="phone" label="电话" width="130" />
      <el-table-column prop="address" label="地址" min-width="150" show-overflow-tooltip />
      <el-table-column prop="salesperson_name" label="业务员" width="80" />
      <el-table-column label="欠款" width="90" align="right">
        <template #default="{ row }">¥{{ (row.debt || 0).toFixed(2) }}</template>
      </el-table-column>
    </el-table>

    <div style="margin-top:8px;text-align:right;font-size:12px;color:#999">
      双击客户行选定 / 共 {{ total }} 条
    </div>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :disabled="!selected" @click="confirmSelect">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { customerApi } from '@/api'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue', 'select'])

const visible = ref(false)
const list = ref([])
const total = ref(0)
const loading = ref(false)
const selected = ref(null)
const tableRef = ref(null)

const query = reactive({ keyword: '', page: 1, page_size: 15 })

watch(() => props.modelValue, (v) => { visible.value = v })
watch(visible, (v) => { emit('update:modelValue', v) })

async function search() {
  loading.value = true
  query.page = 1
  try {
    const res = await customerApi.list({
      keyword: query.keyword,
      page: query.page,
      page_size: query.page_size,
    })
    list.value = res.items || []
    total.value = res.total || 0
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

function onOpen() {
  query.keyword = ''
  selected.value = null
  search()
}

function handleSelect(row) {
  selected.value = row
  confirmSelect()
}

function confirmSelect() {
  if (!selected.value) return
  emit('select', selected.value)
  visible.value = false
}

// 表格行点击选中
function handleCurrentChange(row) {
  selected.value = row
}
</script>

<style scoped>
.compact-table { font-size: 13px; }
.compact-table :deep(.el-table__header th) { padding: 4px 0; font-size: 13px; }
.compact-table :deep(.el-table__cell) { padding: 4px 6px; }
.compact-table :deep(.el-table__body td) { padding: 4px 6px; }
</style>
