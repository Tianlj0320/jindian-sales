# 金典软装销售系统 V4.0 — 开发任务清单

> 按阶段（Phase）组织，每个功能点标注优先级和预计工时

---

## Phase 1：基础设施 & 核心数据（预计 3 周）

### 1.1 项目初始化

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| 创建 FastAPI 项目骨架（目录结构/配置文件） | P0 | 4h | system |
| 配置 SQLAlchemy 2.0 数据库连接（SQLite 开发环境） | P0 | 2h | system |
| 配置 Alembic 数据库迁移工具 | P0 | 2h | system |
| 配置 JWT 认证中间件 | P0 | 4h | system |
| 配置 CORS 中间件 | P1 | 1h | system |
| 配置日志系统 | P1 | 2h | system |
| 统一异常处理中间件 | P1 | 2h | system |

### 1.2 用户与权限

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| users 表设计与模型 | P0 | 2h | system |
| 用户登录接口 POST /api/auth/login | P0 | 4h | system |
| JWT Token 签发与验证 | P0 | 3h | system |
| 获取当前用户 GET /api/auth/me | P1 | 1h | system |
| 退出登录 POST /api/auth/logout | P1 | 1h | system |
| 用户 CRUD 接口 | P1 | 6h | system |
| 操作日志中间件（记录所有写请求） | P1 | 4h | system |
| 角色权限设计（admin/manager/staff） | P1 | 4h | system |

### 1.3 通用字典与基础数据

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| 通用字典接口 GET /api/system/dict/{type} | P1 | 3h | system |
| suppliers 表设计与接口 | P1 | 4h | system |
| 供应商 CRUD 接口 | P1 | 4h | system |

---

## Phase 2：核心业务基础模块（预计 4 周）

### 2.1 客户管理

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| customers 表设计与模型 | P0 | 2h | customers |
| 客户 CRUD 接口（含分页/搜索） | P0 | 6h | customers |
| 客户跟进记录 followup_records 表 | P1 | 2h | customers |
| 客户跟进记录接口（增/查） | P1 | 4h | customers |
| 客户跟进提醒（基于 next_followup_date） | P2 | 4h | customers |
| 客户合并（去重） | P2 | 4h | customers |

### 2.2 产品管理

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| products 表设计与模型 | P0 | 2h | products |
| 产品分类管理（category/sub_category） | P0 | 3h | products |
| 产品 CRUD 接口（含搜索/筛选） | P0 | 6h | products |
| 产品上下架管理 | P1 | 2h | products |
| 产品多图上传（图片路径存储） | P1 | 4h | products |
| 产品快速搜索（关键词联想） | P2 | 3h | products |
| 产品成本价/最低售价保护逻辑 | P1 | 3h | products |

### 2.3 仓库管理

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| warehouse 表设计与模型 | P0 | 2h | warehouse |
| 仓库 CRUD 接口 | P0 | 4h | warehouse |
| inventory 表设计与模型 | P0 | 3h | warehouse |
| inventory_flow 表设计与模型 | P0 | 3h | warehouse |
| 仓库库存查询接口 | P0 | 4h | warehouse |
| 库存流水查询接口 | P0 | 4h | warehouse |
| 库存盘点调整接口 | P1 | 4h | warehouse |
| 库存预警接口（低于 safety_stock） | P1 | 3h | warehouse |
| 批次管理（batch_no） | P1 | 4h | warehouse |

### 2.4 采购管理

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| purchase_orders 表设计与模型 | P0 | 2h | purchase |
| purchase_items 表设计与模型 | P0 | 2h | purchase |
| 采购单 CRUD 接口 | P0 | 6h | purchase |
| 采购单明细管理 | P0 | 4h | purchase |
| 采购审核流程（待审核→已审核） | P1 | 3h | purchase |
| 采购入库确认（自动更新 inventory） | P0 | 6h | purchase |
| 采购入库联动生成应付账款 | P1 | 4h | purchase, finance |
| 采购退货（红字入库） | P2 | 4h | purchase |
| 采购统计报表 | P2 | 4h | purchase, reports |

