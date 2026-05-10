"""
订单管理 API
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import paginated, success
from app.domain.order import Order, OrderItem
from app.domain.installation import InstallationOrder
from app.domain.purchase import PurchaseOrder, PurchaseOrderItem
from app.services.status_engine import (
    ORDER_STATUS_CONFIG,
    STATUS_STEPS,
    TERMINAL_STATUSES,
    can_transition,
    get_next_status,
    get_status_color,
    get_status_label,
    is_terminal,
    normalize_status_key,
)
from app.schemas.order import OrderCreate, OrderItemCreate, OrderUpdate, OrderRollbackRequest

router = APIRouter(prefix="/api/v1/orders", tags=["订单管理"])


def _generate_order_no(session, today_str: str, seq: int) -> str:
    """生成订单号：YYYYMMDD + 3位序号"""
    return f"{today_str}{seq:03d}"


def _build_order_history(status_key: str) -> list[dict]:
    """创建订单时的初始历史记录"""
    label = get_status_label(status_key)
    return [{
        "s": "创建订单",
        "s2": label,
        "c": status_key,
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
    }]


def _build_history_entry(old_label: str, new_label: str, new_key: str) -> dict:
    return {
        "s": old_label,
        "s2": new_label,
        "c": new_key,
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
    }


# ─── 订单列表 ─────────────────────────────────────────────────


@router.get("")
async def list_orders(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    status_key: str | None = Query(None, description="状态筛选"),
    order_type: str | None = Query(None, description="订单类型"),
    keyword: str | None = Query(None, description="搜索订单号/客户名"),
    year: int | None = Query(None, description="年份"),
    month: int | None = Query(None, description="月份"),
):
    """订单列表（分页 + 多条件筛选）"""
    conditions = []

    if status_key:
        conditions.append(Order.status_key == status_key)
    if order_type:
        conditions.append(Order.order_type == order_type)
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(or_(Order.order_no.ilike(kw), Order.customer_name.ilike(kw)))
    if year:
        conditions.append(Order.order_date >= f"{year}-01-01")
        conditions.append(Order.order_date < f"{year + 1}-01-01")
    if month and year:
        import calendar
        m_start = f"{year}-{month:02d}-01"
        m_end_day = calendar.monthrange(year, month)[1]
        conditions.append(Order.order_date >= m_start)
        conditions.append(Order.order_date <= f"{year}-{month:02d}-{m_end_day:02d}")

    where = and_(*conditions) if conditions else True

    total = (await session.execute(
        select(func.count()).select_from(Order).where(where)
    )).scalar() or 0

    result = await session.execute(
        select(Order)
        .where(where)
        .order_by(Order.created_at.desc())
        .offset(page.offset)
        .limit(page.page_size)
    )
    orders = result.scalars().all()

    items = []
    for o in orders:
        items.append({
            "id": o.id,
            "order_no": o.order_no,
            "customer_name": o.customer_name or "",
            "customer_phone": o.customer_phone or "",
            "order_type": o.order_type or "",
            "content": o.content or "",
            "amount": float(o.amount or 0),
            "received": float(o.received or 0),
            "debt": float(o.debt or 0),
            "status_key": o.status_key,
            "status_label": o.status_label,
            "status_color": o.status_color,
            "order_date": o.order_date or "",
            "delivery_date": o.delivery_date or "",
            "salesperson_name": o.salesperson_name or "",
            "created_at": str(o.created_at)[:19] if o.created_at else "",
        })

    return paginated(items=items, total=total, page=page.page, page_size=page.page_size)


# ─── 采购拆分预览/确认（静态路由，必须在 /{order_id} 之前注册） ──


@router.get("/split-preview")
async def split_preview(session: SessionDep, current_user: CurrentUserDep):
    """预览采购拆分结果（不实际创建，操作员确认后再执行）"""
    plan = await _build_split_plan(session)
    if not plan["order_ids"]:
        raise BusinessError("没有「已确认」状态的订单需要拆分")
    return success(data=plan)


@router.post("/confirm-split")
async def confirm_split(session: SessionDep, current_user: CurrentUserDep):
    """操作员确认后执行采购拆分"""
    po_nos = await _auto_split_purchase(session)
    if not po_nos:
        raise BusinessError("没有「已确认」状态的订单需要拆分")
    return success(
        data={"po_nos": po_nos},
        message=f"已拆分为 {len(po_nos)} 张采购单: {', '.join(po_nos)}",
    )


# ─── 订单详情 ─────────────────────────────────────────────────


@router.get("/{order_id}")
async def get_order(session: SessionDep, current_user: CurrentUserDep, order_id: int):
    """订单详情"""
    result = await session.execute(select(Order).where(Order.id == order_id))
    o = result.scalar_one_or_none()
    if not o:
        raise NotFoundError("订单不存在")

    items_data = []
    # 批量获取所有供应商ID
    sup_ids = set()
    for item in o.items or []:
        if item.supplier_id:
            sup_ids.add(item.supplier_id)
    sup_map = {}
    if sup_ids:
        from app.domain.product import Supplier as SupModel
        sup_result = await session.execute(
            select(SupModel).where(SupModel.id.in_(sup_ids))
        )
        for sup in sup_result.scalars().all():
            sup_map[sup.id] = sup.name

    for item in o.items or []:
        items_data.append({
            "id": item.id,
            "item_type": item.item_type,
            "product_id": item.product_id,
            "product_name": item.product_name,
            "product_code": item.product_code,
            "room": item.room,
            "width": float(item.width or 0),
            "height": float(item.height or 0),
            "fold_ratio": float(item.fold_ratio or 2.0),
            "unit": item.unit,
            "unit_price": float(item.unit_price or 0),
            "qty": float(item.qty or 1),
            "discount": float(item.discount or 1.0),
            "amount": float(item.amount or 0),
            "final_amount": float(item.final_amount or 0),
            "open_type": item.open_type or "",
            "style_code": item.style_code or "",
            "process_desc": item.process_desc or "",
            "classification": item.classification or "",
            "calc_type": item.calc_type or "per_meter",
            "material_type": item.material_type or "主料",
            "supplier_id": item.supplier_id,
            "supplier_name": sup_map.get(item.supplier_id, "") if item.supplier_id else "",
            "note": item.note or "",
        })

    return success(data={
        "id": o.id,
        "order_no": o.order_no,
        "customer_id": o.customer_id,
        "customer_name": o.customer_name or "",
        "customer_phone": o.customer_phone or "",
        "order_type": o.order_type or "",
        "salesperson_id": o.salesperson_id,
        "salesperson_name": o.salesperson_name or "",
        "quote_amount": float(o.quote_amount or 0),
        "discount_amount": float(o.discount_amount or 0),
        "round_amount": float(o.round_amount or 0),
        "amount": float(o.amount or 0),
        "received": float(o.received or 0),
        "debt": float(o.debt or 0),
        "discount_reason": o.discount_reason or "",
        "order_date": o.order_date or "",
        "delivery_date": o.delivery_date or "",
        "delivery_method": o.delivery_method or "",
        "status_key": o.status_key,
        "status_label": o.status_label,
        "status_color": o.status_color,
        "content": o.content or "",
        "remark": o.remark or "",
        "install_address": o.install_address or "",
        "install_date": str(o.install_date) if o.install_date else None,
        "install_time_slot": o.install_time_slot or "",
        "history": o.history or [],
        "items": items_data,
        "created_at": str(o.created_at)[:19] if o.created_at else "",
    })


# ─── 创建订单 ─────────────────────────────────────────────────


@router.post("")
async def create_order(session: SessionDep, current_user: CurrentUserDep, req: OrderCreate):
    """创建订单"""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y%m%d")

    # 生成订单号
    seq_result = await session.execute(
        select(func.count(Order.id)).where(Order.order_no.like(f"{today_str}%"))
    )
    seq = (seq_result.scalar() or 0) + 1
    order_no = _generate_order_no(session, today_str, seq)

    # 计算金额（折后金额 = amount × discount，订单报价 = 各明细折后金额之和）
    items_data = req.items or []
    quote_amount = sum(
        float(i.amount or 0) * float(i.discount or 1.0)
        for i in items_data
    )
    discount = float(req.discount_amount or 0)
    round_amt = float(req.round_amount or 0)
    amount = max(0, quote_amount - discount - round_amt)
    received = float(req.received or 0)

    # 处理日期
    order_date = req.order_date or now.strftime("%Y-%m-%d")
    delivery_date = req.delivery_date or ""

    # 安装日期转换
    install_date_val = None
    if req.install_date:
        from datetime import date
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
            try:
                install_date_val = datetime.strptime(req.install_date, fmt).date()
                break
            except ValueError:
                continue

    # 创建订单
    order = Order(
        order_no=order_no,
        customer_id=req.customer_id,
        customer_name=req.customer_name,
        customer_phone=req.customer_phone,
        order_type=req.order_type,
        salesperson_id=req.salesperson_id or current_user.id,
        salesperson_name=req.salesperson_name or current_user.name,
        quote_amount=quote_amount,
        discount_amount=discount,
        round_amount=round_amt,
        amount=amount,
        received=received,
        debt=max(0, amount - received),
        order_date=order_date,
        delivery_date=delivery_date,
        delivery_method=req.delivery_method,
        content=req.content,
        remark=req.remark,
        install_address=req.install_address,
        install_date=install_date_val,
        install_time_slot=req.install_time_slot,
        status_key="initial",
        status_label="待量尺",
        status_color="#909399",
        history=_build_order_history("initial"),
    )
    session.add(order)
    await session.flush()

    # 创建订单明细
    for item_data in items_data:
        item_amount = float(item_data.amount or 0)
        item_discount = float(item_data.discount or 1.0)
        item = OrderItem(
            order_id=order.id,
            item_type=item_data.item_type,
            product_id=item_data.product_id,
            product_name=item_data.product_name,
            product_code=item_data.product_code,
            room=item_data.room,
            width=item_data.width,
            height=item_data.height,
            fold_ratio=item_data.fold_ratio,
            unit=item_data.unit,
            unit_price=item_data.unit_price,
            qty=item_data.qty,
            discount=item_discount,
            amount=item_amount,
            final_amount=round(item_amount * item_discount, 2),
            open_type=item_data.open_type,
            style_code=item_data.style_code,
            process_desc=item_data.process_desc,
            classification=item_data.classification,
            material_type=item_data.material_type,
            calc_type=item_data.calc_type,
            supplier_id=item_data.supplier_id,
            note=item_data.note,
        )
        session.add(item)

    await session.flush()

    return success(data={"id": order.id, "order_no": order_no}, message="订单创建成功")


# ─── 更新订单 ─────────────────────────────────────────────────


@router.put("/{order_id}")
async def update_order(
    session: SessionDep, current_user: CurrentUserDep, order_id: int, req: OrderUpdate
):
    """更新订单"""
    result = await session.execute(select(Order).where(Order.id == order_id))
    o = result.scalar_one_or_none()
    if not o:
        raise NotFoundError("订单不存在")

    # 只允许在初始状态编辑
    if o.status_key not in ("initial", "created"):
        raise BusinessError("订单已进入流程，无法编辑")

    # 更新标量字段
    scalar_fields = [
        "customer_name", "customer_phone", "order_type", "delivery_method",
        "delivery_date", "order_date",
        "content", "remark", "install_address", "install_time_slot",
        "discount_amount", "round_amount", "discount_reason",
        "salesperson_name",
    ]
    for field in scalar_fields:
        val = getattr(req, field, None)
        if val is not None:
            setattr(o, field, val)

    # 更新安装日期
    if req.install_date is not None:
        from datetime import date
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
            try:
                o.install_date = datetime.strptime(req.install_date, fmt).date()
                break
            except ValueError:
                continue

    # 更新收款
    if req.received is not None:
        o.received = float(req.received)
        o.debt = max(0, float(o.amount or 0) - float(req.received))

    # 更新明细（删除旧+创建新）
    if req.items is not None:
        # 删除旧明细
        old_items = await session.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        for old in old_items.scalars().all():
            await session.delete(old)

        # 重新计算金额（使用折后金额，与创建接口一致）
        items_data = req.items
        quote = sum(
            float(i.amount or 0) * float(i.discount or 1.0)
            for i in items_data
        )
        o.quote_amount = round(quote, 2)
        discount = float(req.discount_amount or o.discount_amount or 0)
        round_amt = float(req.round_amount or o.round_amount or 0)
        o.amount = max(0, round(quote - discount - round_amt, 2))
        o.debt = max(0, float(o.amount or 0) - float(o.received or 0))

        for item_data in items_data:
            item_amount = float(item_data.amount or 0)
            item_discount = float(item_data.discount or 1.0)
            item = OrderItem(
                order_id=order_id,
                item_type=item_data.item_type,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                product_code=item_data.product_code,
                room=item_data.room,
                width=item_data.width,
                height=item_data.height,
                fold_ratio=item_data.fold_ratio,
                unit=item_data.unit,
                unit_price=item_data.unit_price,
                qty=item_data.qty,
                discount=item_discount,
                amount=item_amount,
                final_amount=round(item_amount * item_discount, 2),
                open_type=item_data.open_type,
                style_code=item_data.style_code,
                process_desc=item_data.process_desc,
                classification=item_data.classification,
                calc_type=item_data.calc_type,
                supplier_id=item_data.supplier_id,
                material_type=item_data.material_type,
                note=item_data.note,
            )
            session.add(item)

    await session.flush()
    return success(data={"id": order_id}, message="订单更新成功")


# ─── 采购拆分逻辑 ─────────────────────────────────────────────


async def _build_split_plan(session) -> dict:
    """构建拆分计划（预览用），从已确认订单中提取数据，按供应商分组、合并产品，不写入数据库

    Returns:
    {
        "main_orders": [{supplier info, items[], total_amount}, ...],
        "aux_orders": [{supplier info, items[], total_amount}, ...],
        "order_ids": [1,2,3],
        "order_nos": ["20260508001", ...],
    }
    """
    from app.domain.product import Supplier as SupModel

    # 查询所有已确认的订单
    result = await session.execute(
        select(Order).where(Order.status_key == "confirmed")
    )
    orders = result.scalars().all()
    if not orders:
        return {"main_orders": [], "aux_orders": [], "order_ids": [], "order_nos": []}

    order_ids = [o.id for o in orders]
    order_nos = [o.order_no for o in orders]

    # 获取所有订单明细
    items_result = await session.execute(
        select(OrderItem).where(OrderItem.order_id.in_(order_ids))
    )
    all_items = items_result.scalars().all()

    # 分离主料和辅料
    main_items = [it for it in all_items if it.material_type == "主料"]
    aux_items = [it for it in all_items if it.material_type != "主料"]

    async def _resolve_supplier(sid: int | str) -> dict:
        """根据 supplier_id 获取供应商全套信息"""
        if sid == "pending":
            placeholder = (await session.execute(
                select(SupModel).where(SupModel.name == "待定供应商").limit(1)
            )).scalar_one_or_none()
            return {
                "id": placeholder.id if placeholder else None,
                "name": placeholder.name if placeholder else "待定供应商",
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

    def _merge_items(group_items: list, material_label: str) -> tuple[list, float]:
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
                    "material_type": material_label,
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

    main_orders = []
    for sid, group_items in _build_supplier_groups(main_items).items():
        sinfo = await _resolve_supplier(sid)
        merged_items, total_amt = _merge_items(group_items, "主料")
        main_orders.append({
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
            "total_amount": total_amt,
            "item_count": len(merged_items),
        })

    aux_orders = []
    for sid, group_items in _build_supplier_groups(aux_items).items():
        sinfo = await _resolve_supplier(sid)
        merged_items, total_amt = _merge_items(group_items, "辅料")
        aux_orders.append({
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
            "total_amount": total_amt,
            "item_count": len(merged_items),
        })

    return {
        "main_orders": main_orders,
        "aux_orders": aux_orders,
        "order_ids": order_ids,
        "order_nos": order_nos,
        "order_count": len(orders),
    }


async def _auto_split_purchase(session) -> list[str]:
    """执行拆分：根据拆分计划创建采购单，更新订单状态"""
    plan = await _build_split_plan(session)
    if not plan["order_ids"]:
        return []

    order_ids = plan["order_ids"]
    order_nos = plan["order_nos"]
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    po_nos = []

    async def _create_po(supplier_order: dict, material_label: str, remark_label: str) -> str:
        seq_r = await session.execute(
            select(func.count(PurchaseOrder.id)).where(
                PurchaseOrder.po_no.like(f"PO{today_str}%")
            )
        )
        seq = (seq_r.scalar() or 0) + 1
        po_no = f"PO{today_str}{seq:03d}"
        po_nos.append(po_no)

        order_ids_str = ",".join(str(oid) for oid in sorted(order_ids))

        po = PurchaseOrder(
            po_no=po_no,
            supplier_id=supplier_order["supplier_id"],
            supplier_name=supplier_order["supplier_name"],
            contact=supplier_order["contact"],
            phone=supplier_order["phone"],
            qq=supplier_order["qq"],
            wechat=supplier_order["wechat"],
            bank_account=supplier_order["bank_account"],
            bank_name=supplier_order["bank_name"],
            payee=supplier_order["payee"],
            order_ids=order_ids_str,
            total_amount=supplier_order["total_amount"],
            paid_amount=0,
            debt_amount=supplier_order["total_amount"],
            status="待采购",
            order_date=datetime.now(timezone.utc).date(),
            remark=f"{remark_label} - 源自订单 {', '.join(order_nos)}",
        )
        session.add(po)
        await session.flush()

        for m in supplier_order["items"]:
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
                material_type=material_label,
            )
            session.add(poi)

        return po_no

    # 创建主料采购单
    for so in plan["main_orders"]:
        await _create_po(so, "主料", "主料采购")

    # 创建辅料采购单
    for so in plan["aux_orders"]:
        await _create_po(so, "辅料", "辅料集中采购")

    # 将所有已处理订单状态更新为"已分单"
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    po_detail = f"生成采购单: {', '.join(po_nos)}"
    for oid in order_ids:
        o_result = await session.execute(select(Order).where(Order.id == oid))
        o = o_result.scalar_one_or_none()
        if o:
            old_label = o.status_label
            history = o.history or []
            history.append({
                "s": old_label,
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


# (split_preview and confirm_split registered below as static routes)


@router.post("/{order_id}/split")
async def split_order_purchase(session: SessionDep, current_user: CurrentUserDep, order_id: int):
    """手动触发采购拆分（自动执行，后续将替换为预览确认流程）"""
    count = (await session.execute(
        select(func.count(Order.id)).where(Order.status_key == "confirmed")
    )).scalar() or 0
    if count == 0:
        raise BusinessError("没有「已确认」状态的订单需要拆分")

    po_nos = await _auto_split_purchase(session)

    return success(
        data={"po_nos": po_nos},
        message=f"已拆分为 {len(po_nos)} 张采购单",
    )


# ─── 订单状态推进 ─────────────────────────────────────────────


@router.post("/{order_id}/advance")
async def advance_order(session: SessionDep, current_user: CurrentUserDep, order_id: int):
    """订单状态推进到下一阶段"""
    result = await session.execute(select(Order).where(Order.id == order_id))
    o = result.scalar_one_or_none()
    if not o:
        raise NotFoundError("订单不存在")

    if is_terminal(o.status_key):
        raise BusinessError(f"订单已在终态「{o.status_label}」，无法推进")

    old_key = o.status_key
    old_label = o.status_label

    auto_action = None

    # 特殊处理：confirmed → 返回拆分预览，由操作员确认
    if old_key == "confirmed":
        plan = await _build_split_plan(session)
        if plan["order_ids"]:
            return success(
                data={
                    "need_preview": True,
                    "preview": plan,
                    "order_id": order_id,
                    "new_status_key": "split",
                },
                message="请确认采购拆分方案",
            )
        # 没有明细需要拆分，直接推进
        new_key = "split"
    # 特殊处理：completed → 自动生成安装单
    elif old_key == "completed":
        # 检查是否已有安装单
        ins_result = await session.execute(
            select(InstallationOrder).where(InstallationOrder.order_id == order_id)
        )
        existing_ins = ins_result.scalar_one_or_none()
        if existing_ins:
            new_key = "install_scheduled"
        else:
            # 自动生成安装单
            today = datetime.now(timezone.utc).strftime("%Y%m%d")
            seq_r = await session.execute(
                select(func.count(InstallationOrder.id)).where(
                    InstallationOrder.ins_no.like(f"INS{today}%")
                )
            )
            seq = (seq_r.scalar() or 0) + 1
            ins_no = f"INS{today}{seq:03d}"
            ins = InstallationOrder(
                ins_no=ins_no,
                order_id=o.id,
                order_no=o.order_no or "",
                customer_name=o.customer_name or "",
                customer_phone=o.customer_phone or "",
                address=o.install_address or "",
                product_details={},
                status="待分配",
                receivable_amount=o.amount,
                received_amount=o.received,
                unpaid_amount=o.debt,
            )
            session.add(ins)
            await session.flush()
            new_key = "install_scheduled"
            auto_action = f"已自动生成安装单 {ins_no}"
    else:
        new_key = get_next_status(old_key)

    if not new_key:
        raise BusinessError("无法确定下一状态")

    # 特殊处理：installed → accepted 时更新安装单
    if old_key == "installed" and new_key == "accepted":
        ins_result = await session.execute(
            select(InstallationOrder).where(InstallationOrder.order_id == order_id)
        )
        ins = ins_result.scalar_one_or_none()
        if ins:
            ins.status = "已验收"
            ins.confirmed_at = datetime.now(timezone.utc)

    # 执行状态更新
    new_label = get_status_label(new_key)
    new_color = get_status_color(new_key)
    history = o.history or []
    history.append(_build_history_entry(old_label, new_label, new_key))

    o.status_key = new_key
    o.status_label = new_label
    o.status_color = new_color
    o.history = history

    if new_key == "completed":
        o.debt = 0

    await session.flush()

    return success(
        data={
            "id": order_id,
            "status_key": new_key,
            "status_label": new_label,
            "status_color": new_color,
            "auto_action": auto_action,
        },
        message=f"已从「{old_label}」推进至「{new_label}」",
    )


# ─── 订单状态跳转 ─────────────────────────────────────────────


@router.put("/{order_id}/status")
async def update_order_status(
    session: SessionDep, current_user: CurrentUserDep, order_id: int, status_key: str = Query(...),
):
    """直接跳转到指定状态"""
    result = await session.execute(select(Order).where(Order.id == order_id))
    o = result.scalar_one_or_none()
    if not o:
        raise NotFoundError("订单不存在")

    if status_key not in ORDER_STATUS_CONFIG:
        raise BusinessError(f"无效状态: {status_key}")

    if not can_transition(o.status_key, status_key):
        raise BusinessError(f"不允许从「{o.status_label}」跳转到「{get_status_label(status_key)}」")

    old_label = o.status_label
    new_label = get_status_label(status_key)
    new_color = get_status_color(status_key)

    history = o.history or []
    history.append(_build_history_entry(old_label, new_label, status_key))

    o.status_key = status_key
    o.status_label = new_label
    o.status_color = new_color
    o.history = history

    if status_key == "completed":
        o.debt = 0

    await session.flush()
    return success(data={"id": order_id, "status_key": status_key}, message=f"状态已更新为「{new_label}」")


@router.get("/{order_id}/rollback-options")
async def rollback_options(session: SessionDep, current_user: CurrentUserDep, order_id: int):
    """获取订单可回滚的状态列表（包含历史回退 + 异常处理）"""
    if current_user.role not in ("admin", "manager"):
        raise BusinessError("无权限执行状态回滚，仅管理员和店长可操作")

    result = await session.execute(select(Order).where(Order.id == order_id))
    o = result.scalar_one_or_none()
    if not o:
        raise NotFoundError("订单不存在")

    current = o.status_key

    # 1. 正常回滚：历史中经过的状态
    visited = set()
    history = o.history or []
    for h in history:
        c = h.get("c") or h.get("status_key")
        if c:
            visited.add(c)
    visited.add(o.status_key)
    if "initial" not in visited and len(history) > 0:
        visited.add("initial")

    rollback_options = []
    for key in visited:
        if key == current:
            continue
        info = ORDER_STATUS_CONFIG.get(key)
        if info:
            rollback_options.append({
                "key": key,
                "label": info.get("label", key),
                "color": info.get("color", "#909399"),
            })

    step_order = {k: i for i, k in enumerate(STATUS_STEPS)}
    rollback_options.sort(key=lambda x: step_order.get(x["key"], 999))

    # 2. 异常处理选项（从非终态可跳转）
    exception_options = []
    if current not in TERMINAL_STATUSES and current != "after_sale":
        exception_options.append({
            "key": "after_sale",
            "label": "售后中",
            "color": "#ef4444",
            "description": "订单转入售后流程，适用于客户投诉、产品质量问题等异常情况",
        })
    if current not in TERMINAL_STATUSES and current != "cancelled":
        exception_options.append({
            "key": "cancelled",
            "label": "已取消",
            "color": "#d9d9d9",
            "description": "取消该订单，适用于客户退款、无法履约等情况",
        })

    return success(data={
        "current_key": current,
        "current_label": get_status_label(current),
        "current_color": get_status_color(current),
        "rollback_options": rollback_options,
        "exception_options": exception_options,
    })


@router.post("/{order_id}/rollback")
async def rollback_order_status(
    session: SessionDep, current_user: CurrentUserDep, order_id: int, req: OrderRollbackRequest,
):
    """【管理员/店长】订单状态回退（仅可回退到历史中经过的状态；异常处理可跳转到售后/取消）"""
    if current_user.role not in ("admin", "manager"):
        raise BusinessError("无权限执行状态回滚，仅管理员和店长可操作")

    result = await session.execute(select(Order).where(Order.id == order_id))
    o = result.scalar_one_or_none()
    if not o:
        raise NotFoundError("订单不存在")

    status_key = req.status_key

    if status_key not in ORDER_STATUS_CONFIG:
        raise BusinessError(f"无效状态: {status_key}")

    # 判断是否异常处理跳转
    is_exception = status_key in ("after_sale", "cancelled")
    is_terminal_jump = is_exception

    if is_exception:
        # 异常处理：需填写原因
        if not req.remark:
            raise BusinessError(f"异常处理操作（{get_status_label(status_key)}）必须填写原因说明")
        if o.status_key in TERMINAL_STATUSES and o.status_key != "after_sale":
            raise BusinessError(f"订单已在终态「{o.status_label}」，无法进行异常处理")
    else:
        # 正常回退：验证目标状态在历史中
        history = o.history or []
        visited = set()
        for h in history:
            c = h.get("c") or h.get("status_key")
            if c:
                visited.add(c)
        visited.add("initial")

        if status_key not in visited and status_key != o.status_key:
            raise BusinessError(f"不允许回滚到「{get_status_label(status_key)}」，该订单未曾经过此状态")

    old_label = o.status_label
    new_label = get_status_label(status_key)
    new_color = get_status_color(status_key)

    # 记录回滚/异常历史
    history = o.history or []
    detail_parts = [f"{current_user.name}({current_user.role})：从「{old_label}」跳转至「{new_label}」"]
    if req.remark:
        detail_parts.append(f"原因: {req.remark}")
    history.append({
        "s": "⬅ 回滚" if not is_exception else "❗ 异常处理",
        "s2": new_label,
        "c": status_key,
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "detail": "；".join(detail_parts),
    })

    # 异常跳转时：清除相关采购单和安装单
    if is_exception:
        # 清除采购单
        from app.domain.purchase import PurchaseOrder as POModel
        pos = await session.execute(
            select(POModel).where(POModel.order_ids.contains(str(o.id)))
        )
        for po in pos.scalars().all():
            await session.delete(po)

        # 清除安装单
        from app.domain.installation import InstallationOrder as IOModel
        ins_orders = await session.execute(
            select(IOModel).where(IOModel.order_id == o.id)
        )
        for ins in ins_orders.scalars().all():
            await session.delete(ins)

    else:
        # 正常回滚：如果回滚到已确认之前，清除采购拆分相关数据
        status_order_map = {k: i for i, k in enumerate(STATUS_STEPS)}
        if status_key in status_order_map and o.status_key in status_order_map:
            if status_order_map.get(status_key, 0) < status_order_map.get("confirmed", 99) and status_order_map.get(o.status_key, 0) >= status_order_map.get("confirmed", 99):
                o.order_ids = ""

    o.status_key = status_key
    o.status_label = new_label
    o.status_color = new_color
    o.history = history

    await session.flush()
    return success(data={"id": order_id, "status_key": status_key}, message=f"状态已跳转至「{new_label}」")


# ─── 删除订单 ─────────────────────────────────────────────────


@router.delete("/{order_id}")
async def delete_order(session: SessionDep, current_user: CurrentUserDep, order_id: int):
    """删除订单"""
    result = await session.execute(select(Order).where(Order.id == order_id))
    o = result.scalar_one_or_none()
    if not o:
        raise NotFoundError("订单不存在")

    # 删除明细
    items = await session.execute(select(OrderItem).where(OrderItem.order_id == order_id))
    for item in items.scalars().all():
        await session.delete(item)

    await session.delete(o)
    await session.flush()
    return success(message="订单已删除")


# ─── 订单状态选项 ─────────────────────────────────────────────


@router.get("/meta/status-options")
async def get_status_options():
    """获取所有订单状态选项"""
    from app.services.status_engine import get_all_status_options
    return success(data=get_all_status_options())
