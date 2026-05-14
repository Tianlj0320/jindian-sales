"""
种子数据 - 为 V4.0 系统创建演示数据
运行方式: cd /d/project && /c/Python314/python seed_data.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import select, text
from app.database import engine, async_session_factory
from app.domain.base import Base
from app.domain.auth import User
from app.domain.customer import Customer
from app.domain.product import ProductCategory, Supplier, ProductSeries, Product
from app.domain.warehouse import Warehouse
from app.domain.role import Role
from app.domain.processing import ProcessingType, ProcessingMaterialRule
from app.domain.installation import InstallTeam, Installer, InstallTeamMember
from app.domain.system import DictType, DictItem
from datetime import datetime, timezone, date

async def seed():
    print("=" * 50)
    print("金典软装ERP V4.0 - 种子数据初始化")
    print("=" * 50)

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] 数据库表已就绪")

    async with async_session_factory() as session:
        now = datetime.now(timezone.utc)
        today = date.today()

        # ── 检查是否已有数据 ──
        result = await session.execute(select(User).limit(1))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            print("[SKIP] 用户数据已存在，跳过基础种子数据")
        else:
            await _seed_basic(session)
            print("[OK] 基础种子数据已写入")

        # ── 以下数据总是补充写入（幂等） ──
        await _seed_extended(session)
        await session.commit()
        print("[OK] 扩展种子数据已写入")

    print("=" * 50)
    print("种子数据初始化完成！")
    print("=" * 50)


async def _seed_basic(session):
    """基础种子数据（同 main.py startup）"""
    from app.core.security import hash_password

    # 用户
    session.add_all([
        User(username="admin", password_hash=hash_password("admin123"),
             name="系统管理员", phone="13800000000", role="admin", position="管理员"),
        User(username="13900000001", password_hash=hash_password("jd8888"),
             name="韩霜", phone="13900000001", role="admin", position="老板"),
        User(username="13900001111", password_hash=hash_password("jd8888"),
             name="小王", phone="13900001111", role="staff", position="导购"),
    ])

    # 产品分类
    session.add_all([
        ProductCategory(name="布艺窗帘", code="C01", sort_order=1),
        ProductCategory(name="窗纱", code="C02", sort_order=2),
        ProductCategory(name="墙布", code="C03", sort_order=3),
        ProductCategory(name="辅料配件", code="C04", sort_order=4),
    ])

    # 角色
    import json
    session.add_all([
        Role(name="超级管理员", code="admin", permissions=json.dumps(["*"]), sort_order=1),
        Role(name="店长", code="manager", permissions=json.dumps(
            ["dashboard","orders","customers","products","purchases","warehouse","installations","finance","reports"]), sort_order=2),
        Role(name="导购", code="staff", permissions=json.dumps(
            ["dashboard","orders","customers","products"]), sort_order=3),
        Role(name="安装工", code="installer", permissions=json.dumps(["installations"]), sort_order=4),
    ])


async def _seed_extended(session):
    """补充种子数据（幂等）"""
    # ── 先确保字典数据存在 ──
    await _ensure_dict_data(session)

    # ── 供应商（S03, S04 补充，S01, S02 如果不存在也创建） ──
    suppliers = {}
    for s_data in [
        ("S01", "杭州布艺供应商", "布艺", "李经理", "13800138001", 7),
        ("S02", "广州辅料批发", "配件", "张先生", "13900139001", 10),
        ("S03", "佛山成品帘工厂", "成品", "刘经理", "13800338003", 10),
        ("S04", "宁波轨道五金厂", "配件", "陈经理", "13800448004", 6),
    ]:
        code, name, stype, contact, phone, days = s_data
        result = await session.execute(select(Supplier).where(Supplier.code == code))
        s = result.scalar_one_or_none()
        if not s:
            s = Supplier(code=code, name=name, type=stype, contact=contact, phone=phone, delivery_days=days)
            session.add(s)
            await session.flush()
        suppliers[code] = s

    # ── 产品系列 ──
    series_map = {}
    for sr_data in [
        ("S01-A", "雪尼尔系列", "S01"),
        ("S01-B", "高精密系列", "S01"),
        ("S02-A", "基础辅料系列", "S02"),
        ("S03-A", "成品帘系列", "S03"),
        ("S04-A", "电动轨道系列", "S04"),
    ]:
        code, name, s_code = sr_data
        result = await session.execute(select(ProductSeries).where(ProductSeries.code == code))
        sr = result.scalar_one_or_none()
        if not sr:
            sr = ProductSeries(code=code, name=name, supplier_id=suppliers[s_code].id, sort_order=1)
            session.add(sr)
            await session.flush()
        series_map[code] = sr

    # ── 获取分类 ──
    cats = {}
    for cname in ["布艺窗帘", "窗纱", "墙布", "辅料配件"]:
        result = await session.execute(select(ProductCategory).where(ProductCategory.name == cname))
        cats[cname] = result.scalar_one()

    # ── 加工类型 ──
    pt_map = {}
    for pt_data in [
        ("PT001", "常规窗帘", "常规布艺窗帘加工", 1),
        ("PT002", "高精密窗帘", "高精密遮光布窗帘加工", 2),
        ("PT003", "窗纱", "窗纱类加工", 3),
    ]:
        code, name, desc, order = pt_data
        result = await session.execute(select(ProcessingType).where(ProcessingType.code == code))
        pt = result.scalar_one_or_none()
        if not pt:
            pt = ProcessingType(code=code, name=name, description=desc, sort_order=order)
            session.add(pt)
            await session.flush()
        pt_map[code] = pt

    # ── 加工辅料规则 ──
    rules_data = [
        ("PT001", "布袋", "布袋", "米", "width * fold_ratio", 8, 1, True),
        ("PT001", "铅线", "铅线", "米", "width * fold_ratio", 5, 2, False),
        ("PT001", "挂钩", "挂钩", "个", "qty * 8", 1, 3, True),
        ("PT002", "布袋", "高精密布袋", "米", "width * fold_ratio", 10, 1, True),
        ("PT002", "无纺布带", "无纺布带", "米", "width * fold_ratio", 6, 2, True),
        ("PT002", "铅线", "铅线", "米", "width", 6, 3, True),
        ("PT003", "布袋", "窗纱布袋", "米", "width * fold_ratio", 6, 1, True),
        ("PT003", "铅线", "窗纱铅线", "米", "width", 4, 2, True),
    ]
    for pt_code, name, default_name, unit, formula, price, order, required in rules_data:
        pt = pt_map[pt_code]
        result = await session.execute(
            select(ProcessingMaterialRule).where(
                ProcessingMaterialRule.processing_type_id == pt.id,
                ProcessingMaterialRule.material_name == name
            )
        )
        if not result.scalar_one_or_none():
            session.add(ProcessingMaterialRule(
                processing_type_id=pt.id,
                material_name=name,
                default_product_name=default_name,
                unit=unit,
                qty_formula=formula,
                unit_price=price,
                sort_order=order,
                is_required=required,
            ))

    # ── 产品 ──
    products_data = [
        # (code, name, type, classification, category_name, supplier_code, series_code, width, unit, selling_price, is_purchase, pt_code)
        ("ML001", "雪尼尔绒布-奶白", "面料", "定高", "布艺窗帘", "S01", "S01-A", 280, "米", 68, True, "PT001"),
        ("ML002", "雪尼尔绒布-浅灰", "面料", "定高", "布艺窗帘", "S01", "S01-A", 280, "米", 72, True, "PT001"),
        ("ML003", "高精密遮光布-米黄", "面料", "定宽", "布艺窗帘", "S01", "S01-B", 280, "米", 98, True, "PT002"),
        ("FL001", "窗纱-自然白", "面料", "定高", "窗纱", "S01", "S01-A", 280, "米", 48, True, "PT003"),
        ("CP001", "轨道-纳米静音单轨", "辅料", "配件", "辅料配件", "S02", "S02-A", 0, "米", 35, True, None),
        ("CP002", "罗马杆-铝合金2.0m", "辅料", "配件", "辅料配件", "S02", "S02-A", 0, "米", 45, True, None),
        ("CP003", "成品卷帘-白色", "成品", "配件", "辅料配件", "S03", "S03-A", 0, "套", 280, True, None),
        ("CP004", "成品百叶帘-银色", "成品", "配件", "辅料配件", "S03", "S03-A", 0, "套", 320, True, None),
        ("CP005", "电动轨道-2.0m", "辅料", "配件", "辅料配件", "S04", "S04-A", 0, "米", 120, True, None),
        ("CP006", "电动轨道遥控器", "辅料", "配件", "辅料配件", "S04", "S04-A", 0, "个", 80, True, None),
    ]
    for pd in products_data:
        code, name, ptype, classification, cat_name, s_code, sr_code, width, unit, price, is_purchase, pt_code = pd
        result = await session.execute(select(Product).where(Product.code == code))
        if result.scalar_one_or_none():
            continue
        prod = Product(
            code=code, name=name, product_type=ptype, classification=classification,
            category_id=cats[cat_name].id, supplier_id=suppliers[s_code].id,
            series_id=series_map[sr_code].id,
            width=width, unit=unit, cost_price=price * 0.6, selling_price=price,
            is_purchase=is_purchase, stock=0, fold_ratio=2.0, min_price=price * 0.8,
        )
        if pt_code:
            prod.processing_type_id = pt_map[pt_code].id
        session.add(prod)

    # ── 仓库 ──
    wh_data = [
        ("WH-01", "主仓库", "杭州古墩路欧亚达家居广场", "main"),
        ("WH-02", "辅料仓", "杭州古墩路欧亚达家居广场B1", "auxiliary"),
        ("WH-03", "成品仓", "杭州古墩路欧亚达家居广场B2", "finished"),
    ]
    for code, name, addr, wtype in wh_data:
        result = await session.execute(select(Warehouse).where(Warehouse.code == code))
        if not result.scalar_one_or_none():
            session.add(Warehouse(name=name, code=code, address=addr, warehouse_type=wtype))

    # ── 安装团队 ──
    team_data = [
        ("安装一队", "张师傅", "13900001111"),
        ("安装二队", "王师傅", "13900002222"),
    ]
    installer_data = [
        ("张师傅", "13900001111"),
        ("李师傅", "13900002222"),
        ("王师傅", "13900003333"),
        ("赵师傅", "13900004444"),
    ]
    teams = {}
    for name, leader, phone in team_data:
        result = await session.execute(select(InstallTeam).where(InstallTeam.name == name))
        t = result.scalar_one_or_none()
        if not t:
            t = InstallTeam(name=name, leader_name=leader, leader_phone=phone)
            session.add(t)
            await session.flush()
        teams[name] = t

    installers = {}
    for name, phone in installer_data:
        result = await session.execute(select(Installer).where(Installer.phone == phone))
        ins = result.scalar_one_or_none()
        if not ins:
            ins = Installer(name=name, phone=phone)
            session.add(ins)
            await session.flush()
        installers[phone] = ins

    # ── 安装队成员关系 ──
    team_members = [
        ("安装一队", "13900001111"),
        ("安装一队", "13900002222"),
        ("安装二队", "13900003333"),
        ("安装二队", "13900004444"),
    ]
    for team_name, ins_phone in team_members:
        t = teams[team_name]
        ins = installers[ins_phone]
        result = await session.execute(
            select(InstallTeamMember).where(
                InstallTeamMember.team_id == t.id,
                InstallTeamMember.installer_id == ins.id
            )
        )
        if not result.scalar_one_or_none():
            session.add(InstallTeamMember(team_id=t.id, installer_id=ins.id))

    # ── 客户（如果不存在） ──
    customers_data = [
        ("张三", "13800000001", "杭州市西湖区古荡新村12幢302"),
        ("李四", "13800000002", "杭州市拱墅区大关小区8幢503"),
        ("王五", "13800000003", "杭州市滨江区彩虹城15幢201"),
        ("赵六", "13800000004", "杭州市余杭区翡翠城23幢102"),
        ("孙七", "13800000005", "杭州市萧山区金色江南4幢2801"),
    ]
    for name, phone, addr in customers_data:
        result = await session.execute(select(Customer).where(Customer.phone == phone))
        if not result.scalar_one_or_none():
            session.add(Customer(name=name, phone=phone, address=addr))

    print("[OK] 扩展数据: 供应商4个, 产品系列5个, 加工类型3个, 产品10个, 仓库3个, 安装团队2个, 安装工4个, 客户5个")


async def _ensure_dict_data(session):
    """确保字典数据存在"""
    # 如果已有字典类型，跳过
    result = await session.execute(select(DictType).limit(1))
    if result.scalar_one_or_none():
        return

    dict_type_seed = [
        ("order_type", "订单类型", 1), ("customer_source", "客户来源", 2),
        ("expense_category", "费用类别", 3), ("delivery_method", "提货方式", 4),
        ("supplier_type", "供应商类型", 5), ("product_unit", "产品单位", 6),
        ("fabric_width", "门幅", 7), ("material_composition", "材质成分", 8),
        ("customer_category", "客户类别", 9), ("install_location", "安装位置", 10),
        ("finished_type", "成品类型", 11), ("style_item", "款式项目", 12),
        ("after_sale_category", "售后分类", 13), ("bank_account", "银行账号", 14),
        ("payment_type", "收款类型", 15), ("order_fee_type", "订单费用类型", 16),
        ("waste_type", "损耗类型", 17), ("self_use_type", "自用类型", 18),
        ("purchase_return_type", "采购退货类型", 19), ("expense_type", "开销类型", 20),
        ("department", "部门", 21), ("position", "职务", 22),
        ("memo_type", "备忘录类型", 23), ("message_type", "留言类型", 24),
        ("order_status", "订单状态", 25), ("product_category", "产品分类", 26),
        ("warehouse", "仓库", 27), ("store_info", "店铺信息", 28),
        ("processing_type", "加工类型", 29),
    ]
    dict_item_seed = [
        ("order_type", "curtain", "窗帘", 1), ("order_type", "wallpaper", "墙布", 2),
        ("order_type", "hardsheet", "硬包", 3), ("order_type", "wholehouse", "全屋", 4),
        ("order_type", "rockboard", "岩板", 5),
        ("customer_source", "self", "自然进店", 1), ("customer_source", "referral", "老客介绍", 2),
        ("customer_source", "online", "线上引流", 3), ("customer_source", "community", "小区推广", 4),
        ("customer_source", "old", "老客户", 5),
        ("expense_category", "rent", "房租", 1), ("expense_category", "utilities", "水电", 2),
        ("expense_category", "salary", "工资", 3), ("expense_category", "office", "办公", 4),
        ("expense_category", "other", "其他", 5),
        ("delivery_method", "install", "上门安装", 1), ("delivery_method", "pickup", "自提", 2),
        ("delivery_method", "express", "快递", 3),
        ("supplier_type", "fabric", "布艺", 1), ("supplier_type", "finished", "成品", 2),
        ("supplier_type", "accessory", "配件", 3), ("supplier_type", "other", "其他", 4),
        ("product_unit", "meter", "米", 1), ("product_unit", "piece", "个", 2),
        ("product_unit", "set", "套", 3), ("product_unit", "strip", "条", 4),
        ("product_unit", "block", "块", 5), ("product_unit", "roll", "卷", 6),
        ("product_unit", "sqm", "平方米", 7),
        ("fabric_width", "w140", "1.4m", 1), ("fabric_width", "w280", "2.8m", 2),
        ("fabric_width", "w300", "3.0m", 3),
        ("material_composition", "cotton", "棉", 1), ("material_composition", "linen", "麻", 2),
        ("material_composition", "polyester", "涤纶", 3), ("material_composition", "blend", "混纺", 4),
        ("material_composition", "velvet", "丝绒", 5), ("material_composition", "silk", "真丝", 6),
        ("material_composition", "cottonlinen", "棉麻", 7),
        ("customer_category", "normal", "普通客户", 1), ("customer_category", "vip", "VIP客户", 2),
        ("customer_category", "wholesale", "批发客户", 3), ("customer_category", "partner", "合作客户", 4),
        ("install_location", "living", "客厅", 1), ("install_location", "master_bed", "主卧", 2),
        ("install_location", "second_bed", "次卧", 3), ("install_location", "dining", "餐厅", 4),
        ("install_location", "study", "书房", 5), ("install_location", "kitchen", "厨房", 6),
        ("install_location", "bathroom", "卫生间", 7), ("install_location", "balcony", "阳台", 8),
        ("finished_type", "curtain", "成品帘", 1), ("finished_type", "roman", "罗马帘", 2),
        ("finished_type", "vertical", "垂直帘", 3), ("finished_type", "roller", "卷帘", 4),
        ("finished_type", "hundred", "百叶帘", 5),
        ("style_item", "plain", "平帘", 1), ("style_item", "pleated", "褶皱帘", 2),
        ("style_item", "eyelet", "打孔帘", 3), ("style_item", "hook", "挂钩帘", 4),
        ("style_item", "sash", "穿杆帘", 5),
        ("after_sale_category", "quality", "质量问题", 1), ("after_sale_category", "install_issue", "安装问题", 2),
        ("after_sale_category", "size_issue", "尺寸问题", 3), ("after_sale_category", "damage", "人为损坏", 4),
        ("after_sale_category", "other_issue", "其他售后", 5),
        ("bank_account", "icbc", "工商银行", 1), ("bank_account", "abc", "农业银行", 2),
        ("bank_account", "ccb", "建设银行", 3), ("bank_account", "boc", "中国银行", 4),
        ("bank_account", "cib", "兴业银行", 5),
        ("payment_type", "cash", "现金", 1), ("payment_type", "wechat", "微信", 2),
        ("payment_type", "alipay", "支付宝", 3), ("payment_type", "bank_transfer", "银行转账", 4),
        ("payment_type", "pos", "POS机刷卡", 5),
        ("order_fee_type", "measure_fee", "量尺费", 1), ("order_fee_type", "install_fee", "安装费", 2),
        ("order_fee_type", "delivery_fee", "运费", 3), ("order_fee_type", "lift_fee", "上楼费", 4),
        ("order_fee_type", "other_fee", "其他费用", 5),
        ("waste_type", "cut_waste", "裁剪损耗", 1), ("waste_type", "joint_waste", "拼接损耗", 2),
        ("self_use_type", "sample", "样品", 1), ("self_use_type", "display", "展厅", 2),
        ("self_use_type", "gift", "赠送", 3), ("self_use_type", "other", "其他自用", 4),
        ("purchase_return_type", "quality", "质量问题退货", 1), ("purchase_return_type", "wrong", "发错货退货", 2),
        ("purchase_return_type", "overstock", "多采退货", 3),
        ("expense_type", "rent", "房租", 1), ("expense_type", "salary", "工资", 2),
        ("expense_type", "marketing", "营销费用", 3), ("expense_type", "office", "办公费用", 4),
        ("department", "sales", "销售部", 1), ("department", "design", "设计部", 2),
        ("department", "install", "安装部", 3), ("department", "finance", "财务部", 4),
        ("department", "admin", "行政部", 5),
        ("position", "boss", "老板", 1), ("position", "manager", "店长", 2),
        ("position", "sales", "导购", 3), ("position", "designer", "设计师", 4),
        ("position", "installer", "安装工", 5),
        ("memo_type", "customer", "客户备忘", 1), ("memo_type", "order", "订单备忘", 2),
        ("message_type", "system", "系统消息", 1), ("message_type", "order_notify", "订单通知", 2),
        ("order_status", "initial", "待量尺", 1), ("order_status", "measured", "已量尺", 2),
        ("order_status", "confirmed", "已确认", 3), ("order_status", "split", "已分单", 4),
        ("order_status", "purchasing", "采购中", 5), ("order_status", "partial_in", "部分到货", 6),
        ("order_status", "stocked", "已入库", 7), ("order_status", "processing", "加工中", 8),
        ("order_status", "completed", "已完成", 9), ("order_status", "install_scheduled", "已排安装", 10),
        ("order_status", "installed", "已安装", 11), ("order_status", "accepted", "已验收", 12),
        ("product_category", "C01", "布艺窗帘", 1), ("product_category", "C02", "窗纱", 2),
        ("product_category", "C03", "墙布", 3), ("product_category", "C04", "辅料配件", 4),
        ("warehouse", "main", "主仓库", 1), ("warehouse", "auxiliary", "辅料仓", 2),
        ("warehouse", "finished", "成品仓", 3),
        ("store_info", "store_name", "金典软装", 1), ("store_info", "store_phone", "0571-88888888", 2),
        ("store_info", "store_address", "杭州古墩路欧亚达家居广场3楼", 3),
        ("processing_type", "curtain", "常规窗帘", 1), ("processing_type", "high_precision", "高精密窗帘", 2),
        ("processing_type", "sheer", "窗纱", 3),
    ]

    for code, name, order in dict_type_seed:
        session.add(DictType(code=code, name=name, sort_order=order))

    for type_code, key, value, order in dict_item_seed:
        session.add(DictItem(dict_type_code=type_code, dict_key=key, dict_value=value, sort_order=order))


if __name__ == "__main__":
    asyncio.run(seed())