---

## Phase 3：核心业务流程（预计 5 周）

### 3.1 销售订单

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| orders 表设计与模型 | P0 | 2h | orders |
| order_items 表设计与模型 | P0 | 2h | orders |
| 订单创建接口（含明细批量写入） | P0 | 8h | orders |
| 订单号自动生成（日期+序号） | P0 | 2h | orders |
| 订单明细自动计算（面积×单价+加工费） | P0 | 4h | orders |
| 订单总价/折扣/实付金额计算 | P0 | 3h | orders |
| 订单列表查询（多条件+分页） | P0 | 4h | orders |
| 订单详情（含明细/安装单/应收款关联） | P0 | 4h | orders |
| 订单状态流转（状态机） | P0 | 6h | orders |
| 订单变更（含明细增删改） | P1 | 6h | orders |
| 订单取消（含库存回滚逻辑） | P1 | 6h | orders |
| 订单测量管理（测量人员/日期/状态） | P1 | 4h | orders |
| 订单送货管理（送货日期/状态） | P1 | 4h | orders |
| 订单收款记录（部分付款场景） | P0 | 5h | orders |
| 订单导出 Excel | P1 | 4h | orders |
| 订单快速复制 | P2 | 3h | orders |

### 3.2 安装管理

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| install_teams 表设计与模型 | P0 | 2h | installation |
| installers 表设计与模型 | P0 | 2h | installation |
| 安装队 CRUD 接口 | P0 | 4h | installation |
| 安装人员 CRUD 接口 | P0 | 4h | installation |
| 安装队成员管理（增删队员） | P0 | 4h | installation |
| installation_orders 表设计与模型 | P0 | 2h | installation |
| 安装单 CRUD 接口 | P0 | 6h | installation |
| 安装单与订单关联创建 | P0 | 4h | installation |
| 安装时间排程（按安装队/日期） | P1 | 6h | installation |
| 安装状态流转 | P0 | 4h | installation |
| 安装实际时间记录 | P1 | 3h | installation |
| 安装质量检查 | P1 | 3h | installation |
| 安装前后照片上传 | P1 | 4h | installation |
| 安装费用计算（人工费+材料费） | P0 | 3h | installation |
| 安装工人日历（查看空闲时间） | P2 | 6h | installation |
| 安装完工通知（更新订单生产状态） | P1 | 3h | installation |

### 3.3 生产反馈

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| production_feedback 表设计 | P1 | 2h | production |
| 生产工序管理（裁剪/缝制/打孔/整烫） | P1 | 3h | production |
| 生产进度查询（按订单/按工序） | P1 | 4h | production |
| 生产完成自动更新订单生产状态 | P1 | 4h | production |

### 3.4 财务模块

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| finance_receivables 表设计与模型 | P0 | 2h | finance |
| finance_payables 表设计与模型 | P0 | 2h | finance |
| finance_expenses 表设计与模型 | P0 | 2h | finance |
| 订单完成后自动生成应收款记录 | P0 | 4h | finance |
| 安装单完成后自动生成应付款记录 | P0 | 4h | finance |
| 采购入库后生成应付款记录 | P1 | 4h | finance |
| 应收款收款确认接口 | P0 | 4h | finance |
| 应付账款付款确认接口 | P0 | 4h | finance |
| 费用记录 CRUD | P1 | 6h | finance |
| 费用审批流程 | P2 | 6h | finance |
| 经营概况实时查询接口 | P1 | 4h | finance |
| 付款凭证上传 | P2 | 3h | finance |

---

## Phase 4：报表与分析（预计 2 周）

