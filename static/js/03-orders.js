/**
 * 销售订单模块
 * 
 * API 规范：docs/API-FORMAT.md §3
 * 
 * 数据流：
 *   apiOrders.list() → orders[] → filteredOrders[]（前端筛选）
 * 
 * 关键规则：
 *   - 状态显示：只用 status_label（中文），不用 status_key
 *   - 筛选用：status_key（英文键）
 *   - 禁止在模板中写死中文状态值
 */

window.__ordersModule__ = {
  // ── 加载订单列表 ─────────────────────────────────────────
  async loadOrders() {
    const S = window.__STATE__;
    try {
      const d = await apiOrders.list({ page: 1, page_size: 100 });
      S.orders = (d.items || []).map(o => ({
        id: o.id,
        orderNo: o.order_no || '',
        customerId: o.customer_id,
        customerName: o.customer_name || '',        // ← 显示用这个
        orderType: o.order_type || '窗帘',
        customerId: o.customer_id,
        salesperson: o.salesperson || '',
        salespersonId: null,
        amount: o.amount || 0,
        quoteAmount: o.quote_amount || 0,
        discountAmount: o.discount_amount || 0,
        roundAmount: o.round_amount || 0,
        received: o.received || 0,
        debt: o.debt || 0,
        status: o.status_label || '待确认',       // ← 前端直接显示用这个！
        statusKey: o.status_key || 'created',      // ← 筛选/流转用这个
        statusColor: o.status_color || '#909399',
        statusColorKey: o.status_key || 'created',
        orderDate: o.order_date || '',
        deliveryDate: o.delivery_date || '',
        deliveryMethod: o.delivery_method || '上门安装',
        history: o.history || [],
        items: o.items || [],
      }));
    } catch (e) {
      console.error('loadOrders error:', e);
    }
  },

  // ── 选择订单（显示详情）────────────────────────────────────
  selectOrder(o) {
    const S = window.__STATE__;
    S.selOrder = {
      id: o.id,
      orderNo: o.orderNo,
      customerName: o.customerName,
      orderType: o.orderType,
      salesperson: o.salesperson,
      orderDate: o.orderDate,
      deliveryDate: o.deliveryDate,
      deliveryMethod: o.deliveryMethod,
      amount: o.amount,
      received: o.received,
      debt: o.debt,
      roundAmount: o.roundAmount || 0,
      status: o.status || '待确认',
      statusKey: o.statusKey || 'created',
      statusColor: o.statusColor || '#909399',
      statusColorKey: o.statusKey || 'created',
      history: o.history || [],
      items: (o.items || []).map(i => ({
        product_name: i.product_name || i.product || '',
        unit_price: i.unit_price || i.price || 0,
        item_type: i.is_material ? 'material' : (i.item_type || 'product'),
        room: i.room || '',
        width: i.width || '',
        height: i.height || '',
        qty: i.qty || 0,
        discount: i.discount || 1,
        amount: i.amount || 0,
      })),
    };
  },

  // ── 修改状态 ─────────────────────────────────────────────
  async updateOrderStatusByKey() {
    const S = window.__STATE__;
    const sel = S.selOrder;
    if (!sel.id) return;
    const newKey = sel.statusKey;
    const st = (S.dictMap.orderStatus || []).find(x => x.k === newKey);
    if (!st) return;
    // 本地更新
    const old = S.orders.find(o => o.id === sel.id);
    if (old) {
      old.status = st.v;
      old.statusKey = newKey;
      if (!old.history) old.history = [];
      old.history.push({
        s: old.status, s2: st.v, c: newKey,
        time: new Date().toLocaleString(),
      });
      Object.assign(S.selOrder, old);
    }
    // 同步后端
    try {
      await apiOrders.updateStatus(sel.id, newKey);
    } catch (e) {
      console.error('updateOrderStatusByKey error:', e);
    }
  },

  // ── 删除订单 ─────────────────────────────────────────────
  async delOrder() {
    const S = window.__STATE__;
    const o = S.selOrder;
    if (!o.id) return;
    if (!confirm(`确定删除订单「${o.orderNo}」？此操作不可恢复！`)) return;
    try {
      await apiOrders.delete(o.id);
      S.selOrder = {};
      await __ordersModule__.loadOrders();
      ElementPlus.ElMessage.success('已删除');
    } catch (e) {
      ElementPlus.ElMessage.error('删除失败：' + (e.message || ''));
    }
  },
};
