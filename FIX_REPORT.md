# 修复报告：基础资料模块过滤条件失效

## 问题
基础资料模块（产品资料/客户资料/员工资料/供应商管理）的搜索框和下拉筛选条件无效——输入内容或选择后列表不过滤。

## 根因分析

### 核心问题：get/set 包装的对象属性破坏响应性

原有的绑定写法使用了 **get/set 包装对象**：
```javascript
// 原写法（错误示范）
suppSearch: { get: () => S.suppSearch, set: v => { S.suppSearch = v; } }
```

Vue 的响应式系统通过 `Object.defineProperty` 追踪对 `__STATE__` 对象的属性访问和修改。当 `S.suppSearch` 以**直接字符串值**的形式被模板引用时，Vue 能正确追踪。但以 `get()/set()` 函数包装后：

- Vue 3 的模板直接访问响应式数据时建立依赖追踪
- `get: () => S.suppSearch` 是个普通函数，Vue 看不到内部依赖
- 模板通过 `v-model="suppSearch"` 绑定时，调用 `get()` 只返回当前值，Vue 无法建立响应式依赖
- setter 调用 `S.suppSearch = v` 虽然会修改响应式对象，但 Vue 不知道 `filteredSuppliers` computed 依赖了这个 getter

### 受影响的字段（共 6 个）

| 模块 | 字段 | 位置 |
|------|------|------|
| 供应商管理 | suppSearch, suppTypeF | 行 2585-2586 |
| 客户资料 | customerSearch, customerTypeF | 行 2611-2612 |
| 员工资料 | empSearch, empPositionF | 行 2621-2622 |

### 正确写法的类比：page 双向绑定

`page` 字段使用了正确的响应式写法：
```javascript
// 正确：ref 包装 + 双向 watch
page: (() => {
  const pg = ref(S.page);
  watch(() => S.page, v => { if (pg.value !== v) pg.value = v; });
  watch(pg, v => { S.page = v; });
  return pg;
})()
```
因为 `pg` 是真正的 `ref`，`v-model="page"` 能正确工作。

但 `suppSearch` 等字段使用的是"伪双向绑定"（get/set 函数），在 Vue 3 + Element Plus 的模板编译环境下无法建立正确的响应式依赖链。

## 修复方案

将 get/set 包装对象替换为直接引用 `__STATE__` 属性：

```javascript
// 修复前（错误）
suppSearch: { get: () => S.suppSearch, set: v => { S.suppSearch = v; } }

// 修复后（正确）
suppSearch: S.suppSearch,
```

### 修改位置

**行 2585-2586（供应商）**
```javascript
// 修改前
suppSearch: { get: () => S.suppSearch, set: v => { S.suppSearch = v; } },
suppTypeF: { get: () => S.suppTypeF, set: v => { S.suppTypeF = v; } },

// 修改后
suppSearch: S.suppSearch,
suppTypeF: S.suppTypeF,
```

**行 2611-2612（客户）**
```javascript
// 修改前
customerSearch: { get: () => S.customerSearch, set: v => { S.customerSearch = v; } },
customerTypeF: { get: () => S.customerTypeF, set: v => { S.customerTypeF = v; } },

// 修改后
customerSearch: S.customerSearch,
customerTypeF: S.customerTypeF,
```

**行 2621-2622（员工）**
```javascript
// 修改前
empSearch: { get: () => S.empSearch, set: v => { S.empSearch = v; } },
empPositionF: { get: () => S.empPositionF, set: v => { S.empPositionF = v; } },

// 修改后
empSearch: S.empSearch,
empPositionF: S.empPositionF,
```

## 为什么这样修复有效？

`S` 是 `window.__STATE__` = `Vue.reactive({})` 创建的响应式对象。直接返回 `S.suppSearch` 等于让模板访问响应式对象的直接属性，Vue 能够正确追踪：

1. 模板 `v-model="suppSearch"` → 读写 `S.suppSearch`（直接响应式属性）
2. `filteredSuppliers` computed → 读取 `S.suppSearch` → 正确建立依赖追踪
3. 修改搜索框 → `S.suppSearch` 更新 → computed 自动重算 → 列表更新

## 验证方式

重启服务后访问页面：
1. 进入"供应商管理" → 输入搜索词 → 列表应实时过滤
2. 选择类型下拉 → 列表应按类型过滤
3. 同理验证"客户资料"和"员工资料"