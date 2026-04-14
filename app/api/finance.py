# app/api/finance.py
from fastapi import APIRouter, Query, Body
from app.database import async_session
from app.models import FinanceRecord, Order
from app.schemas import CommonResponse
from sqlalchemy import select, func, and_
from datetime import datetime, date
from typing import Optional

router = APIRouter(prefix="/api/finance", tags=["财务结算"])


@router.get("/records", response_model=dict)
async def list_records(
    record_type: Optional[str] = Query(None, description="receive/pay/expense"),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
):
    async with async_session() as session:
        conditions = []
        if record_type:
            conditions.append(FinanceRecord.record_type == record_type)
        if keyword:
            kw = f"%{keyword}%"
            conditions.append(FinanceRecord.customer_name.ilike(kw))

        query = select(FinanceRecord)
        if conditions:
            query = query.where(and_(*conditions))

        r = await session.execute(
            select(func.count()).select_from(FinanceRecord)
            .where(and_(*conditions)) if conditions
            else select(func.count()).select_from(FinanceRecord)
        )
        total = r.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(FinanceRecord.created_at.desc()).offset(offset).limit(page_size)
        result = await session.execute(query)
        records = result.scalars().all()

        await session.commit()
        return {
            "success": True, "total": total, "page": page, "page_size": page_size,
            "items": [{
                "id": r.id, "record_type": r.record_type or "",
                "order_id": r.order_id, "order_no": r.order_no or "",
                "customer_name": r.customer_name or "",
                "amount": float(r.amount or 0),
                "method": r.method or "转账",
                "operator": r.operator or "",
                "remark": r.remark or "",
                "created_at": str(r.created_at)[:19] if r.created_at else ""
            } for r in records]
        }


@router.get("/summary", response_model=dict)
async def get_summary():
    """财务摘要：本期收支汇总"""
    async with async_session() as session:
        today = date.today()
        month_start = today.replace(day=1)

        # 本月收款
        r = await session.execute(
            select(func.sum(FinanceRecord.amount)).where(
                and_(
                    FinanceRecord.record_type == "receive",
                    func.date(FinanceRecord.created_at) >= month_start
                )
            )
        )
        month_receive = r.scalar() or 0

        # 本月付款
        r = await session.execute(
            select(func.sum(FinanceRecord.amount)).where(
                and_(
                    FinanceRecord.record_type == "pay",
                    func.date(FinanceRecord.created_at) >= month_start
                )
            )
        )
        month_pay = r.scalar() or 0

        # 本月费用
        r = await session.execute(
            select(func.sum(FinanceRecord.amount)).where(
                and_(
                    FinanceRecord.record_type == "expense",
                    func.date(FinanceRecord.created_at) >= month_start
                )
            )
        )
        month_expense = r.scalar() or 0

        # 全部欠款
        r = await session.execute(select(func.sum(Order.debt)).where(Order.debt > 0))
        total_debt = r.scalar() or 0

        await session.commit()
        return {
            "success": True, "data": {
                "month_receive": float(month_receive),
                "month_pay": float(month_pay),
                "month_expense": float(month_expense),
                "total_debt": float(total_debt)
            }
        }


@router.post("/receive", response_model=CommonResponse)
async def record_receive(req: dict = Body(...)):
    """记录收款"""
    async with async_session() as session:
        record = FinanceRecord(
            record_type="receive",
            order_id=req.get("order_id"),
            order_no=req.get("order_no", ""),
            customer_name=req.get("customer_name", ""),
            amount=float(req.get("amount", 0)),
            method=req.get("method", "转账"),
            operator=req.get("operator", ""),
            remark=req.get("remark", "")
        )
        session.add(record)

        # 更新订单已收款
        if req.get("order_id"):
            r = await session.execute(select(Order).where(Order.id == req.get("order_id")))
            o = r.scalar_one_or_none()
            if o:
                o.received = float(o.received or 0) + float(req.get("amount", 0))
                o.debt = max(0, float(o.amount or 0) - float(o.received or 0))

        await session.commit()
        return CommonResponse(success=True, data={"id": record.id})


@router.post("/pay", response_model=CommonResponse)
async def record_pay(req: dict = Body(...)):
    """记录付款"""
    async with async_session() as session:
        record = FinanceRecord(
            record_type="pay",
            order_id=req.get("order_id"),
            order_no=req.get("order_no", ""),
            customer_name=req.get("customer_name", ""),
            amount=float(req.get("amount", 0)),
            method=req.get("method", "转账"),
            operator=req.get("operator", ""),
            remark=req.get("remark", "")
        )
        session.add(record)
        await session.commit()
        return CommonResponse(success=True, data={"id": record.id})


@router.post("/expense", response_model=CommonResponse)
async def record_expense(req: dict = Body(...)):
    """记录费用"""
    async with async_session() as session:
        record = FinanceRecord(
            record_type="expense",
            order_id=req.get("order_id"),
            order_no=req.get("order_no", ""),
            customer_name=req.get("customer_name", ""),
            amount=float(req.get("amount", 0)),
            method=req.get("method", "现金"),
            operator=req.get("operator", ""),
            remark=req.get("remark", "")
        )
        session.add(record)
        await session.commit()
        return CommonResponse(success=True, data={"id": record.id})
