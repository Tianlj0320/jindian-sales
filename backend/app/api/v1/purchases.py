"""
采购管理 API
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import paginated, success
from app.domain.order import Order, OrderItem
from app.domain.product import Product, Supplier as SupModel
from app.domain.purchase import PurchaseOrder, PurchaseOrderItem
from app.domain.warehouse import Inventory, InventoryFlow, Warehouse
from app.schemas.purchase import (
    PurchaseOrderCreate,
    PurchasePreviewRequest,
    PurchaseGenerateRequest,
    ReceiveCreate,
)

router = APIRouter(prefix="/api/v1/purchases", tags=["采购管理"])


def _generate_po_no(prefix: str = "PO") -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{prefix}{today}"


# ─── 采购单列表 ───────────────────────────────────────────────


@router.get("")
async def list_purchase_orders(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    status: str | None = Query(None, description="状态"),
    keyword: str | None = Query(None, description="搜索供应商"),
):
    """采购单列表"""
    conditions = []
    if status:
        conditions.append(PurchaseOrder.status == status)
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(PurchaseOrder.supplier_name.ilike(kw))

    where = and_(*conditions) if conditions else True

    total = (await session.execute(
        select(func.count()).select_from(PurchaseOrder).where(where)
    )).scalar() or 0

    result = await session.execute(
        select(PurchaseOrder)
        .where(where)
        .order_by(PurchaseOrder.created_at.desc())
        .offset(page.offset)
        .limit(page.page_size)
    )
    pos = result.scalars().all()

    items = []
    for po in pos:
        items.append({
            "id": po.id,
            "po_no": po.po_no,
            "supplier_id": po.supplier_id,
            "supplier_name": po.supplier_name,
            "contact": po.contact,
            "phone": po.phone,
            "qq": po.qq or "",
            "wechat": po.wechat or "",
            "bank_account": po.bank_account or "",
            "bank_name": po.bank_name or "",
            "payee": po.payee or "",
            "total_amount": float(po.total_amount),
            "paid_amount": float(po.paid_amount),
            "debt_amount": float(po.debt_amount),
            "status": po.status,
            "order_date": str(po.order_date) if po.order_date else None,
            "expected_date": str(po.expected_date) if po.expected_date else None,
            "arrived_date": str(po.arrived_date) if po.arrived_date else None,
            "remark": po.remark,
            "created_at": str(po.created_at)[:19] if po.created_at else "",
        })

    return paginated(items=items, total=total, page=page.page, page_size=page.page_size)


# ─── 采购拆分新流程：待采购订单 → 预览 → 生成 ───────────────


async def _resolve_supplier_info(session, sid: int | str) -> dict:
    """根据 supplier_id 获取供应商信息"""
    if sid == "pending":
        return {
            "id": None, "name": "待定供应商",
            "contact": "", "phone": "",
            "qq": "", "wechat": "",
            "bank_account": "", "bank_name": "", "payee": "",
        }
    sup = (await session.execute(
        select(SupModel).where(SupModel.id == sid)
    )).scalar_one_or_none()
    if sup:
        return {
            "id": sup.id,
            "name": sup.name,
            "contact": sup.contact or "",
            "phone": sup.phone or "",
            "qq": sup.qq or "",
            "wechat": sup.wechat or "",
            "bank_account": sup.bank_account or "",
            "bank_name": sup.bank_name or "",
            "payee": sup.payee or "",
        }
    return {
        "id": None, "name": "待定供应商",
        "contact": "", "phone": "",
        "qq": "", "wechat": "",
        "bank_account": "", "bank_name": "", "payee": "",
    }


def _merge_items(group_items: list) -> tuple[list, float]:
    """合并同一产品，返回(merged_items, total_amount)"""
    merged: dict = {}
    for it in group_items:
        key = it.product_id if it.product_id else f"__name_{it.product_name}__"
        spec = f"{it.room} {it.width}x{it.height} 倍率{it.fold_ratio}" if it.room else ""
        if key in merged:
            merged[key]["qty"] += float(it.qty or 1)
            merged[key]["amount"] += float(it.amount or 0)
            if spec:
                merged[key]["specs"].append(spec)
        else:
            merged[key] = {
                "product_id": it.product_id,
                "product_name": it.product_name or "",
                "product_code": it.product_code or "",
                "qty": float(it.qty or 1),
                "unit": it.unit or "米",
                "unit_price": float(it.unit_price or 0),
                "amount": float(it.amount or 0),
                "specs": [spec] if spec else [],
                "material_type": it.material_type or "主料",
            }
    items = list(merged.values())
    total = sum(it["amount"] for it in items)
    return items, total


def _build_supplier_groups(items: list) -> dict:
    """按 supplier_id 分组"""
    groups: dict = {}
    for it in items:
        sid = it.supplier_id if it.supplier_id else "pending"
        groups.setdefault(sid, []).append(it)
    return groups


async def _build_split_plan(session, order_ids: list[int]) -> dict:
    """为指定订单构建拆分计划（预览用），按供应商分组、合并产品"""
    orders_result = await session.execute(
        select(Order).where(Order.id.in_(order_ids))
    )
    orders = orders_result.scalars().all()
    if not orders:
        return {"groups": [], "order_ids": [], "order_nos": [], "order_count": 0}

    order_nos = [o.order_no for o in orders]

    items_result = await session.execute(
        select(OrderItem).where(OrderItem.order_id.in_(order_ids))
    )
    all_items = items_result.scalars().all()

    main_items = [it for it in all_items if it.material_type == "主料"]
    aux_items = [it for it in all_items if it.material_type != "主料"]

    groups = []
    for items_list, mat_label in [(main_items, "主料"), (aux_items, "辅料")]:
        if not items_list:
            continue
        for sid, group_items in _build_supplier_groups(items_list).items():
            sinfo = await _resolve_supplier_info(session, sid)
            merged_items, total_amt = _merge_items(group_items)
            groups.append({
                "supplier_id": sinfo["id"],
                "supplier_name": sinfo["name"],
                "contact": sinfo["contact"],
                "phone": sinfo["phone"],
                "qq": sinfo["qq"],
                "wechat": sinfo["wechat"],
                "bank_account": sinfo["bank_account"],
                "bank_name": sinfo["bank_name"],
                "payee": sinfo["payee"],
                "items": merged_items,
                "total_amount": round(total_amt, 2),
                "item_count": len(merged_items),
                "material_type": mat_label,
            })

    return {
        "groups": groups,
        "order_ids": order_ids,
        "order_nos": order_nos,
        "order_count": len(orders),
    }


@router.get("/pending-orders")
async def get_pending_orders(
    session: SessionDep,
    current_user: CurrentUserDep,
    keyword: str | None = Query(None, description="搜索订单号/客户名"),
):
    """获取待采购的订单（已确认未分单）"""
    conditions = [Order.status_key == "confirmed"]
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(or_(Order.order_no.ilike(kw), Order.customer_name.ilike(kw)))

    result = await session.execute(
        select(Order).where(and_(*conditions)).order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()

    items_data = []
    for o in orders:
        items_result = await session.execute(
            select(OrderItem).where(OrderItem.order_id == o.id)
        )
        order_items = items_result.scalars().all()
        items_data.append({
            "id": o.id,
            "order_no": o.order_no,
            "customer_name": o.customer_name or "",
            "customer_phone": o.customer_phone or "",
            "order_date": o.order_date or "",
            "content": o.content or "",
            "item_count": len(order_items),
            "items": [{
                "id": it.id,
                "product_name": it.product_name or "",
                "product_code": it.product_code or "",
                "qty": float(it.qty or 1),
                "unit": it.unit or "米",
                "unit_price": float(it.unit_price or 0),
                "material_type": it.material_type or "主料",
                "supplier_id": it.supplier_id,
                "amount": float(it.amount or 0),
            } for it in order_items],
        })

    return success(data=items_data)


@router.get("/tracking")
async def get_purchase_tracking(
    session: SessionDep,
    current_user: CurrentUserDep,
    keyword: str | None = Query(None, description="搜索订单号/客户名"),
):
    """采购跟踪：查看已分单订单及其采购单状态"""
    conditions = [Order.status_key == "split"]
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(or_(Order.order_no.ilike(kw), Order.customer_name.ilike(kw)))

    result = await session.execute(
        select(Order).where(and_(*conditions)).order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()

    tracking_data = []
    for o in orders:
        pos_result = await session.execute(
            select(PurchaseOrder).where(PurchaseOrder.order_ids.contains(str(o.id)))
        )
        pos = pos_result.scalars().all()

        all_arrived = True
        po_list = []
        for po in pos:
            arrived = po.status in ("全部到货", "已结算")
            if not arrived:
                all_arrived = False
            po_list.append({
                "po_id": po.id,
                "po_no": po.po_no,
                "supplier_name": po.supplier_name or "",
                "status": po.status,
                "total_amount": float(po.total_amount),
                "paid_amount": float(po.paid_amount),
                "item_count": len(po.po_items or []),
                "arrived": arrived,
            })

        tracking_data.append({
            "order_id": o.id,
            "order_no": o.order_no,
            "customer_name": o.customer_name or "",
            "customer_phone": o.customer_phone or "",
            "order_date": o.order_date or "",
            "content": o.content or "",
            "purchase_orders": po_list,
            "all_arrived": all_arrived,
            "po_count": len(po_list),
        })

    return success(data=tracking_data)


# ─── 采购单详情 ───────────────────────────────────────────────


@router.get("/{po_id}")
async def get_purchase_order(session: SessionDep, current_user: CurrentUserDep, po_id: int):
    """采购单详情"""
    result = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("采购单不存在")

    po_items = []
    for item in po.po_items or []:
        po_items.append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": item.product_name,
            "product_code": item.product_code,
            "spec": item.spec,
            "quantity": float(item.quantity),
            "unit": item.unit,
            "unit_price": float(item.unit_price),
            "subtotal": float(item.subtotal),
            "arrived_qty": float(item.arrived_qty),
            "material_type": item.material_type,
        })

    return success(data={
        "id": po.id,
        "po_no": po.po_no,
        "supplier_id": po.supplier_id,
        "supplier_name": po.supplier_name,
        "contact": po.contact,
        "phone": po.phone,
        "qq": po.qq or "",
        "wechat": po.wechat or "",
        "bank_account": po.bank_account or "",
        "bank_name": po.bank_name or "",
        "payee": po.payee or "",
        "total_amount": float(po.total_amount),
        "paid_amount": float(po.paid_amount),
        "debt_amount": float(po.debt_amount),
        "status": po.status,
        "order_ids": po.order_ids,
        "order_date": str(po.order_date) if po.order_date else None,
        "expected_date": str(po.expected_date) if po.expected_date else None,
        "arrived_date": str(po.arrived_date) if po.arrived_date else None,
        "remark": po.remark,
        "items": po.items or [],
        "po_items": po_items,
        "created_at": str(po.created_at)[:19] if po.created_at else "",
    })


# ─── 创建采购单 ───────────────────────────────────────────────


@router.post("")
async def create_purchase_order(
    session: SessionDep, current_user: CurrentUserDep, req: PurchaseOrderCreate
):
    """创建采购单"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = _generate_po_no()
    seq = (await session.execute(
        select(func.count(PurchaseOrder.id)).where(PurchaseOrder.po_no.like(f"{prefix}%"))
    )).scalar() or 0
    po_no = f"{prefix}{seq + 1:03d}"

    # 计算总金额
    subtotal = sum(
        float(i.unit_price or 0) * float(i.quantity or 1)
        for i in req.items
    )

    from datetime import date
    expected = None
    if req.expected_date:
        try:
            expected = datetime.strptime(req.expected_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    po = PurchaseOrder(
        po_no=po_no,
        supplier_id=req.supplier_id,
        supplier_name="",  # 由前端传或自动查
        contact=req.contact,
        phone=req.phone,
        order_ids=req.order_ids,
        total_amount=subtotal,
        paid_amount=0,
        debt_amount=subtotal,
        status="待采购",
        expected_date=expected,
        remark=req.remark,
    )
    session.add(po)
    await session.flush()

    # 创建明细
    for item_data in req.items:
        po_item = PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=item_data.product_id,
            product_name=item_data.product_name,
            product_code=item_data.product_code,
            spec=item_data.spec,
            quantity=item_data.quantity,
            unit=item_data.unit,
            unit_price=item_data.unit_price,
            subtotal=float(item_data.unit_price) * float(item_data.quantity),
            material_type=item_data.material_type,
        )
        session.add(po_item)

    await session.flush()
    return success(data={"id": po.id, "po_no": po_no}, message="采购单创建成功")


