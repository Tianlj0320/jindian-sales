# seed_data.py
"""
初始化数据库并写入演示数据
运行方式: python seed_data.py
"""
import asyncio
from datetime import datetime, date, timedelta
from app.database import async_session, engine
from app.models import (
    Base, Order, Customer, Supplier, FabricCategory, Product,
    Employee, InstallerAccount, InstallTask, StoreConfig
)


async def seed():
    print("🗄️  初始化数据库...")
    async with engine.begin() as conn:
        # 删除旧表（如果存在）重新创建
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库创建完成")

    async with async_session() as session:

        # ─── 供应商 ─────────────────────────────────────────────────────────
        suppliers = [
            Supplier(id=1, code="01", name="杭州诺雅布业", type="布艺",
                     contact="李经理", phone="13800001111", delivery_days=7,
                     address="杭州市余杭区布艺城A区108号"),
            Supplier(id=2, code="02", name="杜亚轨道", type="配件",
                     contact="张经理", phone="13800002222", delivery_days=5,
                     address="杭州市萧山区建材市场B区12号"),
            Supplier(id=3, code="03", name="雅居辅料", type="配件",
                     contact="王经理", phone="13800003333", delivery_days=3,
                     address="杭州市拱墅区辅料中心3号"),
        ]
        session.add_all(suppliers)

        # ─── 布版/系列 ──────────────────────────────────────────────────────
        categories = [
            FabricCategory(id=1, code="0101", name="奶油风系列", supplier_id=1,
                          description="适合奶油风/简约风"),
            FabricCategory(id=2, code="0102", name="中古风系列", supplier_id=1,
                          description="适合中古/复古风"),
            FabricCategory(id=3, code="0201", name="静音轨道", supplier_id=2,
                          description="杜亚电动/手动轨道"),
        ]
        session.add_all(categories)

        # ─── 产品 ─────────────────────────────────────────────────────────
        products = [
            Product(id=1, code="01010001", name="婴儿绒雪尼尔-奶白",
                   supplier_id=1, category_id=1, product_type="面料",
                   classification="定高", model="奶白", material="雪尼尔",
                   width=280, weight=320, unit_price=68, unit="米", stock=156),
            Product(id=2, code="01010002", name="缎面雪尼尔-浅咖",
                   supplier_id=1, category_id=1, product_type="面料",
                   classification="定高", model="浅咖", material="雪尼尔",
                   width=280, weight=300, unit_price=65, unit="米", stock=89),
            Product(id=3, code="01020001", name="亚麻纱-自然白",
                   supplier_id=1, category_id=2, product_type="面料",
                   classification="定高", model="自然白", material="亚麻",
                   width=280, weight=180, unit_price=48, unit="米", stock=210),
            Product(id=4, code="01020002", name="复古绿亚麻纱",
                   supplier_id=1, category_id=2, product_type="面料",
                   classification="定高", model="复古绿", material="亚麻",
                   width=280, weight=180, unit_price=52, unit="米", stock=75),
            Product(id=5, code="02010001", name="杜亚静音轨道-2.0",
                   supplier_id=2, category_id=3, product_type="辅料",
                   classification="配件", model="DUOY-2.0",
                   unit_price=88, unit="米", stock=120),
        ]
        session.add_all(products)

        # ─── 员工 ─────────────────────────────────────────────────────────
        employees = [
            Employee(id=1, code="E001", name="小王", gender="男",
                    phone="13900001111", position="导购", department="销售",
                    max_discount=0.75, round_limit=500, is_installer=False),
            Employee(id=2, code="E002", name="小李", gender="女",
                    phone="13900002222", position="导购", department="销售",
                    max_discount=0.80, round_limit=300, is_installer=False),
            Employee(id=3, code="E003", name="小张", gender="男",
                    phone="13900003333", position="导购", department="销售",
                    max_discount=0.75, round_limit=500, is_installer=False),
        ]
        session.add_all(employees)

        # ─── 安装工账号 ────────────────────────────────────────────────────
        installers = [
            InstallerAccount(id=1, name="张师傅", phone="13800001111",
                           status="active"),
            InstallerAccount(id=2, name="王师傅", phone="13800002222",
                           status="active"),
        ]
        session.add_all(installers)

        # ─── 客户 ─────────────────────────────────────────────────────────
        customers = [
            Customer(id=1, name="张三", phone="13712341111", type="零售",
                    address="杭州市西湖区龙湖天街7幢802室",
                    community="龙湖天街", source="小红书", salesperson="小王", debt=2200),
            Customer(id=2, name="李四", phone="13712342222", type="零售",
                    address="杭州市拱墅区远洋公馆2幢1501室",
                    community="远洋公馆", source="抖音", salesperson="小王", debt=8500),
            Customer(id=3, name="王五", phone="13712343333", type="全屋",
                    address="杭州市上城区钱塘府2幢1801室",
                    community="钱塘府", source="店面", salesperson="小李", debt=0),
            Customer(id=4, name="赵六", phone="13712344444", type="零售",
                    address="杭州市西湖区武林郡3幢502室",
                    community="武林郡", source="口碑推荐", salesperson="小张", debt=4800),
            Customer(id=5, name="孙七", phone="13712345555", type="零售",
                    address="杭州市江干区锦绣江南5幢301室",
                    community="锦绣江南", source="小红书", salesperson="小李", debt=0),
        ]
        session.add_all(customers)

        # ─── 订单 ─────────────────────────────────────────────────────────
        orders = [
            Order(
                id=1, order_no="20260413001", customer_id=1,
                customer_name="张三", customer_phone="13712341111",
                order_type="窗帘", status="待确认", status_color="pending",
                status_key="created",
                amount=3200, quote_amount=3400, discount_amount=200,
                received=1000, debt=2200,
                order_date="2026-04-13", delivery_date="2026-04-27",
                delivery_method="上门安装", salesperson="小王",
                content="婴儿绒雪尼尔+亚麻纱",
                history=[
                    {"s": "创建订单", "s2": "待确认", "c": "pending", "time": "2026-04-13 10:00"}
                ],
                items=[
                    {"room": "主卧", "product": "婴儿绒雪尼尔-奶白", "qty": 2, "price": 68, "amount": 272},
                    {"room": "次卧", "product": "亚麻纱-自然白", "qty": 2, "price": 48, "amount": 192},
                ]
            ),
            Order(
                id=2, order_no="20260412003", customer_id=2,
                customer_name="李四", customer_phone="13712342222",
                order_type="窗帘", status="待加工", status_color="process",
                status_key="processing",
                amount=8500, quote_amount=9000, discount_amount=500,
                received=0, debt=8500,
                order_date="2026-04-12", delivery_date="2026-04-26",
                delivery_method="上门安装", salesperson="小王",
                content="全屋窗帘12扇",
                history=[
                    {"s": "创建订单", "s2": "待确认", "c": "pending", "time": "2026-04-12 09:00"},
                    {"s": "待确认", "s2": "已核单确认", "c": "pending", "time": "2026-04-12 14:00"},
                    {"s": "已核单确认", "s2": "待备货", "c": "pending", "time": "2026-04-12 16:00"},
                ],
                items=[
                    {"room": "全屋", "product": "婴儿绒雪尼尔-奶白", "qty": 12, "price": 68, "amount": 8160},
                ]
            ),
            Order(
                id=3, order_no="20260411002", customer_id=3,
                customer_name="王五", customer_phone="13712343333",
                order_type="全屋", status="待安装", status_color="install",
                status_key="install",
                amount=5600, quote_amount=6000, discount_amount=400,
                received=3000, debt=2600,
                order_date="2026-04-11", delivery_date="2026-04-25",
                delivery_method="上门安装", salesperson="小李",
                content="客厅+书房+次卧",
                history=[
                    {"s": "创建订单", "s2": "待确认", "c": "pending", "time": "2026-04-11 10:00"},
                    {"s": "待确认", "s2": "已核单确认", "c": "pending", "time": "2026-04-11 14:00"},
                    {"s": "已核单确认", "s2": "已测量", "c": "pending", "time": "2026-04-12 09:00"},
                    {"s": "已测量", "s2": "已备货", "c": "pending", "time": "2026-04-13 15:00"},
                    {"s": "已备货", "s2": "加工中", "c": "pending", "time": "2026-04-14 10:00"},
                ],
                items=[
                    {"room": "客厅", "product": "婴儿绒雪尼尔-奶白", "qty": 2, "price": 68, "amount": 272},
                    {"room": "书房", "product": "亚麻纱-自然白", "qty": 2, "price": 48, "amount": 192},
                    {"room": "次卧", "product": "高精密-浅灰色", "qty": 2, "price": 128, "amount": 512},
                ],
                installer_id=1,
                install_address="杭州市上城区钱塘府2幢1801室",
                install_date=date.today() + timedelta(days=6),
                install_time_slot="09:00"
            ),
            Order(
                id=4, order_no="20260410001", customer_id=4,
                customer_name="赵六", customer_phone="13712344444",
                order_type="窗帘", status="有尾款", status_color="partial",
                status_key="installed",
                amount=12800, quote_amount=13000, discount_amount=200,
                received=8000, debt=4800,
                order_date="2026-04-10", delivery_date="2026-04-24",
                delivery_method="上门安装", salesperson="小王",
                content="别墅窗帘",
                history=[
                    {"s": "创建订单", "s2": "待确认", "c": "pending", "time": "2026-04-10 09:00"},
                    {"s": "待确认", "s2": "已核单确认", "c": "pending", "time": "2026-04-10 11:00"},
                    {"s": "已核单确认", "s2": "已测量", "c": "pending", "time": "2026-04-11 09:00"},
                    {"s": "已测量", "s2": "已备货", "c": "pending", "time": "2026-04-12 14:00"},
                    {"s": "已备货", "s2": "加工中", "c": "pending", "time": "2026-04-13 10:00"},
                    {"s": "加工中", "s2": "待安装", "c": "pending", "time": "2026-04-15 16:00"},
                ],
                items=[
                    {"room": "全屋", "product": "缎面雪尼尔-浅咖", "qty": 15, "price": 65, "amount": 9750},
                ],
                installer_id=1,
                install_address="杭州市西湖区武林郡3幢502室",
                install_date=date.today() - timedelta(days=2),
                install_time_slot="14:00"
            ),
            Order(
                id=5, order_no="20260409002", customer_id=5,
                customer_name="孙七", customer_phone="13712345555",
                order_type="窗帘", status="完成", status_color="complete",
                status_key="completed",
                amount=4200, quote_amount=4500, discount_amount=300,
                received=4200, debt=0,
                order_date="2026-04-09", delivery_date="2026-04-23",
                delivery_method="上门安装", salesperson="小李",
                content="主卧+次卧",
                history=[
                    {"s": "创建订单", "s2": "待确认", "c": "pending", "time": "2026-04-09 10:00"},
                    {"s": "待确认", "s2": "已核单确认", "c": "pending", "time": "2026-04-09 14:00"},
                    {"s": "已核单确认", "s2": "已测量", "c": "pending", "time": "2026-04-10 09:00"},
                    {"s": "已测量", "s2": "已备货", "c": "pending", "time": "2026-04-11 15:00"},
                    {"s": "已备货", "s2": "加工中", "c": "pending", "time": "2026-04-12 10:00"},
                    {"s": "加工中", "s2": "待安装", "c": "pending", "time": "2026-04-14 16:00"},
                    {"s": "待安装", "s2": "已安装", "c": "pending", "time": "2026-04-18 11:00"},
                    {"s": "已安装", "s2": "完成", "c": "pending", "time": "2026-04-18 12:00"},
                ],
                items=[
                    {"room": "主卧", "product": "婴儿绒雪尼尔-奶白", "qty": 2, "price": 68, "amount": 272},
                    {"room": "次卧", "product": "亚麻纱-自然白", "qty": 2, "price": 48, "amount": 192},
                ],
                installer_id=1,
                install_address="杭州市江干区锦绣江南5幢301室",
                install_date=date.today() - timedelta(days=4),
                install_time_slot="10:00"
            ),
        ]
        session.add_all(orders)

        # ─── 安装任务 ─────────────────────────────────────────────────────
        tasks = [
            # 今日待安装
            InstallTask(
                id=1, order_id=3, order_no="20260411002",
                installer_id=1,
                install_date=date.today() + timedelta(days=6),
                install_time_slot="09:00",
                address="杭州市上城区钱塘府2幢1801室",
                customer_name="王五",
                customer_phone="13712343333",
                raw_customer_phone="13712343333",
                order_content="客厅+书房+次卧 窗帘",
                priority="high",
                status="pending",
                navigate_url="https://uri.amap.com/search?keyword=杭州市上城区钱塘府2幢1801室&src=jd-rz"
            ),
            # 今日待安装
            InstallTask(
                id=2, order_id=2, order_no="20260412003",
                installer_id=1,
                install_date=date.today() + timedelta(days=8),
                install_time_slot="14:00",
                address="杭州市拱墅区远洋公馆2幢1501室",
                customer_name="李四",
                customer_phone="13712342222",
                raw_customer_phone="13712342222",
                order_content="全屋窗帘12扇",
                priority="normal",
                status="pending",
                navigate_url="https://uri.amap.com/search?keyword=杭州市拱墅区远洋公馆2幢1501室&src=jd-rz"
            ),
            # 历史已完成
            InstallTask(
                id=3, order_id=4, order_no="20260410001",
                installer_id=1,
                install_date=date.today() - timedelta(days=2),
                install_time_slot="14:00",
                address="杭州市西湖区武林郡3幢502室",
                customer_name="赵六",
                customer_phone="13712344444",
                raw_customer_phone="13712344444",
                order_content="别墅窗帘",
                priority="normal",
                status="completed",
                completed_at=datetime.now() - timedelta(days=2, hours=3),
                completion_remark="客户满意，安装顺利",
                navigate_url="https://uri.amap.com/search?keyword=杭州市西湖区武林郡3幢502室&src=jd-rz"
            ),
            # 历史已完成
            InstallTask(
                id=4, order_id=5, order_no="20260409002",
                installer_id=1,
                install_date=date.today() - timedelta(days=4),
                install_time_slot="10:00",
                address="杭州市江干区锦绣江南5幢301室",
                customer_name="孙七",
                customer_phone="13712345555",
                raw_customer_phone="13712345555",
                order_content="主卧+次卧 窗帘",
                priority="normal",
                status="completed",
                completed_at=datetime.now() - timedelta(days=4, hours=2),
                completion_remark="",
                navigate_url="https://uri.amap.com/search?keyword=杭州市江干区锦绣江南5幢301室&src=jd-rz"
            ),
        ]
        session.add_all(tasks)

        # ─── 门店配置 ────────────────────────────────────────────────────
        store = StoreConfig(
            id=1,
            store_name="金典软装",
            store_phone="0571-88888888",
            store_address="杭州市古墩路欧亚达家居广场",
            workday_start="09:00",
            workday_end="18:00",
            qrcode_base_url=""
        )
        session.add(store)

        await session.commit()
        print("✅ 演示数据写入完成！")


if __name__ == "__main__":
    asyncio.run(seed())
    print("\n🚀 数据库初始化完毕！运行以下命令启动服务：")
    print("   cd /home/tianlj0320/sales-system-dev")
    print("   pip install -r requirements.txt")
    print("   python -m uvicorn main:app --reload --port 8000")
