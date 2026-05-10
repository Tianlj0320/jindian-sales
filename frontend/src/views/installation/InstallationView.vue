<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <h3>安装管理</h3>
          <div>
            <el-button @click="showCreateOrder = true">新建安装单</el-button>
            <el-button @click="showCreateTeam = true">新建安装队</el-button>
            <el-button @click="showCreateInstaller = true">添加工人</el-button>
            <el-button :type="tab === 'orders' ? 'primary' : 'default'" @click="tab = 'orders'">安装单</el-button>
            <el-button :type="tab === 'teams' ? 'primary' : 'default'" @click="tab = 'teams'">安装队</el-button>
          </div>
        </div>
      </template>

      <!-- 安装单列表 -->
      <div v-show="tab === 'orders'">
        <el-form :inline="true" style="margin-bottom:16px">
          <el-form-item label="搜索">
            <el-input v-model="query.keyword" placeholder="安装单号/客户" clearable @clear="loadOrders" @keyup.enter="loadOrders" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="query.status" clearable style="width:120px" @change="loadOrders">
              <el-option label="待派工" value="pending" />
              <el-option label="已派工" value="scheduled" />
              <el-option label="安装中" value="installing" />
              <el-option label="已完成" value="completed" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadOrders">查询</el-button>
          </el-form-item>
        </el-form>

        <el-table :data="orders" v-loading="loadingOrders" stripe style="width:100%">
          <el-table-column prop="ins_no" label="安装单号" width="160" />
          <el-table-column prop="customer_name" label="客户" width="120" />
          <el-table-column prop="customer_phone" label="电话" width="130" />
          <el-table-column prop="address" label="地址" min-width="180" />
          <el-table-column prop="installer_name" label="安装人员" width="120" />
          <el-table-column prop="scheduled_date" label="安装日期" width="110" />
          <el-table-column prop="total_cost" label="费用" width="100" align="right">
            <template #default="{ row }">¥{{ row.total_cost?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="评分" width="70" align="center">
            <template #default="{ row }">{{ row.quality_score ?? '-' }}</template>
          </el-table-column>
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="orderStatusTag(row.status)" size="small">{{ orderStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.status === 'pending'" text size="small" type="primary" @click="showAssign(row)">派工</el-button>
              <el-button v-if="row.status === 'scheduled'" text size="small" @click="handleStatus(row.id, 'completed')">完成</el-button>
              <el-button text size="small" @click="showOrderDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 安装队列表 -->
      <div v-show="tab === 'teams'">
        <el-table :data="teams" v-loading="loadingTeams" stripe style="width:100%">
          <el-table-column prop="name" label="安装队名称" min-width="160" />
          <el-table-column prop="leader_name" label="队长" width="120" />
          <el-table-column prop="leader_phone" label="队长电话" width="140" />
          <el-table-column prop="member_count" label="人数" width="70" align="center" />
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '停用' }}</el-tag>
            </template>
          </el-table-column>
        </el-table>

        <h4 style="margin:24px 0 12px">工人列表</h4>
        <el-table :data="installers" v-loading="loadingInstallers" stripe style="width:100%">
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="phone" label="电话" width="140" />
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '在职' : '离职' }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 新建安装队 -->
    <el-dialog v-model="showCreateTeam" title="新建安装队" width="450px">
      <el-form :model="teamForm" label-width="90px">
        <el-form-item label="名称"><el-input v-model="teamForm.name" /></el-form-item>
        <el-form-item label="队长姓名"><el-input v-model="teamForm.leader_name" /></el-form-item>
        <el-form-item label="队长电话"><el-input v-model="teamForm.leader_phone" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="teamForm.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateTeam = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreateTeam">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加工人 -->
    <el-dialog v-model="showCreateInstaller" title="添加工人" width="400px">
      <el-form :model="installerForm" label-width="80px">
        <el-form-item label="姓名"><el-input v-model="installerForm.name" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="installerForm.phone" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateInstaller = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreateInstaller">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新建安装单 -->
    <el-dialog v-model="showCreateOrder" title="新建安装单" width="500px">
      <el-form :model="orderForm" label-width="90px">
        <el-form-item label="订单ID">
          <el-input-number v-model="orderForm.order_id" :min="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="安装队">
          <el-select v-model="orderForm.team_id" clearable style="width:100%">
            <el-option v-for="t in teams" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="安装日期">
          <el-date-picker v-model="orderForm.scheduled_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="时段">
          <el-select v-model="orderForm.install_time_slot" style="width:100%" clearable>
            <el-option label="上午" value="上午" />
            <el-option label="下午" value="下午" />
            <el-option label="全天" value="全天" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="人工费"><el-input-number v-model="orderForm.labor_cost" :precision="2" style="width:100%" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="材料费"><el-input-number v-model="orderForm.material_cost" :precision="2" style="width:100%" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="orderForm.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateOrder = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreateOrder">创建</el-button>
      </template>
    </el-dialog>

    <!-- 派工对话框 -->
    <el-dialog v-model="showAssignDialog" title="派工" width="450px">
      <template v-if="assignOrder">
        <p style="margin-bottom:12px;color:#666">{{ assignOrder.ins_no }} — {{ assignOrder.customer_name }}</p>
        <el-form :model="assignForm" label-width="80px">
          <el-form-item label="安装队">
            <el-select v-model="assignForm.team_id" style="width:100%">
              <el-option v-for="t in teams" :key="t.id" :label="t.name" :value="t.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="安装日期">
            <el-date-picker v-model="assignForm.scheduled_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item>
          <el-form-item label="时段">
            <el-select v-model="assignForm.install_time_slot" style="width:100%">
              <el-option label="上午" value="上午" />
              <el-option label="下午" value="下午" />
              <el-option label="全天" value="全天" />
            </el-select>
          </el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="showAssignDialog = false">取消</el-button>
        <el-button type="primary" :loading="assigning" @click="handleAssign">确认派工</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { installationApi } from '@/api'
