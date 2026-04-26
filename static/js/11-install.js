/**
 * 安装管理模块
 * API 规范：docs/API-FORMAT.md §19
 */

window.__installModule__ = {
  async loadInstallOrders() {
    const S = window.__STATE__;
    try {
      const d = await apiInstall.list();
      S.installOrders = (d.items || []).map(i => ({
        id: i.id,
        insNo: i.ins_no || '',
        orderId: i.order_id,
        orderNo: i.order_no || '',
        customerName: i.customer_name || '',
        address: i.address || '',
        installerName: i.installer_name || '',
        scheduledDate: i.scheduled_date || '',
        status: i.status || '待分配',
      }));
    } catch (e) {
      console.error('loadInstallOrders error:', e);
    }
  },

  async confirmInstall(row) {
    const S = window.__STATE__;
    row.status = '已安装';
    try {
      const installRes = await api('/api/installer/tasks', 'GET').catch(() => ({}));
      const t = (installRes.tasks || []).find(t => t.order_no === (row.orderNo || ''));
      if (t) await apiInstall.complete(t.id, {
        completed_at: new Date().toISOString().slice(0, 19).replace('T', ' '),
        remark: '',
      });
      await apiOrders.updateStatus(row.id, 'installed');
    } catch (e) {
      console.error(e);
    }
    ElementPlus.ElMessage.success('已确认安装完成');
  },
};
