# app/api/inventory_v4.py
# V4.0 库存管理 API
from datetime import datetime, date

from fastapi import APIRouter, Body, Header, Path, Query
from sqlalchemy import and_, func, select

from app.api.auth import verify_token
from app.core.response import success_response, error_response
from app.database import async_session
from app.models import InventoryFlow, Product

router = APIRouter(prefix="/api/v4/inventory", tags=["V4.0 库存管理"])



def _str_dt(val) -> str:
    if not val:
        return ""
    return val.strftime("%Y-%m-%d %H:%M:%S") if isinstance(val, datetime) else str(val)[:19]


# ─── 库存流水 ─────────────────────────────────────────────────────────────────
@router.get("/flow", response_model=dict)
async def inventory_flow(
    product_id: int | None = Query(None, alias="product_id"),
    warehouse_id: int | None = Query(None, alias="warehouse_id"),
    flow_type: str | None = Query(None, alias="flow_type"),
    date_from: str | None = Query(None, alias="date_from"),
    date_to: str | None = Query(None, alias="date_to"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    GET /api/v4/inventory/flow
    库存流水，支持 product_id / warehouse_id / flow_type / 日期范围筛选，分页
    flow_type: in(入库) / out(出库) / adjust(调整)
    """
    async with async_session() as session:
        conditions = []
        if product_id:
            conditions.append(InventoryFlow.product_id == product_id)
        if warehouse_id:
            conditions.append(InventoryFlow.warehouse_id == warehouse_id)
        if flow_type:
            conditions.append(InventoryFlow.flow_type == flow_type)
        if date_from:
            try:
                conditions.append(InventoryFlow.created_at >= datetime.strptime(date_from, "%Y-%m-%d"))
            except Exception:
                pass
        if date_to:
            try:
                conditions.append(InventoryFlow.created_at <= datetime.strptime(date_to + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
            except Exception:
                pass

        where_clause = and_(*conditions) if conditions else True

        r = await session.execute(select(func.count(InventoryFlow.id)).where(where_clause))
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
                        "warehouse_id": f.warehouse_id,
                        "flow_type": f.flow_type or "",
                        "qty_before": f.qty_before or 0,
                        "qty_change": f.qty_change or 0,
                        "qty_after": f.qty_after or 0,
                        "ref_type": f.ref_type or "",
                        "ref_id": f.ref_id,
                        "operator_id": f.operator_id,
                        "remark": f.remark or "",
                        "created_at": _str_dt(f.created_at),
                    }
                    for f in flows
                ],
            }
        )


# ─── 库存预警 ─────────────────────────────────────────────────────────────────
@router.get("/warnings", response_model=dict)
async def inventory_warnings(
):
    """
    GET /api/v4/inventory/warnings
    库存预警：低于安全库存的产品列表
    安全库存阈值默认取 product 表的 min_stock 字段，如果没有则取 10
    """
    async with async_session() as session:
        # 查询所有产品，筛选 stock < 安全库存
        r = await session.execute(select(Product).where(Product.stock < 10))
        products = r.scalars().all()

        return success_response(
            data={
                "items": [
                    {
                        "id": p.id,
                        "code": p.code or "",
                        "name": p.name or "",
                        "stock": p.stock or 0,
                        "min_stock": getattr(p, "min_stock", 10) or 10,
                        "unit": p.unit or "米",
                        "unit_price": float(p.unit_price or 0),
                    }
                    for p in products
                ]
            }
        )


# ─── 库存调整 ─────────────────────────────────────────────────────────────────
@router.post("/adjust")
async def inventory_adjust(
    req: dict = Body(...),
):
    """
    POST /api/v4/inventory/adjust
    库存调整：录入盘盈盘亏
    Body: { product_id, warehouse_id, qty_change, flow_type: adjust, remark: "" }
    """
    product_id = req.get("product_id")
    if not product_id:
        return error_response("product_id不能为空")

    async with async_session() as session:
        # 读取当前库存
        r = await session.execute(select(Product).where(Product.id == product_id))
        product = r.scalar_one_or_none()
        if not product:
            return error_response("产品不存在")

        qty_before = product.stock or 0
        qty_change = int(req.get("qty_change", 0))
        qty_after = qty_before + qty_change

        flow = InventoryFlow(
            product_id=product_id,
            warehouse_id=req.get("warehouse_id"),
            flow_type="adjust",
            qty_before=qty_before,
            qty_change=qty_change,
            qty_after=qty_after,
            operator_id=req.get("operator_id"),
            remark=req.get("remark", "盘盈盘亏调整"),
        )
        session.add(flow)

        # 更新产品库存
        product.stock = qty_after

        await session.commit()
        await session.refresh(flow)

        return success_response(
            data={
                "id": flow.id,
                "product_id": product_id,
                "qty_before": qty_before,
                "qty_change": qty_change,
                "qty_after": qty_after,
            }
        )


# ─── 库存汇总 ─────────────────────────────────────────────────────────────────
@router.get("/summary", response_model=dict)
async def inventory_summary(
):
    """
    GET /api/v4/inventory/summary
    库存汇总：各仓库各产品当前库存
    """
    async with async_session() as session:
        r = await session.execute(
            select(Product).where(Product.stock > 0).order_by(Product.category_id, Product.name)
        )
        products = r.scalars().all()

        return success_response(
            data={
                "items": [
                    {
                        "id": p.id,
                        "code": p.code or "",
                        "name": p.name or "",
                        "category_id": p.category_id,
                        "stock": p.stock or 0,
                        "unit": p.unit or "米",
                        "unit_price": float(p.unit_price or 0),
                        "warehouse_id": getattr(p, "warehouse_id", None),
                    }
                    for p in products
                ]
            }
        )

# ─── 库存调拨（P1）────────────────────────────────────────────────────────────
@router.post("/transfer")
async def transfer_inventory(req: dict = Body(...)):
    """
    POST /api/v4/inventory/transfer - 库存调拨（跨仓库转移）
    Body: { product_id, from_warehouse_id, to_warehouse_id, qty }
    """
    product_id = req.get("product_id")
    qty = int(req.get("qty", 0))
    if not product_id or qty <= 0:
        return error_response("product_id 和 qty 必须为正整数")

    async with async_session() as session:
        r = await session.execute(select(Product).where(Product.id == product_id))
        p = r.scalar_one_or_none()
        if not p:
            return error_response("产品不存在")

        if (p.stock or 0) < qty:
            return error_response(f"库存不足，当前{p.stock}，调拨{qty}")

        # 出库
        p.stock = (p.stock or 0) - qty
        flow_out = InventoryFlow(
            product_id=product_id,
            warehouse_id=req.get("from_warehouse_id"),
            flow_type="TRANSFER_OUT",
            qty_before=(p.stock + qty),
            qty_change=-qty,
            qty_after=p.stock,
            ref_type="transfer",
            ref_id=product_id,
            operator_id=req.get("operator_id"),
            remark=f"调拨出库至仓库{req.get('to_warehouse_id')}",
        )
        session.add(flow_out)

        # 入库
        p.stock = (p.stock or 0) + qty
        flow_in = InventoryFlow(
            product_id=product_id,
            warehouse_id=req.get("to_warehouse_id"),
            flow_type="TRANSFER_IN",
            qty_before=(p.stock - qty),
            qty_change=qty,
            qty_after=p.stock,
            ref_type="transfer",
            ref_id=product_id,
            operator_id=req.get("operator_id"),
            remark=f"调拨入库从仓库{req.get('from_warehouse_id')}",
        )
        session.add(flow_in)

        await session.commit()
        return success_response(
            data={
                "product_id": product_id,
                "qty": qty,
                "from_warehouse_id": req.get("from_warehouse_id"),
                "to_warehouse_id": req.get("to_warehouse_id"),
                "stock_after": p.stock,
            }
        )
