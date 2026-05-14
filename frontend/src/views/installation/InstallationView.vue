<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <h3>安装管理</h3>
          <div>
            <el-tag v-if="stats" type="warning" style="margin-right:4px">待安装 {{ stats.pending }}</el-tag>
            <el-tag v-if="stats" type="primary" style="margin-right:4px">安装中 {{ stats.installing }}</el-tag>
            <el-tag v-if="stats" type="success" style="margin-right:4px">已完成 {{ stats.completed }}</el-tag>
            <el-button @click="showCreateOrder = true">新建安装单</el-button>
            <el-button @click="showCreateTeam = true">新建安装队</el-button>
            <el-button @click="showCreateInstaller = true">添加工人</el-button>
            <el-button :type="tab === 'orders' ? 'primary' : 'default'" @click="tab = 'orders'">安装单</el-button>
            <el-button :type="tab === 'teams' ? 'primary' : 'default'" @click="tab = 'teams'">安装队</el-button>
          </div>
        </div>
      </template>

      <!-- 安装单列表（分视图） -->
      <div v-show="tab === 'orders'">
        <el-tabs v-model="orderSubTab" @tab-change="loadOrders">
          <el-tab-pane label="待安装" name="pending">
            <el-table :data="pendingOrders" v-loading="loadingOrders" stripe style="width:100%">
              <el-table-column prop="ins_no" label="安装单号" width="160" />
              <el-table-column prop="order_no" label="订单号" width="120" />
              <el-table-column prop="customer_name" label="客户" width="100" />
              <el-table-column prop="customer_phone" label="电话" width="120" />
              <el-table-column prop="address" label="地址" min-width="160" show-overflow-tooltip />
              <el-table-column prop="scheduled_date" label="安装日期" width="100" />
              <el-table-column prop="install_time_slot" label="时段" width="60" />
              <el-table-column prop="installer_name" label="安装人员" width="100" />
              <el-table-column label="状态" width="80" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'pending' ? 'info' : 'primary'" size="small">{{ row.status === 'pending' ? '待派工' : '已派工' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <el-button text size="small" type="primary" @click="handlePrintInstall(row)">打印</el-button>
                  <el-button v-if="row.status === 'pending'" text size="small" type="primary" @click="showAssign(row)">派工</el-button>
                  <el-button v-if="row.status === 'scheduled'" text size="small" @click="handleStatus(row.id, 'installing')">开始安装</el-button>
                  <el-button text size="small" @click="showOrderDetail(row)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="安装中" name="installing">
            <el-table :data="installingOrders" v-loading="loadingOrders" stripe style="width:100%">
              <el-table-column prop="ins_no" label="安装单号" width="160" />
              <el-table-column prop="order_no" label="订单号" width="120" />
              <el-table-column prop="customer_name" label="客户" width="100" />
              <el-table-column prop="customer_phone" label="电话" width="120" />
              <el-table-column prop="address" label="地址" min-width="160" show-overflow-tooltip />
              <el-table-column prop="installer_name" label="安装人员" width="100" />
              <el-table-column prop="scheduled_date" label="安装日期" width="100" />
              <el-table-column prop="total_cost" label="费用" width="90" align="right">
                <template #default="{ row }">¥{{ row.total_cost?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="160" fixed="right">
                <template #default="{ row }">
                  <el-button text size="small" @click="handleStatus(row.id, 'completed')">完成</el-button>
                  <el-button text size="small" @click="showOrderDetail(row)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="已完成" name="completed">
            <el-form :inline="true" style="margin-bottom:16px">
              <el-input v-model="historyQuery.keyword" placeholder="搜索安装单号/客户" clearable style="width:220px" @clear="loadOrders" @keyup.enter="loadOrders" />
              <el-date-picker v-model="historyQuery.start_date" type="date" placeholder="完成日期起" value-format="YYYY-MM-DD" style="width:140px" @change="loadOrders" />
              <el-date-picker v-model="historyQuery.end_date" type="date" placeholder="完成日期止" value-format="YYYY-MM-DD" style="width:140px" @change="loadOrders" />
              <el-button type="primary" @click="loadOrders">查询</el-button>
            </el-form>
            <el-table :data="completedOrders" v-loading="loadingOrders" stripe style="width:100%">
              <el-table-column prop="ins_no" label="安装单号" width="160" />
              <el-table-column prop="order_no" label="订单号" width="120" />
              <el-table-column prop="customer_name" label="客户" width="100" />
              <el-table-column prop="customer_phone" label="电话" width="120" />
              <el-table-column prop="address" label="地址" min-width="160" show-overflow-tooltip />
              <el-table-column prop="installer_name" label="安装人员" width="100" />
              <el-table-column prop="scheduled_date" label="安装日期" width="100" />
              <el-table-column prop="total_cost" label="费用" width="90" align="right">
                <template #default="{ row }">¥{{ row.total_cost?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column label="评分" width="60" align="center">
                <template #default="{ row }">{{ row.quality_score ?? '-' }}</template>
              </el-table-column>
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="{ row }">
                  <el-button text size="small" @click="showOrderDetail(row)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div style="margin-top:16px;text-align:right">
              <el-pagination v-model:current-page="ordersPage" :page-size="ordersPageSize" :total="ordersTotal" layout="total, prev, pager, next" @current-change="loadOrders" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 安装队列表 -->
      <div v-show="tab === 'teams'">
        <el-table :data="teams" v-loading="loadingTeams" stripe style="width:100%">
          <el-table-column prop="name" label="安装队名称" min-width="160" />
          <el-table-column prop="leader_name" label="队长" width="120" />
          <el-table-column prop="leader_phone" label="队长电话" width="140" />
          <el-table-column prop="member_count" label="人数" width="70" align="center" />
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }"><el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '停用' }}</el-tag></template>
          </el-table-column>
        </el-table>
        <h4 style="margin:24px 0 12px">工人列表</h4>
        <el-table :data="installers" v-loading="loadingInstallers" stripe style="width:100%">
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="phone" label="电话" width="140" />
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }"><el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '在职' : '离职' }}</el-tag></template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 新建安装队 / 添加工人 / 新建安装单 / 派工 / 打印预览 对话框 -->
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
    <el-dialog v-model="showCreateOrder" title="新建安装单" width="500px">
      <el-form :model="orderForm" label-width="90px">
        <el-form-item label="订单ID"><el-input-number v-model="orderForm.order_id" :min="1" style="width:100%" /></el-form-item>
        <el-form-item label="安装队"><el-select v-model="orderForm.team_id" clearable style="width:100%"><el-option v-for="t in teams" :key="t.id" :label="t.name" :value="t.id" /></el-select></el-form-item>
        <el-form-item label="安装日期"><el-date-picker v-model="orderForm.scheduled_date" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="时段"><el-select v-model="orderForm.install_time_slot" style="width:100%" clearable><el-option label="上午" value="上午" /><el-option label="下午" value="下午" /><el-option label="全天" value="全天" /></el-select></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="人工费"><el-input-number v-model="orderForm.labor_cost" :precision="2" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="材料费"><el-input-number v-model="orderForm.material_cost" :precision="2" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="orderForm.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateOrder = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreateOrder">创建</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="showAssignDialog" title="派工" width="450px">
      <template v-if="assignOrder">
        <p style="margin-bottom:12px;color:#666">{{ assignOrder.ins_no }} — {{ assignOrder.customer_name }}</p>
        <el-form :model="assignForm" label-width="80px">
          <el-form-item label="安装队"><el-select v-model="assignForm.team_id" style="width:100%"><el-option v-for="t in teams" :key="t.id" :label="t.name" :value="t.id" /></el-select></el-form-item>
          <el-form-item label="安装日期"><el-date-picker v-model="assignForm.scheduled_date" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
          <el-form-item label="时段"><el-select v-model="assignForm.install_time_slot" style="width:100%"><el-option label="上午" value="上午" /><el-option label="下午" value="下午" /><el-option label="全天" value="全天" /></el-select></el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="showAssignDialog = false">取消</el-button>
        <el-button type="primary" :loading="assigning" @click="handleAssign">确认派工</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="showPrintDialog" :title="`打印预览 - ${printDocType}`" width="95%" top="2vh" :close-on-click-modal="false" destroy-on-close>
      <div class="pv-wrap">
        <div class="pv-bar">
          <span class="pv-label">{{ printDocType }}</span>
          <span class="pv-info">A4 / 纵向</span>
          <div class="pv-spacer"></div>
          <el-button type="primary" :disabled="!iframeReady" @click="doPrint">打印</el-button>
          <el-button @click="showPrintDialog = false">关闭</el-button>
        </div>
        <div class="pv-body">
          <div class="pv-paper">
            <iframe ref="iframeRef" :srcdoc="printHtml" class="pv-frame" @load="iframeReady = true" frameborder="0"></iframe>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { installationApi, orderApi } from '@/api'
