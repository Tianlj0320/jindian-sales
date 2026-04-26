/**
 * 仓库管理模块
 * API 规范：docs/API-FORMAT.md §14
 */

window.__warehouseModule__ = {
  async loadWarehouse() {
    const S = window.__STATE__;
    try {
      const d = await apiWarehouse.records();
      const all = d.items || [];
      S.warehouseRecords = all;
      const whMap = {};
      all.forEach(r => {
        const name = r.record_type === 'in' ? '成品库'
          : r.record_type === 'out' ? '发货库' : '在途库';
        if (!whMap[name]) whMap[name] = [];
        whMap[name].push({
          recordId: r.id,
          name: r.product_name || r.product_code || '',
          stock: r.quantity || 0,
          unit: r.unit || '米',
          recordType: r.record_type,
        });
      });
      S.warehouses = Object.entries(whMap).map(([name, items]) => ({ name, items }));
    } catch (e) {
      console.error('loadWarehouse error:', e);
    }
  },

  async saveRecord(S) {
    const f = S.warehouseForm;
    const payload = {
      record_type: f.recordType,
      product_name: f.productName,
      quantity: parseFloat(f.quantity) || 0,
      unit: f.unit,
      remark: f.remark || '',
    };
    try {
      await apiWarehouse.createRecord(payload);
      S.dlgWarehouseRecord = false;
      ElementPlus.ElMessage.success('登记成功');
      await __warehouseModule__.loadWarehouse();
    } catch (e) {
      ElementPlus.ElMessage.error('登记失败');
    }
  },

  async deleteRecord(id) {
    const S = window.__STATE__;
    if (!confirm('确定删除该记录？')) return;
    try {
      await apiWarehouse.deleteRecord(id);
      ElementPlus.ElMessage.success('已删除');
      await __warehouseModule__.loadWarehouse();
    } catch (e) {
      ElementPlus.ElMessage.error('删除失败');
    }
  },
};
