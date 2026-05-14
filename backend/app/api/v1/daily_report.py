"""
日报/资金日报 API
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep
from app.core.response import paginated, success
from app.domain.customer import Customer
from app.domain.deposit import Deposit
from app.domain.finance import FinanceReceivable
from app.domain.installation import InstallationOrder
from app.domain.order import Order
from app.domain.purchase import PurchaseOrder

router = APIRouter(prefix="/api/v1/daily-report", tags=["日报/资金日报"])


def _extract_order_no_from_remark(remark: str) -> str | None:
    """从定金抵扣备注中提取订单号

    备注格式: "订单 XD20260513001 抵扣定金"
    """
    if "订单 " not in remark:
        return None
    parts = remark.split("订单 ")
    if len(parts) < 2:
        return None
    return parts[1].split()[0] if parts[1].split() else None


@router.get("")
async def get_daily_report(session: SessionDep, current_user: CurrentUserDep):
    """获取今日日报"""
    today = date.today()
    tomorrow = today + timedelta(days=1)

    # ── 1. 今日定金 ──────────────────────────────────────────────
    deposit_result = await session.execute(
        select(Deposit, Customer.name)
        .join(Customer, Deposit.customer_id == Customer.id)
        .where(
            Deposit.received_at == today,
            Deposit.amount > 0,
        )
    )
    deposit_rows = deposit_result.all()

    # 查所有客户的抵扣记录（判断定金是否已关联订单）
    customer_ids = [r.Deposit.customer_id for r in deposit_rows]
    deductions_map: dict[int, list[str | None]] = {}
    if customer_ids:
        ded_result = await session.execute(
            select(Deposit).where(
                Deposit.customer_id.in_(customer_ids),
                Deposit.amount < 0,
            )
        )
        for d in ded_result.scalars().all():
            order_no = _extract_order_no_from_remark(d.remark or "")
            deductions_map.setdefault(d.customer_id, []).append(order_no)

    deposit_total = 0.0
    deposit_items = []
    for row in deposit_rows:
        dep = row.Deposit
        cust_name = row.name
        amount = float(dep.amount)
        deposit_total += amount

        has_order = dep.customer_id in deductions_map
        linked_order_no = None
        if has_order and deductions_map[dep.customer_id]:
            linked_order_no = deductions_map[dep.customer_id][0]

        deposit_items.append({
            "customer_name": cust_name,
            "amount": amount,
            "payment_method": dep.payment_method or "",
            "has_order": has_order,
            "order_no": linked_order_no,
        })

    # ── 2. 今日新订单 ────────────────────────────────────────────
    order_result = await session.execute(
        select(Order)
        .where(func.date(Order.created_at) == today)
        .order_by(Order.id.desc())
    )
    today_orders = order_result.scalars().all()

    order_items = [
        {
            "id": o.id,
            "order_no": o.order_no,
            "customer_name": o.customer_name,
            "amount": float(o.amount),
        }
        for o in today_orders
    ]
    orders_total = sum(float(o.amount) for o in today_orders)

    # ── 3. 待采购 ────────────────────────────────────────────────
    po_result = await session.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.status.notin_(["已完成", "已取消"]),
        )
    )
    pending_pos = po_result.scalars().all()

    pending_purchase_items = []
    for po in pending_pos:
        # 从采购单获取客户名
        customer_name = ""
        order_ids_str = po.order_ids or ""
        if order_ids_str:
            oid_list = [int(x) for x in order_ids_str.split(",") if x.strip().isdigit()]
            if oid_list:
                o_result = await session.execute(
                    select(Order).where(Order.id.in_(oid_list)).limit(1)
                )
                first_order = o_result.scalar_one_or_none()
                if first_order:
                    customer_name = first_order.customer_name

        suppliers = [po.supplier_name] if po.supplier_name else []

        pending_purchase_items.append({
            "order_no": po.po_no,
            "customer_name": customer_name,
            "suppliers": suppliers,
        })

    # ── 4. 待安装 ────────────────────────────────────────────────
    ins_result = await session.execute(
        select(InstallationOrder).where(
            InstallationOrder.scheduled_date.in_([today, tomorrow]),
            InstallationOrder.status != "已完成",
        )
    )
    pending_ins = ins_result.scalars().all()

    pending_install_items = [
        {
            "order_no": ins.ins_no,
            "customer_name": ins.customer_name,
            "install_date": str(ins.scheduled_date) if ins.scheduled_date else None,
        }
        for ins in pending_ins
    ]

    # ── 5. 今日收款 ──────────────────────────────────────────────
    recv_result = await session.execute(
        select(FinanceReceivable).where(
            func.date(FinanceReceivable.updated_at) == today,
        )
    )
    today_recvs = recv_result.scalars().all()

    collections_total = 0.0
    collections_items = []
    for recv in today_recvs:
        amount = float(recv.received_amount)
        collections_total += amount
        collections_items.append({
            "customer_name": recv.customer_name,
            "amount": amount,
            "payment_method": "转账",  # 暂无付款方式记录，默认为转账
            "order_no": recv.order_no,
        })

    return success(data={
        "date": str(today),
        "deposits": {
            "today_total": deposit_total,
            "items": deposit_items,
        },
        "new_orders": {
            "count": len(today_orders),
            "total_amount": orders_total,
            "items": order_items,
        },
        "pending_purchases": {
            "count": len(pending_pos),
            "items": pending_purchase_items,
        },
        "pending_installations": {
            "count": len(pending_ins),
            "items": pending_install_items,
        },
        "collections": {
            "today_total": collections_total,
            "items": collections_items,
        },
    })


@router.get("/history")
async def get_daily_report_history(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    date_from: str = Query(description="开始日期 YYYY-MM-DD"),
    date_to: str = Query(description="结束日期 YYYY-MM-DD"),
):
    """日报历史列表"""
    d_from = date.fromisoformat(date_from)
    d_to = date.fromisoformat(date_to)

    # 按日期汇总定金
    dep_rows = (await session.execute(
        select(
            Deposit.received_at,
            func.coalesce(func.sum(Deposit.amount), 0),
        )
        .where(
            Deposit.received_at >= d_from,
            Deposit.received_at <= d_to,
            Deposit.amount > 0,
        )
        .group_by(Deposit.received_at)
    )).all()
    dep_map = {str(r[0]): float(r[1]) for r in dep_rows}

    # 按日期汇总新订单
    order_rows = (await session.execute(
        select(
            func.date(Order.created_at),
            func.count(Order.id),
            func.coalesce(func.sum(Order.amount), 0),
        )
        .where(
            func.date(Order.created_at) >= d_from,
            func.date(Order.created_at) <= d_to,
        )
        .group_by(func.date(Order.created_at))
    )).all()
    order_map: dict[str, dict] = {}
    for r in order_rows:
        d = str(r[0])
        order_map[d] = {"count": r[1], "amount": float(r[2] or 0)}

    # 按日期汇总收款
    coll_rows = (await session.execute(
        select(
            func.date(FinanceReceivable.updated_at),
            func.coalesce(func.sum(FinanceReceivable.received_amount), 0),
        )
        .where(
            func.date(FinanceReceivable.updated_at) >= d_from,
            func.date(FinanceReceivable.updated_at) <= d_to,
        )
        .group_by(func.date(FinanceReceivable.updated_at))
    )).all()
    coll_map = {str(r[0]): float(r[1]) for r in coll_rows}

    # 构建每日条目（倒序）
    items = []
    current = d_to
    while current >= d_from:
        d = str(current)
        ord_data = order_map.get(d, {})
        items.append({
            "date": d,
            "deposits_total": dep_map.get(d, 0),
            "orders_count": ord_data.get("count", 0),
            "orders_total": ord_data.get("amount", 0),
            "collections_total": coll_map.get(d, 0),
        })
        current -= timedelta(days=1)

    total = len(items)
    offset = (page.page - 1) * page.page_size
    paged_items = items[offset:offset + page.page_size]

    return paginated(
        items=paged_items,
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.get("/deposits/unlinked")
async def get_unlinked_deposits(
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """获取未关联订单的定金（黄标提醒项）"""
    # 查询所有有过抵扣记录的客户ID
    ded_cust_result = await session.execute(
        select(Deposit.customer_id)
        .where(Deposit.amount < 0)
        .distinct()
    )
    ded_customer_ids = ded_cust_result.scalars().all()

    # 筛选：定金且客户未曾抵扣（未关联订单）
    conditions = [Deposit.amount > 0]
    if ded_customer_ids:
        conditions.append(~Deposit.customer_id.in_(ded_customer_ids))

    result = await session.execute(
        select(Deposit, Customer.name)
        .join(Customer, Deposit.customer_id == Customer.id)
        .where(and_(*conditions))
        .order_by(Deposit.received_at.desc(), Deposit.created_at.desc())
    )
    rows = result.all()

    items = [
        {
            "id": r.Deposit.id,
            "customer_id": r.Deposit.customer_id,
            "customer_name": r.name,
            "amount": float(r.Deposit.amount),
            "balance": float(r.Deposit.balance),
            "payment_method": r.Deposit.payment_method or "",
            "received_at": str(r.Deposit.received_at) if r.Deposit.received_at else None,
            "operator_name": r.Deposit.operator_name or "",
            "remark": r.Deposit.remark or "",
        }
        for r in rows
    ]

    return success(data=items)
