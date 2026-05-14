# app/api/warehouses_v4.py
# V4.0 仓库管理 API
from datetime import datetime
from fastapi import APIRouter, Body, Query
from sqlalchemy import func, select

from app.core.response import success_response, error_response
from app.database import async_session
from app.models import Product, WarehouseRecord, InventoryFlow

router = APIRouter(prefix="/api/v4/warehouses", tags=["V4.0 仓库管理"])


# ─── 仓库列表 ────────────────────────────────────────────────────────────────
@router.get("")
async def list_warehouses():
    """
    GET /api/v4/warehouses - 仓库列表（虚拟仓库，默认一个"主仓"）
    V4.0 目前不支持多仓库，支持按 warehouse_id 筛选库存。
    """
    return success_response(
        data={
            "items": [
                {"id": 1, "code": "WH001", "name": "主仓库", "remark": "默认仓库"},
            ]
        }
    )


# ─── 仓库库存 ────────────────────────────────────────────────────────────────
@router.get("/{warehouse_id}/stock")
async def warehouse_stock(
    warehouse_id: int,
    keyword: str | None = Query(None, description="搜索：编码/名称"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """
    GET /api/v4/warehouses/{id}/stock - 仓库库存（产品维度聚合）
    当前版本：所有库存都算在主仓（warehouse_id=1）
    支持按产品编码/名称搜索
    """
    async with async_session() as session:
        conditions = []
        if keyword:
            kw = f"%{keyword}%"
            conditions.append(
                (Product.code.ilike(kw)) | (Product.name.ilike(kw))
            )

        where_clause = Product.id > 0
        if conditions:
            from sqlalchemy import and_
            where_clause = and_(Product.id > 0, *conditions)

        r = await session.execute(select(func.count(Product.id)).where(where_clause))
        total = r.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            select(Product)
            .where(where_clause)
            .order_by(Product.stock.desc(), Product.name)
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(query)
        products = result.scalars().all()

        return success_response(
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "warehouse_id": warehouse_id,
                "items": [
                    {
                        "id": p.id,
                        "code": p.code or "",
                        "name": p.name or "",
                        "stock": p.stock or 0,
                        "unit": p.unit or "米",
                        "unit_price": float(p.unit_price or 0),
                    }
                    for p in products
                ],
            }
        )


# ─── 入库 ─────────────────────────────────────────────────────────────────────
@router.post("/{warehouse_id}/in")
async def stock_in_v4(
    warehouse_id: int,
    req: dict = Body(...),
):
    """
    POST /api/v4/warehouses/{id}/in - 库存入库
    Body: { product_id, product_name, qty, unit, remark, operator }
    同时写入 inventory_flow 表记录库存流水
    """
    product_id = req.get("product_id")
    qty = float(req.get("qty", 0))
    if qty <= 0:
        return error_response("qty 必须大于 0")

    async with async_session() as session:
        qty_before = 0
        product_name = req.get("product_name", "")

        if product_id:
            pr = await session.execute(select(Product).where(Product.id == product_id))
            prod = pr.scalar_one_or_none()
            if prod:
                qty_before = prod.stock or 0
                prod.stock = int(qty_before + qty)
                product_name = prod.name or product_name
            else:
                return error_response("产品不存在")

        # 仓库记录
        record = WarehouseRecord(
            record_type="in",
            product_id=product_id,
            product_name=product_name,
            qty=qty,
            unit=req.get("unit", "米"),
            remark=req.get("remark", ""),
            operator=str(req.get("operator", "")),
        )
        session.add(record)

        # 库存流水
        if product_id:
            flow = InventoryFlow(
                product_id=product_id,
                warehouse_id=warehouse_id,
                flow_type="IN",
                qty_before=int(qty_before),
                qty_change=int(qty),
                qty_after=int(qty_before + qty),
                ref_type="warehouse",
                ref_id=0,
                operator_id=req.get("operator_id"),
                remark=req.get("remark", "仓库入库"),
            )
            session.add(flow)

        await session.commit()
        return success_response(
            data={
                "record_id": record.id,
                "product_id": product_id,
                "qty_before": int(qty_before),
                "qty_added": int(qty),
                "qty_after": int(qty_before + qty),
            }
        )


# ─── 出库 ─────────────────────────────────────────────────────────────────────
@router.post("/{warehouse_id}/out")
async def stock_out_v4(
    warehouse_id: int,
    req: dict = Body(...),
):
    """
    POST /api/v4/warehouses/{id}/out - 库存出库
    Body: { product_id, product_name, qty, unit, remark, operator }
    出库数量不能超过当前库存
    """
    product_id = req.get("product_id")
    qty = float(req.get("qty", 0))
    if qty <= 0:
        return error_response("qty 必须大于 0")

    async with async_session() as session:
        qty_before = 0
        product_name = req.get("product_name", "")

        if product_id:
            pr = await session.execute(select(Product).where(Product.id == product_id))
            prod = pr.scalar_one_or_none()
            if not prod:
                return error_response("产品不存在")
            qty_before = prod.stock or 0
            if qty_before < qty:
                return error_response(f"库存不足，当前 {int(qty_before)}，出库 {int(qty)}")
            prod.stock = int(qty_before - qty)
            product_name = prod.name or product_name

        # 仓库记录
        record = WarehouseRecord(
            record_type="out",
            product_id=product_id,
            product_name=product_name,
            qty=qty,
            unit=req.get("unit", "米"),
            remark=req.get("remark", ""),
            operator=str(req.get("operator", "")),
        )
        session.add(record)

        # 库存流水
        if product_id:
            flow = InventoryFlow(
                product_id=product_id,
                warehouse_id=warehouse_id,
                flow_type="OUT",
                qty_before=int(qty_before),
                qty_change=-int(qty),
                qty_after=int(qty_before - qty),
                ref_type="warehouse",
                ref_id=0,
                operator_id=req.get("operator_id"),
                remark=req.get("remark", "仓库出库"),
            )
            session.add(flow)

        await session.commit()
        return success_response(
            data={
                "record_id": record.id,
                "product_id": product_id,
                "qty_before": int(qty_before),
                "qty_out": int(qty),
                "qty_after": int(qty_before - qty),
            }
        )


# ─── 库存流水 ─────────────────────────────────────────────────────────────────
@router.get("/{warehouse_id}/flow")
async def warehouse_flow(
    warehouse_id: int,
    product_id: int | None = Query(None, description="产品ID筛选"),
    flow_type: str | None = Query(None, description="IN/OUT/TRANSFER_IN/TRANSFER_OUT"),
    date_from: str | None = Query(None, alias="date_from", description="开始日期 YYYY-MM-DD"),
    date_to: str | None = Query(None, alias="date_to", description="结束日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """
    GET /api/v4/warehouses/{id}/flow - 库存流水记录
    支持按产品/类型/日期筛选
    """
    async with async_session() as session:
        conditions = []
        if product_id:
            conditions.append(InventoryFlow.product_id == product_id)
        if flow_type:
            conditions.append(InventoryFlow.flow_type == flow_type)
        if date_from:
            conditions.append(InventoryFlow.created_at >= datetime.strptime(date_from, "%Y-%m-%d"))
        if date_to:
            conditions.append(InventoryFlow.created_at <= datetime.strptime(date_to + " 23:59:59", "%Y-%m-%d %H:%M:%S"))

        where_clause = and_(*conditions) if conditions else True

        r = await session.execute(
            select(func.count(InventoryFlow.id)).where(where_clause)
        )
        total = r.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            select(InventoryFlow)
            .where(where_clause)
            .order_by(InventoryFlow.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(query)
        flows = result.scalars().all()

        return success_response(
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [
                    {
                        "id": f.id,
                        "product_id": f.product_id,
                        "flow_type": f.flow_type or "",
                        "qty_before": f.qty_before or 0,
                        "qty_change": f.qty_change or 0,
                        "qty_after": f.qty_after or 0,
                        "ref_type": f.ref_type or "",
                        "remark": f.remark or "",
                        "created_at": str(f.created_at)[:19] if f.created_at else "",
                    }
                    for f in flows
                ],
            }
        )
