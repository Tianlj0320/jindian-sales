# app/api/purchase.py
from datetime import datetime

from fastapi import APIRouter, Body, Query
from sqlalchemy import and_, func, select

from app.core.response import success_response, error_response
from app.database import async_session
from app.models import Product, Purchase, WarehouseRecord, InventoryFlow
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


@router.delete("/{po_id}", response_model=CommonResponse)
async def delete_purchase(po_id: int):
    async with async_session() as session:
        r = await session.execute(select(Purchase).where(Purchase.id == po_id))
        p = r.scalar_one_or_none()
        if not p:
            return error_response(error="采购单不存在")
        await session.delete(p)
        await session.commit()
        return success_response(message="删除成功")


# ─── V4.0 合入：分批收货逻辑 ─────────────────────────────────────────────────


@router.put("/{po_id}/receive", response_model=CommonResponse)
async def receive_purchase(po_id: int, req: dict = Body(...)):
    """
    分批收货端点（合入 V4.0 purchases_v4.py partial_in 逻辑）
    支持同一采购单多次到货，每次传入本次到货明细。
    到货后：写入 WarehouseRecord + InventoryFlow + 更新产品库存
    自动更新采购单状态（部分到货 / 全部到货）
    """
    arrived_items = req.get("items", [])
    if not arrived_items:
        return error_response(error="到货明细不能为空")

    async with async_session() as session:
        r = await session.execute(select(Purchase).where(Purchase.id == po_id))
        p = r.scalar_one_or_none()
        if not p:
            return error_response(error="采购单不存在")

        if p.status in ("已完成", "已取消"):
            return error_response(error=f"采购单状态为{p.status}，不允许收货")

        inbound_details = []
        operator = req.get("operator", "系统")

        for item in arrived_items:
            product_id = item.get("product_id")
            qty = int(item.get("qty", 0))
            if not product_id or qty <= 0:
                continue

            product_name = item.get("product_name", "")
            unit = item.get("unit", "米")

            # 更新产品库存
            pr = await session.execute(select(Product).where(Product.id == product_id))
            prod = pr.scalar_one_or_none()
            qty_before = (prod.stock or 0) if prod else 0
            qty_after = qty_before + qty

            if prod:
                prod.stock = qty_after

            # 写入库存流水（InventoryFlow）
            flow = InventoryFlow(
                product_id=product_id,
                warehouse_id=1,  # 默认主仓
                flow_type="IN",
                qty_before=qty_before,
                qty_change=qty,
                qty_after=qty_after,
                ref_type="purchase",
                ref_id=po_id,
                operator_id=req.get("operator_id"),
                remark=f"采购收货 {p.po_no}",
            )
            session.add(flow)

            # 写入仓库记录（WarehouseRecord）
            record = WarehouseRecord(
                record_type="in",
                product_id=product_id,
                product_name=product_name,
                qty=qty,
                unit=unit,
                remark=f"采购单 {p.po_no} 到货",
                operator=str(operator),
            )
            session.add(record)

            inbound_details.append({
                "product_id": product_id,
                "product_name": product_name,
                "qty": qty,
            })

        # 更新采购单状态
        # 注意：旧 Purchase 表没有 arrived_qty 字段，简化为状态推进
        if p.status == "待采购":
            p.status = "部分到货"
        elif p.status == "部分到货":
            p.status = "已完成"
            p.debt = 0  # 全额到货，欠款清零

        await session.commit()

        return success_response(
            data={
                "id": po_id,
                "status": p.status,
                "inbound_count": len(inbound_details),
                "details": inbound_details,
            },
            message=f"已录入 {len(inbound_details)} 项到货，当前状态：{p.status}",
        )
