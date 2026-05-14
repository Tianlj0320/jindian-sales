<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <h3>仓库管理</h3>
          <div>
            <el-button :type="tab === 'inventory' ? 'primary' : 'default'" @click="tab = 'inventory'; loadWarehouses()">库存列表</el-button>
            <el-button :type="tab === 'flows' ? 'primary' : 'default'" @click="tab = 'flows'; loadFlows()">出入库记录</el-button>
            <el-button :type="tab === 'storage' ? 'primary' : 'default'" @click="tab = 'storage'; loadStorage()">位置管理</el-button>
            <el-button @click="showPrintProcessing = true">打印加工单</el-button>
          </div>
        </div>
      </template>

      <!-- 库存列表：分仓库→订单→采购单展示 -->
      <div v-show="tab === 'inventory'">
        <!-- 仓库选择 + 类型筛选 -->
        <div style="margin-bottom:12px;display:flex;align-items:center;gap:8px">
          <el-select v-model="filterWarehouseType" clearable placeholder="仓库类型" size="small" style="width:120px" @change="loadWarehouses">
            <el-option label="主仓库" value="main" />
            <el-option label="辅料仓" value="auxiliary" />
            <el-option label="成品仓" value="finished" />
          </el-select>
          <el-radio-group v-model="selectedWarehouseId" @change="onWarehouseChange">
            <el-radio-button v-for="w in warehouses" :key="w.id" :value="w.id">
              {{ w.name }}
            </el-radio-button>
          </el-radio-group>
          <span v-if="warehouses.length === 0 && !loadingInv" style="color:#999;font-size:13px">暂无仓库</span>
        </div>

        <!-- 搜索 -->
        <el-form :inline="true" style="margin-bottom:8px">
          <el-form-item label="搜索">
            <el-input v-model="invKeyword" placeholder="订单号/采购单号/产品" clearable style="width:180px" @clear="loadGrouped" @keyup.enter="loadGrouped" />
          </el-form-item>
          <el-form-item label="订单号">
            <el-input v-model="invOrderNo" placeholder="订单号" clearable style="width:140px" @clear="loadGrouped" @keyup.enter="loadGrouped" />
          </el-form-item>
          <el-form-item label="采购单号">
            <el-input v-model="invPoNo" placeholder="采购单号" clearable style="width:140px" @clear="loadGrouped" @keyup.enter="loadGrouped" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadGrouped">查询</el-button>
            <el-button type="warning" @click="showAdjustDialog = true">库存调整</el-button>
          </el-form-item>
        </el-form>

        <div v-if="!selectedWarehouseId" style="text-align:center;padding:40px 0;color:#999">
          请先选择一个仓库
        </div>

        <template v-else-if="warehouseGroups.length === 0 && !loadingInv">
          <div style="text-align:center;padding:40px 0;color:#999">该仓库暂无库存记录</div>
        </template>

        <template v-else>
          <div v-for="wg in warehouseGroups" :key="wg.warehouse_id">
            <!-- 每个仓库下的采购单卡片 -->
            <el-card v-for="po in wg.pos" :key="po.po_id" shadow="hover" style="margin-bottom:12px">
              <template #header>
                <div class="po-header">
                  <div>
                    <strong style="font-size:15px">{{ po.po_no }}</strong>
                    <el-tag size="small" style="margin-left:8px">{{ po.supplier_name }}</el-tag>
                    <el-tag :type="po.status === '全部到货' ? 'success' : 'warning'" size="small" style="margin-left:4px">{{ po.status }}</el-tag>
                  </div>
                  <div class="po-header-right">
                    <span v-for="o in po.orders" :key="o.order_id" style="margin-right:8px;color:#666;font-size:13px">
                      {{ o.order_no }}（{{ o.customer_name }}）
                    </span>
                    <span style="color:#999;font-size:13px">到货总量: {{ po.total_qty }}</span>
                  </div>
                </div>
              </template>
              <el-table :data="po.items" size="small" stripe style="width:100%">
                <el-table-column label="产品ID" width="80" align="center">
                  <template #default="{ row }">{{ row.product_id }}</template>
                </el-table-column>
                <el-table-column label="类型" width="60" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.flow_type === 'IN' ? 'success' : 'danger'" size="small">
                      {{ row.flow_type === 'IN' ? '入库' : '出库' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="数量" width="80" align="center">
                  <template #default="{ row }">{{ row.qty }}</template>
                </el-table-column>
                <el-table-column label="时间" width="160">
                  <template #default="{ row }">{{ row.created_at }}</template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
        </template>
      </div>

      <!-- 出入库记录 -->
      <div v-show="tab === 'flows'">
        <el-form :inline="true" style="margin-bottom:16px">
          <el-form-item label="仓库">
            <el-select v-model="flowQuery.warehouse_id" clearable style="width:140px" @change="loadFlows">
              <el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="flowQuery.flow_type" clearable style="width:100px" @change="loadFlows">
              <el-option label="入库" value="IN" />
              <el-option label="出库" value="OUT" />
              <el-option label="调拨" value="TRANSFER" />
              <el-option label="盘点" value="ADJUST" />
            </el-select>
          </el-form-item>
          <el-form-item label="来源">
            <el-select v-model="flowQuery.ref_type" clearable style="width:120px" @change="loadFlows">
              <el-option label="采购收货" value="purchase" />
              <el-option label="采购回退" value="purchase_rollback" />
              <el-option label="手动调整" value="manual" />
              <el-option label="其他" value="other" />
            </el-select>
          </el-form-item>
          <el-form-item label="搜索">
            <el-input v-model="flowQuery.keyword" placeholder="产品名称" clearable @keyup.enter="loadFlows" style="width:160px" />
          </el-form-item>
          <el-form-item label="日期">
            <el-date-picker v-model="flowQuery.start_date" type="date" placeholder="起" value-format="YYYY-MM-DD" style="width:120px" @change="loadFlows" />
            <span style="margin:0 6px">-</span>
            <el-date-picker v-model="flowQuery.end_date" type="date" placeholder="止" value-format="YYYY-MM-DD" style="width:120px" @change="loadFlows" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadFlows">查询</el-button>
          </el-form-item>
        </el-form>

        <el-table :data="flows" v-loading="loadingFlows" stripe style="width:100%">
          <el-table-column prop="created_at" label="时间" width="155" />
          <el-table-column prop="product_name" label="产品" min-width="130" />
          <el-table-column prop="product_code" label="编码" width="100" />
          <el-table-column prop="warehouse_name" label="仓库" width="90" />
          <el-table-column label="类型" width="70" align="center">
            <template #default="{ row }">
              <el-tag :type="row.flow_type === 'IN' ? 'success' : row.flow_type === 'OUT' ? 'danger' : 'warning'" size="small">
                {{ { IN: '入库', OUT: '出库', TRANSFER: '调拨', ADJUST: '盘点' }[row.flow_type] || row.flow_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="来源" width="100">
            <template #default="{ row }">
              <span style="font-size:13px;color:#666">
                {{ { purchase: '采购收货', purchase_rollback: '采购回退', manual: '手动调整' }[row.ref_type] || row.ref_type }}
              </span>
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
          <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        </el-table>
        <div style="margin-top:16px;text-align:right">
          <el-pagination v-model:current-page="flowPage" :page-size="flowPageSize" :total="flowTotal" layout="total, prev, pager, next" @current-change="loadFlows" />
        </div>
      </div>

      <!-- 位置管理（三级分类） -->
      <div v-show="tab === 'storage'">
        <div style="margin-bottom:16px">
          <el-select v-model="storageWhId" style="width:200px" placeholder="选择仓库" @change="loadStorage">
            <el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" />
          </el-select>
          <el-button type="primary" style="margin-left:8px" @click="showAddLocation(1)" :disabled="!storageWhId">添加区域</el-button>
        </div>
        <el-row :gutter="16">
          <el-col v-for="zone in storageTree" :key="zone.id" :span="8" style="margin-bottom:16px">
            <el-card shadow="hover">
              <template #header>
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <strong>{{ zone.name }} <span style="color:#999;font-weight:normal;font-size:13px">{{ zone.code }}</span></strong>
                  <div>
                    <el-button text size="small" @click="showAddLocation(2, zone.id)">+货架</el-button>
                    <el-button text size="small" type="danger" @click="handleDelLocation(zone.id)">删</el-button>
                  </div>
                </div>
              </template>
              <div v-if="zone.children && zone.children.length">
                <div v-for="shelf in zone.children" :key="shelf.id" style="margin-bottom:8px;padding:6px 8px;background:#f8f9fa;border-radius:4px">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <span><strong>{{ shelf.name }}</strong> <span style="color:#999;font-size:12px">{{ shelf.code }}</span></span>
                    <div>
                      <el-button text size="small" @click="showAddLocation(3, shelf.id)">+库位</el-button>
                      <el-button text size="small" type="danger" @click="handleDelLocation(shelf.id)">删</el-button>
                    </div>
                  </div>
                  <div v-if="shelf.children && shelf.children.length" style="margin-top:4px;padding-left:8px">
                    <el-tag v-for="bin in shelf.children" :key="bin.id" size="small" style="margin:2px">
                      {{ bin.name }}
                      <el-button text size="small" type="danger" @click="handleDelLocation(bin.id)" style="margin-left:2px">&times;</el-button>
                    </el-tag>
                  </div>
                  <div v-else style="color:#ccc;font-size:12px;padding-left:8px;margin-top:2px">暂无库位</div>
                </div>
              </div>
              <div v-else style="color:#ccc;font-size:13px;text-align:center;padding:8px">暂无货架</div>
            </el-card>
          </el-col>
        </el-row>
        <div v-if="!storageWhId" style="text-align:center;padding:40px 0;color:#999">请先选择一个仓库</div>
      </div>
    </el-card>

    <!-- 设置库存位置 -->
    <el-dialog v-model="showLocationDlg" title="设置库存位置" width="400px">
      <el-form :model="locationForm" label-width="80px">
        <el-form-item label="产品">{{ locationProductName }}</el-form-item>
        <el-form-item label="仓库">
          <el-select v-model="locationForm.warehouse_id" style="width:100%">
            <el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="区域">
          <el-input v-model="locationForm.zone" placeholder="如：A区" />
        </el-form-item>
        <el-form-item label="货架">
          <el-input v-model="locationForm.shelf" placeholder="如：A-01" />
        </el-form-item>
        <el-form-item label="库位">
          <el-input v-model="locationForm.bin" placeholder="如：A-01-001" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showLocationDlg = false">取消</el-button>
        <el-button type="primary" :loading="savingLocation" @click="handleSaveLocation">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加位置节点 -->
    <el-dialog v-model="showAddLocationDlg" :title="addLocationTitle" width="380px">
      <el-form :model="addLocationForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="addLocationForm.name" :placeholder="'请输入' + addLocationLevelLabel" /></el-form-item>
        <el-form-item label="编码"><el-input v-model="addLocationForm.code" placeholder="选填" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddLocationDlg = false">取消</el-button>
        <el-button type="primary" :loading="savingLocation" @click="handleAddLocation">保存</el-button>
      </template>
    </el-dialog>

    <!-- 打印加工单 -->
    <!-- ── 库存调整对话框 ── -->
    <el-dialog v-model="showAdjustDialog" title="库存手动调整" width="500px" top="25vh" @close="resetAdjustForm">
      <el-form label-width="100px" :model="adjustForm">
        <el-form-item label="产品" required>
          <el-select v-model="adjustForm.product_id" filterable remote :remote-method="searchAdjustProducts"
            placeholder="搜索产品" style="width:100%" :loading="searchingAdjustProducts">
            <el-option v-for="p in adjustProductOptions" :key="p.id" :label="`[${p.code}] ${p.name}`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="仓库" required>
          <el-select v-model="adjustForm.warehouse_id" placeholder="选择仓库" style="width:100%">
            <el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="调整数量" required>
          <el-input-number v-model="adjustForm.quantity" :step="0.1" :min="-99999" :max="99999"
            style="width:100%" placeholder="正数=入库，负数=出库" />
          <span style="color:#999;font-size:12px;margin-top:4px;display:block">正数表示入库（增加库存），负数表示出库（减少库存）</span>
        </el-form-item>
        <el-form-item label="调整原因">
          <el-input v-model="adjustForm.remark" type="textarea" :rows="2" placeholder="简要说明调整原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdjustDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingAdjust" @click="handleAdjust">确认调整</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showPrintProcessing" title="打印加工单" width="400px" top="30vh">
      <el-form label-width="80px">
        <el-form-item label="订单编号" required>
          <el-input v-model="printOrderNo" placeholder="输入订单号" @keyup.enter="handlePrintProcessing" />
        </el-form-item>
        <p style="color:#999;font-size:13px;margin:0">输入订单号后点击确认，预览并打印加工单</p>
      </el-form>
      <template #footer>
        <el-button @click="showPrintProcessing = false">取消</el-button>
        <el-button type="primary" :loading="loadingPrintOrder" @click="handlePrintProcessing">确认</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showPrintPreview" :title="`打印预览 - ${printDocType}`" width="95%" top="2vh"
      :close-on-click-modal="false" destroy-on-close>
      <div class="pv-wrap">
        <div class="pv-bar">
          <span class="pv-label">{{ printDocType }}</span>
          <span class="pv-info">A4 / 纵向</span>
          <div class="pv-spacer"></div>
          <el-button type="primary" :disabled="!iframeReady" @click="doPrint">打印</el-button>
          <el-button @click="showPrintPreview = false">关闭</el-button>
        </div>
        <div class="pv-body">
          <div class="pv-paper">
            <iframe ref="iframeRef" :srcdoc="printHtml" class="pv-frame"
              @load="iframeReady = true" frameborder="0"></iframe>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { warehouseApi, orderApi, productApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { generateProcessingHtml } from '@/utils/print'

const tab = ref('inventory')
const warehouses = ref([])
const loadingInv = ref(false)
const loadingFlows = ref(false)
const savingLocation = ref(false)
const filterWarehouseType = ref('')

// ── 库存分组视图 ──────────────────────────────────────────
const selectedWarehouseId = ref(null)
const warehouseGroups = ref([])
const invKeyword = ref('')
const invOrderNo = ref('')
const invPoNo = ref('')
const invLowStock = ref(false)

// ── 库存手动调整 ──────────────────────────────────────────
const showAdjustDialog = ref(false)
const savingAdjust = ref(false)
const searchingAdjustProducts = ref(false)
const adjustProductOptions = ref([])
const adjustForm = reactive({
  product_id: null,
  warehouse_id: null,
  quantity: 0,
  remark: '',
})
function resetAdjustForm() {
  adjustForm.product_id = null
  adjustForm.warehouse_id = null
  adjustForm.quantity = 0
  adjustForm.remark = ''
  adjustProductOptions.value = []
}
async function searchAdjustProducts(query) {
  if (!query || query.length < 1) { adjustProductOptions.value = []; return }
  searchingAdjustProducts.value = true
  try {
    const { data } = await productApi.search(query)
    adjustProductOptions.value = (data || []).slice(0, 20)
  } catch (e) { /* ignore */ }
  finally { searchingAdjustProducts.value = false }
}
async function handleAdjust() {
  if (!adjustForm.product_id) { ElMessage.warning('请选择产品'); return }
  if (!adjustForm.warehouse_id) { ElMessage.warning('请选择仓库'); return }
  if (adjustForm.quantity === 0) { ElMessage.warning('调整数量不能为0'); return }
  savingAdjust.value = true
  try {
    await warehouseApi.adjustInventory(adjustForm)
    ElMessage.success('库存调整成功')
    showAdjustDialog.value = false
    loadGrouped()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '调整失败')
  } finally {
    savingAdjust.value = false
  }
}

async function loadWarehouses() {
  try {
    const params = {}
    if (filterWarehouseType.value) params.warehouse_type = filterWarehouseType.value
    const res = await warehouseApi.list(params)
    warehouses.value = res.items || res.data || res || []
    // 如果当前选中的仓库不在新列表中，重置
    if (selectedWarehouseId.value && !warehouses.value.find(w => w.id === selectedWarehouseId.value)) {
      selectedWarehouseId.value = null
    }
    // 默认选中第一个仓库
    if (warehouses.value.length > 0 && !selectedWarehouseId.value) {
      selectedWarehouseId.value = warehouses.value[0].id
      loadGrouped()
    }
  } catch {}
}

async function loadGrouped() {
  if (!selectedWarehouseId.value) return
  loadingInv.value = true
  try {
    const params = { warehouse_id: selectedWarehouseId.value }
    if (invKeyword.value) params.keyword = invKeyword.value
    if (invOrderNo.value) params.order_no = invOrderNo.value
    if (invPoNo.value) params.po_no = invPoNo.value
    const res = await warehouseApi.inventoryGrouped(params)
    const data = res.data || {}
    warehouseGroups.value = data.warehouses || []
  } catch {} finally { loadingInv.value = false }
}

function onWarehouseChange(val) {
  selectedWarehouseId.value = val
  loadGrouped()
}

// ── 出入库记录 ──────────────────────────────────────────
const flows = ref([])
const flowTotal = ref(0)
const flowPage = ref(1)
const flowPageSize = ref(20)
const flowQuery = reactive({
  flow_type: '', warehouse_id: '', ref_type: '', keyword: '',
  start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
  end_date: new Date().toISOString().slice(0, 10),
})

async function loadFlows() {
  loadingFlows.value = true
  try {
    const params = {}
    if (flowQuery.flow_type) params.flow_type = flowQuery.flow_type
    if (flowQuery.warehouse_id) params.warehouse_id = flowQuery.warehouse_id
    if (flowQuery.ref_type) params.ref_type = flowQuery.ref_type
    if (flowQuery.keyword) params.keyword = flowQuery.keyword
    if (flowQuery.start_date) params.start_date = flowQuery.start_date
    if (flowQuery.end_date) params.end_date = flowQuery.end_date
    params.page = flowPage.value
    params.page_size = flowPageSize.value
    const res = await warehouseApi.flows(params)
    flows.value = res.items || []
    flowTotal.value = res.total || 0
  } catch {} finally { loadingFlows.value = false }
}

// ── 三级分类管理 ─────────────────────────────────────────
const storageWhId = ref('')
const storageTree = ref([])
const showLocationDlg = ref(false)
const locationProductName = ref('')
const locationForm = reactive({ warehouse_id: '', zone: '', shelf: '', bin: '' })

const showAddLocationDlg = ref(false)
const addLocationLevel = ref(1)
const addLocationParentId = ref(null)
const addLocationForm = reactive({ name: '', code: '' })

const addLocationLevelLabel = computed(() => ['', '区域', '货架', '库位'][addLocationLevel.value] || '')
const addLocationTitle = computed(() => `添加${addLocationLevelLabel.value}`)

async function loadStorage() {
  if (!storageWhId.value) { storageTree.value = []; return }
  try {
    const res = await warehouseApi.listStorage({ warehouse_id: storageWhId.value })
    storageTree.value = res.data || []
  } catch {}
}

function showAddLocation(level, parentId) {
  addLocationLevel.value = level
  addLocationParentId.value = parentId
  addLocationForm.name = ''
  addLocationForm.code = ''
  showAddLocationDlg.value = true
}

async function handleAddLocation() {
  if (!addLocationForm.name) { ElMessage.warning('请输入名称'); return }
  savingLocation.value = true
  try {
    await warehouseApi.createStorage({
      warehouse_id: parseInt(storageWhId.value),
      level: addLocationLevel.value,
      name: addLocationForm.name,
      code: addLocationForm.code,
      parent_id: addLocationParentId.value,
    })
    ElMessage.success('添加成功')
    showAddLocationDlg.value = false
    loadStorage()
  } catch {} finally { savingLocation.value = false }
}

async function handleDelLocation(id) {
  ElMessageBox.confirm('确定删除该位置？', '提示').then(async () => {
    await warehouseApi.deleteStorage(id)
    ElMessage.success('已删除')
    loadStorage()
  }).catch(() => {})
}

// ── 库存位置设置 ────────────────────────────────────────
function showLocationDialog(row) {
  locationProductName.value = row.product_name
  locationForm.warehouse_id = row.warehouse_id || ''
  locationForm.zone = row.zone || ''
  locationForm.shelf = row.shelf || ''
  locationForm.bin = row.bin || ''
  showLocationDlg.value = true
}

async function handleSaveLocation() {
  savingLocation.value = true
  try {
    const res = await warehouseApi.list({ warehouse_id: locationForm.warehouse_id })
    // 简单处理：直接用 API 设置位置
    if (!locationForm.warehouse_id) { ElMessage.warning('请选择仓库'); return }
    await warehouseApi.setLocation(locationProductName.value, locationForm.warehouse_id, {
      zone: locationForm.zone,
      shelf: locationForm.shelf,
      bin: locationForm.bin,
    })
    ElMessage.success('位置已保存')
    showLocationDlg.value = false
  } catch {} finally { savingLocation.value = false }
}

// ── 打印加工单 ──────────────────────────────────────────
const showPrintProcessing = ref(false)
const showPrintPreview = ref(false)
const printOrderNo = ref('')
const loadingPrintOrder = ref(false)
const printHtml = ref('')
const printDocType = ref('')
const iframeReady = ref(false)
const iframeRef = ref(null)

async function handlePrintProcessing() {
  if (!printOrderNo.value.trim()) { ElMessage.warning('请输入订单号'); return }
  loadingPrintOrder.value = true
  try {
    const res = await orderApi.list({ keyword: printOrderNo.value.trim(), page_size: 1 })
    const orders = res.items || []
    if (!orders.length) { ElMessage.warning('未找到该订单'); return }
    const orderRes = await orderApi.get(orders[0].id)
    const order = orderRes.data
    if (!order) { ElMessage.warning('订单数据不存在'); return }
    // 剔除成品及无需发给加工单位的物料
    const filtered = { ...order, items: (order.items || []).filter(i => i.procurement_type !== '成品') }
    printHtml.value = generateProcessingHtml(filtered)
    printDocType.value = '加工单'
    iframeReady.value = false
    showPrintProcessing.value = false
    showPrintPreview.value = true
    printOrderNo.value = ''
  } catch { ElMessage.warning('无法加载订单数据')
  } finally { loadingPrintOrder.value = false }
}

function doPrint() {
  const el = iframeRef.value
  if (el && el.contentWindow) { el.contentWindow.focus(); el.contentWindow.print() }
}

onMounted(() => {
  loadWarehouses()
  loadFlows()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h3 { font-size: 18px; }
.po-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.po-header-right { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }
.pv-wrap { display: flex; flex-direction: column; }
.pv-bar { display: flex; align-items: center; padding: 0 0 10px 0; gap: 8px; border-bottom: 1px solid #e8e8e8; margin-bottom: 10px; }
.pv-label { font-weight: bold; font-size: 15px; }
.pv-info { color: #999; font-size: 12px; }
.pv-spacer { flex: 1; }
.pv-body { flex: 1; overflow: auto; background: #e8e8e8; display: flex; justify-content: center; padding: 20px; border-radius: 4px; min-height: 65vh; }
.pv-paper { width: 100%; max-width: 210mm; min-height: 297mm; background: #fff; box-shadow: 0 2px 12px rgba(0,0,0,0.12); }
.pv-frame { width: 100%; max-width: 210mm; height: 297mm; border: none; display: block; }
</style>