import { ElMessage } from 'element-plus'
import { generateInstallationHtml } from '@/utils/print'

const tab = ref('orders')
const orderSubTab = ref('pending')
const ordersTotal = ref(0)
const ordersPage = ref(1)
const ordersPageSize = ref(20)
const stats = ref(null)

const pendingOrders = ref([])
const installingOrders = ref([])
const completedOrders = ref([])
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

const teamForm = reactive({ name: '', leader_name: '', leader_phone: '', remark: '' })
const installerForm = reactive({ name: '', phone: '' })
const orderForm = reactive({ order_id: null, team_id: null, scheduled_date: '', install_time_slot: '', labor_cost: 0, material_cost: 0, remark: '' })
const assignForm = reactive({ team_id: null, scheduled_date: '', install_time_slot: '上午' })
const historyQuery = reactive({ keyword: '', start_date: '', end_date: '' })

const showPrintDialog = ref(false)
const printHtml = ref('')
const printDocType = ref('')
const iframeReady = ref(false)
const iframeRef = ref(null)

async function loadStats() {
  try { const res = await installationApi.stats(); stats.value = res.data } catch {}
}

async function loadOrders() {
  loadingOrders.value = true
  try {
    if (orderSubTab.value === 'pending') {
      const r1 = await installationApi.listOrders({ status: 'pending', page: 1, page_size: 200 })
      const r2 = await installationApi.listOrders({ status: 'scheduled', page: 1, page_size: 200 })
      pendingOrders.value = [...(r1.items || []), ...(r2.items || [])]
    } else if (orderSubTab.value === 'installing') {
      const res = await installationApi.listOrders({ status: 'installing', page: 1, page_size: 200 })
      installingOrders.value = res.items || []
    } else {
      const hp = { status: 'completed', page: ordersPage.value, page_size: ordersPageSize.value }
      if (historyQuery.keyword) hp.keyword = historyQuery.keyword
      if (historyQuery.start_date) hp.start_date = historyQuery.start_date
      if (historyQuery.end_date) hp.end_date = historyQuery.end_date
      const res = await installationApi.listOrders(hp)
      completedOrders.value = res.items || []
      ordersTotal.value = res.total || 0
    }
  } catch {} finally { loadingOrders.value = false }
}