import { ElMessage } from 'element-plus'

const tab = ref('orders')
const orders = ref([])
const teams = ref([])
const installers = ref([])
const loadingOrders = ref(false)
const loadingTeams = ref(false)
const loadingInstallers = ref(false)
const saving = ref(false)
const assigning = ref(false)
const showCreateOrder = ref(false)
const showCreateTeam = ref(false)
const showCreateInstaller = ref(false)
const showAssignDialog = ref(false)
const assignOrder = ref(null)

const query = reactive({ keyword: '', status: '', page: 1, page_size: 50 })
const teamForm = reactive({ name: '', leader_name: '', leader_phone: '', remark: '' })
const installerForm = reactive({ name: '', phone: '' })
const orderForm = reactive({ order_id: null, team_id: null, scheduled_date: '', install_time_slot: '', labor_cost: 0, material_cost: 0, remark: '' })
const assignForm = reactive({ team_id: null, scheduled_date: '', install_time_slot: '上午' })

function orderStatusTag(status) {
  const map = { pending: 'info', scheduled: 'primary', installing: 'warning', completed: 'success' }
  return map[status] || 'info'
}
function orderStatusLabel(status) {
  const map = { pending: '待派工', scheduled: '已派工', installing: '安装中', completed: '已完成' }
  return map[status] || status
}

async function loadOrders() {
  loadingOrders.value = true
  try {
    const res = await installationApi.listOrders(query)
    orders.value = res.items || []
  } catch {} finally { loadingOrders.value = false }
}

async function loadTeams() {
  try {
    const res = await installationApi.listTeams()
    teams.value = res.items || res.data || res || []
  } catch {}
}

async function loadInstallers() {
  try {
    const res = await installationApi.listInstallers()
    installers.value = res.items || res.data || res || []
  } catch {}
}

async function handleCreateTeam() {
  if (!teamForm.name) { ElMessage.warning('请输入名称'); return }
  saving.value = true
  try {
    await installationApi.createTeam(teamForm)
    ElMessage.success('创建成功')
    showCreateTeam.value = false
    teamForm.name = ''; teamForm.leader_name = ''; teamForm.leader_phone = ''; teamForm.remark = ''
    loadTeams()
  } catch {} finally { saving.value = false }
}

async function handleCreateInstaller() {
  if (!installerForm.name || !installerForm.phone) { ElMessage.warning('请填写完整信息'); return }
  saving.value = true
  try {
    await installationApi.createInstaller(installerForm)
    ElMessage.success('添加成功')
    showCreateInstaller.value = false
    installerForm.name = ''; installerForm.phone = ''
    loadInstallers()
  } catch {} finally { saving.value = false }
}

async function handleCreateOrder() {
  if (!orderForm.order_id) { ElMessage.warning('请输入订单ID'); return }
  saving.value = true
  try {
    await installationApi.createOrder(orderForm)
    ElMessage.success('安装单已创建')
    showCreateOrder.value = false
    orderForm.order_id = null; orderForm.team_id = null; orderForm.scheduled_date = ''; orderForm.install_time_slot = ''; orderForm.labor_cost = 0; orderForm.material_cost = 0; orderForm.remark = ''
    loadOrders()
  } catch {} finally { saving.value = false }
}

function showAssign(row) {
  assignOrder.value = row
  assignForm.team_id = null
  assignForm.scheduled_date = ''
  assignForm.install_time_slot = '上午'
  showAssignDialog.value = true
}

async function handleAssign() {
  if (!assignForm.team_id) { ElMessage.warning('请选择安装队'); return }
  assigning.value = true
  try {
    await installationApi.updateStatus(assignOrder.value.id, 'scheduled')
    ElMessage.success('派工成功')
    showAssignDialog.value = false
    loadOrders()
  } catch {} finally { assigning.value = false }
}

async function handleStatus(id, status) {
  try {
    await installationApi.updateStatus(id, status)
    ElMessage.success('状态已更新')
    loadOrders()
  } catch {}
}

function showOrderDetail(row) {
  installationApi.getOrder(row.id).then(res => {
    const d = res.data
    ElMessage.info(`安装单 ${d.ins_no}: 客户 ${d.customer_name}, 地址 ${d.address}, 费用 ¥${d.total_cost?.toFixed(2)}`)
  }).catch(() => {})
}

onMounted(() => {
  loadOrders()
  loadTeams()
  loadInstallers()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.page-header h3 { font-size: 18px; }
</style>
