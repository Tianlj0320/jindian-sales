/**
 * 首页仪表盘模块
 * API 规范：docs/API-FORMAT.md §2
 */

window.__homeModule__ = {
  async loadDashboard() {
    const S = window.__STATE__;
    try {
      const d = await apiDashboard.getSummary();
      S.stats = {
        todayOrders: d.today_orders || 0,
        monthSales: d.month_sales || 0,
        pendingInstall: d.pending_install || 0,
        overdueOrders: d.overdue_orders || 0,
        pendingPayment: d.pending_payment || 0,
        totalCustomers: d.total_customers || 0,
      };
    } catch (e) {
      console.error('loadDashboard error:', e);
    }
  },
};
