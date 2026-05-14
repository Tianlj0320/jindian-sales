# V4.0 报表 API 扩展
# 扩展自 app/api/reports.py（V3.0 原版）
from calendar import monthrange
from datetime import date, datetime

from fastapi import APIRouter, Query
from sqlalchemy import and_, desc, func, select

from app.core.response import success_response, error_response
from app.database import async_session
from app.models import Order, InstallationOrder

router = APIRouter(prefix="/api/v4/reports", tags=["V4.0 统计报表"])



def _get_valid_statuses() -> list[str]:
    """有效订单状态（排除取消等）"""
    return [
        "confirmed", "split", "purchasing", "stocked", "processing",
        "completed", "install_order_generated", "installed", "accepted",
    ]


# ─── 每日销售报表 ─────────────────────────────────────────────────────────────
@router.get("/daily", response_model=dict)
async def daily_sales_report(
    report_date: str = Query(None, alias="date", description="报表日期 YYYY-MM-DD，不传则默认今天"),
):
    """
    GET /api/v4/reports/daily
    每日销售报表：订单数 / 销售额 / 收款额
    """
    if not report_date:
        report_date = date.today().strftime("%Y-%m-%d")

    try:
        target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
    except Exception:
        return error_response("日期格式错误，请使用 YYYY-MM-DD")

    async with async_session() as session:
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())

        r = await session.execute(
            select(
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.amount), 0).label("total_amount"),
                func.coalesce(func.sum(Order.received), 0).label("received_amount"),
            ).where(
                and_(
                    Order.order_date >= start.strftime("%Y-%m-%d"),
                    Order.order_date <= end.strftime("%Y-%m-%d"),
                    Order.status_key.in_(_get_valid_statuses()),
                )
            )
        )
        row = r.one()

        return success_response(
            data={
                "date": report_date,
                "order_count": row.order_count or 0,
                "total_amount": float(row.total_amount or 0),
                "received_amount": float(row.received_amount or 0),
                "unpaid_amount": float(row.total_amount or 0) - float(row.received_amount or 0),
            }
        )


# ─── 员工业绩 ─────────────────────────────────────────────────────────────────
@router.get("/staff-performance", response_model=dict)
async def staff_performance_report(
    year: int = Query(default=None),
    month: int = Query(default=None),
    report_date: str = Query(None, alias="date", description="指定月份 YYYY-MM，不传则默认当前月"),
):
    """
    GET /api/v4/reports/staff-performance
    员工业绩（按销售维度，含订单数/金额/评分）
    """
    today = date.today()
    if report_date:
        try:
            y, m = map(int, report_date.split("-"))
            year, month = y, m
        except Exception:
            return error_response("date 格式应为 YYYY-MM")
    elif not year:
        year, month = today.year, today.month

    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)

    async with async_session() as session:
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # 销售业绩
        r = await session.execute(
            select(
                Order.salesperson,
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.amount), 0).label("total_amount"),
                func.coalesce(func.sum(Order.received), 0).label("received_amount"),
            ).where(
                and_(
                    Order.salesperson.isnot(None),
                    Order.salesperson != "",
                    Order.order_date >= start_str,
                    Order.order_date <= end_str,
                    Order.status_key.in_(_get_valid_statuses()),
                )
            ).group_by(Order.salesperson).order_by(desc("total_amount"))
        )
        sales_rows = r.all()

        # 安装工业绩（关联 installation_orders 表）
        ir = await session.execute(
            select(
                InstallationOrder.installer_id,
                func.count(InstallationOrder.id).label("install_count"),
                func.avg(InstallationOrder.quality_score).label("avg_score"),
            ).where(
                and_(
                    InstallationOrder.installer_id.isnot(None),
                    InstallationOrder.scheduled_date >= start_str,
                    InstallationOrder.scheduled_date <= end_str,
                    InstallationOrder.status.in_(["已完成", "已验收"]),
                )
            ).group_by(InstallationOrder.installer_id)
        )
        install_rows = ir.all()

        install_map = {
            row.installer_id: {
                "install_count": row.install_count,
                "avg_score": float(row.avg_score or 0),
            }
            for row in install_rows
        }

        return success_response(
            data={
                "year": year,
                "month": month,
                "sales": [
                    {
                        "salesperson": row.salesperson or "未知",
                        "order_count": row.order_count or 0,
                        "total_amount": float(row.total_amount or 0),
                        "received_amount": float(row.received_amount or 0),
                    }
                    for row in sales_rows
                ],
                "installers": [
                    {
                        "operator_id": op_id,
                        "install_count": data["install_count"],
                        "avg_score": data["avg_score"],
                    }
                    for op_id, data in install_map.items()
                ],
            }
        )


