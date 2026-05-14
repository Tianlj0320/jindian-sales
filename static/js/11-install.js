/**
 * 安装管理模块
 * API 规范：docs/API-FORMAT.md §19
 */

window.__installModule__ = {
  async loadInstallOrders() {
    const S = window.__STATE__;
    try {
      const [d, instRes] = await Promise.all([
        apiInstall.list(),
        apiInstall.listInstallers().catch(() => ({ items: [] })),
      ]);
      S.installers = instRes.items || [];
      S.installOrders = (d.items || []).map(i => ({
        id: i.id,
        insNo: i.ins_no || '',
        orderId: i.order_id,
        orderNo: i.order_no || '',
        customerName: i.customer_name || '',
        address: i.address || '',
        installerId: i.installer_id,
        installerName: i.installer_name || '',
        scheduledDate: i.scheduled_date || '',
        status: i.status || '待分配',
      }));
    } catch (e) {
      console.error('loadInstallOrders error:', e);
    }
  },

  openAssignDlg(row) {
    const M = window.__initModule__;
    M.assigningOrder.value = row;
    M.assignInstallerId.value = row.installerId || '';
    M.dlgAssignInstaller.value = true;
  },

  async doAssignInstaller() {
    const S = window.__STATE__;
    const M = window.__initModule__;
    const row = M.assigningOrder.value;
    const installerId = M.assignInstallerId.value;
    if (!installerId) { ElementPlus.ElMessage.warning('请选择安装工'); return; }
    const inst = (S.installers || []).find(i => String(i.id) === String(installerId));
    try {
      await api(`/api/installation-orders/${row.id}`, 'PATCH', {
        installer_id: Number(installerId),
        installer_name: inst?.name || '',
        status: '已分配',
      });
      row.installerId = Number(installerId);
      row.installerName = inst?.name || '';
      row.status = '已分配';
      M.dlgAssignInstaller.value = false;
      ElementPlus.ElMessage.success('已分配安装工');
    } catch (e) {
      console.error(e);
      ElementPlus.ElMessage.error('分配失败');
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
