"""
仓库与库存管理 API
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep
from app.core.exceptions import NotFoundError
from app.core.response import paginated, success
from app.domain.product import Product
from app.domain.warehouse import Inventory, InventoryFlow, Warehouse
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate, InventoryAdjust

router = APIRouter(prefix="/api/v1/warehouses", tags=["仓库管理"])


# ─── 仓库管理 ─────────────────────────────────────────────────


@router.get("")
async def list_warehouses(session: SessionDep, current_user: CurrentUserDep):
    """仓库列表"""
    result = await session.execute(
        select(Warehouse).where(Warehouse.is_active == True).order_by(Warehouse.id)
    )
    warehouses = result.scalars().all()
    return success(data=[
        {
            "id": w.id,
            "name": w.name,
            "code": w.code,
            "address": w.address,
            "is_active": w.is_active,
            "remark": w.remark,
        }
        for w in warehouses
    ])


@router.post("")
async def create_warehouse(session: SessionDep, current_user: CurrentUserDep, req: WarehouseCreate):
    """创建仓库"""
    wh = Warehouse(**req.model_dump())
    session.add(wh)
    await session.flush()
    return success(data={"id": wh.id}, message="仓库创建成功")


@router.put("/{warehouse_id}")
async def update_warehouse(
    session: SessionDep, current_user: CurrentUserDep, warehouse_id: int, req: WarehouseUpdate
):
    """更新仓库"""
    result = await session.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    wh = result.scalar_one_or_none()
    if not wh:
        raise NotFoundError("仓库不存在")

    for field, value in req.model_dump(exclude_none=True).items():
        setattr(wh, field, value)
    await session.flush()
    return success(data={"id": warehouse_id}, message="仓库更新成功")


@router.delete("/{warehouse_id}")
async def delete_warehouse(session: SessionDep, current_user: CurrentUserDep, warehouse_id: int):
    """删除仓库（软删除）"""
    result = await session.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    wh = result.scalar_one_or_none()
    if not wh:
        raise NotFoundError("仓库不存在")

    wh.is_active = False
    await session.flush()
    return success(message="仓库已禁用")


# ─── 手动库存调整 ──────────────────────────────────────────────


@router.post("/inventory/adjust")
async def adjust_inventory(session: SessionDep, current_user: CurrentUserDep, req: InventoryAdjust):
    """手动调整库存"""
    from datetime import datetime, timezone
    from app.domain.warehouse import Inventory

    # 查找库存记录
    result = await session.execute(
        select(Inventory).where(
            Inventory.product_id == req.product_id,
            Inventory.warehouse_id == req.warehouse_id,
        )
    )
    inv = result.scalar_one_or_none()

    if not inv:
        # 创建新库存记录
        inv = Inventory(
            product_id=req.product_id,
            warehouse_id=req.warehouse_id,
            quantity=0,
            safety_stock=0,
        )
        session.add(inv)
        await session.flush()

    qty_before = float(inv.quantity)
    qty_after = qty_before + req.quantity
    if qty_after < 0:
        from app.core.exceptions import BusinessError
        raise BusinessError("调整后库存不能为负数")

    inv.quantity = qty_after

    # 记录流水
    flow = InventoryFlow(
        product_id=req.product_id,
        flow_type="adjust_in" if req.quantity > 0 else "adjust_out",
        qty_before=qty_before,
        qty_change=req.quantity,
        qty_after=qty_after,
        ref_type="manual",
        ref_id=current_user.id,
        remark=req.remark,
    )
    session.add(flow)
    await session.flush()
    return success(
        data={"product_id": req.product_id, "qty_before": qty_before, "qty_after": qty_after},
        message="库存调整成功",
    )


# ─── 库存查询 ─────────────────────────────────────────────────


@router.get("/inventory")
async def list_inventory(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    keyword: str | None = Query(None, description="搜索产品"),
    low_stock: bool = Query(False, description="仅显示低库存"),
):
    """库存列表"""
    conditions = []

    if keyword:
        kw = f"%{keyword}%"
        from sqlalchemy import or_
        conditions.append(
            or_(Product.name.ilike(kw), Product.code.ilike(kw))
        )
    if low_stock:
        conditions.append(Inventory.quantity <= Inventory.safety_stock)

    query = (
        select(Inventory)
        .join(Product, Inventory.product_id == Product.id)
        .order_by(Inventory.id)
    )
    if conditions:
        query = query.where(and_(*conditions))

    total_q = select(func.count()).select_from(Inventory)
    if conditions:
        total_q = total_q.where(and_(*conditions))
    total = (await session.execute(total_q)).scalar() or 0

    result = await session.execute(query.offset(page.offset).limit(page.page_size))
    items = result.scalars().all()

    return paginated(
        items=[
            {
                "product_id": i.product_id,
                "product_name": i.product.name if i.product else "",
                "product_code": i.product.code if i.product else "",
                "warehouse_id": i.warehouse_id,
                "quantity": float(i.quantity),
                "safety_stock": float(i.safety_stock),
            }
            for i in items
        ],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


# ─── 库存流水 ─────────────────────────────────────────────────


@router.get("/flows")
async def list_inventory_flows(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    product_id: int | None = Query(None),
    flow_type: str | None = Query(None),
):
    """库存流水"""
    conditions = []
    if product_id:
        conditions.append(InventoryFlow.product_id == product_id)
    if flow_type:
        conditions.append(InventoryFlow.flow_type == flow_type)

    where = and_(*conditions) if conditions else True
    total = (await session.execute(
        select(func.count()).select_from(InventoryFlow).where(where)
    )).scalar() or 0

    result = await session.execute(
        select(InventoryFlow)
        .where(where)
        .order_by(InventoryFlow.created_at.desc())
        .offset(page.offset)
        .limit(page.page_size)
    )
    flows = result.scalars().all()

    items = []
    for f in flows:
        prod = await session.get(Product, f.product_id)
        items.append({
            "id": f.id,
            "product_id": f.product_id,
            "product_name": prod.name if prod else "",
            "flow_type": f.flow_type,
            "qty_before": float(f.qty_before),
            "qty_change": float(f.qty_change),
            "qty_after": float(f.qty_after),
            "ref_type": f.ref_type,
            "ref_id": f.ref_id,
            "remark": f.remark,
            "created_at": str(f.created_at)[:19] if f.created_at else "",
        })

    return paginated(items=items, total=total, page=page.page, page_size=page.page_size)
