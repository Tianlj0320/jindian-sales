/**
 * 产品/供应商/布版模块
 * API 规范：docs/API-FORMAT.md §7-9
 */

window.__productModule__ = {
  async loadAll() {
    const S = window.__STATE__;
    const [sups, cats, prods] = await Promise.all([
      apiProducts.suppliers().catch(() => ({ items: [] })),
      apiProducts.categories().catch(() => ({ items: [] })),
      apiProducts.list().catch(() => ({ items: [] })),
    ]);
    // 供应商
    S.suppliers = (sups.items || []).map(s => ({
      id: s.id,
      code: s.code || '',
      name: s.name || '',
      type: s.type || '',
      contact: s.contact || '',
      phone: s.phone || '',
      deliveryDays: s.delivery_days || 7,       // ← snake_case → camelCase
      address: s.address || '',
      payment: s.payment || '',
    }));
    // 布版分类
    S.categories = (cats.items || []).map(c => ({
      id: c.id,
      code: c.code || '',
      name: c.name || '',
      supplierId: c.supplier_id || 0,
      desc: c.description || '',
    }));
    // 产品
    S.products = (prods.items || []).map(p => ({
      id: p.id,
      code: p.code || '',
      name: p.name || '',
      supplierId: p.supplier_id || 0,
      categoryId: p.category_id || 0,
      category: p.category || p.product_type || '窗帘',
      type: p.product_type || '窗帘',
      classification: p.classification || '',
      model: p.model || '',
      material: p.material || '',
      mat: p.material || '',
      width: p.width || 280,
      weight: p.weight || 0,
      cf: p.cf || 0,
      price: p.unit_price || 0,
      stock: p.stock || 0,
      unit: p.unit || '米',
      remark: p.remark || '',
      series: p.series || '',
    }));
  },

  // ── 计算属性：按供应商分组的布版 ──────────────────────────
  supCategories(S) {
    const m = {};
    (S.categories || []).forEach(c => {
      if (!m[c.supplierId]) m[c.supplierId] = [];
      m[c.supplierId].push(c);
    });
    return m;
  },

  // ── 产品筛选计算属性 ──────────────────────────────────────
  filteredProducts(S) {
    let list = S.products;
    const q = (S.prodSearch || '').toLowerCase();
    if (q) list = list.filter(p =>
      ((p.name || '') + (p.code || '') + (p.category || '') +
        __productModule__.getSupplierName(p.supplierId, S)).toLowerCase().includes(q)
    );
    if (S.prodSupplierF) list = list.filter(p => String(p.supplierId) === String(S.prodSupplierF));
    if (S.prodCatF) list = list.filter(p => String(p.categoryId) === String(S.prodCatF));
    return list;
  },

  getSupplierName(id, S) {
    return (S.suppliers.find(s => s.id === id) || {}).name || '';
  },
  getCatName(id, S) {
    return (S.categories.find(c => c.id === id) || {}).name || '';
  },
};
