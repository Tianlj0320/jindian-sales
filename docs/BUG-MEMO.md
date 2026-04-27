# Bug Memo — V3.0 调试记录

> 记录本次调试过程中发现的所有 bug 及根因，避免重蹈覆辙。

---

## 一、Vue 3 响应式系统相关

### 1. computed 只读陷阱 ⚠️ 重要
**文件：** `15-init.js` + 模板

**错误写法：**
```javascript
// ❌ 错误：computed 返回的是只读 Proxy，模板里无法写入
const loginLoading = computed(() => S.loginLoading);
loginForm: computed(() => S.loginForm),

// v-model 写入只读 computed → 无任何反应，DOM 不更新
<el-form :model="loginForm">  <!-- 只读！ -->
<el-form-item v-model="loginForm.phone">  <!-- 失败！ -->
```

**正确写法：**
```javascript
// ✅ 正确：用 ref 存储，用 watch 同步到 S
const loginLoading = ref(false);
watch(() => S.loginLoading, v => { loginLoading.value = v; });
watch(loginLoading, v => { S.loginLoading = v; });

// ✅ 或者直接用 S 的属性，但不要包 computed
// 模板直接用 S.xxx（S 是 reactive，Vue 3 会自动解包）
```

**影响范围：** 登录表单、loading 状态、showLogin 弹窗控制。

---

### 2. getter/setter 对象作为 Vue prop 传递 ⚠️ 重要
**文件：** `index.html`（多处）

**错误写法：**
```javascript
// ❌ 错误：getter/setter 对象不是原始值
activeMenu: { get: () => S.activeMenu, set: v => { S.activeMenu = v; } },

// 模板中：
<el-menu :default-active="activeMenu">  <!-- 期望 String，传入了 Object -->
```

**症状：**
- Vue warn: `Invalid prop: type check failed for prop "defaultActive". Expected String with value "[object Object]", got Object`
- ElementPlus el-menu / el-drawer / el-select 无法正常工作

**正确写法：**
```javascript
// ✅ 方案 A：模板用 computed 返回原始值
activeMenuStr: computed(() => S.activeMenu || ''),
// 模板：:default-active="activeMenuStr"

// ✅ 方案 B：plain ref + 双 watch
activeMenu: (() => {
  const am = ref(S.activeMenu);
  watch(() => S.activeMenu, v => { if (am.value !== v) am.value = v; });
  watch(am, v => { S.activeMenu = v; });
  return am;
})();
```

---

### 3. ref 双向循环覆盖（page 状态卡死） ⚠️ 重要
**文件：** `index.html` — `page` 属性的 getter/setter

**错误写法：**
```javascript
// ❌ 错误：watch(page) 每次把 page.value 写回 S.page，S.page 又触发 watch(page)
page: { get: () => S.page, set: v => { S.page = v; } },

// 登录后 S.page='home'，但 page getter 读到 S.page 初始值 undefined
// → 页面永远停在初始状态（白屏）
```

**根因分析：**
- `page` 在 setup() 开头定义为 `ref(S.page)`（初始 undefined）
- getter 每次返回 S.page（初始 undefined/''）
- setter 每次把值写回 S.page，触发 watcher
- watcher 再把 S.page 同步到 page.value
- 形成循环：S.page 被覆盖回初始值 → 页面卡死

**正确写法（最终方案）：**
```javascript
// ✅ ref + 单向 watch：只从 S.page 同步到 pg.value，禁止反向写回
page: (() => {
  const pg = ref(S.page);
  watch(() => S.page, v => { if (pg.value !== v) pg.value = v; });
  watch(pg, v => { S.page = v; }); // 写操作直接改 S.page
  return pg;
})(),

// 登录成功后：
S.page = 'home';  // 不要用 page.value = 'home'
S.activeMenu = 'home';
```

---

## 二、菜单导航相关

### 4. el-sub-menu 没有 index 属性
**文件：** `index.html` — 左侧导航菜单

**症状：** 点击基础资料的子菜单（供应商/产品/客户等），`@select` 事件收到的 key 是 `null`，页面不跳转。

