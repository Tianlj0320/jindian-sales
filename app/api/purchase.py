# app/api/purchase.py
from datetime import datetime

from fastapi import APIRouter, Body, Query
from sqlalchemy import and_, func, select

from app.core.response import success_response, error_response
from app.database import async_session
from app.models import Product, Purchase
from app.schemas import CommonResponse

router = APIRouter(prefix="/api/purchase", tags=["采购管理"])


@router.get("", response_model=dict)
async def list_purchases(
    status: str | None = Query(None),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    async with async_session() as session:
        conditions = []
        if status:
            conditions.append(Purchase.status == status)
        if keyword:
            kw = f"%{keyword}%"
            conditions.append(Purchase.supplier_name.ilike(kw))

        query = select(Purchase)
        if conditions:
            query = query.where(and_(*conditions))

        r = await session.execute(
            select(func.count()).select_from(Purchase).where(and_(*conditions))
            if conditions
            else select(func.count()).select_from(Purchase)
        )
        total = r.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(Purchase.created_at.desc()).offset(offset).limit(page_size)
        result = await session.execute(query)
        items = result.scalars().all()

        await session.commit()
        return success_response(
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [
                    {
                        "id": p.id,
                        "po_no": p.po_no or "",
                        "supplier_id": p.supplier_id,
                        "supplier_name": p.supplier_name or "",
                        "contact": p.contact or "",
                        "phone": p.phone or "",
                        "amount": float(p.amount or 0),
                        "paid": float(p.paid or 0),
                        "debt": float(p.debt or 0),
                        "status": p.status or "待采购",
                        "order_date": str(p.order_date) if p.order_date else "",
                        "expected_date": str(p.expected_date) if p.expected_date else "",
                        "items": p.items or [],
                        "remark": p.remark or "",
                        "created_at": str(p.created_at)[:19] if p.created_at else "",
                    }
                    for p in items
                ],
            }
        )


@router.post("", response_model=CommonResponse)
async def create_purchase(req: dict = Body(...)):
    async with async_session() as session:
        today = datetime.now().strftime("%Y%m%d")
        seq_r = await session.execute(
            select(func.count(Purchase.id)).where(Purchase.po_no.like(f"PO{today}%"))
        )
        seq = (seq_r.scalar() or 0) + 1
        po_no = f"PO{today}{seq:03d}"

        items = req.get("items", [])
        amount = sum(float(i.get("price", 0)) * float(i.get("qty", 0)) for i in items)

        p = Purchase(
            po_no=po_no,
            supplier_id=req.get("supplier_id"),
            supplier_name=req.get("supplier_name", ""),
            contact=req.get("contact", ""),
            phone=req.get("phone", ""),
            amount=amount,
            paid=0,
            debt=amount,
            status="待采购",
            order_date=datetime.strptime(req.get("order_date", today), "%Y-%m-%d").date(),
            expected_date=datetime.strptime(req.get("expected_date", today), "%Y-%m-%d").date()
            if req.get("expected_date")
            else None,
            items=items,
            remark=req.get("remark", ""),
        )
        session.add(p)
        await session.commit()
        await session.refresh(p)
        return success_response(data={"id": p.id, "po_no": po_no})


@router.put("/{po_id}/status", response_model=CommonResponse)
async def update_purchase_status(po_id: int, req: dict = Body(...)):
    async with async_session() as session:
        r = await session.execute(select(Purchase).where(Purchase.id == po_id))
        p = r.scalar_one_or_none()
        if not p:
            return error_response(error="采购单不存在")

        new_status = req.get("status", "已完成")
        p.status = new_status

        if new_status == "已完成":
            # 同时入库：增加产品库存
            for item in p.items or []:
                pr = await session.execute(
                    select(Product).where(Product.id == item.get("product_id"))
                )
                prod = pr.scalar_one_or_none()
                if prod:
                    prod.stock = (prod.stock or 0) + float(item.get("qty", 0))

        await session.commit()
        return success_response(data={"id": po_id, "status": new_status})
