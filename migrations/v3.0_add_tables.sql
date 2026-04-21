-- V3.0 数据模型迁移脚本
-- 执行前请备份数据库！
-- sqlite3 sales.db < migrations/v3.0_add_tables.sql

-- ============================================================
-- 1. order_items 表：新增 supplier_id, material_type
-- ============================================================
ALTER TABLE order_items ADD COLUMN supplier_id INTEGER;
ALTER TABLE order_items ADD COLUMN material_type VARCHAR(20) DEFAULT '主料';  -- '主料' / '辅料'

-- ============================================================
-- 2. orders 表：新增 status_key 支持 V3.0 新状态
-- ============================================================
-- V3.0 新增状态：split(已拆分)/purchasing(采购中)/production_abnormal(生产异常)/
--                install_order_generated(安装单已生成)/shipped(已发货)
-- 原有8态保持兼容，status_key 字段已是 JSON，现扩展定义

-- ============================================================
-- 3. purchase_orders 表（独立采购单，区别于旧的 purchases 表）
-- ============================================================
CREATE TABLE IF NOT EXISTS purchase_orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    po_no           VARCHAR(30) UNIQUE NOT NULL,       -- PO + 年月日 + 序号
    supplier_id     INTEGER,
    supplier_name   VARCHAR(100),
    contact         VARCHAR(50),
    phone           VARCHAR(30),
    total_amount    DECIMAL(12,2) DEFAULT 0,
    paid_amount     DECIMAL(12,2) DEFAULT 0,
    debt_amount     DECIMAL(12,2) DEFAULT 0,
    status          VARCHAR(30) DEFAULT '待采购',      -- 待采购/已下单/部分到货/全部到货/已取消
    order_ids       VARCHAR(200),                       -- 逗号分隔关联订单ID，多个订单合并时用
    expected_date   DATE,
    arrived_date    DATE,
    items           TEXT DEFAULT '[]',                  -- JSON: [{product_id, product_code, product_name, spec, qty, unit_price, amount}]
    remark          VARCHAR(500),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_po_no ON purchase_orders(po_no);
CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_po_supplier ON purchase_orders(supplier_id);

-- ============================================================
-- 4. production_feedback 表（生产反馈）
-- ============================================================
CREATE TABLE IF NOT EXISTS production_feedback (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    feedback_no     VARCHAR(30) UNIQUE NOT NULL,       -- FB + 年月日 + 序号
    order_id        INTEGER,
    order_no        VARCHAR(30),
    purchase_order_id INTEGER,
    feedback_type   VARCHAR(20) NOT NULL,              -- quality(质量)/defect(残次)/shortage(米数不足)
    description     TEXT,
    photos          TEXT DEFAULT '[]',                  -- JSON: [url1, url2]
    status          VARCHAR(20) DEFAULT '待处理',      -- 待处理/处理中/已解决
    resolver        VARCHAR(50),
    resolution      TEXT,
    resolved_at     DATETIME,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fb_order ON production_feedback(order_id);
CREATE INDEX IF NOT EXISTS idx_fb_type ON production_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_fb_status ON production_feedback(status);

-- ============================================================
-- 5. installation_orders 表（安装单，区别于 install_task）
-- ============================================================
CREATE TABLE IF NOT EXISTS installation_orders (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ins_no              VARCHAR(30) UNIQUE NOT NULL,   -- INS + 年月日 + 序号
    order_id            INTEGER,
    order_no            VARCHAR(30),
    customer_name       VARCHAR(50),
    customer_phone      VARCHAR(20),
    address             VARCHAR(300),
    product_details     TEXT DEFAULT '{}',             -- JSON: {windows: [{location, product, qty, remark}]}
    measure_summary     TEXT,                          -- 测量摘要
    install_requirements TEXT,                        -- 安装特殊要求
    scheduled_date      DATE,
    installer_id        INTEGER,
    installer_name      VARCHAR(50),
    install_time_slot   VARCHAR(20),                   -- '09:00-12:00' / '14:00-18:00'
    status              VARCHAR(20) DEFAULT '待分配',  -- 待分配/已分配/已安装/已验收/已取消
    install_photo       TEXT DEFAULT '[]',             -- JSON: [url1, url2]
    customer_signature  TEXT,                          -- 签名字符串/Base64
    confirmed_at        DATETIME,
    receivable_amount   DECIMAL(12,2) DEFAULT 0,      -- 应收
    received_amount     DECIMAL(12,2) DEFAULT 0,      -- 实收
    unpaid_amount       DECIMAL(12,2) DEFAULT 0,       -- 未收
    remark              VARCHAR(500),
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ins_order ON installation_orders(order_id);
CREATE INDEX IF NOT EXISTS idx_ins_status ON installation_orders(status);
CREATE INDEX IF NOT EXISTS idx_ins_installer ON installation_orders(installer_id);
CREATE INDEX IF NOT EXISTS idx_ins_scheduled ON installation_orders(scheduled_date);

-- ============================================================
-- 6. orders 表新增字段（辅助安装单生成）
-- ============================================================
ALTER TABLE orders ADD COLUMN measure_data TEXT;       -- JSON: 测量数据
ALTER TABLE orders ADD COLUMN install_requires TEXT;   -- 安装特殊要求
