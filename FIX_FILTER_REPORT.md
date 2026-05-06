# 基础资料过滤修复报告

**日期：** 2026-05-05
**执行者：** dev-swarm
**模型：** deepseek/deepseek-v4-flash

---

## 问题根因

前端 el-option 下拉的 `:value` 使用 `t.v`（item_value），但 DB 实际存储的值与 dict_items.item_value 不完全匹配，导致"选了条件不过滤"。

| 模块 | 码表 item_value | DB 实际值 | 后果 |
|------|----------------|---------|------|
| 客户类型 | 零售/工程/设计师 | 零售/全屋/个人/设计师 | "工程"匹配不到 |
| 供应商类型 | 面料供应商/辅料供应商/配件供应商 | 面料供应商/配件/辅料供应商/fabric | "配件供应商"匹配不到"配件" |
| 员工职务 | 老板/财务/安装工/经理/导购 | 导购/店长/高级导购等 | "导购"匹配不到"店长" |
| 产品品类 | 窗帘/墙纸墙布/硬包/岩板/辅料 | 窗帘/面料/辅料/curtain等 | 部分匹配失败 |

---

## 修复内容

### Step 1: 码表数据对齐

**commit:** `be35cf3`

**insert_dict_items.py** 新增：
```sql
INSERT OR IGNORE INTO dict_items (category_key, item_key, item_value, sort, enabled) VALUES
  ('customerType', '个人', '个人', 3, 1),
  ('customerType', '全屋', '全屋', 4, 1),
  ('supplierType', '布艺', '布艺', 3, 1),
  ('supplierType', '配件', '配件', 4, 1),
  ('position', '店长', '店长', 2, 1),
  ('position', '高级导购', '高级导购', 3, 1),
  ('productType', '面料', '面料', 5, 1);
```

### Step 2: 前端 el-option :value 改为 item_key

**static/index.html** 修改：

```diff
- <el-option v-for="t in (dictMap.supplierType||[])" ... :value="t.v"/>
+ <el-option v-for="t in (dictMap.supplierType||[])" ... :value="t.k"/>

- <el-option v-for="t in (dictMap.customerType||[])" ... :value="t.v"/>
+ <el-option v-for="t in (dictMap.customerType||[])" ... :value="t.k"/>

- <el-option v-for="t in (dictMap.position||[])" ... :value="t.v"/>
+ <el-option v-for="t in (dictMap.position||[])" ... :value="t.k"/>

- <el-option v-for="t in (dictMap.productType||[])" ... :value="t.v"/>
+ <el-option v-for="t in (dictMap.productType||[])" ... :value="t.k"/>
```

### Step 3: 产品形态过滤

`classification` 字段在 DB 中大量为空，当前过滤逻辑无效。建议后续按 supplier/category 二级过滤替代 classification。

---

## 改动文件

| 文件 | 改动类型 |
|------|---------|
| insert_dict_items.py | 新增（数据修复脚本） |
| static/index.html | 修改 el-option :value |

**Commit:** `be35cf3 fix: change el-option :value from t.v to t.k for filter dropdowns`

---

## 未解决问题

- 产品形态（productForm vs classification）过滤逻辑：classification 字段为空是数据问题，需清理历史数据或改为 supplier/category 二级过滤