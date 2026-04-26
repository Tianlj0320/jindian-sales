#!/usr/bin/env python3
"""
产品资料字段规范化迁移脚本
执行时间: 2026-04-26

字段新定义:
  product_type  → 商品品类: 窗帘/墙布/墙纸/岩板/全屋
  material      → 面料材质: 雪尼尔/棉麻/绒布/高精密/丝绸/亚麻/刺绣/提花/仿真丝/无纺布/PVC
  classification→ 产品形态: 帷幔/罗马帘/蜂巢帘/柔纱帘/基膜胶水/垂直帘/软包/硬包/岩板
  category      → 新增，商品品类(订单级别): 窗帘/墙布/墙纸/岩板

迁移规则:
  product_type='面料' → product_type='窗帘'
  material: 已有值保留；classification在材质候选里 → classification→material
  classification: '定高' → '' (待重新填)
  category: 新增，product_type='窗帘'填'窗帘'，product_type='辅料'填'辅料'
"""

import sqlite3

DB = 'sales.db'

MATERIALS = {'雪尼尔','棉麻','绒布','高精密','丝绸','亚麻','刺绣','提花','仿真丝','无纺布','PVC','测试材质'}
ACCESSORIES = {'配件','轨道','罗马杆','电动轨','铅块'}

def migrate(conn):
    cur = conn.cursor()

    # 1. 加 category 列
    cur.execute("ALTER TABLE products ADD COLUMN category VARCHAR(50)")
    print("✅ 加了 products.category 列")

    # 2. 迁移数据
    cur.execute("SELECT id, code, name, product_type, classification, material FROM products")
    products = cur.fetchall()

    updated = 0
    for p in products:
        pid, code, name, pt, cls, mat = p
        changes = {}

        # product_type: 面料→窗帘，辅料保持
        if pt == '面料':
            changes['product_type'] = '窗帘'
        elif pt == '辅料':
            changes['product_type'] = '辅料'

        # material: 优先用已有的material，其次用classification里的材质词
        if mat and mat.strip():
            new_mat = mat.strip()
        elif cls and cls.strip() in MATERIALS:
            new_mat = cls.strip()
        else:
            new_mat = ''
        changes['material'] = new_mat

        # classification: 转为产品形态
        # 已有形态映射
        FORM_MAP = {
            '定高': '',        # 待重新填（不再使用定高概念）
            '配件': '配件',
            '轨道': '轨道',
            '罗马杆': '罗马杆',
        }
        new_cls = FORM_MAP.get(cls, '')  # 其他一律清空，待重新填
        changes['classification'] = new_cls

        # category: 商品品类
        if pt == '面料' or changes.get('product_type') == '窗帘':
            changes['category'] = '窗帘'
        else:
            changes['category'] = '辅料'

        # 执行更新
        if changes:
            sets = ', '.join(f"{k} = ?" for k in changes.keys())
            vals = list(changes.values()) + [pid]
            cur.execute(f"UPDATE products SET {sets} WHERE id = ?", vals)
            updated += 1

    conn.commit()
    print(f"✅ 迁移完成，共处理 {updated} 条产品记录")

    # 3. 验证结果
    cur.execute("SELECT DISTINCT product_type FROM products")
    print(f"  product_type 去重: {[r[0] for r in cur.fetchall()]}")
    cur.execute("SELECT DISTINCT material FROM products WHERE material IS NOT NULL AND material != ''")
    print(f"  material 去重: {[r[0] for r in cur.fetchall()]}")
    cur.execute("SELECT DISTINCT classification FROM products")
    print(f"  classification 去重: {[r[0] for r in cur.fetchall()]}")
    cur.execute("SELECT DISTINCT category FROM products")
    print(f"  category 去重: {[r[0] for r in cur.fetchall()]}")
    cur.execute("SELECT id, name, product_type, material, classification, category FROM products LIMIT 10")
    print("\n=== 迁移后前10条 ===")
    for r in cur.fetchall():
        print(f"  {r}")


if __name__ == '__main__':
    conn = sqlite3.connect(DB)
    migrate(conn)
    conn.close()
    print("\n迁移脚本执行完毕")
