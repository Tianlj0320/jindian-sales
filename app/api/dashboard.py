# app/api/dashboard.py
from fastapi import APIRouter
from app.database import async_session
from app.models import Order, Customer
from app.schemas import DashboardResponse, DashboardData
from sqlalchemy import select, func, and_
from datetime import date, timedelta

router = APIRouter(prefix="/api/dashboard", tags=["首页统计"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard():
    async with async_session() as session:
        today = date.today()
        month_start = today.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # 今日新增订单
        r = await session.execute(select(func.count(Order.id)).where(func.date(Order.created_at) == today))
        today_orders = r.scalar() or 0

        # 本月销售额
        r = await session.execute(
            select(func.sum(Order.amount)).where(
                and_(
                    Order.status_key.notin_(["cancelled", "created"]),
                    func.date(Order.created_at) >= month_start,
                    func.date(Order.created_at) <= month_end
                )
            )
        )
        month_sales = r.scalar() or 0

        # 待安装
        r = await session.execute(select(func.count(Order.id)).where(Order.status_key == "install"))
        pending_install = r.scalar() or 0

        # 逾期订单
        r = await session.execute(
            select(func.count(Order.id)).where(
                and_(
                    Order.status_key.notin_(["completed", "installed", "cancelled"]),
                    Order.delivery_date < str(today)
                )
            )
        )
        overdue_orders = r.scalar() or 0

        # 待收款
        r = await session.execute(
            select(func.count(Order.id)).where(
                and_(Order.debt > 0, Order.status_key.notin_(["cancelled"]))
            )
        )
        pending_payment = r.scalar() or 0

        # 客户总数
        r = await session.execute(select(func.count(Customer.id)))
        total_customers = r.scalar() or 0

        await session.commit()

        return DashboardResponse(success=True, data=DashboardData(
            today_orders=today_orders,
            month_sales=float(month_sales),
            pending_install=pending_install,
            overdue_orders=overdue_orders,
            pending_payment=pending_payment,
            total_customers=total_customers
        ))
