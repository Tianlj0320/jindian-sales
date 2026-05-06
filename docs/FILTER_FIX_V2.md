# 基础资料模块过滤条件修复 V2

## 修复日期
2026-05-03

## 修改文件总览

| 文件 | 修改内容 |
|------|---------|
| `static/js/00-base.js` | 新增 `prodCategoryF`、`prodClassificationF` 到 `__STATE__` |
| `static/js/05-product.js` | `filteredProducts` 增加品类和形态过滤逻辑 |
| `static/index.html` | 产品/客户/员工/供应商页面过滤控件全面升级 |

---

## 1. `static/js/00-base.js`

**行 85-86** — 在 `window.__STATE__` 的产品区块新增两个过滤字段：

```javascript
prodCategoryF: '',       // 产品品类（dictMap.productType 码表值）
prodClassificationF: '', // 产品形态（dictMap.productForm 码表值）
```

---

## 2. `static/js/05-product.js`

**行 77-79** — `filteredProducts` 函数新增两个 AND 条件：

```javascript
if (S.prodCategoryF) list = list.filter(p => p.category === S.prodCategoryF);
if (S.prodClassificationF) list = list.filter(p => p.classification === S.prodClassificationF);
```

---

## 3. `static/index.html` — 各模块过滤控件

### 3.1 产品资料（page='product'）

**行 ~318-333**：搜索框增加 `@keyup.enter`；新增品类、形态两个下拉

```html
<el-input v-model="prodSearch" ... @keyup.enter="prodSearch = prodSearch">
  <!-- 供应商下拉 -->
  <!-- 布版下拉 -->
  <el-select v-model="prodCategoryF" placeholder="品类" ...>
    <el-option v-for="t in (dictMap.productType||[])" .../>
  </el-select>
  <el-select v-model="prodClassificationF" placeholder="形态" ...>
    <el-option v-for="t in (dictMap.productForm||[])" .../>
  </el-select>
```

**行 ~2609-2610**：`return {}` 绑定

```javascript
prodCategoryF: { get: () => S.prodCategoryF, set: v => { S.prodCategoryF = v; } },
prodClassificationF: { get: () => S.prodClassificationF, set: v => { S.prodClassificationF = v; } },
```

### 3.2 客户资料（page='customer'）

**行 ~382-392**：搜索框增加 `@keyup.enter`；客户类型下拉改为 dictMap 取值

```html
<el-input v-model="customerSearch" ... @keyup.enter="customerSearch = customerSearch">
  <el-select v-model="customerTypeF" ...>
    <el-option v-for="t in (dictMap.customerType||[])" :key="t.k" :label="t.v" :value="t.v"/>
  </el-select>
```

### 3.3 员工资料（page='employee'）

**行 ~435-440**：搜索框增加 `@keyup.enter`；职务下拉改为 dictMap.position 取值

```html
<el-input v-model="empSearch" ... @keyup.enter="empSearch = empSearch">
  <el-select v-model="empPositionF" ...>
    <el-option v-for="t in (dictMap.position||[])" :key="t.k" :label="t.v" :value="t.v"/>
  </el-select>
```

### 3.4 供应商管理（page='suppliers'）

**行 ~488**：搜索框增加 `@keyup.enter`（供应商类型下拉已是 dictMap，无需修改）

```html
<el-input v-model="suppSearch" ... @keyup.enter="suppSearch = suppSearch">
```

---

## 验证要点

1. **产品资料**：供应商+布版+品类+形态四个下拉联动筛选，搜索框回车触发
2. **客户资料**：类型下拉来自 dictMap.customerType，搜索框回车触发
3. **员工资料**：职务下拉来自 dictMap.position，搜索框回车触发
4. **供应商管理**：类型下拉来自 dictMap.supplierType，搜索框回车触发
5. 所有下拉均从码表 dictMap 取值，非硬编码；搜索框支持回车触发过滤