### 4.1 销售报表

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| 销售汇总报表（按时段/人员/产品） | P1 | 6h | reports |
| 客户分析报表（新客户/复购/流失） | P2 | 6h | reports |
| 产品销售排行 | P1 | 4h | reports |
| 产品销售趋势（按月/季度） | P2 | 4h | reports |

### 4.2 财务报表

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| 应收账款账龄分析 | P1 | 5h | reports |
| 应付账款账龄分析 | P1 | 5h | reports |
| 月度收支汇总 | P1 | 4h | reports |
| 利润统计（收入-成本-费用） | P1 | 6h | reports |

### 4.3 库存报表

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| 库存预警报表 | P1 | 4h | reports |
| 库存流水汇总 | P1 | 4h | reports |
| 库存周转分析 | P2 | 6h | reports |

### 4.4 安装报表

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| 安装工工作量统计 | P2 | 4h | reports |
| 安装质量统计 | P2 | 4h | reports |

---

## Phase 5：前端开发（预计 6 周，与后端并行）

> 前端采用原生 JavaScript，预计分模块逐步交付

| 功能模块 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| 前端项目骨架（HTML/CSS/JS 分离） | P0 | 4h | 前端 |
| 登录页面 | P0 | 4h | 前端 |
| 主框架布局（侧边栏+顶部导航） | P0 | 8h | 前端 |
| 客户管理页面（列表+新建+编辑） | P0 | 16h | customers |
| 客户跟进记录页面 | P1 | 8h | customers |
| 产品管理页面 | P0 | 16h | products |
| 订单管理页面（列表+详情+新建） | P0 | 24h | orders |
| 订单明细编辑（多行表格） | P0 | 16h | orders |
| 安装单管理页面 | P1 | 16h | installation |
| 采购管理页面 | P1 | 16h | purchase |
| 仓库管理页面 | P1 | 12h | warehouse |
| 财务收款页面 | P1 | 16h | finance |
| 财务报表页面 | P2 | 20h | reports |
| 公共组件（弹窗/分页/表格） | P0 | 20h | 前端 |
| 全局样式优化 | P1 | 12h | 前端 |

---

## Phase 6：集成与优化（预计 2 周）

| 功能名称 | 优先级 | 工时 | 关联模块 |
|----------|--------|------|----------|
| 后端接口联调（所有端到端测试） | P0 | 16h | 全模块 |
| 前端与后端接口对接 | P0 | 16h | 全模块 |
| 订单全流程测试（创建→生产→安装→收款） | P0 | 12h | 全模块 |
| 数据迁移（v3.0 数据导入 v4.0） | P1 | 16h | system |
| 性能优化（数据库索引/查询优化） | P1 | 12h | system |
| PostgreSQL 生产环境切换 | P1 | 8h | system |
| 部署文档编写 | P1 | 4h | docs |
| 用户手册编写 | P1 | 12h | docs |

---

## 任务统计汇总

| 阶段 | 功能点数 | 预计工时 |
|------|----------|----------|
| Phase 1：基础设施 | 15 | ~40h |
| Phase 2：基础模块 | 23 | ~70h |
| Phase 3：核心流程 | 37 | ~120h |
| Phase 4：报表分析 | 14 | ~55h |
| Phase 5：前端开发 | 19 | ~200h |
| Phase 6：集成优化 | 7 | ~84h |
| **合计** | **~115** | **~569h** |

---

## 里程碑

| 里程碑 | 完成标准 | 对应 Phase |
|--------|----------|------------|
| M1：可运行骨架 | 项目启动，认证可用 | Phase 1 |
| M2：基础数据可用 | 客户/产品/仓库/采购 CRUD | Phase 2 |
| M3：订单流程闭环 | 订单→安装→财务全流程 | Phase 3 |
| M4：报表可用 | 核心报表均可查看 | Phase 4 |
| M5：前端集成 | 前后端联调完成 | Phase 5 |
| M6：生产上线 | 部署文档+数据迁移+上线 | Phase 6 |
