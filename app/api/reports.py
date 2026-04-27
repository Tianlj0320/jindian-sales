# app/api/reports.py
from fastapi import APIRouter, Query
from app.database import async_session
from app.models import Order, Customer, Employee, FinanceRecord
from sqlalchemy import select, func, and_, desc
from datetime import datetime, date, timedelta
from calendar import monthrange

router = APIRouter(prefix="/api/reports", tags=["统计报表"])


def get_month_range(year: int, month: int):
    start = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end = date(year, month, last_day)
    return start, end


@router.get("/sales", response_model=dict)
async def sales_report(
    year: int = Query(default=date.today().year),
    month: int = Query(default=date.today().month)
):
    """月度销售报表"""
    async with async_session() as session:
        start, end = get_month_range(year, month)

        r = await session.execute(
            select(func.count(Order.id), func.sum(Order.amount))
            .where(and_(
                Order.status_key.notin_(["cancelled", "created"]),
                Order.order_date >= start,
                Order.order_date <= end
            ))
        )
        row = r.one()
        order_count = row[0] or 0
        total_amount = row[1] or 0

        # 按状态分布
        status_dist = {}
        for sk in ["confirmed", "measured", "stocked", "processing", "install", "installed", "completed"]:
            cr = await session.execute(
                select(func.count(Order.id)).where(
                    and_(
                        Order.status_key == sk,
                        Order.order_date >= start,
                        Order.order_date <= end
                    )
                )
            )
            status_dist[sk] = cr.scalar() or 0

        await session.commit()
        return {
            "success": True, "data": {
                "year": year, "month": month,
                "order_count": order_count,
                "total_amount": float(total_amount),
                "avg_amount": float(total_amount / order_count) if order_count else 0,
                "status_distribution": status_dist
            }
        }


@router.get("/product-rank", response_model=dict)
async def product_rank(
    year: int = Query(default=date.today().year),
    month: int = Query(default=date.today().month),
    top: int = Query(default=10, le=50)
):
    """产品销量排行"""
    async with async_session() as session:
        start, end = get_month_range(year, month)

        r = await session.execute(
            select(Order).where(and_(
                Order.status_key.notin_(["cancelled"]),
                Order.order_date >= start,
                Order.order_date <= end
            ))
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
        await session.commit()
        return {
            "success": True, "data": {
                "year": year, "month": month,
                "items": [{"product": k, "qty": v["qty"], "amount": v["amount"]} for k, v in ranked]
            }
        }


@router.get("/employee-performance", response_model=dict)
async def employee_report(
    year: int = Query(default=date.today().year),
    month: int = Query(default=date.today().month)
):
    """员工业绩报表"""
    async with async_session() as session:
        start, end = get_month_range(year, month)

        r = await session.execute(
            select(Order.salesperson, func.count(Order.id), func.sum(Order.amount))
            .where(and_(
                Order.salesperson.isnot(None),
                Order.status_key.notin_(["cancelled"]),
                Order.order_date >= start,
                Order.order_date <= end
            ))
            .group_by(Order.salesperson)
            .order_by(desc(func.sum(Order.amount)))
        )
        rows = r.all()

        await session.commit()
        return {
            "success": True, "data": {
                "year": year, "month": month,
                "items": [{
                    "salesperson": row[0] or "未知",
                    "order_count": row[1] or 0,
                    "total_amount": float(row[2] or 0)
                } for row in rows]
            }
        }


@router.get("/trend", response_model=dict)
async def sales_trend(
    year: int = Query(default=date.today().year),
    month: int = Query(default=date.today().month)
):
    """月度趋势（每日累计）"""
    async with async_session() as session:
        start, end = get_month_range(year, month)

        r = await session.execute(
            select(Order.order_date, func.sum(Order.amount))
            .where(and_(
                Order.status_key.notin_(["cancelled", "created"]),
                Order.order_date >= start,
                Order.order_date <= end
            ))
            .group_by(Order.order_date)
            .order_by(Order.order_date)
        )
        rows = r.all()

        await session.commit()
        return {
            "success": True, "data": {
                "items": [{"date": str(row[0]), "amount": float(row[1] or 0)} for row in rows]
            }
        }
