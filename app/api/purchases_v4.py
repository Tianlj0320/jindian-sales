# app/api/purchases_v4.py
# V4.0 采购管理 API（P0: 5个 + P1: 2个）
from datetime import date, datetime
from fastapi import APIRouter, Body, Path, Query
from sqlalchemy import and_, func, select

from app.core.response import success_response, error_response
from app.database import async_session
from app.models import PurchaseOrder, Supplier, Product, WarehouseRecord, InventoryFlow

router = APIRouter(prefix="/api/v4/purchases", tags=["V4.0 采购管理"])

VALID_STATUSES = {"待采购", "已下单", "部分到货", "全部到货", "已取消"}


def make_po_no() -> str:
    today = datetime.now().strftime("%Y%m%d")
    return f"PO{today}"


def _str_date(val) -> str:
    if not val:
        return ""
    return val.strftime("%Y-%m-%d") if isinstance(val, (date, datetime)) else str(val)[:10]


# ─── 采购单列表 ──────────────────────────────────────────────────────────────
@router.get("")
async def list_purchases_v4(
    status: str | None = Query(None, description="状态：待采购/已下单/部分到货/全部到货"),
    supplier_id: int | None = Query(None, alias="supplier_id"),
    date_from: str | None = Query(None, alias="date_from"),
    date_to: str | None = Query(None, alias="date_to"),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    GET /api/v4/purchases - 采购单列表
    """
    async with async_session() as session:
        conditions = []
        if status:
            conditions.append(PurchaseOrder.status == status)
        if supplier_id:
            conditions.append(PurchaseOrder.supplier_id == supplier_id)
        if date_from:
            try:
                conditions.append(PurchaseOrder.created_at >= datetime.strptime(date_from, "%Y-%m-%d"))
            except Exception:
                pass
        if date_to:
            try:
                conditions.append(PurchaseOrder.created_at <= datetime.strptime(date_to + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
            except Exception:
                pass
        if keyword:
            kw = f"%{keyword}%"
            conditions.append(PurchaseOrder.po_no.ilike(kw))

        where_clause = and_(*conditions) if conditions else True

        r = await session.execute(select(func.count(PurchaseOrder.id)).where(where_clause))
        total = r.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            select(PurchaseOrder)
            .where(where_clause)
            .order_by(PurchaseOrder.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(query)
        orders = result.scalars().all()

        return success_response(
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [
                    {
                        "id": o.id,
                        "po_no": o.po_no or "",
                        "supplier_id": o.supplier_id,
                        "supplier_name": o.supplier_name or "",
                        "contact": o.contact or "",
                        "phone": o.phone or "",
                        "total_amount": float(o.total_amount or 0),
                        "paid_amount": float(o.paid_amount or 0),
                        "debt_amount": float(o.debt_amount or 0),
                        "status": o.status or "",
                        "expected_date": str(o.expected_date)[:10] if o.expected_date else "",
                        "arrived_date": str(o.arrived_date)[:10] if o.arrived_date else "",
                        "items_count": len(o.items or []),
                        "remark": o.remark or "",
                        "created_at": _str_date(o.created_at),
                    }
                    for o in orders
                ],
            }
        )


# ─── 创建采购单 ──────────────────────────────────────────────────────────────
@router.post("")
async def create_purchase_v4(req: dict = Body(...)):
    """
    POST /api/v4/purchases - 创建采购单
    Body: {
        supplier_id, supplier_name, contact, phone,
        items: [{product_id, product_code, product_name, spec, qty, unit, unit_price}],
        expected_date, remark
    }
    """
    items = req.get("items", [])
    if not items:
        return error_response("采购明细不能为空")

    # 计算总金额
    total_amount = sum(float(item.get("qty", 0) or 0) * float(item.get("unit_price", 0) or 0) for item in items)

    async with async_session() as session:
        # 生成 po_no
        r = await session.execute(
            select(func.count(PurchaseOrder.id)).where(PurchaseOrder.po_no.like(f"PO{datetime.now().strftime('%Y%m%d')}%"))
        )
        seq = (r.scalar() or 0) + 1
        po_no = f"PO{datetime.now().strftime('%Y%m%d')}{seq:03d}"

        po = PurchaseOrder(
            po_no=po_no,
            supplier_id=req.get("supplier_id"),
            supplier_name=req.get("supplier_name", ""),
            contact=req.get("contact", ""),
            phone=req.get("phone", ""),
            total_amount=total_amount,
            paid_amount=0,
            debt_amount=total_amount,
            status="待采购",
            expected_date=datetime.strptime(req["expected_date"][:10], "%Y-%m-%d").date() if req.get("expected_date") else None,
            items=items,
            remark=req.get("remark", ""),
        )
        session.add(po)
        await session.commit()
        await session.refresh(po)

        return success_response(
            data={
                "id": po.id,
                "po_no": po.po_no,
                "total_amount": float(po.total_amount),
                "status": po.status,
            }
        )


# ─── 采购单详情 ─────────────────────────────────────────────────────────────

@router.get("/pending", response_model=dict)
async def pending_purchases():
    """
    GET /api/v4/purchases/pending - 待收货统计
    返回当前所有"待采购"和"部分到货"状态的采购单数量和总金额
    """
    async with async_session() as session:
        r = await session.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.status.in_(["待采购", "已下单", "部分到货"])
            )
        )
        orders = r.scalars().all()

        total_amount = sum(float(o.total_amount or 0) for o in orders)
        pending_count = len(orders)

        return success_response(
            data={
                "pending_count": pending_count,
                "pending_amount": float(total_amount),
                "items": [
                    {
                        "id": o.id,
                        "po_no": o.po_no or "",
                        "supplier_name": o.supplier_name or "",
                        "total_amount": float(o.total_amount or 0),
                        "status": o.status or "",
                        "expected_date": str(o.expected_date)[:10] if o.expected_date else "",
                    }
                    for o in orders
                ],
            }
        )


# ══════════════════════════════════════════════════════════════
# P1: 更新采购单 / 删除采购单
# ══════════════════════════════════════════════════════════════



@router.get("/{purchase_id}", response_model=dict)
async def get_purchase_v4(purchase_id: int = Path(...)):
    """
    GET /api/v4/purchases/{id} - 采购单详情（包含明细）
    """
    async with async_session() as session:
        r = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == purchase_id))
        po = r.scalar_one_or_none()
        if not po:
            return error_response("采购单不存在")

        return success_response(
            data={
                "id": po.id,
                "po_no": po.po_no or "",
                "supplier_id": po.supplier_id,
                "supplier_name": po.supplier_name or "",
                "contact": po.contact or "",
                "phone": po.phone or "",
                "total_amount": float(po.total_amount or 0),
                "paid_amount": float(po.paid_amount or 0),
                "debt_amount": float(po.debt_amount or 0),
                "status": po.status or "",
                "expected_date": str(po.expected_date)[:10] if po.expected_date else "",
                "arrived_date": str(po.arrived_date)[:10] if po.arrived_date else "",
                "items": po.items or [],
                "remark": po.remark or "",
                "created_at": _str_date(po.created_at),
            }
        )


# ─── 部分收货 ───────────────────────────────────────────────────────────────
@router.put("/{purchase_id}/receive")
async def receive_purchase_v4(purchase_id: int = Path(...), req: dict = Body(...)):
    """
    PUT /api/v4/purchases/{id}/receive - 部分收货
    Body: { items: [{product_id, product_code, product_name, qty, unit}] }
    支持分批到货，每次传入本次到货明细。
    到货后自动更新采购单状态（部分到货/全部到货）。
    """
    arrived_items = req.get("items", [])
    if not arrived_items:
        return error_response("到货明细不能为空")

    async with async_session() as session:
        r = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == purchase_id))
        po = r.scalar_one_or_none()
        if not po:
            return error_response("采购单不存在")

        # 记录每次到货，写入库存流水和入库
        inbound_details = []
        operator = req.get("operator_id", 1)

        for item in arrived_items:
            product_id = item.get("product_id")
            qty = int(item.get("qty", 0))
            if not product_id or qty <= 0:
                continue

            product_name = item.get("product_name", "")

            # 更新产品库存
            pr = await session.execute(select(Product).where(Product.id == product_id))
            prod = pr.scalar_one_or_none()
            if prod:
                prod.stock = (prod.stock or 0) + qty

            # 写入库存流水
            flow = InventoryFlow(
                product_id=product_id,
                warehouse_id=1,  # 默认主仓
                flow_type="IN",
                qty_before=(prod.stock - qty) if prod else 0,
                qty_change=qty,
                qty_after=(prod.stock) if prod else qty,
                ref_type="purchase",
                ref_id=purchase_id,
                operator_id=operator,
                remark=f"采购到货 {po.po_no}",
            )
            session.add(flow)

            # 写入仓库记录
            record = WarehouseRecord(
                record_type="in",
                product_id=product_id,
                product_name=product_name,
                qty=qty,
                unit=item.get("unit", "米"),
                remark=f"采购单 {po.po_no} 到货",
                operator=str(operator),
            )
            session.add(record)

            inbound_details.append({"product_id": product_id, "product_name": product_name, "qty": qty})

        # 更新采购单已到货数量和状态
        # 正确逻辑：按实际到货品种数判断是否全部到齐
        import json
        total_items = 0
        arrived_items_count = 0
        if po.items:
            try:
                items_list = json.loads(po.items) if isinstance(po.items, str) else po.items
                total_items = len(items_list)
            except Exception:
                total_items = 1  # 保底

        # 已到货品种数 = 当前 inbound_details 品种数
        # 简化：每次到货都累加品种数，超过1个品种就视为部分到货，全部到了才标全部
        if po.status not in ("部分到货", "全部到货"):
            po.status = "部分到货"
        elif po.status == "部分到货":
            # 已有部分到货记录，检查是否所有品种都已到货
            # 简单逻辑：本次到货品种数达到总品种数则标全部
            if total_items > 0 and len(inbound_details) >= total_items:
                po.status = "全部到货"
            # 否则保持"部分到货"（多次部分到货场景）

        po.arrived_date = datetime.now().date()
        await session.commit()

        return success_response(
            data={
                "id": po.id,
                "status": po.status,
                "inbound_count": len(inbound_details),
                "details": inbound_details,
            }
        )


# ─── 待收货统计 ─────────────────────────────────────────────────────────────
@router.put("/{purchase_id}")
async def update_purchase_v4(purchase_id: int = Path(...), req: dict = Body(...)):
    """
    PUT /api/v4/purchases/{id} - 更新采购单（只能更新备注/联系信息）
    状态不可回退，items 不可修改（有到货记录后锁定）
    """
    async with async_session() as session:
        r = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == purchase_id))
        po = r.scalar_one_or_none()
        if not po:
            return error_response("采购单不存在")

        if po.status in ("全部到货", "已取消"):
            return error_response(f"采购单状态为{po.status}，不可修改")

        for field in ["contact", "phone", "remark", "expected_date"]:
            if field in req:
                val = req[field]
                if field == "expected_date" and val:
                    try:
                        val = datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
                    except Exception:
                        val = None
                setattr(po, field, val)

        await session.commit()
        return success_response(data={"id": po.id})


@router.delete("/{purchase_id}")
async def delete_purchase_v4(purchase_id: int = Path(...)):
    """
    DELETE /api/v4/purchases/{id} - 删除采购单（只能删除待采购状态）
    """
    async with async_session() as session:
        r = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == purchase_id))
        po = r.scalar_one_or_none()
        if not po:
            return error_response("采购单不存在")

        if po.status != "待采购":
            return error_response(f"只能删除待采购状态的采购单，当前状态：{po.status}")

        await session.delete(po)
        await session.commit()
        return success_response(data={"id": purchase_id})