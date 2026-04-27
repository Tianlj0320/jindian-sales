/**
 * 初始化模块
 * app.mount() 前最后一个加载
 */

window.__initModule__ = {
  async initAll() {
    const S = window.__STATE__;
    const { ElMessage } = ElementPlus;

    try {
      // ── 第1批：基础数据（并行）──────────────────────────────
      const [dash, supS, catsS, prodsS, custS, empsS, finS, ordS] = await Promise.all([
        apiDashboard.getSummary().catch(() => ({})),
        apiProducts.suppliers().catch(() => ({ items: [] })),
        apiProducts.categories().catch(() => ({ items: [] })),
        apiProducts.list().catch(() => ({ items: [] })),
        apiCustomers.list().catch(() => ({ items: [] })),
        apiEmployees.list().catch(() => ({ items: [] })),
        apiFinance.summary().catch(() => ({})),
        apiOrders.list({ page: 1, page_size: 100 }).catch(() => ({ items: [] })),
      ]);

      // 仪表盘
      if (dash.today_orders !== undefined) {
        S.stats = {
          todayOrders: dash.today_orders || 0,
          monthSales: dash.month_sales || 0,
          pendingInstall: dash.pending_install || 0,
          overdueOrders: dash.overdue_orders || 0,
          pendingPayment: dash.pending_payment || 0,
          totalCustomers: dash.total_customers || 0,
        };
      }

      // 供应商
      S.suppliers = (supS.items || []).map(s => ({
        id: s.id, code: s.code || '', name: s.name || '',
        type: s.type || '', contact: s.contact || '',
        phone: s.phone || '', deliveryDays: s.delivery_days || 7,
        address: s.address || '', payment: s.payment || '',
      }));

      // 布版
      S.categories = (catsS.items || []).map(c => ({
        id: c.id, code: c.code || '', name: c.name || '',
        supplierId: 's' + c.supplier_id,
        desc: c.description || '',
      }));

      // 产品
      S.products = (prodsS.items || []).map(p => ({
        id: p.id, code: p.code || '', name: p.name || '',
        supplierId: 's' + p.supplier_id, categoryId: 'c' + p.category_id,
        type: p.product_type || '面料', classification: p.classification || '定高',
        model: p.model || '', mat: p.material || '',
        width: p.width || 280, weight: p.weight || 0,
        cf: 0, price: p.unit_price || 0, stock: p.stock || 0,
        unit: p.unit || '米', remark: '',
      }));

      // 客户
      S.customers = (custS.items || []).map(c => ({
        id: c.id, code: c.id, name: c.name || '',
        phone: c.phone || '', community: c.community || '',
        type: c.type || '零售', salesperson: c.salesperson || '',
        salespersonId: c.salesperson_id || null,
        source: c.source || '', debt: c.debt || 0,
        debtLimit: c.debt || 0, address: c.address || '',
        contact: '', remark: '',
      }));

      // 员工
      S.employees = (empsS.items || []).map(e => ({
        id: e.id, code: e.code || '', name: e.name || '',
        gender: e.gender || '男', phone: e.phone || '',
        position: e.position || '', dept: e.department || '',
        maxDiscount: e.max_discount || 1, roundLimit: e.round_limit || 0,
        status: e.status || '启用', hireDate: '',
      }));

      // 财务
      const finData = finS.data || finS;
      if (finData.month_receive !== undefined) {
        S.financeData = {
          monthRevenue: finData.month_receive || 0,
          monthCost: finData.month_pay || 0,
          monthProfit: (finData.month_receive || 0) - (finData.month_pay || 0),
          totalDebt: finData.total_debt || 0,
          pendingCommission: finData.pending_commission || 0,
        };
      }

      // 订单
      S.orders = (ordS.items || []).map(o => ({
        id: o.id, orderNo: o.order_no || '',
        customerId: o.customer_id, customerName: o.customer_name || '',
        orderType: o.order_type || '窗帘',
        amount: o.amount || 0, quoteAmount: o.quote_amount || 0,
        discountAmount: o.discount_amount || 0, roundAmount: o.round_amount || 0,
        received: o.received || 0, debt: o.debt || 0,
        status: o.status_label || '待确认',       // ← 用 status_label！
        statusKey: o.status_key || 'created',
        statusColor: o.status_color || '#909399',
        statusColorKey: o.status_key || 'created',
        orderDate: o.order_date || '',
        deliveryDate: o.delivery_date || '',
        deliveryMethod: o.delivery_method || '上门安装',
        salesperson: o.salesperson || '',
        salespersonId: null,
        history: o.history || [],
        items: o.items || [],
      }));

      // ── 第2批：报表数据（并行）──────────────────────────────
      const y = S.rptYear, m = S.rptMonth;
      const [trend, empRpt, prodRpt, purchD] = await Promise.all([
        apiReports.trend(y, m).catch(() => ({ items: [] })),
        apiReports.employeePerformance(y, m).catch(() => ({ items: [] })),
        apiReports.productRank(y, m).catch(() => ({ items: [] })),
        apiPurchase.list().catch(() => ({ items: [] })),
      ]);

      S.salesTrend = (trend.items || []).filter(Boolean).map(t => t.amount || 0);
      S.staffRank = (empRpt.items || []).filter(Boolean).map(e => ({
        name: e.salesperson || '', amount: e.total_amount || 0,
        orders: e.order_count || 0,
      }));
      S.topProducts = (prodRpt.items || []).filter(Boolean).map(p => ({
        name: p.product || '', times: p.qty || 0, amount: p.amount || 0,
      }));
      S.purchases = (purchD.items || []).map(p => ({
        id: p.id, purchaseNo: p.po_no || '',
        supplierId: p.supplier_id, supplierName: p.supplier_name || '',
        orderIds: p.order_ids || '',
        items: Array.isArray(p.items) ? p.items.map(i => i.product_name || '').join(' ') : (p.items || ''),
        itemsRaw: p.items || [],
        status: p.status || '待采购',
        amount: p.total_amount || p.amount || 0,
        date: p.expected_date || p.order_date || '',
        remark: p.remark || '',
      }));

      // 码表初始化（订单状态）
      S.dictMap.orderStatus = [
        { k: 'created', v: '待确认', c: '#909399' },
        { k: 'confirmed', v: '已核单', c: '#409eff' },
        { k: 'measured', v: '已测量', c: '#67c23a' },
        { k: 'stocked', v: '已备货', c: '#e6a23c' },
        { k: 'processing', v: '加工中', c: '#f56c6c' },
        { k: 'install', v: '待安装', c: '#9c27b0' },
        { k: 'installed', v: '已安装', c: '#1a3a5c' },
        { k: 'completed', v: '已完成', c: '#222' },
      ];

      // 码表：从API加载所有分类
      try {
        const allDicts = await apiDicts.list();
        for (const [cat, items] of Object.entries(allDicts)) {
          if (!S.dictMap[cat]) S.dictMap[cat] = [];
          S.dictMap[cat] = items.map(it => ({ k: it.k, v: it.v, c: it.c || '' }));
        }
        localStorage.setItem('dictMap', JSON.stringify(S.dictMap));
      } catch(e) {
        console.warn('[dict] load failed, using cache', e);
      }

      // 报表当前月
      await __reportModule__.loadReportData();

      console.log('[initAll] DONE. orders=', S.orders.length, 'customers=', S.customers.length, 'products=', S.products.length);
    } catch (e) {
      console.error('initAll error:', e);
    }
  },

  async doLogin() {
    console.log("[doLogin] called, loginLoading=", window.__initModule__?.loginLoading?.value);
    const S = window.__STATE__;
    const M = window.__initModule__;
    const ElMsg = (window.ElementPlus || {}).ElMessage;
    // 模块未就绪时显示提示
    if (!M || !M.loginForm) {
      ElMsg?.error('页面加载中，请稍后刷新再试'); window.alert('页面加载中，请稍后刷新再试');
      console.error('[doLogin] __initModule__ not ready, loginForm:', M?.loginForm);
      return;
    }
    if (!M.loginForm.phone) { ElMsg?.warning('请输入手机号'); return; }
    if (!M.loginForm.password) { ElMsg?.warning('请输入密码'); return; }
    try {
      M.loginLoading.value = true;
      const res = await apiAuth.login(M.loginForm.phone, M.loginForm.password || '');
      const token = res?.token || res?.data?.token;
      if (token) {
        AUTH_TOKEN = token;
        S.authToken = token;
        localStorage.setItem('authToken', token);
        const u = { id: res.user_id || res.data?.user_id, name: res.name || res.data?.name || '员工', role: res.role || res.data?.role || 'staff' };
        S.currentUser = u;
        localStorage.setItem('currentUser', JSON.stringify(u));
        M.loginLoading.value = false;
        S.isLoggedIn = true;
        S.page = 'home';
        S.showNewOrder = false;
        S.activeMenu = 'home';
        M.showLogin.value = false;
        try { ElMsg?.success('登录成功'); } catch(e) {}
        try { document.getElementById('login-overlay').style.display = 'none'; } catch(e) {}
        try { document.querySelector('.main-layout').style.display = 'flex'; } catch(e) {}
        // 加载业务数据
        __initModule__.initAll().catch(e => console.error('[initAll error]', e));
      } else {
        M.loginLoading.value = false;
        const errMsg = res?.message || res?.error || '';
        if (errMsg.includes('401') || errMsg.includes('账号') || errMsg.includes('密码') || errMsg.includes('无效')) {
          ElMsg?.error('手机号或密码错误'); window.alert('手机号或密码错误');
        } else if (errMsg) {
          ElMsg?.error(errMsg);
        } else {
          ElMsg?.error('登录失败，请检查账号密码');
        }
      }
    } catch (e) {
      M.loginLoading.value = false;
      const msg = e?.message || String(e) || '';
      if (msg.includes('Failed to fetch') || msg.includes('NetworkError') || msg.includes('network') || msg.includes('ERR_')) {
        ElMsg?.error('网络连接失败，请检查网络或服务器状态'); window.alert('网络连接失败，请检查网络或服务器状态');
      } else if (msg.includes('401') || msg.includes('Unauthorized')) {
        ElMsg?.error('手机号或密码错误'); window.alert('手机号或密码错误');
      } else if (msg.includes('timeout') || msg.includes('Timeout')) {
        ElMsg?.error('请求超时，请重试'); window.alert('请求超时，请重试');
      } else {
        ElMsg?.error('登录异常: ' + (msg || '未知错误')); window.alert('登录异常: ' + (msg || '未知错误'));
      }
    }
  },

  logout() {
    const S = window.__STATE__;
    S.showNewOrder = false;
    AUTH_TOKEN = '';
    S.currentUser = null;
    S.isLoggedIn = false;
    S.authToken = '';
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    ElementPlus.ElMessage.success('已退出');
  },
};
