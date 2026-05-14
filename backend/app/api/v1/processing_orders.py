"""加工单管理 API"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import paginated, success
from app.domain.order import Order, OrderItem
from app.domain.processing_order import ProcessingOrder, ProcessingOrderItem
from app.domain.warehouse import Inventory
from app.services.status_engine import get_status_label, get_status_color
from app.schemas.processing_order import (
    ProcessingOrderItemUpdate,
    ProcessingOrderStatusUpdate,
)

router = APIRouter(prefix="/api/v1/processing", tags=["加工单管理"])


def _generate_po_no(session, today_str: str, seq: int) -> str:
    """生成加工单号：JG + YYYYMMDD + 3位序号"""
    return f"JG{today_str}{seq:03d}"


# ─── 从订单自动生成加工单 ─────────────────────────────────────


@router.post("/generate-from-order/{order_id}")
async def generate_from_order(
    session: SessionDep,
    current_user: CurrentUserDep,
    order_id: int,
    aux_processing: bool = Query(False, description="是否包含辅料"),
):
    """从订单的已确认明细自动生成加工单

    默认仅包含 procurement_type='物料' 的明细；
    设置 aux_processing=true 时可同时包含 '辅料'。
    """
    # 查询订单
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError("订单不存在")

    # 查询订单明细，筛选物料类型
    items_query = select(OrderItem).where(
        OrderItem.order_id == order_id,
        OrderItem.procurement_type == "物料",
    )
    items_result = await session.execute(items_query)
    order_items = list(items_result.scalars().all())

    if not order_items:
        raise BusinessError("该订单没有可生成加工单的物料明细")

    # 如果有辅料一并包含
    if aux_processing:
        aux_result = await session.execute(
            select(OrderItem).where(
                OrderItem.order_id == order_id,
                OrderItem.procurement_type == "辅料",
            )
        )
        order_items.extend(aux_result.scalars().all())

    # 生成加工单号
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y%m%d")
    seq_result = await session.execute(
        select(func.count(ProcessingOrder.id)).where(
            ProcessingOrder.po_no.like(f"JG{today_str}%")
        )
    )
    seq = (seq_result.scalar() or 0) + 1
    po_no = _generate_po_no(session, today_str, seq)

    # 创建加工单
    processing_order = ProcessingOrder(
        po_no=po_no,
        order_id=order.id,
        order_no=order.order_no or "",
        customer_name=order.customer_name or "",
        total_items=len(order_items),
        status="pending",
        printed=False,
    )
    session.add(processing_order)
    await session.flush()

    # 创建加工单明细 + 自动减库存
    for oi in order_items:
        item = ProcessingOrderItem(
            processing_order_id=processing_order.id,
            order_item_id=oi.id,
            product_name=oi.product_name or "",
            product_code=oi.product_code or "",
            width=float(oi.width or 0),
            height=float(oi.height or 0),
            qty=float(oi.qty or 1),
            unit=oi.unit or "",
            process_desc=oi.process_desc or "",
        )
        session.add(item)

        # 自动减库存：扣减主仓库（warehouse_id=1）的对应产品库存
        inv_result = await session.execute(
            select(Inventory).where(
                Inventory.product_id == oi.product_id,
                Inventory.warehouse_id == 1,
            )
        )
        inv = inv_result.scalar_one_or_none()
        deduct_qty = float(oi.qty or 0)
        if inv:
            inv.qty = max(0, float(inv.qty or 0) - deduct_qty)
        # 如果没有库存记录，跳过（无需创建负库存）

    await session.flush()

    # ── 自动推进订单状态：stocked → processing ──
    if order.status_key == "stocked":
        old_label = order.status_label
        new_key = "processing"
        new_label = get_status_label(new_key)
        new_color = get_status_color(new_key)
        history = order.history or []
        history.append({
            "s": old_label,
            "s2": new_label,
            "c": new_key,
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "detail": f"生成加工单「{po_no}」，自动推进到「加工中」",
        })
        order.status_key = new_key
        order.status_label = new_label
        order.status_color = new_color
        order.history = history

    return success(
        data={"id": processing_order.id, "po_no": po_no},
        message=f"加工单「{po_no}」生成成功",
    )


# ─── 待生成加工单列表 ─────────────────────────────────────


@router.get("/pending-orders")
async def list_pending_processing_orders(
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """查询已入库但尚未生成加工单的订单（即有物料待加工的订单）"""
    # 查询所有 stocked 状态的订单，且有关联的物料明细
    result = await session.execute(
        select(Order).where(
            Order.status_key == "stocked",
        ).order_by(Order.id.desc())
    )
    all_orders = list(result.scalars().all())

    pending = []
    for o in all_orders:
        # 检查是否有物料明细
        mat_result = await session.execute(
            select(OrderItem).where(
                OrderItem.order_id == o.id,
                OrderItem.procurement_type == "物料",
            )
        )
        mat_items = list(mat_result.scalars().all())
        if not mat_items:
            continue
        # 检查是否已有加工单
        po_check = await session.execute(
            select(ProcessingOrder.id).where(ProcessingOrder.order_id == o.id)
        )
        if po_check.scalar_one_or_none():
            continue
        pending.append({
            "order_id": o.id,
            "order_no": o.order_no or "",
            "customer_name": o.customer_name or "",
            "material_count": len(mat_items),
            "order_date": str(o.order_date) if o.order_date else "",
        })

    return success(data=pending)


# ─── 加工单列表 ───────────────────────────────────────────────


@router.get("")
async def list_processing_orders(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    status: str | None = Query(None, description="状态筛选: pending/processing/completed"),
    keyword: str | None = Query(None, description="搜索单号/客户名"),
    order_status: str | None = Query(None, description="按关联订单状态筛选"),
):
    """加工单列表（分页 + 筛选）"""
    conditions = []

    if status:
        conditions.append(ProcessingOrder.status == status)
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(or_(
            ProcessingOrder.po_no.ilike(kw),
            ProcessingOrder.customer_name.ilike(kw),
            ProcessingOrder.order_no.ilike(kw),
        ))

    # 按关联订单状态筛选（需关联 orders 表）
    if order_status:
        conditions.append(Order.status_key == order_status)

    where = and_(*conditions) if conditions else True

    # 构建查询
    query = select(ProcessingOrder)
    if order_status:
        query = query.join(Order, ProcessingOrder.order_id == Order.id)

    total = (await session.execute(
        select(func.count()).select_from(
            ProcessingOrder.__table__.join(Order, ProcessingOrder.order_id == Order.id)
            if order_status else ProcessingOrder.__table__
        ).where(where)
    )).scalar() or 0

    result = await session.execute(
        query
        .where(where)
        .order_by(ProcessingOrder.id.desc())
        .offset(page.offset)
        .limit(page.page_size)
    )
    orders = result.scalars().all()

    items = [
        {
            "id": po.id,
            "po_no": po.po_no,
            "order_id": po.order_id,
            "order_no": po.order_no or "",
            "customer_name": po.customer_name or "",
            "warehouse_id": po.warehouse_id,
            "processing_factory": po.processing_factory or "",
            "total_items": po.total_items or 0,
            "total_process_fee": float(po.total_process_fee or 0),
            "status": po.status,
            "printed": bool(po.printed),
            "remark": po.remark or "",
            "completed_at": str(po.completed_at)[:19] if po.completed_at else None,
            "created_at": str(po.created_at)[:19] if po.created_at else "",
        }
        for po in orders
    ]

    return paginated(items=items, total=total, page=page.page, page_size=page.page_size)


# ─── 加工单详情 ───────────────────────────────────────────────


@router.get("/{po_id}")
async def get_processing_order(session: SessionDep, current_user: CurrentUserDep, po_id: int):
    """加工单详情（含明细）"""
    result = await session.execute(
        select(ProcessingOrder).where(ProcessingOrder.id == po_id)
    )
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("加工单不存在")

    # 获取明细
    items_result = await session.execute(
        select(ProcessingOrderItem)
        .where(ProcessingOrderItem.processing_order_id == po_id)
        .order_by(ProcessingOrderItem.id)
    )
    items = items_result.scalars().all()

    return success(data={
        "id": po.id,
        "po_no": po.po_no,
        "order_id": po.order_id,
        "order_no": po.order_no or "",
        "customer_name": po.customer_name or "",
        "warehouse_id": po.warehouse_id,
        "processing_factory": po.processing_factory or "",
        "total_items": po.total_items or 0,
        "total_process_fee": float(po.total_process_fee or 0),
        "status": po.status,
        "printed": bool(po.printed),
        "remark": po.remark or "",
        "completed_at": str(po.completed_at)[:19] if po.completed_at else None,
        "created_at": str(po.created_at)[:19] if po.created_at else "",
        "updated_at": str(po.updated_at)[:19] if po.updated_at else "",
        "items": [
            {
                "id": item.id,
                "processing_order_id": item.processing_order_id,
                "order_item_id": item.order_item_id,
                "product_name": item.product_name or "",
                "product_code": item.product_code or "",
                "width": float(item.width or 0),
                "height": float(item.height or 0),
                "qty": float(item.qty or 0),
                "unit": item.unit or "",
                "process_desc": item.process_desc or "",
                "process_fee_unit": float(item.process_fee_unit or 0),
                "process_fee_subtotal": float(item.process_fee_subtotal or 0),
                "checked": bool(item.checked),
                "remark": item.remark or "",
            }
            for item in items
        ],
    })


# ─── 更新明细 ─────────────────────────────────────────────────


@router.put("/{po_id}/items/{item_id}")
async def update_processing_order_item(
    session: SessionDep,
    current_user: CurrentUserDep,
    po_id: int,
    item_id: int,
    req: ProcessingOrderItemUpdate,
):
    """更新加工单明细（加工单价、验收状态、备注）"""
    # 验证加工单存在
    po_result = await session.execute(select(ProcessingOrder).where(ProcessingOrder.id == po_id))
    po = po_result.scalar_one_or_none()
    if not po:
        raise NotFoundError("加工单不存在")

    # 验证明细存在且属于该加工单
    item_result = await session.execute(
        select(ProcessingOrderItem).where(
            ProcessingOrderItem.id == item_id,
            ProcessingOrderItem.processing_order_id == po_id,
        )
    )
    item = item_result.scalar_one_or_none()
    if not item:
        raise NotFoundError("加工单明细不存在")

    # 更新字段
    if req.process_fee_unit is not None:
        item.process_fee_unit = req.process_fee_unit
        # 重新计算小计
        item.process_fee_subtotal = round(float(req.process_fee_unit) * float(item.qty or 0), 2)
    if req.checked is not None:
        item.checked = req.checked
    if req.remark is not None:
        item.remark = req.remark

    await session.flush()

    return success(message="加工单明细更新成功")


# ─── 更新状态 ──────────────────────────────────────────────────


@router.put("/{po_id}/status")
async def update_processing_order_status(
    session: SessionDep,
    current_user: CurrentUserDep,
    po_id: int,
    req: ProcessingOrderStatusUpdate,
):
    """更新加工单状态: pending → processing → completed"""
    result = await session.execute(select(ProcessingOrder).where(ProcessingOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("加工单不存在")

    valid_statuses = ["pending", "processing", "completed"]
    new_status = req.status

    if new_status not in valid_statuses:
        raise BusinessError(f"无效状态: {new_status}，仅支持 pending/processing/completed")

    # 校验状态流转
    current = po.status
    if current == "pending" and new_status not in ("processing", "completed"):
        raise BusinessError("pending 状态只能流转到 processing 或 completed")
    if current == "processing" and new_status != "completed":
        raise BusinessError("processing 状态只能流转到 completed")
    if current == "completed":
        raise BusinessError("加工单已完成，无法变更状态")

    po.status = new_status

    # 如果标记为 completed，记录完成时间
    if new_status == "completed":
        po.completed_at = datetime.now(timezone.utc)
        # 重新结算加工费
        items_result = await session.execute(
            select(ProcessingOrderItem).where(
                ProcessingOrderItem.processing_order_id == po_id
            )
        )
        items = items_result.scalars().all()
        total_fee = sum(float(item.process_fee_subtotal or 0) for item in items)
        po.total_process_fee = round(total_fee, 2)

        # ── 自动推进订单状态：processing → completed ──
        order_result = await session.execute(select(Order).where(Order.id == po.order_id))
        o = order_result.scalar_one_or_none()
        if o and o.status_key == "processing":
            old_label = o.status_label
            new_key = "completed"
            new_label = get_status_label(new_key)
            new_color = get_status_color(new_key)
            history = o.history or []
            history.append({
                "s": old_label,
                "s2": new_label,
                "c": new_key,
                "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                "detail": f"加工单「{po.po_no}」已完成，自动推进到「已完成」",
            })
            o.status_key = new_key
            o.status_label = new_label
            o.status_color = new_color
            o.history = history

    await session.flush()

    return success(
        data={
            "id": po.id,
            "status": po.status,
            "completed_at": str(po.completed_at)[:19] if po.completed_at else None,
        },
        message=f"加工单状态已更新为「{new_status}」",
    )


# ─── 标记已打印 ────────────────────────────────────────────────


@router.put("/{po_id}/mark-printed")
async def mark_printed(session: SessionDep, current_user: CurrentUserDep, po_id: int):
    """标记加工单为已打印"""
    result = await session.execute(select(ProcessingOrder).where(ProcessingOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("加工单不存在")

    po.printed = True
    await session.flush()

    return success(message="加工单已标记为已打印")


# ─── 打印数据 ──────────────────────────────────────────────────


@router.get("/{po_id}/print")
async def get_print_data(session: SessionDep, current_user: CurrentUserDep, po_id: int):
    """获取打印数据"""
    result = await session.execute(select(ProcessingOrder).where(ProcessingOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("加工单不存在")

    items_result = await session.execute(
        select(ProcessingOrderItem)
        .where(ProcessingOrderItem.processing_order_id == po_id)
        .order_by(ProcessingOrderItem.id)
    )
    items = items_result.scalars().all()

    return success(data={
        "po_no": po.po_no,
        "order_no": po.order_no or "",
        "customer_name": po.customer_name or "",
        "processing_factory": po.processing_factory or "",
        "status": po.status,
        "total_items": po.total_items or 0,
        "total_process_fee": float(po.total_process_fee or 0),
        "remark": po.remark or "",
        "created_at": str(po.created_at)[:19] if po.created_at else "",
        "items": [
            {
                "product_name": item.product_name or "",
                "product_code": item.product_code or "",
                "width": float(item.width or 0),
                "height": float(item.height or 0),
                "qty": float(item.qty or 0),
                "unit": item.unit or "",
                "process_desc": item.process_desc or "",
                "process_fee_unit": float(item.process_fee_unit or 0),
                "process_fee_subtotal": float(item.process_fee_subtotal or 0),
                "checked": bool(item.checked),
                "remark": item.remark or "",
            }
            for item in items
        ],
    })


# ─── 结算加工费 ────────────────────────────────────────────────


@router.post("/{po_id}/settle")
async def settle_processing_fees(
    session: SessionDep,
    current_user: CurrentUserDep,
    po_id: int,
):
    """结算加工费：重新计算所有明细的加工费小计并汇总总额"""
    result = await session.execute(select(ProcessingOrder).where(ProcessingOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("加工单不存在")

    # 重新计算所有明细的小计
    items_result = await session.execute(
        select(ProcessingOrderItem).where(
            ProcessingOrderItem.processing_order_id == po_id
        )
    )
    items = items_result.scalars().all()

    if not items:
        raise BusinessError("加工单无明细，无法结算")

    total_fee = 0.0
    for item in items:
        fee_unit = float(item.process_fee_unit or 0)
        qty = float(item.qty or 0)
        item.process_fee_subtotal = round(fee_unit * qty, 2)
        total_fee += float(item.process_fee_subtotal)

    total_fee = round(total_fee, 2)
    po.total_process_fee = total_fee

    await session.flush()

    return success(
        data={
            "id": po.id,
            "po_no": po.po_no,
            "total_process_fee": total_fee,
            "item_count": len(items),
        },
        message=f"加工费结算完成，总额: {total_fee}",
    )
