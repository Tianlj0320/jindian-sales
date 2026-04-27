/**
 * 弹窗控制模块（open/save/delete）
 * 所有弹窗的状态定义在 00-base.js 的 __STATE__ 中
 */

window.__dialogsModule__ = {
  // ── 供应商 ─────────────────────────────────────────────
  openSupplierDlg(row, S) {
    S.editingSupplier = row ? { ...row } : null;
    S.sForm = row
      ? { code: row.code || '', name: row.name || '', type: row.type || '布艺',
          contact: row.contact || '', phone: row.phone || '',
          deliveryDays: row.deliveryDays || 7, address: row.address || '',
          payment: row.payment || '' }
      : { code: '', name: '', type: '布艺', contact: '', phone: '',
          deliveryDays: 7, address: '', payment: '' };
    S.dlgSupplier = true;
  },

  async saveSupplier(S) {
    const f = S.sForm;
    const payload = {
      code: f.code, name: f.name, type: f.type || '布艺',
      contact: f.contact || '', phone: f.phone || '',
      delivery_days: f.deliveryDays || 7, address: f.address || '',
      payment: f.payment || '',
    };
    try {
      let d;
      if (S.editingSupplier) {
        d = await apiProducts.updateSupplier(S.editingSupplier.id, payload);
        const idx = S.suppliers.findIndex(s => s.id === S.editingSupplier.id);
        if (idx > -1) S.suppliers.splice(idx, 1, {
          ...S.suppliers[idx],
          code: f.code, name: f.name, type: f.type || '布艺',
          contact: f.contact || '', phone: f.phone || '',
          deliveryDays: f.deliveryDays || 7,
          address: f.address || '', payment: f.payment || '',
        });
      } else {
        d = await apiProducts.createSupplier(payload);
        S.suppliers.push({
          id: d.id, code: d.code || f.code, name: f.name,
          type: f.type || '布艺', contact: f.contact || '',
          phone: f.phone || '', deliveryDays: f.deliveryDays || 7,
          address: f.address || '', payment: f.payment || '',
        });
      }
      S.dlgSupplier = false;
      ElementPlus.ElMessage.success('保存成功');
    } catch (e) {
      console.error('[saveSupplier] error:', e, 'payload:', payload);
      ElementPlus.ElMessage.error('保存失败');
    }
  },

  async delSupplier(row, S) {
    if (!confirm(`确定删除供应商「${row.name}」？`)) return;
    try {
      await apiProducts.deleteSupplier(row.id);
      S.suppliers = S.suppliers.filter(s => s.id !== row.id);
      ElementPlus.ElMessage.success('已删除');
    } catch (e) {
      ElementPlus.ElMessage.error('删除失败');
    }
  },

  // ── 布版 ────────────────────────────────────────────────
  openCategoryDlg(row, S) {
    S.editingCategory = row ? { ...row } : null;
    S.cForm = row
      ? { code: row.code || '', name: row.name || '', supplierId: row.supplierId || '', desc: row.desc || '' }
      : { code: '', name: '', supplierId: '', desc: '' };
    S.dlgCategory = true;
  },

  async saveCategory(S) {
    const f = S.cForm;
    const payload = {
      code: f.code, name: f.name,
      supplier_id: parseInt((f.supplierId || '').replace('s', '')) || 0,
      description: f.desc || '',
    };
    try {
      let d;
      if (S.editingCategory) {
        d = await apiProducts.updateCategory(S.editingCategory.id, payload);
        const idx = S.categories.findIndex(c => c.id === S.editingCategory.id);
        if (idx > -1) S.categories.splice(idx, 1, {
          ...S.categories[idx], ...d,
          supplierId: 's' + (d.supplier_id || 0),
        });
      } else {
        d = await apiProducts.createCategory(payload);
        S.categories.push({
          id: d.id, code: d.code, name: d.name,
          supplierId: 's' + (d.supplier_id || 0),
          desc: d.description || '',
        });
      }
      S.dlgCategory = false;
      ElementPlus.ElMessage.success('保存成功');
    } catch (e) {
      ElementPlus.ElMessage.error('保存失败');
    }
  },

  // ── 产品 ────────────────────────────────────────────────
  openProductDlg(row, S) {
    S.editingProduct = row;
    S.pForm = row
      ? { code: row.code || '', name: row.name || '',
          supplierId: row.supplierId || '', categoryId: row.categoryId || '',
          category: row.category || '窗帘',
          classification: row.classification || '',
          model: row.model || '', material: row.material || row.mat || '',
          width: row.width || 280, weight: row.weight || 0,
          cf: row.cf || 0, price: row.price || 0,
          stock: row.stock || 0, unit: row.unit || '米', remark: '' }
      : { code: '', name: '',
          supplierId: S.suppliers[0]?.id ? 's' + S.suppliers[0].id : '',
          categoryId: '', category: '窗帘', classification: '',
          model: '', material: '', width: 280, weight: 0, cf: 0,
          price: 0, stock: 0, unit: '米', remark: '' };
    S.dlgProduct = true;
  },

  async saveProduct(S) {
    const f = S.pForm;
    if (!f.name) { ElementPlus.ElMessage.warning('请填写产品名称'); return; }
    const payload = {
      code: f.code, name: f.name,
      supplier_id: parseInt((f.supplierId || '').replace('s', '')) || 0,
      category_id: parseInt((f.categoryId || '').replace('c', '')) || 0,
      product_type: f.category, classification: f.classification,
      model: f.model, material: f.material,
      width: f.width, weight: f.weight,
      cf: f.cf || 0, unit_price: f.price,
      stock: f.stock, unit: f.unit, remark: f.remark || '',
    };
    try {
      if (S.editingProduct) {
        const d = await apiProducts.update(S.editingProduct.id, payload);
        const idx = S.products.findIndex(p => p.id === S.editingProduct.id);
        if (idx > -1) S.products.splice(idx, 1, {
          ...S.products[idx],
          id: S.editingProduct.id, code: f.code, name: f.name,
          supplierId: f.supplierId, categoryId: f.categoryId,
          category: f.category, classification: f.classification,
          model: f.model, material: f.material,
          width: f.width, weight: f.weight,
          cf: f.cf || 0, price: f.price,
          stock: f.stock, unit: f.unit, remark: f.remark || '',
        });
        ElementPlus.ElMessage.success('更新成功');
      } else {
        const d = await apiProducts.create(payload);
        S.products.push({
          id: d.id, code: d.code, name: d.name,
          supplierId: f.supplierId,
          categoryId: f.categoryId,
          category: f.category || '窗帘',
          classification: f.classification || '',
          model: f.model || '', material: f.material || '',
          width: f.width || 280, weight: f.weight || 0,
          cf: 0, price: f.price || 0,
          stock: f.stock || 0, unit: f.unit || '米', remark: f.remark || '',
        });
        ElementPlus.ElMessage.success('添加成功');
      }
      S.dlgProduct = false;
    } catch (e) {
      console.error('[saveProduct] error:', e, 'payload:', payload);
      ElementPlus.ElMessage.error('保存失败');
    }
  },

  // 兼容旧名称
  addProduct(S) { return this.saveProduct(S); },

  async delProduct(row, S) {
    if (!confirm(`确定删除产品「${row.name}」？`)) return;
    try {
      await apiProducts.delete(row.id);
      S.products = S.products.filter(p => p.id !== row.id);
      ElementPlus.ElMessage.success('已删除');
    } catch (e) {
      ElementPlus.ElMessage.error('删除失败');
    }
  },

  // ── 采购单弹窗 ──────────────────────────────────────────
  openPurchaseDlg(row, S) {
    S.editingPurchase = row ? { ...row } : null;
    S.purchaseForm = row
      ? { supplierId: row.supplierId ? 's' + row.supplierId : '',
          orderIds: row.orderIds || '', expectedDate: row.date || '',
          status: row.status || '待采购', remark: row.remark || '' }
      : { supplierId: S.suppliers[0] ? 's' + S.suppliers[0].id : '',
          orderIds: '', expectedDate: '', status: '待采购', remark: '' };
    S.dlgPurchase = true;
  },

  async savePurchase(S) {
    const f = S.purchaseForm;
    const sid = parseInt((f.supplierId || '').replace('s', '')) || null;
    const payload = {
      supplier_id: sid,
      order_ids: f.orderIds,
      expected_date: f.expectedDate,
      status: f.status,
      remark: f.remark || '',
    };
    try {
      let d;
      if (S.editingPurchase) {
        d = await api(`/api/purchase-orders/${S.editingPurchase.id}`, 'PATCH', { status: f.status, remark: f.remark || '', expected_date: f.expectedDate });
        const idx = S.purchases.findIndex(p => p.id === S.editingPurchase.id);
        if (idx > -1) S.purchases.splice(idx, 1, { ...S.purchases[idx], ...d });
      } else {
        d = await apiPurchase.create(payload);
        S.purchases.push({
          id: d.id, purchaseNo: d.po_no || '',
          supplierId: sid, supplierName: '',
          orderIds: f.orderIds, items: '', itemsRaw: [],
          status: f.status, amount: 0, date: f.expectedDate, remark: f.remark,
        });
      }
      S.dlgPurchase = false;
      ElementPlus.ElMessage.success('保存成功');
      await __purchaseModule__.loadPurchases();
    } catch (e) {
      ElementPlus.ElMessage.error('保存失败');
    }
  },
};
