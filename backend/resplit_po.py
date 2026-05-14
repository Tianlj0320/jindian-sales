"""
重新拆分采购单脚本
用法: python resplit_po.py PO20260508001
将指定采购单的源订单恢复为"已确认"状态，然后按新逻辑重新拆分。
"""
import sys
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, '.')

from sqlalchemy import select, func
from app.database import async_session_factory
from app.domain.order import Order, OrderItem
from app.domain.purchase import PurchaseOrder, PurchaseOrderItem
from app.api.v1.orders import _auto_split_purchase


async def resplit(po_no: str):
    async with async_session_factory() as session:
        # 1. 查找采购单
        result = await session.execute(
            select(PurchaseOrder).where(PurchaseOrder.po_no == po_no)
        )
        po = result.scalar_one_or_none()
        if not po:
            print(f"采购单 {po_no} 不存在")
            return

        order_ids_str = po.order_ids or ""
        print(f"找到采购单: {po_no} (id={po.id})")
        print(f"关联订单: {order_ids_str}")

        # 2. 删除采购单明细
        items = await session.execute(
            select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == po.id)
        )
        for item in items.scalars().all():
            await session.delete(item)

        # 3. 删除采购单
        await session.delete(po)
        await session.flush()
        print(f"已删除原采购单 {po_no}")

        # 4. 恢复关联订单状态为"已确认"
        if order_ids_str:
            ids = [int(x.strip()) for x in order_ids_str.split(",") if x.strip()]
            for oid in ids:
                o_result = await session.execute(select(Order).where(Order.id == oid))
                o = o_result.scalar_one_or_none()
                if o:
                    # 记录历史
                    history = o.history or []
                    history.append({
                        "s": o.status_label,
                        "s2": "已确认",
                        "c": "confirmed",
                        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                        "detail": f"重新拆分：删除原采购单 {po_no}",
                    })
                    o.status_key = "confirmed"
                    o.status_label = "已确认"
                    o.status_color = "#67c23a"
                    o.history = history
                    print(f"已恢复订单 {o.order_no} (id={oid}) → 已确认")
        else:
            print("警告：采购单没有关联订单")

        await session.flush()

        # 5. 重新拆分（处理所有已确认的订单）
        print("\n正在按新逻辑重新拆分...")
        po_nos = await _auto_split_purchase(session)
        if po_nos:
            print(f"重新拆分完成，生成采购单: {', '.join(po_nos)}")
        else:
            print("没有已确认的订单需要拆分")

if __name__ == "__main__":
    po_no = sys.argv[1] if len(sys.argv) > 1 else "PO20260508001"
    asyncio.run(resplit(po_no))
