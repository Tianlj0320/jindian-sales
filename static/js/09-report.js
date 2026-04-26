/**
 * 统计报表/财务模块
 * API 规范：docs/API-FORMAT.md §15-18
 */

window.__reportModule__ = {
  async loadReportData() {
    const S = window.__STATE__;
    const y = S.rptYear, m = S.rptMonth;
    const [trend, empRpt, prodRpt, ordData] = await Promise.all([
      apiReports.trend(y, m).catch(() => ({ items: [] })),
      apiReports.employeePerformance(y, m).catch(() => ({ items: [] })),
      apiReports.productRank(y, m).catch(() => ({ items: [] })),
      apiOrders.list({ page: 1, page_size: 100, year: y, month: m }).catch(() => ({ items: [] })),
    ]);
    S.salesTrend = (trend.items || []).filter(Boolean).map(t => t.amount || 0);
    S.staffRank = (empRpt.items || []).filter(Boolean).map(e => ({
      name: e.salesperson || '',
      amount: e.total_amount || 0,
      orders: e.order_count || 0,
    }));
    S.topProducts = (prodRpt.items || []).filter(Boolean).map(p => ({
      name: p.product || '',
      times: p.qty || 0,
      amount: p.amount || 0,
    }));
    S.reportOrders = (ordData.items || []).filter(Boolean).map(o => ({
      orderNo: o.order_no || '',
      customerName: o.customer_name || '',
      orderType: o.order_type || '',
      amount: o.amount || 0,
      status: o.status_label || '',
      statusColor: o.status_color || '#999',
      received: o.received || 0,
      debt: o.debt || 0,
      orderDate: o.order_date || '',
    }));
  },

  async loadFinance() {
    const S = window.__STATE__;
    try {
      const fin = await apiFinance.summary();
      S.financeData = {
        monthRevenue: fin.data?.month_receive || 0,
        monthCost: fin.data?.month_pay || 0,
        monthProfit: (fin.data?.month_receive || 0) - (fin.data?.month_pay || 0),
        totalDebt: fin.data?.total_debt || 0,
        pendingCommission: fin.data?.pending_commission || 0,
      };
    } catch (e) {
      console.error('loadFinance error:', e);
    }
  },
};