# ─── 采购收货 ─────────────────────────────────────────────────


@router.post("/{po_id}/receive")
async def receive_purchase(
    session: SessionDep, current_user: CurrentUserDep, po_id: int, req: ReceiveCreate
):
    """采购收货（分批到货 + 自动更新库存）"""
    result = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("采购单不存在")

    if po.status in ("全部到货", "已取消"):
        raise BusinessError(f"采购单状态为{po.status}，不允许收货")

    inbound_details = []

    for item in req.items:
        product_id = item.product_id
        qty = float(item.qty or 0)
        if qty <= 0:
            continue

        # 更新采购单明细的已到货数量
        po_item_result = await session.execute(
            select(PurchaseOrderItem).where(
                PurchaseOrderItem.purchase_order_id == po_id,
                PurchaseOrderItem.product_id == product_id,
            )
        )
        po_item = po_item_result.scalar_one_or_none()
        if po_item:
            po_item.arrived_qty = (po_item.arrived_qty or 0) + qty

        # 更新产品库存
        prod_result = await session.execute(select(Product).where(Product.id == product_id))
        prod = prod_result.scalar_one_or_none()
        qty_before = prod.stock if prod else 0
        qty_after = qty_before + qty
        if prod:
            prod.stock = qty_after

        # 写入库存流水
        flow = InventoryFlow(
            product_id=product_id,
            warehouse_id=req.warehouse_id,
            flow_type="IN",
            qty_before=qty_before,
            qty_change=qty,
            qty_after=qty_after,
            ref_type="purchase",
            ref_id=po_id,
            operator_id=current_user.id,
            remark=f"采购收货 {po.po_no}",
        )
        session.add(flow)

        inbound_details.append({
            "product_id": product_id,
            "product_name": item.product_name,
            "qty": qty,
        })

    # 更新采购单状态
    if po.status == "待采购" or po.status == "已下单":
        po.status = "部分到货"
    else:
        po.status = "全部到货"
        po.debt_amount = 0
        from datetime import date
        po.arrived_date = date.today()

    await session.flush()
    return success(
        data={"id": po_id, "status": po.status, "details": inbound_details},
        message=f"已收货 {len(inbound_details)} 项，当前状态：{po.status}",
    )


