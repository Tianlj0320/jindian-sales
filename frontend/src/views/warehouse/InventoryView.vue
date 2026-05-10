<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <h3>仓库管理</h3>
          <div>
            <el-button type="primary" @click="showCreate = true">新建仓库</el-button>
            <el-button :type="tab === 'inventory' ? 'primary' : 'default'" @click="tab = 'inventory'">库存列表</el-button>
            <el-button :type="tab === 'flows' ? 'primary' : 'default'" @click="tab = 'flows'">出入库记录</el-button>
          </div>
        </div>
      </template>

      <!-- 库存列表 -->
      <div v-show="tab === 'inventory'">
        <el-form :inline="true" style="margin-bottom:16px">
          <el-form-item label="搜索">
            <el-input v-model="invQuery.keyword" placeholder="产品名称/编码" clearable @clear="loadInventory" @keyup.enter="loadInventory" />
          </el-form-item>
          <el-form-item label="仓库">
            <el-select v-model="invQuery.warehouse_id" clearable style="width:120px" @change="loadInventory">
              <el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-checkbox v-model="invQuery.low_stock" label="仅看低库存" border size="small" @change="loadInventory" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadInventory">查询</el-button>
          </el-form-item>
        </el-form>

        <el-table :data="inventory" v-loading="loadingInv" stripe style="width:100%">
          <el-table-column prop="product_code" label="编码" width="120" />
          <el-table-column prop="product_name" label="产品名称" min-width="160" />
          <el-table-column prop="warehouse_name" label="仓库" width="120" />
          <el-table-column prop="quantity" label="库存数量" width="110" align="center">
            <template #default="{ row }">
              <span :style="{ color: row.quantity <= row.safety_stock ? '#f56c6c' : '#67c23a', fontWeight: 'bold' }">
                {{ row.quantity }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="safety_stock" label="安全库存" width="100" align="center" />
        </el-table>
      </div>

      <!-- 出入库记录 -->
      <div v-show="tab === 'flows'">
        <el-form :inline="true" style="margin-bottom:16px">
          <el-form-item label="类型">
            <el-select v-model="flowQuery.flow_type" clearable style="width:120px" @change="loadFlows">
              <el-option label="入库" value="IN" />
              <el-option label="出库" value="OUT" />
              <el-option label="调拨" value="TRANSFER" />
              <el-option label="盘点" value="ADJUST" />
            </el-select>
          </el-form-item>
          <el-form-item label="产品">
            <el-input v-model="flowQuery.keyword" placeholder="产品名称" clearable @keyup.enter="loadFlows" style="width:200px" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadFlows">查询</el-button>
          </el-form-item>
        </el-form>

        <el-table :data="flows" v-loading="loadingFlows" stripe style="width:100%">
          <el-table-column prop="created_at" label="时间" width="160" />
          <el-table-column prop="product_name" label="产品" min-width="140" />
          <el-table-column label="类型" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.flow_type === 'IN' ? 'success' : row.flow_type === 'OUT' ? 'danger' : 'warning'" size="small">
                {{ { IN: '入库', OUT: '出库', TRANSFER: '调拨', ADJUST: '盘点' }[row.flow_type] || row.flow_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="qty_before" label="调整前" width="80" align="center" />
          <el-table-column label="变动" width="80" align="center">
            <template #default="{ row }">
              <span :style="{ color: row.qty_change > 0 ? '#67c23a' : '#f56c6c' }">
                {{ row.qty_change > 0 ? '+' : '' }}{{ row.qty_change }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="qty_after" label="调整后" width="80" align="center" />
          <el-table-column prop="remark" label="备注" min-width="150" />
        </el-table>
      </div>
    </el-card>

    <!-- 新建仓库 -->
    <el-dialog v-model="showCreate" title="新建仓库" width="450px">
      <el-form :model="whForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="whForm.name" /></el-form-item>
        <el-form-item label="编码"><el-input v-model="whForm.code" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="whForm.address" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="whForm.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { warehouseApi } from '@/api'
import { ElMessage } from 'element-plus'

const tab = ref('inventory')
const warehouses = ref([])
const inventory = ref([])
const flows = ref([])
const loadingInv = ref(false)
const loadingFlows = ref(false)
const saving = ref(false)
const showCreate = ref(false)

const invQuery = reactive({ keyword: '', warehouse_id: '', low_stock: false, page: 1, page_size: 200 })
const flowQuery = reactive({ flow_type: '', keyword: '', page: 1, page_size: 100 })
const whForm = reactive({ name: '', code: '', address: '', remark: '' })

async function loadWarehouses() {
  try {
    const res = await warehouseApi.list()
    warehouses.value = res.items || res.data || res || []
  } catch {}
}

async function loadInventory() {
  loadingInv.value = true
  try {
    const params = {}
    if (invQuery.keyword) params.keyword = invQuery.keyword
    if (invQuery.warehouse_id) params.warehouse_id = invQuery.warehouse_id
    if (invQuery.low_stock) params.low_stock = true
    const res = await warehouseApi.inventory(params)
    inventory.value = res.items || []
  } catch {} finally { loadingInv.value = false }
}

async function loadFlows() {
  loadingFlows.value = true
  try {
    const params = {}
    if (flowQuery.flow_type) params.flow_type = flowQuery.flow_type
    if (flowQuery.keyword) params.keyword = flowQuery.keyword
    const res = await warehouseApi.flows(params)
    flows.value = res.items || []
  } catch {} finally { loadingFlows.value = false }
}

async function handleCreate() {
  if (!whForm.name) { ElMessage.warning('请输入仓库名称'); return }
  saving.value = true
  try {
    await warehouseApi.create(whForm)
    ElMessage.success('创建成功')
    showCreate.value = false
    whForm.name = ''; whForm.code = ''; whForm.address = ''; whForm.remark = ''
    loadWarehouses()
  } catch {} finally { saving.value = false }
}

onMounted(() => {
  loadWarehouses()
  loadInventory()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h3 { font-size: 18px; }
</style>
