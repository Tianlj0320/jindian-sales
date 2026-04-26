/**
 * 客户管理模块
 * API 规范：docs/API-FORMAT.md §10
 */

window.__customerModule__ = {
  async loadCustomers() {
    const S = window.__STATE__;
    try {
      const d = await apiCustomers.list();
      S.customers = (d.items || []).map(c => ({
        id: c.id,
        code: c.id,
        name: c.name || '',
        phone: c.phone || '',
        type: c.type || '零售',
        contact: c.contact || '',
        community: c.community || '',
        address: c.address || '',
        salesperson: c.salesperson || '',
        salespersonId: c.salesperson_id || null,
        source: c.source || '',
        debt: c.debt || 0,
        debtLimit: c.debt_limit || 0,
        remark: '',
      }));
    } catch (e) {
      console.error('loadCustomers error:', e);
    }
  },

  filteredCustomers(S) {
    let list = S.customers;
    if (S.customerSearch) {
      const q = S.customerSearch.toLowerCase();
      list = list.filter(c =>
        c.name.toLowerCase().includes(q) ||
        (c.phone || '').toLowerCase().includes(q) ||
        (c.community || '').toLowerCase().includes(q)
      );
    }
    if (S.customerTypeF) list = list.filter(c => c.type === S.customerTypeF);
    return list;
  },

  async saveCustomer(editing, S) {
    const cuForm = S.cuForm;
    const payload = {
      name: cuForm.name,
      type: cuForm.type || '零售',
      contact: cuForm.contact || '',
      phone: cuForm.phone || '',
      community: cuForm.community || '',
      address: cuForm.address || '',
      salesperson: cuForm.salesperson || '',
      source: cuForm.source || '',
      debt_limit: cuForm.debtLimit || 0,
      remark: cuForm.remark || '',
    };
    try {
      if (editing) {
        const d = await apiCustomers.update(editing.id, payload);
        const idx = S.customers.findIndex(c => c.id === editing.id);
        if (idx > -1) S.customers.splice(idx, 1, { ...S.customers[idx], ...d });
      } else {
        const d = await apiCustomers.create(payload);
        S.customers.push({
          id: d.id, code: d.id, name: d.name, phone: d.phone,
          community: d.community || '', type: d.type || '零售',
          salesperson: d.salesperson || '', address: d.address || '',
          debt: 0, debtLimit: 0, remark: '',
        });
      }
      S.dlgCustomer = false;
      ElementPlus.ElMessage.success('保存成功');
    } catch (e) {
      ElementPlus.ElMessage.error('保存失败');
    }
  },

  async deleteCustomer(row, S) {
    if (!confirm(`确定删除客户「${row.name}」？`)) return;
    try {
      await apiCustomers.delete(row.id);
      S.customers = S.customers.filter(c => c.id !== row.id);
      ElementPlus.ElMessage.success('已删除');
    } catch (e) {
      ElementPlus.ElMessage.error('删除失败');
    }
  },
};
