# 🐛 Bug 修复协议

修 Bug 前必读！遵循此协议可以避免「修一处、坏另一处」。

---

## 第一步：定位问题（5分钟）

### 1.1 确认问题模块
- [ ] 明确是哪个功能报错？（订单/客户/产品/财务...）
- [ ] 错误信息是什么？（前端报错 / 后端异常 / 数据不对）
- [ ] 能否复现？（操作步骤）

### 1.2 搜索同类问题
修之前先搜一遍，确认同类问题分布：

```bash
# 例如：修复 orders 的 quote_amount 计算
# 先搜所有文件里有多少处类似逻辑
grep -rn "quote_amount\|amount\|price" app/api/orders.py

# 搜前端对应的字段处理
grep -rn "quoteAmount\|quote_amount" static/js/
```

---

## 第二步：制定修复方案（10分钟）

### 2.1 确认修复范围
一个 Bug 可能影响多个模块，修复方案必须包含：

| 需要检查的模块 | 检查什么 |
|-------------|---------|
| `app/models.py` | 数据库列定义是否正确 |
| `app/schemas.py` | Pydantic 模型字段是否匹配 |
| `app/api/xxx.py` | API 层数据处理逻辑 |
| `app/core/` | 中间件/响应格式/认证 |
| `static/js/` | 前端字段绑定和 API 调用 |

### 2.2 填写修复清单

```markdown
## Bug: [简单描述]
影响模块: orders, finance
同类检查:
- [ ] orders.py 的 quote_amount 计算 ✓
- [ ] finance.py 收款记录是否受影响 ✓
- [ ] reports.py 报表统计是否受影响 ✓
- [ ] 前端静态文件字段名是否一致 ✓
```

---

## 第三步：实施修复

### 3.1 按顺序修改
1. **先改后端**（models → schemas → api）
2. **再改前端**（01-api.js → 具体模块 js）
3. **最后测试**（本地验证）

### 3.2 每次修改后自测
```bash
# 每次修改完，跑一遍冒烟测试
python tests/test_api.py

# 跑模式检查器
python scripts/pattern_checker.py
```

---

## 第四步：提交代码

### 4.1 Git Commit 格式
```
cur-gm@金典软装: [模块] 修复问题描述

问题：什么问题
修复：怎么修的
自检：检查了哪些同类模块（必须列出）
测试：本地测试结果
```

### 4.2 提交前检查清单
- [ ] 同类字段/函数/模式 已全部检查
- [ ] 单元测试通过（`pytest tests/`）
- [ ] 冒烟测试通过（`python tests/test_api.py`）
- [ ] 模式检查器通过（`python scripts/pattern_checker.py`）
- [ ] 无 `print()` 调试语句残留
- [ ] 无 `except:` 裸异常捕获

---

## 常见同类问题快速对照

| 修复项 | 必须同步检查的模块 |
|--------|------------------|
| 修改 `orders` 表字段 | `orders.py`, `finance.py`, `reports.py`, `purchase.py` |
| 修改 `customers` 字段 | `customers.py`, `orders.py` |
| 修改 `products` 字段 | `products.py`, `purchase.py`, `warehouse.py` |
| 修改认证逻辑 | `auth.py`, `middleware.py`, `installer.py` |
| 修改响应格式 | 所有 `app/api/*.py` |
| 修改前端 API 调用 | 所有 `static/js/03-*.js` |

---

## 禁止事项

- ❌ 修 Bug 不检查同类模块
- ❌ 直接 return 裸 dict（用 `success_response()`）
- ❌ 用 `print()` 做调试
- ❌ 用 `except:` 捕获所有异常
- ❌ 不测试就提交
