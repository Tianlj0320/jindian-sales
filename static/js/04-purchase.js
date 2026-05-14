/**
 * 采购管理模块
 * 
 * API 规范：docs/API-FORMAT.md §12-13
 */

window.__purchaseModule__ = {
  // ── 加载采购单列表 ─────────────────────────────────────────
  async loadPurchases() {
    const S = window.__STATE__;
    try {
      const d = await apiPurchase.list();
      S.purchases = (d.items || []).map(p => ({
        id: p.id,
        purchaseNo: p.po_no || '',
        supplierId: p.supplier_id,
        supplierName: p.supplier_name || '',    // ← 显示用这个
        orderIds: p.order_ids || '',
        items: Array.isArray(p.items)
          ? p.items.map(i => i.product_name || '').join(', ')
          : (p.items || ''),
        itemsRaw: p.items || [],
        status: p.status || '待采购',
        amount: p.total_amount || p.amount || 0,
        date: p.expected_date || p.order_date || '',
        remark: p.remark || '',
      }));
    } catch (e) {
      console.error('loadPurchases error:', e);
    }
  },

  // ── 加载待采购订单（拆分生成）───────────────────────────────
  async loadPurchaseOrdersForSplit() {
    const S = window.__STATE__;
    try {
      const d = await apiOrders.list({ status_key: 'confirmed' });
      S.purchaseOrdersForSplit = (d.items || []).map(o => ({
        id: o.id,
        orderNo: o.order_no || '',
        customerName: o.customer_name || '',
        orderType: o.order_type || '窗帘',
        content: o.content || '',
        amount: o.amount || 0,
        orderDate: o.order_date || '',
        deliveryDate: o.delivery_date || '',
      }));
      S.selectedSplitOrders = [];
    } catch (e) {
      console.error('loadPurchaseOrdersForSplit error:', e);
    }
  },

  toggleSplitOrder(id) {
    const S = window.__STATE__;
    const idx = S.selectedSplitOrders.indexOf(id);
    if (idx > -1) S.selectedSplitOrders.splice(idx, 1);
    else S.selectedSplitOrders.push(id);
  },

  toggleAllSplitOrders() {
    const S = window.__STATE__;
    if (S.selectedSplitOrders.length === S.purchaseOrdersForSplit.length) {
      S.selectedSplitOrders = [];
    } else {
      S.selectedSplitOrders = S.purchaseOrdersForSplit.map(o => o.id);
    }
  },

  async doBatchSplit() {
    const S = window.__STATE__;
    if (S.selectedSplitOrders.length === 0) {
      ElementPlus.ElMessage.warning('请先勾选订单');
      return;
    }
    try {
      const d = await apiPurchase.batchSplit(S.selectedSplitOrders);
      ElementPlus.ElMessage.success(d.message || '采购单生成成功');
      S.selectedSplitOrders = [];
      await __purchaseModule__.loadPurchaseOrdersForSplit();
      await __purchaseModule__.loadPurchases();
    } catch (e) {
      ElementPlus.ElMessage.error('生成失败：' + (e.message || '未知错误'));
    }
  },

  async updateStatus(row, newStatus) {
    try {
      await apiPurchase.updateStatus(row.id, newStatus);
      row.status = newStatus;
      ElementPlus.ElMessage.success('状态已更新');
    } catch (e) {
      ElementPlus.ElMessage.error('更新失败');
    }
  },

  async deletePurchase(row) {
    const S = window.__STATE__;
    if (!confirm(`确定删除采购单「${row.purchaseNo}」？`)) return;
    try {
      await apiPurchase.delete(row.id);
      S.purchases = S.purchases.filter(p => p.id !== row.id);
      ElementPlus.ElMessage.success('已删除');
    } catch (e) {
      ElementPlus.ElMessage.error('删除失败');
    }
  },
};
