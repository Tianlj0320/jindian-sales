/**
 * 新建订单表单模块
 * API 规范：docs/API-FORMAT.md §3-4
 */

window.__orderFormModule__ = {
  onCustomerSelect(S) {
    const c = (S.customers || []).find(x => x.id === S.orderF.customerId);
    if (c) {
      S.orderF.customerPhone = c.phone || '';
      S.orderF.installAddress = c.address || '';
    }
  },

  // 自动填交期（接单日+14天）
  autoDelivery(S) {
    if (!S.orderF.orderDate) return;
    const d = new Date(S.orderF.orderDate);
    d.setDate(d.getDate() + 14);
    S.orderF.deliveryDate = d.toISOString().slice(0, 10);
  },

  addOrderItem(S) {
    S.orderF.items.push({
      productType: '窗帘', location: '客厅', style: '001挂钩',
      itemName: '窗帘', productId: null, size: '',
      qty: 1, discount: 1, price: null, amount: null,
    });
  },

  addOrderMaterial(S) {
    S.orderF.materials.push({
      category: '布料', productId: null, model: '',
      qty: 1, unit: '米', price: null, amount: null, remark: '',
    });
  },

  calcItem(row, S) {
    try {
      if (row && row.price && row.qty)
        row.amount = Math.round(row.price * row.qty * (row.discount || 1) * 100) / 100;
      __orderFormModule__.calcTotals(S);
    } catch (e) {
      console.error('calcItem error', e);
    }
  },

  calcMaterial(row, S) {
    try {
      if (row && row.price && row.qty)
        row.amount = Math.round(row.price * row.qty * 100) / 100;
      const mats = S.orderF.materials || [];
      S.orderF.materialsTotal = mats.reduce((s, r) => s + ((r && r.amount) || 0), 0);
      __orderFormModule__.calcTotals(S);
    } catch (e) {
      console.error('calcMaterial error', e);
    }
  },

  calcTotals(S) {
    try {
      const items = S.orderF.items || [];
      const mats = S.orderF.materials || [];
      const itemsTotal = items.reduce((s, r) => s + ((r && r.amount) || 0), 0);
      const materialsTotal = mats.reduce((s, r) => s + ((r && r.amount) || 0), 0);
      S.orderF.itemsTotal = itemsTotal;
      S.orderF.materialsTotal = materialsTotal;
      S.orderF.quoteAmount = itemsTotal + materialsTotal;
      S.orderF.amount = Math.max(
        0,
        S.orderF.quoteAmount - (S.orderF.discountAmount || 0) - (S.orderF.roundAmount || 0)
      );
    } catch (e) {
      console.error('calcTotals error', e);
    }
  },

  // ── 保存新建订单 ───────────────────────────────────────────
  async saveNewOrder(S) {
    if (!S.orderF.customerId) {
      ElementPlus.ElMessage.warning('请选择客户');
      return;
    }
    const customer = (S.customers || []).find(c => c.id === S.orderF.customerId);
    const today = new Date().toISOString().slice(0, 10);
    const prods = S.products;
    const emps = S.employees;

    const amount = Math.max(
      0,
      (S.orderF.items || []).reduce((s, r) => s + ((r && r.amount) || 0), 0)
        - (S.orderF.discountAmount || 0) - (S.orderF.roundAmount || 0)
    );

    const payload = {
      customer_id: S.orderF.customerId,
      customer_name: customer?.name || '',
      customer_phone: customer?.phone || '',
      order_type: S.orderF.orderType,
      content: (S.orderF.items || [])
        .map(i => (prods.find(p => p.id === i.productId) || {}).name || '')
        .filter(Boolean).join('+') || '窗帘',
      quote_amount: S.orderF.quoteAmount,
      discount_amount: S.orderF.discountAmount || 0,
      round_amount: S.orderF.roundAmount || 0,
      amount,
      received: S.orderF.received || 0,
      order_date: S.orderF.orderDate || today,
      delivery_date: S.orderF.deliveryDate || '',
      delivery_method: S.orderF.deliveryMethod,
      salesperson_id: S.orderF.salespersonId || null,
      install_address: S.orderF.installAddress || '',
      install_date: S.orderF.installDate || '',
      items: (S.orderF.items || [])
        .filter(i => i.productId)
        .map(i => ({
          product_id: i.productId,
          product_name: (prods.find(p => p.id === i.productId) || {}).name || '',
          product_type: i.productType || '窗帘',
          room: i.location || '',
          style: i.style || '',
          item_name: i.itemName || '',
          width: i.width || '',
          height: i.height || '',
          qty: i.qty || 1,
          discount: i.discount || 1,
          price: i.price || 0,
          amount: i.amount || 0,
        })),
    };

    try {
      const d = await apiOrders.create(payload);
      S.orders.unshift({
        id: d.id,
        orderNo: d.order_no || '',
        customerName: customer?.name || '',
        orderType: S.orderF.orderType,
        salesperson: (emps.find(e => e.id === S.orderF.salespersonId) || {}).name || '',
        orderDate: S.orderF.orderDate || today,
        deliveryDate: S.orderF.deliveryDate || '',
        deliveryMethod: S.orderF.deliveryMethod,
        amount,
        received: S.orderF.received || 0,
        debt: amount - (S.orderF.received || 0),
        items: payload.items,
        status: '待确认',
        statusKey: 'created',
        history: [],
      });
      const closeForm = () => {
        if (window.__initModule__?.showNewOrder) window.__initModule__.showNewOrder.value = false;
        else S.showNewOrder = false;
      };
      closeForm();
      S.orderF = {
        customerId: null, orderType: '窗帘', orderDate: '', deliveryDate: '',
        deliveryMethod: '上门安装', salespersonId: '',
        items: [], materials: [], quoteAmount: 0,
        discountAmount: 0, roundAmount: 0, amount: 0,
        received: 0, itemsTotal: 0, materialsTotal: 0,
      };
      ElementPlus.ElMessage.success('订单已创建');
    } catch (e) {
      ElementPlus.ElMessage.error('创建失败');
    }
  },
};
