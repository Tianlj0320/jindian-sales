/**
 * 码表管理模块
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

  saveDictItem(editing, S) {
    const diForm = S.diForm;
    const cat = S.dictCat;
    const items = S.dictMap[cat] || [];
    if (!editing) {
      const newK = diForm.k || ('i' + (items.length + 1));
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

  delDictItem(row, S) {
    const cat = S.dictCat;
    const items = S.dictMap[cat] || [];
    S.dictMap[cat] = items.filter(i => i.k !== row.k);
    SLS('dictMap', S.dictMap);
    ElementPlus.ElMessage.success('已删除');
  },
};