**原因：** `el-menu-item` 有 `index`，但 `el-sub-menu` 也有 `index` 属性时才会触发 `@select`。子菜单的 `index` 写在子项 `el-menu-item` 上，不在父级 `el-sub-menu` 上。

**修复：** 基础资料展开时，子项 `el-menu-item` 全部加上 `index="base-X"` 属性。

---

### 5. 内联 @select 处理函数过于复杂
**文件：** `index.html` — 移动端 drawer 菜单

**错误写法：**
```html
<!-- ❌ 超过 Vue 模板一行最大长度，且 page.value= 在 getter/setter 场景下无效 -->
@select="(k)=>{const pm={...};if(k!=='basic'){page.value=pm[k];...}else{page.value='product';}...}"
```

**正确写法：**
```html
<!-- ✅ 抽到 JS 里 -->
@select="handleNav"
```

```javascript
const handleNav = k => {
  const navMap = { home:'home', product:'product', ... };
  if (k !== 'basic') {
    S.page = navMap[k] || k;
    S.activeMenu = k;
  } else {
    S.page = 'product';
    S.activeMenu = 'product';
  }
};
```

---

## 三、码表管理模块

### 6. dictCat 作为 el-menu default-active 传入 getter/setter 对象
**文件：** `index.html` — 码表管理页

**症状：** 码表管理的分类菜单只能显示"订单状态"，切换到其他分类无效；Console 有 `[Vue warn]: Invalid prop`。

**根因：** 同 Bug #2。`dictCat` 是 `{ get: () => S.dictCat, set: v => { S.dictCat = v; } }`，el-menu 收到了对象而不是字符串。

**修复：**
```javascript
dictCat: { get: () => S.dictCat, set: v => { S.dictCat = v; } },
dictCatStr: computed(() => S.dictCat || ''),  // 纯字符串

// 模板：
<el-menu :default-active="dictCatStr" @select="setDictCat($event)">

// JS：
setDictCat: k => { S.dictCat = k; },
```

---

### 7. dict type prop 检查过严
**文件：** `15-init.js` — dict 数据结构

**症状：** Console 报错 `Error parsing JSON: Key 'type': expected String but got Object`。

**原因：** `dictCat` 字段在 reactive state 中是对象（因为 Vue reactive 会把 `{}` 包成 Proxy），而 `dictType: { type: String }` prop 校验发现传入的是对象不是字符串。

**修复：** 去掉 dict type 的 prop type 校验，或改为 `type: Object`。

---

## 四、登录流程相关

### 8. 登录成功后未设置 S.page
**文件：** `15-init.js`

**症状：** 登录页消失，主内容区显示白屏（因为 `v-if="page==='home'"` 条件不满足）。

**修复：** 登录成功后：
```javascript
S.isLoggedIn = true;
S.page = 'home';        // ← 必须设置
S.activeMenu = 'home';  // ← 菜单高亮也要设置
```

自动登录（刷新页）也要同样处理。

---

### 9. 自动登录代码在 setup() 外部执行
**文件：** `index.html` 底部 `<script>` 部分

**症状：** 刷新页面后 `S.page` 没有被设置为 `'home'`，主内容区白屏。

**原因：** 登录保护逻辑在 `setup()` return 之后的 `<script>` 块里执行，这里对 `S.page` 的修改没有触发 Vue 响应式更新（因为不在 reactive 上下文中）。

**修复：** 把 `S.page = 'home'` 放在 `setup()` 内部，或通过 `watch` 在 `isLoggedIn` 变化时设置。

---

## 五、ElementPlus 组件相关

### 10. el-drawer modelValue prop 类型
**文件：** `index.html`

**症状：** `[Vue warn]: Invalid prop: type check failed for prop "modelValue". Expected Boolean, got Object`

**原因：** `drawerVisible` 传入的是 getter/setter 对象，`el-drawer` 期望 Boolean。

**修复：** 改为 plain `ref(false)`：
```javascript
drawerVisible: ref(false),
```
同时模板中所有修改 drawerVisible 的地方用 `S.drawerVisible = false`（因为 `el-drawer v-model="drawerVisible"` 绑定的是组件内部状态，不能直接双向绑定到 S.drawerVisible）。

---

## 六、已知的架构问题（暂未修复）

