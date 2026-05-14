"""
仓库与库存管理 API
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep, require_permission
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import paginated, success
from app.domain.product import Product
from app.domain.warehouse import Inventory, InventoryFlow, Warehouse, WarehouseStorage
from app.schemas.warehouse import (
    InventoryAdjust,
    InventorySetLocation,
    StorageLocationCreate,
    StorageLocationUpdate,
    WarehouseCreate,
    WarehouseUpdate,
)

router = APIRouter(prefix="/api/v1/warehouses", tags=["仓库管理"])


# ─── 仓库管理 ─────────────────────────────────────────────────


@router.get("")
async def list_warehouses(
    session: SessionDep,
    current_user: CurrentUserDep,
    warehouse_type: str | None = Query(None, description="按类型筛选: main/auxiliary/finished"),
):
    """仓库列表（支持按类型筛选）"""
    conditions = [Warehouse.is_active == True]
    if warehouse_type:
        conditions.append(Warehouse.warehouse_type == warehouse_type)

    result = await session.execute(
        select(Warehouse).where(and_(*conditions)).order_by(Warehouse.id)
    )
    warehouses = result.scalars().all()
    return success(data=[
        {
            "id": w.id,
            "name": w.name,
            "code": w.code,
            "address": w.address,
            "is_active": w.is_active,
            "warehouse_type": w.warehouse_type,
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
async def adjust_inventory(
    session: SessionDep, current_user: CurrentUserDep,
    req: InventoryAdjust, _: None = require_permission("warehouse"),
):
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


@router.get("/inventory/grouped")
async def list_inventory_grouped(
    session: SessionDep,
    current_user: CurrentUserDep,
    warehouse_id: int | None = Query(None, description="仓库ID"),
    keyword: str | None = Query(None, description="搜索订单号/采购单号/产品"),
    order_no: str | None = Query(None, description="按订单号筛选"),
    po_no: str | None = Query(None, description="按采购单号筛选"),
    supplier_id: int | None = Query(None, description="按供应商筛选"),
):
    """按仓库→订单→采购单分组的库存视图（支持多维度筛选）"""
    from app.domain.purchase import PurchaseOrder, PurchaseOrderItem as POItem
    from app.domain.order import Order

    conditions = [InventoryFlow.ref_type == "purchase"]
    if warehouse_id:
        conditions.append(InventoryFlow.warehouse_id == warehouse_id)

    # 如果涉及采购单级筛选，先定位 PO id 范围
    extra_po_ids = None
    if po_no or supplier_id:
        po_conds = []
        if po_no:
            po_conds.append(PurchaseOrder.po_no.ilike(f"%{po_no}%"))
        if supplier_id:
            po_conds.append(PurchaseOrder.supplier_id == supplier_id)
        po_result = await session.execute(
            select(PurchaseOrder.id).where(and_(*po_conds))
        )
        extra_po_ids = set(row[0] for row in po_result.all())
        if not extra_po_ids:
            return success(data={"warehouses": []})

    if extra_po_ids:
        conditions.append(InventoryFlow.ref_id.in_(extra_po_ids))

    where = and_(*conditions) if conditions else True
    result = await session.execute(
        select(InventoryFlow)
        .where(where)
        .order_by(InventoryFlow.created_at.desc())
    )
    flows = result.scalars().all()

    # 按 (warehouse_id, ref_id=po_id) 分组
    groups: dict = {}
    for f in flows:
        po_id = f.ref_id
        wh_id = f.warehouse_id
        key = (wh_id, po_id)
        if key not in groups:
            groups[key] = {
                "warehouse_id": wh_id,
                "po_id": po_id,
                "items": [],
                "total_qty": 0,
            }
        groups[key]["items"].append({
            "product_id": f.product_id,
            "qty": float(f.qty_change),
            "flow_type": f.flow_type,
            "created_at": str(f.created_at)[:19] if f.created_at else "",
        })
        if f.flow_type == "IN":
            groups[key]["total_qty"] += float(f.qty_change)

    # 解析 PO 和 Order 信息
    result_data = []
    for (wh_id, po_id), g in groups.items():
        # 查询 PO
        po_result = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
        po = po_result.scalar_one_or_none()
        if not po:
            continue

        # 解析关联的订单
        order_ids = [int(x.strip()) for x in (po.order_ids or '').split(',') if x.strip().isdigit()]
        orders_info = []
        for oid in order_ids:
            o_result = await session.execute(select(Order).where(Order.id == oid))
            o = o_result.scalar_one_or_none()
            if o:
                orders_info.append({
                    "order_id": o.id,
                    "order_no": o.order_no or "",
                    "customer_name": o.customer_name or "",
                })

        # order_no 筛选（需要在拿到 orders_info 后过滤）
        if order_no:
            kw = order_no.lower()
            if not any(kw in (oi["order_no"] or "").lower() for oi in orders_info):
                continue

        wh_name = ""
        if wh_id:
            wh = await session.get(Warehouse, wh_id)
            wh_name = wh.name if wh else ""

        result_data.append({
            "warehouse_id": wh_id,
            "warehouse_name": wh_name,
            "po_id": po.id,
            "po_no": po.po_no,
            "supplier_name": po.supplier_name or "",
            "total_amount": float(po.total_amount),
            "status": po.status,
            "orders": orders_info,
            "total_qty": g["total_qty"],
            "items": g["items"],
        })

    # 按 warehouse 分组
    warehouse_groups: dict = {}
    for item in result_data:
        wid = item["warehouse_id"]
        warehouse_groups.setdefault(wid, {
            "warehouse_id": wid,
            "warehouse_name": item["warehouse_name"],
            "pos": [],
        })
        warehouse_groups[wid]["pos"].append(item)

    return success(data={
        "warehouses": list(warehouse_groups.values()),
    })


@router.get("/inventory")
async def list_inventory(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    keyword: str | None = Query(None, description="搜索产品"),
    low_stock: bool = Query(False, description="仅显示低库存"),
    warehouse_id: int | None = Query(None, description="仓库ID"),
    zone: str | None = Query(None, description="存放区域"),
    shelf: str | None = Query(None, description="货架"),
    bin: str | None = Query(None, description="库位"),
):
    """库存列表（增强版：支持仓库/位置筛选）"""
    conditions = []

    if keyword:
        kw = f"%{keyword}%"
        from sqlalchemy import or_
        conditions.append(
            or_(Product.name.ilike(kw), Product.code.ilike(kw))
        )
    if low_stock:
        conditions.append(Inventory.quantity <= Inventory.safety_stock)
    if warehouse_id:
        conditions.append(Inventory.warehouse_id == warehouse_id)
    if zone:
        conditions.append(Inventory.zone == zone)
    if shelf:
        conditions.append(Inventory.shelf == shelf)
    if bin:
        conditions.append(Inventory.bin == bin)

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

    items_data = []
    for i in items:
        # resolve warehouse name
        wh_name = ""
        if i.warehouse_id:
            wh = await session.get(Warehouse, i.warehouse_id)
            wh_name = wh.name if wh else ""
        items_data.append({
            "product_id": i.product_id,
            "product_name": i.product.name if i.product else "",
            "product_code": i.product.code if i.product else "",
            "warehouse_id": i.warehouse_id,
            "warehouse_name": wh_name,
            "quantity": float(i.quantity),
            "safety_stock": float(i.safety_stock),
            "zone": i.zone or "",
            "shelf": i.shelf or "",
            "bin": i.bin or "",
        })

    return paginated(
        items=items_data,
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
    product_id: int | None = Query(None, description="产品ID"),
    warehouse_id: int | None = Query(None, description="仓库ID"),
    flow_type: str | None = Query(None, description="类型: IN/OUT/TRANSFER/ADJUST"),
    keyword: str | None = Query(None, description="搜索产品名称"),
    start_date: str | None = Query(None, description="日期起 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="日期止 YYYY-MM-DD"),
):
    """库存流水（增强版：支持仓库/关键字/日期筛选）"""
    conditions = []
    if product_id:
        conditions.append(InventoryFlow.product_id == product_id)
    if warehouse_id:
        conditions.append(InventoryFlow.warehouse_id == warehouse_id)
    if flow_type:
        conditions.append(InventoryFlow.flow_type == flow_type)
    if keyword:
        kw = f"%{keyword}%"
        # Subquery: find product_ids matching keyword
        prod_ids_q = select(Product.id).where(or_(Product.name.ilike(kw), Product.code.ilike(kw)))
        prod_ids = (await session.execute(prod_ids_q)).scalars().all()
        if prod_ids:
            conditions.append(InventoryFlow.product_id.in_(prod_ids))
        else:
            conditions.append(InventoryFlow.product_id == 0)  # force empty
    if start_date:
        from datetime import datetime
        sd = datetime.strptime(start_date, "%Y-%m-%d")
        conditions.append(InventoryFlow.created_at >= sd)
    if end_date:
        from datetime import datetime
        ed = datetime.strptime(f"{end_date} 23:59:59", "%Y-%m-%d %H:%M:%S")
        conditions.append(InventoryFlow.created_at <= ed)

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
        wh_name = ""
        if f.warehouse_id:
            wh = await session.get(Warehouse, f.warehouse_id)
            wh_name = wh.name if wh else ""
        items.append({
            "id": f.id,
            "product_id": f.product_id,
            "product_name": prod.name if prod else "",
            "product_code": prod.code if prod else "",
            "warehouse_id": f.warehouse_id,
            "warehouse_name": wh_name,
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


# ─── 仓库三级分类管理（区域 → 货架 → 库位） ──────────


@router.get("/storage")
async def list_storage_locations(
    session: SessionDep, current_user: CurrentUserDep,
    warehouse_id: int | None = Query(None, description="仓库ID"),
    level: int | None = Query(None, description="层级: 1/2/3"),
):
    """获取存储位置列表（支持按仓库和层级筛选）"""
    conditions = []
    if warehouse_id:
        conditions.append(WarehouseStorage.warehouse_id == warehouse_id)
    if level:
        conditions.append(WarehouseStorage.level == level)

    where = and_(*conditions) if conditions else True
    result = await session.execute(
        select(WarehouseStorage).where(where).order_by(WarehouseStorage.warehouse_id, WarehouseStorage.level, WarehouseStorage.id)
    )
    locations = result.scalars().all()

    # 构建树形结构（level 1 → level 2 → level 3）
    tree = {}
    for loc in locations:
        if loc.level == 1:
            tree[loc.id] = {
                "id": loc.id, "warehouse_id": loc.warehouse_id, "level": loc.level,
                "name": loc.name, "code": loc.code, "parent_id": loc.parent_id,
                "remark": loc.remark, "children": [],
            }
    for loc in locations:
        if loc.level == 2 and loc.parent_id in tree:
            tree[loc.parent_id]["children"].append({
                "id": loc.id, "warehouse_id": loc.warehouse_id, "level": loc.level,
                "name": loc.name, "code": loc.code, "parent_id": loc.parent_id,
                "remark": loc.remark, "children": [],
            })
    # Level 3 under level 2
    l2_lookup = {}
    for loc in locations:
        if loc.level == 2:
            l2_lookup[loc.id] = loc.parent_id
    for loc in locations:
        if loc.level == 3 and loc.parent_id in l2_lookup:
            parent_l1_id = l2_lookup[loc.parent_id]
            if parent_l1_id in tree:
                for l2 in tree[parent_l1_id]["children"]:
                    if l2["id"] == loc.parent_id:
                        l2["children"].append({
                            "id": loc.id, "warehouse_id": loc.warehouse_id, "level": loc.level,
                            "name": loc.name, "code": loc.code, "parent_id": loc.parent_id,
                            "remark": loc.remark, "children": [],
                        })

    return success(data=list(tree.values()))


@router.post("/storage")
async def create_storage_location(
    session: SessionDep, current_user: CurrentUserDep, req: StorageLocationCreate
):
    """创建存储位置（区域/货架/库位）"""
    loc = WarehouseStorage(**req.model_dump())
    session.add(loc)
    await session.flush()
    return success(data={"id": loc.id}, message="创建成功")


@router.put("/storage/{location_id}")
async def update_storage_location(
    session: SessionDep, current_user: CurrentUserDep, location_id: int, req: StorageLocationUpdate
):
    """更新存储位置"""
    result = await session.execute(select(WarehouseStorage).where(WarehouseStorage.id == location_id))
    loc = result.scalar_one_or_none()
    if not loc:
        raise NotFoundError("位置不存在")
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(loc, field, value)
    await session.flush()
    return success(message="已更新")


@router.delete("/storage/{location_id}")
async def delete_storage_location(
    session: SessionDep, current_user: CurrentUserDep, location_id: int
):
    """删除存储位置"""
    result = await session.execute(select(WarehouseStorage).where(WarehouseStorage.id == location_id))
    loc = result.scalar_one_or_none()
    if not loc:
        raise NotFoundError("位置不存在")
    await session.delete(loc)
    await session.flush()
    return success(message="已删除")


# ─── 库存位置设置 ────────────────────────────────────────


@router.put("/inventory/{product_id}/location")
async def set_inventory_location(
    session: SessionDep, current_user: CurrentUserDep,
    product_id: int,
    warehouse_id: int = Query(..., description="仓库ID"),
    req: InventorySetLocation | None = None,
):
    """设置库存位置（三级分类）"""
    result = await session.execute(
        select(Inventory).where(
            Inventory.product_id == product_id,
            Inventory.warehouse_id == warehouse_id,
        )
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise NotFoundError("库存记录不存在")

    if req:
        inv.zone = req.zone
        inv.shelf = req.shelf
        inv.bin = req.bin
    await session.flush()
    return success(data={
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "zone": inv.zone,
        "shelf": inv.shelf,
        "bin": inv.bin,
    }, message="位置已设置")


# ─── 增强库存查询 ────────────────────────────────────────
