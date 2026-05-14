"""
仪表盘 & 报表 API
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, select

from app.api.deps import CurrentUserDep, SessionDep
from app.core.response import success
from app.domain.customer import Customer
from app.domain.finance import FinanceExpense, FinanceReceivable
from app.domain.installation import InstallationOrder
from app.domain.order import Order, OrderItem
from app.domain.product import Product

router = APIRouter(prefix="/api/v1/dashboard", tags=["仪表盘"])


@router.get("")
async def get_dashboard(session: SessionDep, current_user: CurrentUserDep):
    """首页仪表盘统计"""
    today = date.today()
    month_start = today.replace(day=1)

    # 今日订单数
    today_orders = (await session.execute(
        select(func.count(Order.id)).where(func.date(Order.created_at) == today)
    )).scalar() or 0

    # 本月销售额
    month_sales = (await session.execute(
        select(func.coalesce(func.sum(Order.amount), 0)).where(
            and_(
                Order.status_key.notin_(["cancelled"]),
                func.date(Order.created_at) >= month_start,
            )
        )
    )).scalar() or 0

    # 待安装
    pending_install = (await session.execute(
        select(func.count(Order.id)).where(
            Order.status_key.in_(["completed", "install_scheduled"])
        )
    )).scalar() or 0

    # 逾期订单
    overdue = (await session.execute(
        select(func.count(Order.id)).where(
            and_(
                Order.status_key.notin_(["accepted", "cancelled", "after_sale"]),
                Order.delivery_date != "",
                Order.delivery_date < str(today),
            )
        )
    )).scalar() or 0

    # 待收款
    pending_payment = (await session.execute(
        select(func.count(Order.id)).where(
            and_(Order.debt > 0, Order.status_key.notin_(["cancelled"]))
        )
    )).scalar() or 0

    # 客户总数
    total_customers = (await session.execute(
        select(func.count(Customer.id)).where(Customer.is_deleted == 0)
    )).scalar() or 0

    # 低库存预警
    low_stock = (await session.execute(
        select(func.count(Product.id)).where(
            Product.stock <= Product.safety_stock,
            Product.safety_stock > 0,
        )
    )).scalar() or 0

    return success(data={
        "today_orders": today_orders,
        "month_sales": float(month_sales),
        "pending_install": pending_install,
        "overdue_orders": overdue,
        "pending_payment": pending_payment,
        "total_customers": total_customers,
        "low_stock": low_stock,
    })


# ─── 销售报表 ─────────────────────────────────────────────────


@router.get("/sales-report")
async def get_sales_report(
    session: SessionDep,
    current_user: CurrentUserDep,
    year: int = Query(default=None),
    month: int = Query(default=None),
):
    """月度销售报表"""
    today = date.today()
    y = year or today.year
    m = month or today.month

    import calendar
    m_start = date(y, m, 1)
    m_end = date(y, m, calendar.monthrange(y, m)[1])

    # 本月销售额
    sales = (await session.execute(
        select(func.coalesce(func.sum(Order.amount), 0)).where(
            and_(
                func.date(Order.created_at) >= m_start,
                func.date(Order.created_at) <= m_end,
                Order.status_key.notin_(["cancelled"]),
            )
        )
    )).scalar() or 0

    # 本月订单数
    order_count = (await session.execute(
        select(func.count(Order.id)).where(
            and_(
                func.date(Order.created_at) >= m_start,
                func.date(Order.created_at) <= m_end,
            )
        )
    )).scalar() or 0

    # 本月收款
    received = (await session.execute(
        select(func.coalesce(func.sum(Order.received), 0)).where(
            and_(
                func.date(Order.created_at) >= m_start,
                func.date(Order.created_at) <= m_end,
            )
        )
    )).scalar() or 0

    # 本月费用
    expense = (await session.execute(
        select(func.coalesce(func.sum(FinanceExpense.amount), 0)).where(
            and_(
                FinanceExpense.expense_date >= m_start,
                FinanceExpense.expense_date <= m_end,
            )
        )
    )).scalar() or 0

    # 订单状态分布
    status_dist = (await session.execute(
        select(Order.status_key, func.count(Order.id))
        .where(func.date(Order.created_at) >= m_start, func.date(Order.created_at) <= m_end)
        .group_by(Order.status_key)
    )).all()

    return success(data={
        "year": y,
        "month": m,
        "total_sales": float(sales),
        "total_received": float(received),
        "total_expense": float(expense),
        "order_count": order_count,
        "status_distribution": {k: v for k, v in status_dist},
    })


# ─── 产品排行 ─────────────────────────────────────────────────


@router.get("/product-rank")
async def get_product_rank(
    session: SessionDep,
    current_user: CurrentUserDep,
    year: int = Query(default=None),
    month: int = Query(default=None),
):
    """产品销售排行"""
    today = date.today()
    y = year or today.year
    m = month or today.month

    import calendar
    m_start = date(y, m, 1)
    m_end = date(y, m, calendar.monthrange(y, m)[1])

    result = await session.execute(
        select(
            OrderItem.product_name,
            func.sum(OrderItem.qty).label("total_qty"),
            func.sum(OrderItem.amount).label("total_amount"),
            func.count(func.distinct(OrderItem.order_id)).label("order_count"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .where(
            and_(
                func.date(Order.created_at) >= m_start,
                func.date(Order.created_at) <= m_end,
                Order.status_key.notin_(["cancelled"]),
            )
        )
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.amount).desc())
        .limit(20)
    )
    rows = result.all()

    return success(data=[
        {
            "product_name": r[0],
            "total_qty": float(r[1] or 0),
            "total_amount": float(r[2] or 0),
            "order_count": r[3] or 0,
        }
        for r in rows
    ])
