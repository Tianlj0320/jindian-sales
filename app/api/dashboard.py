# app/api/dashboard.py
from datetime import date, timedelta

from fastapi import APIRouter
from sqlalchemy import and_, func, select

from app.database import async_session
from app.models import Customer, Order, InstallationOrder, Product
from app.core.response import success_response
from app.schemas import DashboardData, DashboardResponse

router = APIRouter(prefix="/api/dashboard", tags=["首页统计"])


# ── V3.0 ──────────────────────────────────────────────────────────────────────
@router.get("", response_model=DashboardResponse)
async def get_dashboard():
    async with async_session() as session:
        today = date.today()
        month_start = today.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # 今日新增订单
        r = await session.execute(
            select(func.count(Order.id)).where(func.date(Order.created_at) == today)
        )
        today_orders = r.scalar() or 0

        # 本月销售额（排除取消/待确认）
        r = await session.execute(
            select(func.sum(Order.amount)).where(
                and_(
                    Order.status_key.notin_(["cancelled", "created", "initial"]),
                    func.date(Order.created_at) >= month_start,
                    func.date(Order.created_at) <= month_end,
                )
            )
        )
        month_sales = r.scalar() or 0

        # 待安装 = 已派工（install_order_generated）+ 已安装待验收（installed）
        r = await session.execute(
            select(func.count(Order.id)).where(
                Order.status_key.in_(["install_order_generated", "installed"])
            )
        )
        pending_install = r.scalar() or 0

        # 逾期订单（已过 delivery_date 但未完成/未安装/未取消）
        r = await session.execute(
            select(func.count(Order.id)).where(
                and_(
                    Order.status_key.notin_(["completed", "installed", "cancelled", "accepted"]),
                    Order.delivery_date.isnot(None),
                    Order.delivery_date < str(today),
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
        r = await session.execute(
            select(func.count(Customer.id)).where(Customer.is_deleted == False)
        )
        total_customers = r.scalar() or 0

        await session.commit()

        return DashboardResponse(
            success=True,
            data=DashboardData(
                today_orders=today_orders,
                month_sales=float(month_sales),
                pending_install=pending_install,
                overdue_orders=overdue_orders,
                pending_payment=pending_payment,
                total_customers=total_customers,
            ),
        )


# ── V4.0 ──────────────────────────────────────────────────────────────────────
@router.get("/v4", response_model=dict)
async def get_dashboard_v4():
    """
    GET /api/dashboard/v4 - V4.0 仪表盘增强版
    包含：今日/本月统计 + 待处理事项 + 库存预警 + 销售趋势
    """
    async with async_session() as session:
        today = date.today()
        month_start = today.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        month_start_str = month_start.strftime("%Y-%m-%d")
        month_end_str = month_end.strftime("%Y-%m-%d")

        # 有效订单状态（排除取消/草稿）
        valid_statuses = [
            "confirmed", "split", "purchasing", "partial_in", "stocked",
            "processing", "completed", "install_order_generated", "installed", "accepted",
        ]

        # 今日统计
        r = await session.execute(
            select(
                func.count(Order.id).label("cnt"),
                func.coalesce(func.sum(Order.amount), 0).label("amt"),
                func.coalesce(func.sum(Order.received), 0).label("recv"),
            ).where(
                and_(
                    Order.status_key.in_(valid_statuses),
                    func.date(Order.created_at) == today,
                )
            )
        )
        today_row = r.one()

        # 本月统计
        r = await session.execute(
            select(
                func.count(Order.id).label("cnt"),
                func.coalesce(func.sum(Order.amount), 0).label("amt"),
                func.coalesce(func.sum(Order.received), 0).label("recv"),
            ).where(
                and_(
                    Order.status_key.in_(valid_statuses),
                    func.date(Order.created_at) >= month_start_str,
                    func.date(Order.created_at) <= month_end_str,
                )
            )
        )
        month_row = r.one()

        # 待安装单数（已派工+已安装）
        r = await session.execute(
            select(func.count(Order.id)).where(
                Order.status_key.in_(["install_order_generated", "installed"])
            )
        )
        pending_install = r.scalar() or 0

        # 待验收安装单
        r = await session.execute(
            select(func.count(InstallationOrder.id)).where(
                InstallationOrder.status.in_(["已分配", "已安装"])
            )
        )
        pending_accept = r.scalar() or 0

        # 逾期订单
        r = await session.execute(
            select(func.count(Order.id)).where(
                and_(
                    Order.status_key.notin_(["completed", "installed", "cancelled", "accepted"]),
                    Order.delivery_date.isnot(None),
                    Order.delivery_date < str(today),
                )
            )
        )
        overdue_orders = r.scalar() or 0

        # 待收款订单数 + 金额
        r = await session.execute(
            select(
                func.count(Order.id),
                func.coalesce(func.sum(Order.debt), 0),
            ).where(and_(Order.debt > 0, Order.status_key.notin_(["cancelled"])))
        )
        debt_row = r.one()

        # 客户总数
        r = await session.execute(
            select(func.count(Customer.id)).where(Customer.is_deleted == False)
        )
        total_customers = r.scalar() or 0

        # 库存预警数（stock <= min_stock 的产品）
        r = await session.execute(
            select(func.count()).select_from(Product).where(
                and_(Product.stock.isnot(None), Product.stock <= 0)
            )
        )
        low_stock_count = r.scalar() or 0

        await session.commit()

        return success_response(
            data={
                "today": {
                    "order_count": today_row.cnt or 0,
                    "order_amount": float(today_row.amt or 0),
                    "received_amount": float(today_row.recv or 0),
                },
                "month": {
                    "order_count": month_row.cnt or 0,
                    "order_amount": float(month_row.amt or 0),
                    "received_amount": float(month_row.recv or 0),
                    "unpaid_amount": float(month_row.amt or 0) - float(month_row.recv or 0),
                },
                "pending": {
                    "install_orders": pending_install,
                    "pending_acceptance": pending_accept,
                    "overdue_orders": overdue_orders,
                    "debt_orders": debt_row[0] or 0,
                    "debt_amount": float(debt_row[1] or 0),
                    "low_stock_products": low_stock_count,
                },
                "total_customers": total_customers,
            }
        )