# ─── 更新采购单状态 ───────────────────────────────────────────


@router.put("/{po_id}/status")
async def update_purchase_status(
    session: SessionDep, current_user: CurrentUserDep, po_id: int, status: str = Query(...),
):
    """更新采购单状态"""
    result = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("采购单不存在")

    po.status = status
    await session.flush()
    return success(data={"id": po_id, "status": status}, message="状态已更新")


# ─── 删除采购单 ───────────────────────────────────────────────


@router.delete("/{po_id}")
async def delete_purchase_order(session: SessionDep, current_user: CurrentUserDep, po_id: int):
    """删除采购单"""
    result = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("采购单不存在")

    # 删除明细
    items = await session.execute(
        select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == po_id)
    )
    for item in items.scalars().all():
        await session.delete(item)

    await session.delete(po)
    await session.flush()
    return success(message="采购单已删除")


# ─── 采购拆分（POST 路由） ──────────────────────────────────


async def _execute_create_pos(session, order_ids: list[int], current_user) -> list[str]:
    """执行拆分：创建采购单并更新订单状态"""
    plan = await _build_split_plan(session, order_ids)
    if not plan["groups"]:
        return []

    order_nos = plan["order_nos"]
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    po_nos = []

    for group in plan["groups"]:
        seq_r = await session.execute(
            select(func.count(PurchaseOrder.id)).where(
                PurchaseOrder.po_no.like(f"PO{today_str}%")
            )
        )
        seq = (seq_r.scalar() or 0) + 1
        po_no = f"PO{today_str}{seq:03d}"
        po_nos.append(po_no)

        order_ids_str = ",".join(str(oid) for oid in sorted(order_ids))
        remark = f"【{group['material_type']}采购】源自订单 {', '.join(order_nos)}"

        po = PurchaseOrder(
            po_no=po_no,
            supplier_id=group["supplier_id"],
            supplier_name=group["supplier_name"],
            contact=group["contact"],
            phone=group["phone"],
            qq=group["qq"],
            wechat=group["wechat"],
            bank_account=group["bank_account"],
            bank_name=group["bank_name"],
            payee=group["payee"],
            order_ids=order_ids_str,
            total_amount=group["total_amount"],
            paid_amount=0,
            debt_amount=group["total_amount"],
            status="待采购",
            order_date=datetime.now(timezone.utc).date(),
            remark=remark,
        )
        session.add(po)
        await session.flush()

        for m in group["items"]:
            poi = PurchaseOrderItem(
                purchase_order_id=po.id,
                product_id=m["product_id"],
                product_name=m["product_name"],
                product_code=m["product_code"],
                spec="；".join(m.get("specs", [])),
                quantity=m["qty"],
                unit=m["unit"],
                unit_price=m["unit_price"],
                subtotal=m["amount"],
                material_type=m["material_type"],
            )
            session.add(poi)

    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    po_detail = f"生成采购单: {', '.join(po_nos)}"
    for oid in order_ids:
        o_result = await session.execute(select(Order).where(Order.id == oid))
        o = o_result.scalar_one_or_none()
        if o:
            history = o.history or []
            history.append({
                "s": o.status_label,
                "s2": "已分单",
                "c": "split",
                "time": now_ts,
                "detail": po_detail,
            })
            o.status_key = "split"
            o.status_label = "已分单"
            o.status_color = "#7c3aed"
            o.history = history

    await session.flush()
    return po_nos


@router.post("/preview")
async def preview_purchase_split(
    session: SessionDep, current_user: CurrentUserDep, req: PurchasePreviewRequest
):
    """预览选定订单的采购拆分方案"""
    if not req.order_ids:
        raise BusinessError("请选择至少一个订单")
    plan = await _build_split_plan(session, req.order_ids)
    if not plan["groups"]:
        raise BusinessError("选定订单中没有需要采购的商品")
    return success(data=plan)


@router.post("/generate")
async def generate_purchase_orders(
    session: SessionDep, current_user: CurrentUserDep, req: PurchaseGenerateRequest
):
    """确认并生成采购单"""
    if not req.order_ids:
        raise BusinessError("请选择至少一个订单")
    po_nos = await _execute_create_pos(session, req.order_ids, current_user)
    if not po_nos:
        raise BusinessError("选定订单中没有需要采购的商品")
    return success(
        data={"po_nos": po_nos},
        message=f"已生成 {len(po_nos)} 张采购单: {', '.join(po_nos)}",
    )