### 11. 老板账号 password_hash 缺失
**文件：** 数据库 `employees` 表

**症状：** 老板账号 `13900000001` 的 `password_hash` 字段为 NULL，导致无法登录（或登录逻辑需特殊处理）。

**状态：** ⚠️ 未修复

---

### 12. 前端 truck 图标缺失
**文件：** `static/index.html`

**症状：** 某些页面的 truck（货车）图标显示为空白方块。

**状态：** ⚠️ 未修复

---

## 七、调试方法备忘

### 如何确认是哪个 bug
1. **白屏无数据** → 先看 Console 有没有 Vue warn/error
2. **菜单点击无反应** → 检查 el-menu 的 `@select` 是否触发，el-menu-item 有无 `index` 属性
3. **下拉菜单/弹窗不显示** → 检查 `v-model` 绑定的值是否是 plain primitive（不是 getter/setter）
4. **数据变了页面不变** → 检查是否在模板中给 computed 或 getter/setter 赋值（computed 只读）
5. **控制台报 prop type warning** → 说明传入了错误类型的对象，找到那个 prop 的来源改成原始值

### 关键调试命令
```javascript
// 浏览器 F12 Console：
localStorage.clear()  // 清除缓存，重新登录
window.__STATE__.page  // 当前页面
window.__STATE__.dictCat  // 码表当前分类
window.__STATE__.orders.length  // 订单数量
```

---

## 版本历史

| 日期 | 版本 | 主要修复 |
|------|------|---------|
| 2026-04-26 | v3.0 | 页面导航状态异常、码表切换、登录流程 |
| 2026-04-25 | v2.5 | JS 模块化重构 |
| 2026-04-21 | v2.4 | 初始稳定版 |

---

## 八、API 方法不一致问题（2026-04-27 发现并修复）

### 13. 登录函数 loginForm 访问路径错误 ⚠️ 已修复
**文件：** `static/js/15-init.js`

**根因**：`M.loginForm.value.phone` 访问了 `loginForm.value.phone`，但 `loginForm` 本身是 ref（暴露给 `__initModule__` 时 Vue 已自动解包），所以 `.value` 是 `null`。

**修复**：
```javascript
// ❌ 错误
if (!M.loginForm.value.phone) { ... }
const res = await apiAuth.login(M.loginForm.value.phone, M.loginForm.value.password || '');

// ✅ 正确
if (!M.loginForm.phone) { ... }
const res = await apiAuth.login(M.loginForm.phone, M.loginForm.password || '');
```

---

### 14. 产品模块无编辑功能 ⚠️ 已修复
**文件：** `static/js/14-dialogs.js`, `static/js/01-api.js`, `app/api/products.py`

**问题**：
- 前端有 `addProduct` 但没有 `updateProduct`
- 后端没有 PUT `/api/products/{id}` 端点

**修复**：
1. 后端添加 `PUT /api/products/{product_id}` 端点
2. 前端添加 `apiProducts.update()` 方法
3. 将 `addProduct` 改名为 `saveProduct`，支持新增和编辑两种模式

---

### 15. 分类模块无编辑功能 ⚠️ 已修复
**文件：** `static/js/01-api.js`, `app/api/products.py`

**问题**：
- 前端 `updateCategory` 使用 POST 方法
- 后端没有 PUT `/api/products/categories/{id}` 端点

**修复**：
1. 后端添加 `PUT /api/products/categories/{category_id}` 端点
2. 前端 `updateCategory` 改为 PUT 方法

---

### 16. 客户/员工更新 API 方法错误 ⚠️ 已修复
**文件：** `static/js/01-api.js`

**问题**：前端 `update` 方法使用 POST，但后端期望 PUT

**修复**：将 `apiCustomers.update` 和 `apiEmployees.update` 从 POST 改为 PUT

---

### 17. 采购单更新 API 方法不匹配 ⚠️ 已修复
**文件：** `static/js/14-dialogs.js`

**问题**：前端使用 PUT 调用 `/api/purchase-orders/{id}`，但后端只有 PATCH

**修复**：将调用改为 PATCH 方法

---

## 九、数据库迁移

### 18. products 表缺少 remark 列 ⚠️ 已修复
**文件：** `migrations/add_product_remark.sql`

