/**
 * 员工管理模块
 * API 规范：docs/API-FORMAT.md §11
 */

window.__employeeModule__ = {
  async loadEmployees() {
    const S = window.__STATE__;
    try {
      const d = await apiEmployees.list();
      S.employees = (d.items || []).map(e => ({
        id: e.id,
        code: e.code || '',
        name: e.name || '',
        gender: e.gender || '男',
        phone: e.phone || '',
        position: e.position || '',
        dept: e.department || '',
        maxDiscount: e.max_discount || 1,        // 0.85 → 85折
        roundLimit: e.round_limit || 0,
        status: e.status || '启用',
        hireDate: e.join_date || '',
      }));
    } catch (e) {
      console.error('loadEmployees error:', e);
    }
  },

  filteredEmployees(S) {
    let list = S.employees;
    const q = (S.empSearch || '').toLowerCase();
    if (q) list = list.filter(e =>
      ((e.name || '') + (e.code || '') + (e.phone || '')).toLowerCase().includes(q)
    );
    if (S.empPositionF) list = list.filter(e => e.position === S.empPositionF);
    return list;
  },

  async saveEmployee(editing, S) {
    const f = S.empForm;
    const payload = {
      name: f.name || '',
      gender: f.gender || '男',
      phone: f.phone || '',
      position: f.position || '',
      department: f.dept || '',
      max_discount: f.maxDiscount || 1,
      round_limit: f.roundLimit || 0,
      id_card: f.idCard || '',
      join_date: f.joinDate || '',
      status: f.status || '在职',
      remark: f.remark || '',
    };
    try {
      if (editing) {
        const d = await apiEmployees.update(editing.id, payload);
        const idx = S.employees.findIndex(e => e.id === editing.id);
        if (idx > -1) S.employees.splice(idx, 1, {
          ...S.employees[idx], ...d,
          maxDiscount: d.max_discount || 1,
          roundLimit: d.round_limit || 0,
        });
      } else {
        const d = await apiEmployees.create(payload);
        S.employees.push({
          id: d.id, code: d.code, name: d.name,
          gender: '男', phone: d.phone,
          position: d.position || '', dept: d.department || '',
          maxDiscount: 1, roundLimit: 0,
          status: d.status || '启用',
          hireDate: d.join_date || '',
        });
      }
      S.dlgEmployee = false;
      ElementPlus.ElMessage.success('保存成功');
      await window.__employeeModule__.loadEmployees();  // 刷新列表
    } catch (e) {
      ElementPlus.ElMessage.error('保存失败');
    }
  },
};
