<template>
  <div>
    <el-card shadow="never">
      <!-- 标签页导航 -->
      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <el-tab-pane label="待采购订单" name="pending">
          <div class="tab-toolbar">
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
              <el-input v-model="pendingQuery.keyword" placeholder="搜索订单号/客户" clearable style="width:180px" @clear="loadPending" @keyup.enter="loadPending" />
              <el-date-picker v-model="pendingQuery.start_date" type="date" placeholder="下单日期起" value-format="YYYY-MM-DD" style="width:140px" @change="loadPending" />
              <el-date-picker v-model="pendingQuery.end_date" type="date" placeholder="下单日期止" value-format="YYYY-MM-DD" style="width:140px" @change="loadPending" />
            </div>
            <div>
              <el-button :disabled="selectedIds.length === 0" type="primary" @click="handlePreview">生成采购单 ({{ selectedIds.length }})</el-button>
            </div>
          </div>
          <el-table :data="pendingOrders" v-loading="pendingLoading" stripe style="width:100%" @selection-change="(rows) => selectedIds = rows.map(r => r.id)">
            <el-table-column type="selection" width="44" />
            <el-table-column prop="order_no" label="订单号" width="150" />
            <el-table-column prop="customer_name" label="客户" width="120" />
            <el-table-column prop="customer_phone" label="电话" width="130" />
            <el-table-column prop="order_date" label="下单日期" width="110" />
            <el-table-column prop="content" label="内容" min-width="160" show-overflow-tooltip />
            <el-table-column label="商品数" width="70" align="center">
              <template #default="{ row }">{{ row.item_count }}</template>
            </el-table-column>
            <el-table-column label="物料" width="160">
              <template #default="{ row }">
                <el-tag v-for="m in getMaterialTypes(row.items)" :key="m" size="small" style="margin-right:4px">{{ m }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ row }">
                <el-button text size="small" @click="toggleExpand(row)">{{ expandedRows.has(row.id) ? '收起' : '明细' }}</el-button>
              </template>
            </el-table-column>
            <!-- 展开行 -->
            <el-table-column type="expand" width="1">
              <template #default="{ row }">
                <el-table :data="row.items" size="small" stripe style="width:100%">
                  <el-table-column prop="product_name" label="产品" width="160" />
                  <el-table-column prop="product_code" label="编码" width="110" />
                  <el-table-column prop="qty" label="数量" width="70" align="center" />
                  <el-table-column prop="unit" label="单位" width="60" />
                  <el-table-column prop="material_type" label="物料类型" width="80">
                    <template #default="{ row: it }">
                      <el-tag :type="it.material_type === '主料' ? 'primary' : 'warning'" size="small">{{ it.material_type }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="采购类型" width="80">
                    <template #default="{ row: it }">
                      <el-tag :type="it.procurement_type === '物料' ? 'primary' : it.procurement_type === '成品' ? 'success' : 'warning'" size="small">{{ it.procurement_type || '物料' }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="unit_price" label="单价" width="90" align="right">
                    <template #default="{ row: it }">¥{{ it.unit_price?.toFixed(2) }}</template>
                  </el-table-column>
                  <el-table-column prop="amount" label="金额" width="100" align="right">
                    <template #default="{ row: it }">¥{{ it.amount?.toFixed(2) }}</template>
                  </el-table-column>
                </el-table>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="pendingOrders.length === 0 && !pendingLoading" style="text-align:center;padding:40px 0;color:#999">暂无待采购订单（已确认的订单将显示在这里）</div>
        </el-tab-pane>

        <el-tab-pane label="采购单管理" name="list">
          <!-- 层级导航 -->
          <div v-if="supplierHierarchy.length > 0" style="margin-bottom:12px;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <el-tag>{{ currentLevelLabel }}</el-tag>
            <el-button v-if="selectedSupplier" size="small" text @click="clearSupplier">全部供应商</el-button>
          </div>

          <div class="tab-toolbar">
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
              <el-select v-model="listQuery.supplier_id" clearable style="width:180px" placeholder="选择供应商" @change="onSupplierChange">
                <el-option v-for="s in supplierOptions" :key="s.id" :label="(s.code || '') + ' - ' + (s.name || '')" :value="s.id" />
              </el-select>
              <el-input v-model="listQuery.keyword" placeholder="采购单号/供应商" clearable style="width:180px" @clear="loadPurchaseList" @keyup.enter="loadPurchaseList" />
              <el-date-picker v-model="listQuery.start_date" type="date" placeholder="下单日期起" value-format="YYYY-MM-DD" style="width:140px" @change="loadPurchaseList" />
              <el-date-picker v-model="listQuery.end_date" type="date" placeholder="下单日期止" value-format="YYYY-MM-DD" style="width:140px" @change="loadPurchaseList" />
              <el-select v-model="listQuery.status" clearable style="width:110px" placeholder="状态筛选" @change="loadPurchaseList">
                <el-option label="待采购" value="待采购" />
                <el-option label="已下单" value="已下单" />
                <el-option label="部分到货" value="部分到货" />
                <el-option label="全部到货" value="全部到货" />
                <el-option label="已结算" value="已结算" />
              </el-select>
            </div>
            <div style="display:flex;gap:8px">
              <el-button type="primary" @click="goToPending">生成采购单</el-button>
              <el-button type="success" plain @click="openScanner">扫码收货</el-button>
            </div>
          </div>

          <!-- 采购单表格 -->
          <el-table :data="purchaseList" v-loading="listLoading" stripe style="width:100%"
            @row-click="(row) => showDetail(row)">
            <el-table-column prop="po_no" label="采购单号" width="150" />
            <el-table-column label="供应商" width="160">
              <template #default="{ row }">
                <template v-if="row.supplier_code && row.supplier_name">{{ row.supplier_code }} - {{ row.supplier_name }}</template>
                <template v-else-if="row.supplier_code">{{ row.supplier_code }}</template>
                <template v-else-if="row.supplier_name">{{ row.supplier_name }}</template>
                <template v-else>-</template>
              </template>
            </el-table-column>
            <el-table-column prop="order_date" label="下单日期" width="100" />
            <el-table-column prop="expected_date" label="预计到货" width="100" />
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="220" fixed="right">
              <template #default="{ row }">
                <el-button text size="small" @click.stop="showDetail(row)">详情</el-button>
                <el-button text size="small" type="primary" @click.stop="showReceive(row)" :disabled="row.status === '全部到货' || row.status === '已结算'">收货</el-button>
                <el-button text size="small" type="danger" @click.stop="showRollback(row)" :disabled="row.status === '待采购' || row.status === '已取消'">回退</el-button>
                <el-button text size="small" type="warning" @click.stop="handleShare(row)">发送</el-button>
                <el-button text size="small" type="success" @click.stop="showQrCode(row)">收货码</el-button>
                <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
                  <template #reference><el-button text size="small" type="danger" @click.stop>删除</el-button></template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top:16px;text-align:right">
            <el-pagination v-model:current-page="listQuery.page" :page-size="listQuery.page_size" :total="listTotal" layout="total, prev, pager, next" @current-change="loadPurchaseList" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="采购跟踪" name="tracking">
          <div class="tab-toolbar">
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
              <el-input v-model="trackQuery.keyword" placeholder="搜索订单号/客户" clearable style="width:200px" @clear="loadTracking" @keyup.enter="loadTracking" />
              <el-date-picker v-model="trackQuery.start_date" type="date" placeholder="下单日期起" value-format="YYYY-MM-DD" style="width:140px" @change="loadTracking" />
              <el-date-picker v-model="trackQuery.end_date" type="date" placeholder="下单日期止" value-format="YYYY-MM-DD" style="width:140px" @change="loadTracking" />
              <el-select v-model="trackQuery.po_status" clearable style="width:120px" placeholder="采购单状态" @change="loadTracking">
                <el-option label="待采购" value="待采购" />
                <el-option label="已下单" value="已下单" />
                <el-option label="部分到货" value="部分到货" />
                <el-option label="全部到货" value="全部到货" />
              </el-select>
              <el-select v-model="batchReceiveWarehouseId" style="width:140px" placeholder="收货仓库">
                <el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" />
              </el-select>
            </div>
          </div>
          <template v-if="trackingList.length > 0">
            <el-card v-for="item in trackingList" :key="item.order_id" shadow="never" style="margin-bottom:12px">
              <div class="track-header">
                <div>
                  <strong>{{ item.order_no }}</strong>
                  <span style="margin-left:12px;color:#666">{{ item.customer_name }}</span>
                  <span style="margin-left:8px;color:#999;font-size:13px">{{ item.order_date }}</span>
                  <el-tag :type="item.all_arrived ? 'success' : 'warning'" size="small" style="margin-left:12px">
                    {{ item.all_arrived ? '已全部到货' : '采购中' }}
                  </el-tag>
                </div>
                <div style="display:flex;align-items:center;gap:8px">
                  <span style="color:#999;font-size:13px">关联 {{ item.po_count }} 张采购单</span>
                  <el-button v-if="!item.all_arrived" size="small" type="primary" plain
                    :loading="batchReceivingId === item.order_id"
                    @click.stop="handleBatchReceive(item)">一键全部收货</el-button>
                </div>
              </div>
              <el-table :data="item.purchase_orders" size="small" stripe style="width:100%;margin-top:8px" @row-click="(po) => showPurchaseOrders(po)">
                <el-table-column prop="po_no" label="采购单号" width="150" />
                <el-table-column prop="supplier_name" label="供应商" width="140" />
                <el-table-column label="状态" width="90" align="center">
                  <template #default="{ row: po }">
                    <el-tag :type="po.arrived ? 'success' : po.status === '待采购' ? 'info' : po.status === '部分到货' ? 'warning' : 'primary'" size="small">{{ po.status }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80">
                  <template #default="{ row: po }">
                    <el-button text size="small" @click.stop="showPurchaseOrders(po)">查看</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </template>
          <div v-else style="text-align:center;padding:40px 0;color:#999">暂无采购跟踪数据</div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 采购拆分预览对话框 -->
    <el-dialog v-model="showPreviewDialog" title="采购拆分预览" width="800px" @closed="previewData = null">
      <template v-if="previewData">
        <div style="margin-bottom:12px">
          涉及 {{ previewData.order_count }} 个订单: {{ previewData.order_nos?.join(', ') }}
        </div>
        <el-card v-for="(g, gi) in previewData.groups" :key="gi" shadow="never" style="margin-bottom:12px">
          <template #header>
            <div class="preview-group-header">
              <div>
                <strong>
                  <template v-if="g.supplier_code && g.supplier_name">{{ g.supplier_code }} - {{ g.supplier_name }}</template>
                  <template v-else-if="g.supplier_code">{{ g.supplier_code }}</template>
                  <template v-else-if="g.supplier_name">{{ g.supplier_name }}</template>
                  <template v-else>待定供应商</template>
                </strong>
                <span style="margin-left:12px;color:#666">{{ g.contact }} {{ g.phone }}</span>
              </div>
              <span style="font-size:15px;font-weight:bold">¥{{ g.total_amount?.toFixed(2) }}</span>
            </div>
          </template>
          <template v-for="(section, pt, si) in g.sections" :key="si">
            <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px">
              <el-tag :type="pt === '物料' ? 'primary' : pt === '成品' ? 'success' : 'warning'" size="small">{{ pt }}</el-tag>
              <span style="color:#999;font-size:13px">{{ section.count }} 项，小计 ¥{{ section.total_amount?.toFixed(2) }}</span>
            </div>
            <el-table :data="section.items" size="small" stripe style="width:100%">
              <el-table-column prop="product_name" label="产品" width="150" />
              <el-table-column prop="product_code" label="编码" width="100" />
              <el-table-column prop="qty" label="数量" width="70" align="center" />
              <el-table-column prop="unit" label="单位" width="60" />
              <el-table-column prop="unit_price" label="单价" width="90" align="right">
                <template #default="{ row: it }">¥{{ it.unit_price?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="amount" label="金额" width="100" align="right">
                <template #default="{ row: it }">¥{{ it.amount?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column label="规格" min-width="140" show-overflow-tooltip>
                <template #default="{ row: it }">{{ it.specs?.join('；') || '-' }}</template>
              </el-table-column>
            </el-table>
            <div v-if="si < Object.keys(g.sections).length - 1" style="margin:12px 0;border-bottom:1px dashed #e8e8e8"></div>
          </template>
          <div v-if="g.qq || g.wechat || g.bank_account" style="margin-top:8px;font-size:13px;color:#999">
            <span v-if="g.qq">QQ: {{ g.qq }}</span>
            <span v-if="g.wechat" style="margin-left:12px">微信: {{ g.wechat }}</span>
            <span v-if="g.bank_account" style="margin-left:12px">账号: {{ g.bank_account }}</span>
            <span v-if="g.bank_name" style="margin-left:4px">({{ g.bank_name }})</span>
          </div>
        </el-card>
      </template>
      <template #footer>
        <el-button @click="showPreviewDialog = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="handleConfirmGenerate">确认生成采购单</el-button>
      </template>
    </el-dialog>

    <!-- 采购单详情对话框（精简版：6个核心字段 + 成品行列展示尺寸+工艺） -->
    <el-dialog v-model="showDetailDialog" title="采购单详情" width="720px">
      <template v-if="detailOrder">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="采购单号">{{ detailOrder.po_no }}</el-descriptions-item>
          <el-descriptions-item label="供应商">{{ detailOrder.supplier_name }}</el-descriptions-item>
          <el-descriptions-item label="联系人">{{ detailOrder.contact || '-' }}</el-descriptions-item>
          <el-descriptions-item label="电话">{{ detailOrder.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="下单日期">{{ detailOrder.order_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="关联订单" :span="2">
            <template v-if="detailOrder.order_nos && detailOrder.order_nos.length > 0">
              <el-tag v-for="ono in detailOrder.order_nos" :key="ono" size="small" style="margin-right:4px">{{ ono }}</el-tag>
            </template>
            <span v-else>-</span>
          </el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:16px 0 8px">采购明细</h4>
        <el-table :data="detailOrder.po_items || []" size="small" stripe style="width:100%">
          <el-table-column prop="product_code" label="编码" width="100" />
          <el-table-column prop="product_name" label="产品" width="140" />
          <el-table-column label="采购类型" width="70" align="center">
            <template #default="{ row }">
              <el-tag :type="row.procurement_type === '物料' ? 'primary' : row.procurement_type === '成品' ? 'success' : 'warning'" size="small">
                {{ row.procurement_type || '物料' }}
              </el-tag>
            </template>
          </el-table-column>
          <!-- 成品行显示尺寸+工艺 -->
          <el-table-column label="尺寸" width="100" v-if="detailOrder.po_items.some(i => i.procurement_type === '成品')">
            <template #default="{ row }">
              <template v-if="row.procurement_type === '成品'">{{ row.spec || '-' }}</template>
              <span v-else style="color:#ccc">-</span>
            </template>
          </el-table-column>
          <el-table-column label="工艺" width="100" v-if="detailOrder.po_items.some(i => i.procurement_type === '成品')">
            <template #default="{ row }">
              <template v-if="row.procurement_type === '成品'">{{ row.process_desc || '-' }}</template>
              <span v-else style="color:#ccc">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="70" align="center" />
          <el-table-column label="已到货" width="70" align="center">
            <template #default="{ row }">{{ row.arrived_qty || 0 }}</template>
          </el-table-column>
        </el-table>
        <div v-if="detailOrder.remark" style="margin-top:12px"><strong>备注：</strong>{{ detailOrder.remark }}</div>
        <div style="margin-top:12px;text-align:right">
          <el-button type="warning" @click="handleShare(detailOrder)">发送给供应商</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 收货对话框 -->
    <el-dialog v-model="showReceiveDialog" title="收货" width="550px">
      <template v-if="receiveOrder">
        <p style="margin-bottom:12px;color:#666">采购单：{{ receiveOrder.po_no }} — {{ receiveOrder.supplier_name }}</p>
        <el-form :inline="true" style="margin-bottom:12px">
          <el-form-item label="收货仓库">
            <el-select v-model="receiveWarehouseId" style="width:160px" placeholder="选择仓库">
              <el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" />
            </el-select>
          </el-form-item>
        </el-form>
        <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px">
          <el-checkbox v-model="receiveSelectAll" @change="onReceiveSelectAll">全选（全部按最大可收数量）</el-checkbox>
          <el-tag type="info" size="small">{{ receiveSelectedCount }} 项待收货</el-tag>
        </div>
        <el-table :data="receiveOrder.po_items || []" size="small" style="width:100%">
          <el-table-column prop="product_name" label="产品" width="140" />
          <el-table-column prop="quantity" label="采购数量" width="80" align="center" />
          <el-table-column label="已到货" width="70" align="center">
            <template #default="{ row }">{{ row.arrived_qty || 0 }}</template>
          </el-table-column>
          <el-table-column label="本次收货" width="100">
            <template #default="{ $index }">
              <el-input v-model.number="receiveItems[$index].qty" type="number" :min="0" size="small" style="width:90px" />
            </template>
          </el-table-column>
        </el-table>
      </template>
      <template #footer>
        <el-button @click="showReceiveDialog = false">取消</el-button>
        <el-button type="primary" :loading="receiving" @click="handleReceive">确认收货</el-button>
      </template>
    </el-dialog>

    <!-- 收货回退对话框 -->
    <el-dialog v-model="showRollbackDialog" title="收货回退" width="550px">
      <template v-if="rollbackOrder">
        <p style="margin-bottom:12px;color:#f56c6c">回退将扣减库存，该操作不可恢复！</p>
        <p style="margin-bottom:12px;color:#666">采购单：{{ rollbackOrder.po_no }} — {{ rollbackOrder.supplier_name }}</p>
        <el-form :inline="true" style="margin-bottom:12px">
          <el-form-item label="回退仓库">
            <el-select v-model="rollbackWarehouseId" style="width:160px" placeholder="选择仓库">
              <el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" />
            </el-select>
          </el-form-item>
        </el-form>
        <el-table :data="rollbackOrder.po_items || []" size="small" style="width:100%">
          <el-table-column prop="product_name" label="产品" width="140" />
          <el-table-column prop="quantity" label="采购数量" width="70" align="center" />
          <el-table-column label="已到货" width="70" align="center">
            <template #default="{ row }">{{ row.arrived_qty || 0 }}</template>
          </el-table-column>
          <el-table-column label="回退数量" width="100">
            <template #default="{ $index }">
              <el-input v-model.number="rollbackItems[$index].qty" type="number" :min="0" size="small" style="width:90px" />
            </template>
          </el-table-column>
        </el-table>
      </template>
      <template #footer>
        <el-button @click="showRollbackDialog = false">取消</el-button>
        <el-button type="danger" :loading="rollbacking" @click="handleRollback">确认回退</el-button>
      </template>
    </el-dialog>

    <!-- 发送给供应商对话框 -->
    <el-dialog v-model="showShareDialog" title="发送采购单给供应商" width="95%" top="2vh">
      <template v-if="shareData">
        <el-tabs v-model="shareTab">
          <el-tab-pane label="复制文本" name="text">
            <p style="color:#666;margin-bottom:8px">复制以下内容发送给供应商（微信/QQ）</p>
            <el-input type="textarea" :rows="12" :model-value="shareData.text" readonly
              style="font-size:13px;font-family: monospace;" />
            <div style="margin-top:12px">
              <el-button type="primary" @click="copyText(shareData.text)">复制文本</el-button>
            </div>
          </el-tab-pane>
          <el-tab-pane label="打印预览" name="print">
            <div class="pv-wrap">
              <div class="pv-bar">
                <el-button type="primary" :disabled="!shareIframeReady" @click="doSharePrint">打印</el-button>
              </div>
              <div class="pv-body">
                <div class="pv-paper">
                  <iframe ref="shareIframeRef" :srcdoc="shareData.html" class="pv-frame"
                    @load="shareIframeReady = true" frameborder="0"></iframe>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </template>
    </el-dialog>

    <!-- QR码显示对话框 -->
    <el-dialog v-model="showQrDialog" :title="'采购单收货码 - ' + (qrPoNo || '')" width="400px" top="10vh">
      <div style="text-align:center;padding:20px">
        <div v-if="qrLoading" style="padding:40px">
          <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        </div>
        <img v-else-if="qrImageUrl" :src="qrImageUrl" alt="QR码" style="width:240px;height:240px;display:block;margin:0 auto;border:1px solid #eee;padding:12px;border-radius:8px" />
        <p style="margin-top:16px;font-size:16px;font-weight:bold">{{ qrPoNo }}</p>
        <p style="color:#999;font-size:13px">仓库扫码快速完成收货</p>
      </div>
      <template #footer>
        <el-button @click="showQrDialog = false">关闭</el-button>
        <el-button type="primary" :disabled="!qrImageUrl" @click="printQrCode">打印</el-button>
      </template>
    </el-dialog>

    <!-- QR扫码收货对话框 -->
    <el-dialog v-model="showScanDialog" title="扫码收货" width="450px" top="5vh" @closed="stopScanner">
      <div style="text-align:center">
        <div v-if="!scanningStarted" style="padding:40px;color:#999">
          <el-icon :size="48"><Camera /></el-icon>
          <p style="margin-top:12px">点击下方按钮启动摄像头</p>
          <el-button type="primary" style="margin-top:12px" @click="startScanner">启动摄像头</el-button>
        </div>
        <div v-show="scanningStarted" id="qr-reader" style="width:100%;max-width:400px;margin:0 auto"></div>
        <p v-if="scanningStatus" style="margin-top:8px;color:#666">{{ scanningStatus }}</p>
        <p v-if="scanningStarted" style="margin-top:8px">
          <el-input v-model="manualCode" placeholder="或手动输入采购单号" style="width:260px;display:inline-block" @keyup.enter="lookupAndReceive(manualCode)" />
          <el-button style="margin-left:8px" @click="lookupAndReceive(manualCode)">查询</el-button>
        </p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { purchaseApi, warehouseApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, Camera } from '@element-plus/icons-vue'
import { Html5Qrcode } from 'html5-qrcode'

const activeTab = ref('pending')

// ── 待采购订单 ──────────────────────────────────────────────
const pendingOrders = ref([])
const pendingLoading = ref(false)
const pendingQuery = reactive({ keyword: '', start_date: '', end_date: '' })
const selectedIds = ref([])
const expandedRows = ref(new Set())

function toggleExpand(row) {
  if (expandedRows.value.has(row.id)) {
    expandedRows.value.delete(row.id)
  } else {
    expandedRows.value.add(row.id)
  }
}

function getMaterialTypes(items) {
  const types = new Set()
  items.forEach(it => types.add(it.material_type))
  return [...types]
}

async function loadPending() {
  pendingLoading.value = true
  try {
    const params = {}
    if (pendingQuery.keyword) params.keyword = pendingQuery.keyword
    if (pendingQuery.start_date) params.start_date = pendingQuery.start_date
    if (pendingQuery.end_date) params.end_date = pendingQuery.end_date
    const res = await purchaseApi.pendingOrders(params)
    pendingOrders.value = res.data || []
  } catch {} finally { pendingLoading.value = false }
}

// ── 采购拆分预览 ────────────────────────────────────────────
const showPreviewDialog = ref(false)
const previewData = ref(null)
const generating = ref(false)

async function handlePreview() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请选择至少一个订单')
    return
  }
  try {
    const res = await purchaseApi.preview({ order_ids: selectedIds.value })
    previewData.value = res.data
    showPreviewDialog.value = true
  } catch {}
}

async function handleConfirmGenerate() {
  generating.value = true
  try {
    const res = await purchaseApi.generate({ order_ids: selectedIds.value })
    ElMessage.success(res.message || '采购单已生成')
    showPreviewDialog.value = false
    previewData.value = null
    selectedIds.value = []
    loadPending()
    loadSupplierOptions()
  } finally { generating.value = false }
}

// ── 采购单列表 ──────────────────────────────────────────────
const purchaseList = ref([])
const listTotal = ref(0)
const listLoading = ref(false)
const listQuery = reactive({
  keyword: '', status: '', supplier_id: '',
  start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
  end_date: new Date().toISOString().slice(0, 10),
  page: 1, page_size: 20,
})
const supplierOptions = ref([])
const selectedSupplier = ref(null)

// 层级导航
const supplierHierarchy = ref([])
const currentLevelLabel = ref('全部采购单')

async function loadSupplierOptions() {
  try {
    const res = await purchaseApi.suppliers()
    supplierOptions.value = res.data || []
  } catch {}
}

function onSupplierChange(val) {
  listQuery.supplier_id = val || ''
  selectedSupplier.value = val
  if (val) {
    const s = supplierOptions.value.find(x => x.id === val)
    currentLevelLabel.value = `供应商: ${s?.name || val}`
    supplierHierarchy.value = [s || { id: val, name: val }]
  } else {
    currentLevelLabel.value = '全部采购单'
    supplierHierarchy.value = []
  }
  listQuery.page = 1
  loadPurchaseList()
}

function clearSupplier() {
  listQuery.supplier_id = ''
  selectedSupplier.value = null
  currentLevelLabel.value = '全部采购单'
  supplierHierarchy.value = []
  listQuery.page = 1
  loadPurchaseList()
}

async function loadPurchaseList() {
  listLoading.value = true
  try {
    const params = {}
    if (listQuery.keyword) params.keyword = listQuery.keyword
    if (listQuery.status) params.status = listQuery.status
    if (listQuery.supplier_id) params.supplier_id = listQuery.supplier_id
    if (listQuery.start_date) params.start_date = listQuery.start_date
    if (listQuery.end_date) params.end_date = listQuery.end_date
    params.page = listQuery.page
    params.page_size = listQuery.page_size
    const res = await purchaseApi.list(params)
    purchaseList.value = res.items
    listTotal.value = res.total
  } catch {} finally { listLoading.value = false }
}

function goToPending() {
  activeTab.value = 'pending'
}

// ── 采购跟踪 ────────────────────────────────────────────────
const trackingList = ref([])
const trackQuery = reactive({ keyword: '', start_date: '', end_date: '', po_status: '' })
const batchReceivingId = ref(null)
const batchReceiveWarehouseId = ref(1)

async function loadTracking() {
  try {
    const params = {}
    if (trackQuery.keyword) params.keyword = trackQuery.keyword
    if (trackQuery.start_date) params.start_date = trackQuery.start_date
    if (trackQuery.end_date) params.end_date = trackQuery.end_date
    if (trackQuery.po_status) params.po_status = trackQuery.po_status
    const res = await purchaseApi.tracking(params)
    trackingList.value = res.data || []
  } catch {}
}

async function handleBatchReceive(item) {
  if (!batchReceiveWarehouseId.value) {
    ElMessage.warning('请先选择收货仓库')
    return
  }
  const poIds = (item.purchase_orders || [])
    .filter(po => po.po_id && !po.arrived)
    .map(po => po.po_id)
  if (poIds.length === 0) {
    ElMessage.info('该订单没有需要收货的采购单')
    return
  }
  batchReceivingId.value = item.order_id
  try {
    const res = await purchaseApi.batchReceive({
      po_ids: poIds,
      warehouse_id: batchReceiveWarehouseId.value,
    })
    const data = res.data || {}
    const msg = `成功收货 ${data.results?.length || 0} 单`
    if (data.errors?.length) {
      ElMessage.warning(`${msg}，${data.errors.length} 单跳过`)
    } else {
      ElMessage.success(msg)
    }
    await loadTracking()
  } catch {
    ElMessage.error('批量收货失败')
  } finally {
    batchReceivingId.value = null
  }
}

// ── 采购单详情 ──────────────────────────────────────────────
const showDetailDialog = ref(false)
const detailOrder = ref(null)

function showDetail(row) {
  purchaseApi.get(row.id).then(res => { detailOrder.value = res.data || res; showDetailDialog.value = true }).catch(() => {})
}

function showPurchaseOrders(po) {
  purchaseApi.get(po.po_id).then(res => { detailOrder.value = res.data || res; showDetailDialog.value = true }).catch(() => {})
}

// ── 发送给供应商 ────────────────────────────────────────────
const showShareDialog = ref(false)
const shareData = ref(null)
const shareTab = ref('text')
const shareIframeReady = ref(false)
const shareIframeRef = ref(null)

async function handleShare(row) {
  try {
    const res = await purchaseApi.share(row.id || row.po_id)
    shareData.value = res.data
    shareTab.value = 'text'
    shareIframeReady.value = false
    showShareDialog.value = true
  } catch {}
}

function copyText(text) {
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    // Fallback
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    ElMessage.success('已复制到剪贴板')
  })
}

function doSharePrint() {
  const el = shareIframeRef.value
  if (el && el.contentWindow) {
    el.contentWindow.focus()
    el.contentWindow.print()
  }
}

// ── 收货 ────────────────────────────────────────────────────
const showReceiveDialog = ref(false)
const receiveOrder = ref(null)
const receiveItems = ref([])
const receiving = ref(false)
const receiveWarehouseId = ref(1)
const warehouses = ref([])
const receiveSelectAll = ref(false)
const receiveSelectedCount = ref(0)

function onReceiveSelectAll(val) {
  const items = receiveOrder.value?.po_items || []
  receiveItems.value.forEach((it, idx) => {
    if (val) {
      const item = items[idx]
      const maxQty = Math.max(0, (item.quantity || 0) - (item.arrived_qty || 0))
      it.qty = maxQty
    } else {
      it.qty = 0
    }
  })
  receiveSelectedCount.value = val
    ? receiveItems.value.filter(it => it.qty > 0).length
    : 0
}

function showReceive(row) {
  purchaseApi.get(row.id).then(res => {
    receiveOrder.value = res.data || res
    const items = receiveOrder.value.po_items || []
    receiveItems.value = items.map(i => ({ product_id: i.product_id || i.id, qty: Math.max(0, (i.quantity || 0) - (i.arrived_qty || 0)), unit: i.unit || '米', product_name: i.product_name }))
    receiveSelectAll.value = true
    receiveSelectedCount.value = receiveItems.value.filter(it => it.qty > 0).length
    if (warehouses.value.length > 0) {
      receiveWarehouseId.value = warehouses.value[0].id
    }
    showReceiveDialog.value = true
  }).catch(() => {})
}

async function handleReceive() {
  receiving.value = true
  try {
    await purchaseApi.receive(receiveOrder.value.id, {
      items: receiveItems.value.filter(i => i.qty > 0),
      warehouse_id: receiveWarehouseId.value,
    })
    ElMessage.success('收货成功')
    showReceiveDialog.value = false
    loadPurchaseList()
    loadSupplierOptions()
  } catch {} finally { receiving.value = false }
}

// ── 收货回退 ────────────────────────────────────────────────
const showRollbackDialog = ref(false)
const rollbackOrder = ref(null)
const rollbackItems = ref([])
const rollbacking = ref(false)
const rollbackWarehouseId = ref(1)

function showRollback(row) {
  purchaseApi.get(row.id).then(res => {
    rollbackOrder.value = res.data || res
    const items = rollbackOrder.value.po_items || []
    rollbackItems.value = items.map(i => ({
      product_id: i.product_id || i.id,
      qty: i.arrived_qty || 0,
      unit: i.unit || '米',
      product_name: i.product_name,
    }))
    if (warehouses.value.length > 0) {
      rollbackWarehouseId.value = warehouses.value[0].id
    }
    showRollbackDialog.value = true
  }).catch(() => {})
}

async function handleRollback() {
  const validItems = rollbackItems.value.filter(i => i.qty > 0)
  if (validItems.length === 0) {
    ElMessage.warning('请至少输入一个回退数量')
    return
  }
  try {
    await ElMessageBox.confirm('确认要回退收货？将扣减库存且不可恢复！', '警告', {
      confirmButtonText: '确认回退',
      cancelButtonText: '取消',
      type: 'warning',
    })
    rollbacking.value = true
    await purchaseApi.receiveRollback(rollbackOrder.value.id, {
      items: validItems,
      warehouse_id: rollbackWarehouseId.value,
    })
    ElMessage.success('收货回退成功')
    showRollbackDialog.value = false
    loadPurchaseList()
    loadSupplierOptions()
  } catch (e) {
    if (e !== 'cancel') throw e
  } finally { rollbacking.value = false }
}

// ── 删除 ────────────────────────────────────────────────────
async function handleDelete(id) {
  await purchaseApi.delete(id)
  ElMessage.success('已删除')
  loadPurchaseList()
  loadSupplierOptions()
}

// ── 工具 ────────────────────────────────────────────────────
function statusTag(status) {
  const map = { '待采购': 'info', '已下单': 'primary', '部分到货': 'warning', '全部到货': 'success', '已结算': 'success' }
  return map[status] || 'info'
}

function onTabChange(tab) {
  if (tab === 'list') {
    loadPurchaseList()
    loadSupplierOptions()
  } else if (tab === 'tracking') {
    loadTracking()
  }
}

// ── QR码 ──────────────────────────────────────────────────────
const showQrDialog = ref(false)
const qrImageUrl = ref('')
const qrPoNo = ref('')
const qrLoading = ref(false)

async function showQrCode(row) {
  qrPoNo.value = row.po_no
  qrLoading.value = true
  showQrDialog.value = true
  try {
    const blob = await purchaseApi.qrcode(row.id)
    if (qrImageUrl.value) URL.revokeObjectURL(qrImageUrl.value)
    qrImageUrl.value = URL.createObjectURL(blob)
  } catch {
    ElMessage.error('获取二维码失败')
  } finally {
    qrLoading.value = false
  }
}

function printQrCode() {
  const win = window.open('', '_blank')
  if (!win) return
  win.document.write(`
    <html><head><title>收货码 - ${qrPoNo.value}</title>
    <style>body{text-align:center;padding:40px;font-family:sans-serif}
    img{width:300px;height:300px;border:1px solid #eee;padding:12px;border-radius:8px}
    p{font-size:18px;margin-top:20px;font-weight:bold}
    .hint{color:#999;font-size:14px;font-weight:normal}</style>
    </head><body>
    <img src="${qrImageUrl.value}" />
    <p>${qrPoNo.value}</p>
    <p class="hint">仓库扫码快速完成收货</p>
    <script>window.onload=function(){window.print();window.close()}<\/script>
    </body></html>
  `)
  win.document.close()
}

// ── 扫码收货 ──────────────────────────────────────────────────
const showScanDialog = ref(false)
const scanningStarted = ref(false)
const scanningStatus = ref('')
const manualCode = ref('')
let html5QrCode = null

async function openScanner() {
  manualCode.value = ''
  scanningStarted.value = false
  scanningStatus.value = ''
  showScanDialog.value = true
  await nextTick()
}

async function startScanner() {
  scanningStatus.value = '正在启动摄像头...'
  scanningStarted.value = true
  await nextTick()
  try {
    html5QrCode = new Html5Qrcode('qr-reader')
    await html5QrCode.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: { width: 250, height: 250 } },
      (code) => {
        scanningStatus.value = '扫码成功！'
        showScanDialog.value = false
        lookupAndReceive(code)
      },
      () => {},
    )
    scanningStatus.value = '对准采购单QR码扫描'
  } catch (err) {
    scanningStatus.value = '摄像头启动失败：' + (err.message || '未知错误')
    scanningStarted.value = false
  }
}

function stopScanner() {
  if (html5QrCode) {
    html5QrCode.stop().catch(() => {})
    html5QrCode = null
  }
  scanningStatus.value = ''
  scanningStarted.value = false
}

async function lookupAndReceive(code) {
  const poNo = (code || '').trim()
  if (!poNo) {
    ElMessage.warning('请输入采购单号')
    return
  }
  try {
    const res = await purchaseApi.scan(poNo)
    const po = res.data
    if (!po) {
      ElMessage.error('未找到采购单：' + poNo)
      return
    }
    // 复用现有收货弹窗逻辑
    receiveOrder.value = po
    const items = po.po_items || []
    receiveItems.value = items.map(i => ({
      product_id: i.product_id || i.id,
      qty: Math.max(0, (i.quantity || 0) - (i.arrived_qty || 0)),
      unit: i.unit || '米',
      product_name: i.product_name,
    }))
    receiveSelectAll.value = true
    receiveSelectedCount.value = receiveItems.value.filter(it => it.qty > 0).length
    if (warehouses.value.length > 0) {
      receiveWarehouseId.value = warehouses.value[0].id
    }
    showReceiveDialog.value = true
    ElMessage.success('已加载采购单：' + po.po_no)
  } catch (e) {
    ElMessage.error('未找到采购单：' + poNo)
  }
}

onMounted(async () => {
  await loadPending()
  loadSupplierOptions()
  // 加载仓库列表
  try {
    const res = await warehouseApi.list()
    warehouses.value = res.data || []
    if (warehouses.value.length > 0) {
      receiveWarehouseId.value = warehouses.value[0].id
    }
  } catch {}
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h3 { font-size: 18px; }
.tab-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px; }
.track-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px; }
.preview-group-header { display: flex; justify-content: space-between; align-items: center; }
:deep(.el-table__expanded-cell) { padding: 8px 8px 8px 48px; }

/* 打印预览样式 */
.pv-wrap { display: flex; flex-direction: column; }
.pv-bar { display: flex; align-items: center; padding: 0 0 10px 0; gap: 8px; border-bottom: 1px solid #e8e8e8; margin-bottom: 10px; }
.pv-body { flex: 1; overflow: auto; background: #e8e8e8; display: flex; justify-content: center; padding: 20px; border-radius: 4px; min-height: 65vh; }
.pv-paper { width: 100%; max-width: 210mm; min-height: 297mm; background: #fff; box-shadow: 0 2px 12px rgba(0,0,0,0.12); }
.pv-frame { width: 100%; max-width: 210mm; height: 297mm; border: none; display: block; }
</style>
