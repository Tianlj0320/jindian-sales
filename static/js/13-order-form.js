/**
 * 新建订单表单模块
 * API 规范：docs/API-FORMAT.md §3-4
 */

window.__orderFormModule__ = {
  // ── 打开新建订单（自动初始化） ────────────────────────────────
  openNewOrder(S) {
    const today = new Date().toISOString().slice(0, 10);
    // 生成订单号：JD-YYYYMMDD-NNN（当日序号）
    const todayOrders = (S.orders || []).filter(o => o.orderDate === today).length;
    const seq = String(todayOrders + 1).padStart(3, '0');
    const orderNo = `JD-${today.replace(/-/g, '')}-${seq}`;

    // 自动填当前登录人
    const curUserId = S.currentUser?.id || S.currentUser?.employee_id || null;

    S.orderF = {
      orderNo,
      customerId: null, customerName: '', customerPhone: '', customerSource: '',
      orderType: '窗帘', orderDate: today, deliveryDate: '', installDate: '',
      deliveryMethod: '上门安装', salespersonId: curUserId,
      installAddress: '', items: [], materials: [],
      itemsTotal: 0, materialsTotal: 0,
      quoteAmount: 0, discountAmount: 0, roundAmount: 0, amount: 0, received: 0,
    };
    S.orderF.items.push({ productType: '窗帘', location: '客厅', style: '韩褶', itemName: '窗帘', productId: null, code: '', model: '', size: '', qty: 1, discount: 1, price: null, amount: null });
    S.orderF.materials.push({ productId: null, code: '', name: '', model: '', qty: 1, unit: '米', price: null, amount: null, remark: '' });
    S.showNewOrder = true;
    S.page = 'order';
  },

  // ── 客户选择后自动填手机和地址 ──────────────────────────────
  onCustomerSelect(S, customerId) {
    S.orderF.customerId = customerId;
    const c = (S.customers || []).find(x => String(x.id) === String(customerId));
    if (c) {
      S.orderF.customerPhone = c.phone || '';
      S.orderF.installAddress = c.address || '';
      S.orderF.customerName = c.name || '';
    } else {
      S.orderF.customerPhone = '';
      S.orderF.installAddress = '';
      S.orderF.customerName = '';
    }
  },

  // ── 主料产品选择后自动带出型号/单价 ────────────────────────
  onItemProductSelect(S, idx, productId) {
    const row = S.orderF.items[idx];
    if (!row) return;
    row.productId = productId;
    if (productId) {
      const p = (S.products || []).find(x => String(x.id) === String(productId));
      if (p) {
        row.model = p.model || '';
        row.price = p.unit_price || 0;
        row.code = p.code || '';
        row.productName = p.name || '';
        // 自动计算金额
        if (row.price && row.qty) {
          row.amount = Math.round(row.price * row.qty * (row.discount || 1) * 100) / 100;
        }
      }
    } else {
      row.model = ''; row.price = null; row.code = ''; row.productName = '';
      row.amount = null;
    }
    __orderFormModule__.calcTotals(S);
  },

  // ── 辅料产品选择后自动带出型号/单价 ────────────────────────
  onMatProductSelect(S, idx, productId) {
    const row = S.orderF.materials[idx];
    if (!row) return;
    row.productId = productId;
    if (productId) {
      const p = (S.products || []).find(x => String(x.id) === String(productId));
      if (p) {
        row.model = p.model || '';
        row.name = p.name || '';
        row.code = p.code || '';
        row.price = p.unit_price || 0;
        if (row.price && row.qty) {
          row.amount = Math.round(row.price * row.qty * 100) / 100;
        }
      }
    } else {
      row.model = ''; row.name = ''; row.code = ''; row.price = null;
      row.amount = null;
    }
    __orderFormModule__.calcTotals(S);
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
      productType: '窗帘', location: '客厅', style: '韩褶', itemName: '窗帘',
      productId: null, code: '', model: '', productName: '',
      size: '', qty: 1, discount: 1, price: null, amount: null,
    });
  },

  addOrderMaterial(S) {
    S.orderF.materials.push({
      productId: null, code: '', name: '', model: '',
      qty: 1, unit: '米', price: null, amount: null, remark: '',
    });
  },

  calcItem(row, S) {
    try {
      if (row && row.price && row.qty) {
        row.amount = Math.round(row.price * row.qty * (row.discount || 1) * 100) / 100;
      }
      __orderFormModule__.calcTotals(S);
    } catch (e) {
      console.error('calcItem error', e);
    }
  },

  calcMaterial(row, S) {
    try {
      if (row && row.price && row.qty) {
        row.amount = Math.round(row.price * row.qty * 100) / 100;
      }
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
    const customer = (S.customers || []).find(c => String(c.id) === String(S.orderF.customerId));
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
      customer_name: customer?.name || S.orderF.customerName || '',
      customer_phone: customer?.phone || S.orderF.customerPhone || '',
      order_type: S.orderF.orderType,
      content: (S.orderF.items || [])
        .map(i => i.productName || (prods.find(p => String(p.id) === String(i.productId)) || {}).name || '')
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
          product_name: i.productName || (prods.find(p => String(p.id) === String(i.productId)) || {}).name || '',
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
      materials: (S.orderF.materials || [])
        .filter(i => i.productId)
        .map(i => ({
          product_id: i.productId,
          product_name: i.name || '',
          product_code: i.code || '',
          model: i.model || '',
          qty: i.qty || 1,
          unit: i.unit || '米',
          price: i.price || 0,
          amount: i.amount || 0,
          remark: i.remark || '',
        })),
    };

    try {
      const d = await apiOrders.create(payload);
      S.orders.unshift({
        id: d.id,
        orderNo: d.order_no || S.orderF.orderNo || '',
        customerName: customer?.name || S.orderF.customerName || '',
        orderType: S.orderF.orderType,
        salesperson: (emps.find(e => String(e.id) === String(S.orderF.salespersonId)) || {}).name || '',
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
      S.showNewOrder = false;
      ElementPlus.ElMessage.success('订单已创建');
    } catch (e) {
      console.error('[saveNewOrder] error:', e);
      const msg = e?.message || e?.err?.message || String(e) || '网络错误';
      try { ElementPlus.ElMessage.error('创建失败：' + msg); } catch(e2) { alert('创建失败：' + msg); }
    }
  },
};