# ─── 产品销售排行 ──────────────────────────────────────────────────────────────
@router.get("/product-sales", response_model=dict)
async def product_sales_rank(
    report_date: str = Query(None, alias="date", description="指定月份 YYYY-MM，不传则默认当前月"),
    top: int = Query(default=10, ge=1, le=50, description="返回前N名"),
):
    """
    GET /api/v4/reports/product-sales
    产品销售排行（按周期，支持TOP N）
    """
    today = date.today()
    if report_date:
        try:
            year, month = map(int, report_date.split("-"))
        except Exception:
            return error_response("date 格式应为 YYYY-MM")
    else:
        year, month = today.year, today.month

    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    async with async_session() as session:
        r = await session.execute(
            select(Order).where(
                and_(
                    Order.order_date >= start_str,
                    Order.order_date <= end_str,
                    Order.status_key.in_(_get_valid_statuses()),
                )
            )
        )
        orders = r.scalars().all()

        prod_sales = {}
        for o in orders:
            for item in (o.items or []):
                key = item.get("product", item.get("name", "未知"))
                qty = int(item.get("qty", 0))
                price = float(item.get("price", 0))
                if key not in prod_sales:
                    prod_sales[key] = {"qty": 0, "amount": 0}
                prod_sales[key]["qty"] += qty
                prod_sales[key]["amount"] += qty * price

        ranked = sorted(prod_sales.items(), key=lambda x: x[1]["amount"], reverse=True)[:top]

        return success_response(
            data={
                "year": year,
                "month": month,
                "top": top,
                "items": [
                    {"rank": i + 1, "product": k, "qty": v["qty"], "amount": v["amount"]}
                    for i, (k, v) in enumerate(ranked)
                ],
            }
        )


# ─── 月度趋势 ─────────────────────────────────────────────────────────────────
@router.get("/trend", response_model=dict)
async def monthly_trend(
    year: int = Query(default=None),
    month: int = Query(default=None),
    report_date: str = Query(None, alias="date", description="指定月份 YYYY-MM，不传则默认当月"),
):
    """
    GET /api/v4/reports/trend
    月度趋势（每日累计）：返回指定月份的每日销售数据
    """
    today = date.today()
    if report_date:
        try:
            y, m = map(int, report_date.split("-"))
            year, month = y, m
        except Exception:
            return error_response("date 格式应为 YYYY-MM")
    elif not year:
        year, month = today.year, today.month

    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    async with async_session() as session:
        r = await session.execute(
            select(
                Order.order_date,
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.amount), 0).label("daily_amount"),
                func.coalesce(func.sum(Order.received), 0).label("daily_received"),
            )
            .where(
                and_(
                    Order.status_key.in_(_get_valid_statuses()),
                    Order.order_date >= start_str,
                    Order.order_date <= end_str,
                )
            )
            .group_by(Order.order_date)
            .order_by(Order.order_date)
        )
        rows = r.all()

        # 构建每日数据（补全当月所有日期，无数据则为0）
        daily_data = {}
        cumulative_amount = 0
        cumulative_received = 0
        for row in rows:
            d = str(row.order_date)
            daily_amount = float(row.daily_amount or 0)
            daily_received = float(row.daily_received or 0)
            cumulative_amount += daily_amount
            cumulative_received += daily_received
            daily_data[d] = {
                "date": d,
                "order_count": row.order_count or 0,
                "daily_amount": daily_amount,
                "daily_received": daily_received,
                "cumulative_amount": round(cumulative_amount, 2),
                "cumulative_received": round(cumulative_received, 2),
            }

        # 补全缺失日期
        from datetime import timedelta
        items = []
        cur = start_date
        while cur <= end_date:
            d = cur.strftime("%Y-%m-%d")
            items.append(daily_data.get(d, {
                "date": d,
                "order_count": 0,
                "daily_amount": 0,
                "daily_received": 0,
                "cumulative_amount": cumulative_amount,
                "cumulative_received": cumulative_received,
            }))
            cur += timedelta(days=1)

        return success_response(
            data={
                "year": year,
                "month": month,
                "items": items,
            }
        )