/**
 * 码表管理模块
 *
 * P1：码表前端持久化
 * 原来 saveDictItem / delDictItem 只写 localStorage
 * 现在改为：先调后端 API 持久化，再更新本地状态并同步 localStorage
 */

window.__dictModule__ = {
  get dictCatLabel() {
    const S = window.__STATE__;
    return (S.dictCats.find(d => d.k === S.dictCat) || {}).l || '';
  },

  get dictItems() {
    const S = window.__STATE__;
    return S.dictMap[S.dictCat] || [];
  },

  get orderStatusAll() {
    const S = window.__STATE__;
    return S.dictMap.orderStatus || [];
  },

  async saveDictItem(editing, S) {
    const diForm = S.diForm;
    const cat = S.dictCat;
    const items = S.dictMap[cat] || [];

    const payload = {
      category_key: cat,
      item_key: editing ? editing.k : (diForm.k || ('i' + (items.length + 1))),
      item_value: diForm.v || '',
      color: diForm.c || '',
    };

    try {
      if (!editing) {
        await apiDicts.createItem(payload);
      } else {
        await apiDicts.updateItem(payload);
      }
    } catch (e) {
      console.error('[saveDictItem] API error:', e);
      // 即使 API 失败，仍保留本地状态（本地优先，降级处理）
    }

    // 本地状态更新
    if (!editing) {
      const newK = payload.item_key;
      S.dictMap[cat] = [...items, { k: newK, v: diForm.v, c: diForm.c }];
    } else {
      const idx = editing.idx;
      if (idx > -1) {
        items[idx] = { k: editing.k, v: diForm.v, c: diForm.c };
        S.dictMap[cat] = [...items];
      }
    }
    SLS('dictMap', S.dictMap);
    S.dlgDictItem = false;
    ElementPlus.ElMessage.success('保存成功');
  },

  async delDictItem(row, S) {
    const cat = S.dictCat;
    const items = S.dictMap[cat] || [];

    try {
      await apiDicts.deleteItem(cat, row.k);
    } catch (e) {
      console.error('[delDictItem] API error:', e);
      // 即使 API 失败，仍保留本地状态
    }

    S.dictMap[cat] = items.filter(i => i.k !== row.k);
    SLS('dictMap', S.dictMap);
    ElementPlus.ElMessage.success('已删除');
  },
};