**问题**：Product 模型添加了 remark 字段，但数据库表没有该列

**修复**：
```sql
ALTER TABLE products ADD COLUMN remark VARCHAR(500) DEFAULT '';
```

---

## 十、防重复 Bug 规范

### 开发规范：添加新 API 端点时
1. 确保前端 API 调用方法（GET/POST/PUT/PATCH/DELETE）与后端一致
2. 确保前端传字段名与后端期望一致（snake_case vs camelCase）
3. 确保数据库表结构与 Model 一致
4. 提交前在本地测试 API 调用

### 开发规范：添加新的 Dialog/Form 时
1. 表单值用 `form.xxx` 而非 `form.value.xxx`（ref 在 setup return 时已解包）
2. 保存函数检查 `editingXxx` 是否存在来决定是新增还是更新
3. 保存成功后正确更新列表数据

---

## 七、Day 1 (4月27日) 新增修复

### 28. 客户保存后列表不刷新
**文件：** `06-customer.js`
**原因：** 保存后未调用 `loadCustomers()` 刷新
**修复：** 保存成功后添加 `await window.__customerModule__.loadCustomers()`

### 29. 员工表单字段缺失
**文件：** `index.html` + `07-employee.js`
**原因：** 员工编辑弹窗的 `empForm` 缺少 gender/dept/code/maxDiscount/roundLimit 字段映射
**修复：** 补充完整字段映射和 payload 字段

### 30. 员工保存后列表不刷新
**文件：** `07-employee.js`
**原因：** 保存后未调用 `loadEmployees()` 刷新
**修复：** 保存成功后添加 `await window.__employeeModule__.loadEmployees()`

### 31. 财务摘要 fin.data 多层访问
**文件：** `09-report.js`
**原因：** `apiFinance.summary()` 返回 `data` 对象而非外层包装，前端错误访问 `fin.data?.month_receive`
**修复：** 改为 `fin.month_receive || 0`

### 32. 财务 API 缺少 receive/pay/expense 方法
**文件：** `01-api.js`
**原因：** 前端 `apiFinance` 只有 `summary()`，缺少收/付/费用记录方法
**修复：** 补充 `receive/pay/expense` 三个 POST 方法

### 33. 仓库列表字段名错误
**文件：** `10-warehouse.js`
**原因：** API 返回 `qty`，前端映射为 `quantity`
**修复：** `r.quantity` → `r.qty`

### 34. 中间件拦截 track/installer/sms 公开 API
**文件：** `app/middleware.py`
**原因：** `/api/track`、`/api/installer`、`/api/sms` 被 `AuthMiddleware` 拦截，需要登录
**修复：** 添加这三个路径到 `ALLOWED_PATHS`

### 35. 订单创建 quote_amount 计算错误
**文件：** `app/api/orders.py`
**原因：** 用 `price * qty` 计算，应该用前端已计算的 `item.amount`（含折扣）
**修复：** `quote_amount = sum(i.amount for i in items) + sum(m.amount for m in materials)`

### 36. 产品列表 API 缺少 supplier_id/category_id
**文件：** `app/api/products.py` + `app/schemas.py`
**原因：** `ProductListItem` schema 缺少这两个字段
**修复：** 补充到 schema 和 API 返回值

### 37. 报表模块 API 响应 data 对象访问
**文件：** `09-report.js`
**原因：** trend/empRpt/prodRpt 响应是 `{success, data: {items}}`，前端访问 `trend.items`
**修复：** 改为 `trend.data?.items`

### 38. 产品 remark 字段未保存
**文件：** `app/api/products.py`
**原因：** `update_product` 中缺少 `cf` 和 `remark` 字段处理
**修复：** 已添加 `remark` 字段处理（cf 字段待确认）

### 39. 安装工 API 路径测试注意
**文件：** -
**说明：** 安装工任务列表是 `/api/installer/tasks`，不是 `/api/installation-orders`（后者是管理端用）

### 40. 订单编辑功能缺失
**文件：** `index.html`
**状态：** ⚠️ 未修复（功能缺失）
**说明：** 目前只有新建订单功能，没有编辑已有订单的功能。订单状态通过下拉框切换状态 key 来更新状态。