async function loadTeams() {
  try { teams.value = (await installationApi.listTeams()).data || [] } catch {}
}
async function loadInstallers() {
  try { installers.value = (await installationApi.listInstallers()).data || [] } catch {}
}

async function handleCreateTeam() {
  if (!teamForm.name) { ElMessage.warning('请输入名称'); return }
  saving.value = true
  try {
    await installationApi.createTeam(teamForm)
    ElMessage.success('创建成功'); showCreateTeam.value = false
    teamForm.name = ''; teamForm.leader_name = ''; teamForm.leader_phone = ''; teamForm.remark = ''
    loadTeams()
  } catch {} finally { saving.value = false }
}
async function handleCreateInstaller() {
  if (!installerForm.name || !installerForm.phone) { ElMessage.warning('请填写完整信息'); return }
  saving.value = true
  try {
    await installationApi.createInstaller(installerForm)
    ElMessage.success('添加成功'); showCreateInstaller.value = false
    installerForm.name = ''; installerForm.phone = ''
    loadInstallers()
  } catch {} finally { saving.value = false }
}
async function handleCreateOrder() {
  if (!orderForm.order_id) { ElMessage.warning('请输入订单ID'); return }
  saving.value = true
  try {
    await installationApi.createOrder(orderForm)
    ElMessage.success('安装单已创建'); showCreateOrder.value = false
    orderForm.order_id = null; orderForm.team_id = null; orderForm.scheduled_date = ''
    orderForm.install_time_slot = ''; orderForm.labor_cost = 0; orderForm.material_cost = 0; orderForm.remark = ''
    loadOrders(); loadStats()
  } catch {} finally { saving.value = false }
}
function showAssign(row) {
  assignOrder.value = row; assignForm.team_id = null; assignForm.scheduled_date = ''; assignForm.install_time_slot = '上午'; showAssignDialog.value = true
}
async function handleAssign() {
  if (!assignForm.team_id) { ElMessage.warning('请选择安装队'); return }
  assigning.value = true
  try {
    await installationApi.updateStatus(assignOrder.value.id, 'scheduled', {
      team_id: assignForm.team_id,
      scheduled_date: assignForm.scheduled_date,
      install_time_slot: assignForm.install_time_slot,
    })
    ElMessage.success('派工成功'); showAssignDialog.value = false; loadOrders(); loadStats()
  } catch {} finally { assigning.value = false }
}
async function handleStatus(id, status) {
  try { await installationApi.updateStatus(id, status); ElMessage.success('状态已更新'); loadOrders(); loadStats() } catch {}
}
function showOrderDetail(row) {
  installationApi.getOrder(row.id).then(res => {
    const d = res.data; ElMessage.info(`安装单 ${d.ins_no}: 客户 ${d.customer_name}, 地址 ${d.address}, 费用 ¥${d.total_cost?.toFixed(2)}`)
  }).catch(() => {})
}
async function handlePrintInstall(row) {
  if (!row.order_id) { ElMessage.warning('该安装单未关联订单，无法打印'); return }
  try {
    const res = await orderApi.get(row.order_id); const order = res.data
    if (!order) { ElMessage.warning('关联订单不存在'); return }
    printHtml.value = generateInstallationHtml(order); printDocType.value = '安装派工单'
    iframeReady.value = false; showPrintDialog.value = true
  } catch { ElMessage.warning('无法加载关联订单数据') }
}
function doPrint() {
  const el = iframeRef.value
  if (el && el.contentWindow) { el.contentWindow.focus(); el.contentWindow.print() }
}

onMounted(() => { loadOrders(); loadTeams(); loadInstallers(); loadStats() })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.page-header h3 { font-size: 18px; }
.pv-wrap { display: flex; flex-direction: column; }
.pv-bar { display: flex; align-items: center; padding: 0 0 10px 0; gap: 8px; border-bottom: 1px solid #e8e8e8; margin-bottom: 10px; }
.pv-body { flex: 1; overflow: auto; background: #e8e8e8; display: flex; justify-content: center; padding: 20px; border-radius: 4px; min-height: 65vh; }
.pv-paper { width: 210mm; min-height: 297mm; background: #fff; box-shadow: 0 2px 12px rgba(0,0,0,0.12); }
.pv-frame { width: 210mm; height: 297mm; border: none; display: block; }
</style>
