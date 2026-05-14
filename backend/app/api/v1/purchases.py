"""
采购管理 API
"""

from __future__ import annotations

import base64
import io
from datetime import date, datetime, timezone

import qrcode
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func, or_, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import paginated, success
from app.domain.order import Order, OrderItem
from app.domain.product import Product, Supplier as SupModel
from app.domain.purchase import PurchaseOrder, PurchaseOrderItem
from app.domain.processing_order import ProcessingOrder, ProcessingOrderItem
from app.domain.warehouse import Inventory, InventoryFlow, Warehouse
from app.services.status_engine import get_status_label, get_status_color
from app.schemas.purchase import (
    BatchReceiveRequest,
    PurchaseOrderCreate,
    PurchasePreviewRequest,
    PurchaseGenerateRequest,
    ReceiveCreate,
    ReceiveItem,
    ReceiveRollbackCreate,
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
    keyword: str | None = Query(None, description="搜索供应商/采购单号"),
    supplier_id: int | None = Query(None, description="供应商ID"),
    start_date: str | None = Query(None, description="下单日期起 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="下单日期止 YYYY-MM-DD"),
):
    """采购单列表（支持日期筛选、供应商筛选、层级下钻）"""
    conditions = []
    if status:
        conditions.append(PurchaseOrder.status == status)
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(or_(
            PurchaseOrder.supplier_name.ilike(kw),
            PurchaseOrder.po_no.ilike(kw),
        ))
    if supplier_id:
        conditions.append(PurchaseOrder.supplier_id == supplier_id)
    if start_date:
        conditions.append(PurchaseOrder.order_date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        conditions.append(PurchaseOrder.order_date <= datetime.strptime(end_date, "%Y-%m-%d").date())

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

    from app.domain.product import Supplier as SupModel

    # Collect unique suppliers for hierarchy + resolve code
    supplier_ids = set()
    for po in pos:
        if po.supplier_id:
            supplier_ids.add(po.supplier_id)

    # Bulk-resolve supplier codes
    supplier_code_map: dict = {}
    if supplier_ids:
        sup_result = await session.execute(
            select(SupModel).where(SupModel.id.in_(supplier_ids))
        )
        for sup in sup_result.scalars().all():
            supplier_code_map[sup.id] = sup.code or ""

    items = []
    for po in pos:
        items.append({
            "id": po.id,
            "po_no": po.po_no,
            "supplier_id": po.supplier_id,
            "supplier_name": po.supplier_name,
            "supplier_code": supplier_code_map.get(po.supplier_id) if po.supplier_id else "",
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
            "item_count": len(po.po_items or []),
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
            "code": sup.code or "",
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
        spec = f"{it.room} {it.width}x{it.height}" if it.room else ""
        pdesc = (it.process_desc or "").strip()
        if key in merged:
            merged[key]["qty"] += float(it.qty or 1)
            merged[key]["amount"] += float(it.amount or 0)
            if spec:
                merged[key]["specs"].append(spec)
            if pdesc and pdesc not in (merged[key].get("process_descs") or []):
                merged[key].setdefault("process_descs", []).append(pdesc)
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
                "process_descs": [pdesc] if pdesc else [],
                "material_type": it.material_type or "主料",
                "procurement_type": it.procurement_type or "物料",
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
    """为指定订单构建拆分计划（预览用），按供应商分组、按采购类型分 sections"""
    orders_result = await session.execute(
        select(Order).where(Order.id.in_(order_ids))
    )
    orders = orders_result.scalars().all()
    if not orders:
        return {"groups": [], "order_ids": [], "order_nos": [], "order_count": 0}

    from app.domain.product import Product as ProdModel

    order_nos = [o.order_no for o in orders]

    # 仅取 is_purchase=True 的项（同时检查产品和订单级配置）
    items_result = await session.execute(
        select(OrderItem).join(ProdModel, OrderItem.product_id == ProdModel.id, isouter=True).where(
            OrderItem.order_id.in_(order_ids),
            OrderItem.is_purchase == True,
            or_(
                ProdModel.is_purchase == True,
                ProdModel.is_purchase.is_(None),
                ProdModel.id.is_(None),
            ),
        )
    )
    all_items = items_result.scalars().all()

    # 按 supplier_id 分组
    supplier_groups: dict = {}
    for it in all_items:
        sid = it.supplier_id if it.supplier_id else "pending"
        supplier_groups.setdefault(sid, []).append(it)

    PROCUREMENT_TYPES = ["物料", "成品", "辅料"]

    groups = []
    for sid, group_items in supplier_groups.items():
        sinfo = await _resolve_supplier_info(session, sid)

        sections = {}
        section_total = 0
        section_count = 0

        for pt in PROCUREMENT_TYPES:
            pt_items = [it for it in group_items if it.procurement_type == pt]
            if pt_items:
                merged_items, total_amt = _merge_items(pt_items)
                sections[pt] = {
                    "items": merged_items,
                    "count": len(merged_items),
                    "total_amount": round(total_amt, 2),
                }
                section_total += total_amt
                section_count += len(merged_items)

        if not sections:
            continue

        groups.append({
            "supplier_id": sinfo["id"],
            "supplier_code": sinfo["code"],
            "supplier_name": sinfo["name"],
            "contact": sinfo["contact"],
            "phone": sinfo["phone"],
            "qq": sinfo["qq"],
            "wechat": sinfo["wechat"],
            "bank_account": sinfo["bank_account"],
            "bank_name": sinfo["bank_name"],
            "payee": sinfo["payee"],
            "sections": sections,
            "total_amount": round(section_total, 2),
            "item_count": section_count,
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
    start_date: str | None = Query(None, description="下单日期起 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="下单日期止 YYYY-MM-DD"),
):
    """获取待采购的订单（已确认未分单），支持日期筛选"""
    conditions = [Order.status_key == "confirmed"]
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(or_(Order.order_no.ilike(kw), Order.customer_name.ilike(kw)))
    if start_date:
        conditions.append(Order.order_date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        conditions.append(Order.order_date <= datetime.strptime(end_date, "%Y-%m-%d").date())

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
    start_date: str | None = Query(None, description="下单日期起 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="下单日期止 YYYY-MM-DD"),
    po_status: str | None = Query(None, description="采购单状态筛选"),
):
    """采购跟踪：查看已分单订单及其采购单状态，支持日期筛选"""
    conditions = [Order.status_key == "split"]
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(or_(Order.order_no.ilike(kw), Order.customer_name.ilike(kw)))
    if start_date:
        conditions.append(Order.order_date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        conditions.append(Order.order_date <= datetime.strptime(end_date, "%Y-%m-%d").date())

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
            # Filter by po_status if specified
            if po_status and po.status != po_status:
                continue
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

        if po_status and not po_list:
            continue

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
            "procurement_type": item.procurement_type,
            "process_desc": item.process_desc or "",
        })

    # Resolve order numbers from order_ids
    order_nos = []
    if po.order_ids:
        oids = [int(x.strip()) for x in po.order_ids.split(",") if x.strip().isdigit()]
        if oids:
            o_result = await session.execute(
                select(Order.order_no).where(Order.id.in_(oids))
            )
            order_nos = [r[0] for r in o_result.all()]

    # Resolve supplier code
    supplier_code = ""
    if po.supplier_id:
        sup = await session.get(SupModel, po.supplier_id)
        supplier_code = sup.code if sup else ""

    return success(data={
        "id": po.id,
        "po_no": po.po_no,
        "supplier_id": po.supplier_id,
        "supplier_name": po.supplier_name,
        "supplier_code": supplier_code,
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
        "order_nos": order_nos,
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
            procurement_type=item_data.procurement_type,
        )
        session.add(po_item)

    await session.flush()
    return success(data={"id": po.id, "po_no": po_no}, message="采购单创建成功")


# ─── 采购收货 ─────────────────────────────────────────────────


async def _execute_receive(
    session, current_user, po_id: int, req: ReceiveCreate
):
    """执行单个采购单的收货逻辑（内部函数，供单 PO 和批量收货共用）"""
    po_result = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = po_result.scalar_one_or_none()
    if not po:
        return [], None
    if po.status in ("全部到货", "已取消"):
        return [], {"error": f"状态为{po.status}，不允许收货"}

    inbound_details = []

    for item in req.items:
        product_id = item.product_id
        qty = float(item.qty or 0)
        if qty <= 0:
            continue

        po_item_result = await session.execute(
            select(PurchaseOrderItem).where(
                PurchaseOrderItem.purchase_order_id == po_id,
                PurchaseOrderItem.product_id == product_id,
            )
        )
        po_item = po_item_result.scalar_one_or_none()
        if po_item:
            current_arrived = float(po_item.arrived_qty or 0)
            max_qty = float(po_item.quantity or 0)
            if current_arrived + qty > max_qty:
                return [], {"error": f"产品「{item.product_name or product_id}」采购 {max_qty}，已到货 {current_arrived}，超出采购数量"}
            po_item.arrived_qty = current_arrived + qty

        prod_result = await session.execute(select(Product).where(Product.id == product_id))
        prod = prod_result.scalar_one_or_none()
        qty_before = float(prod.stock) if prod else 0
        qty_after = qty_before + qty
        if prod:
            prod.stock = qty_after

        inv_result = await session.execute(
            select(Inventory).where(
                Inventory.product_id == product_id,
                Inventory.warehouse_id == req.warehouse_id,
            )
        )
        inv = inv_result.scalar_one_or_none()
        if inv:
            inv.quantity = float(inv.quantity or 0) + qty
        else:
            session.add(Inventory(
                product_id=product_id,
                warehouse_id=req.warehouse_id,
                quantity=qty,
                safety_stock=0,
            ))

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

    await session.flush()

    # 检查是否所有明细已全部到货
    po_items_result = await session.execute(
        select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == po_id)
    )
    all_po_items = po_items_result.scalars().all()
    this_po_all_arrived = all(
        (item.arrived_qty or 0) >= (item.quantity or 0)
        for item in all_po_items
    )
    if this_po_all_arrived:
        order_ids_set = set(
            oid.strip() for oid in (po.order_ids or '').split(',')
            if oid.strip().isdigit()
        )
        target_pos = [po]
        if order_ids_set:
            sibling_result = await session.execute(
                select(PurchaseOrder).where(PurchaseOrder.order_ids != '')
            )
            all_siblings = sibling_result.scalars().all()
            same_order_pos = []
            for sibling in all_siblings:
                sib_ids = set(s.strip() for s in (sibling.order_ids or '').split(',') if s.strip().isdigit())
                if sibling.id == po_id:
                    continue
                if sib_ids & order_ids_set:
                    same_order_pos.append(sibling)
            all_arrived = True
            for sibling in same_order_pos:
                sib_items = await session.execute(
                    select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == sibling.id)
                )
                sib_list = sib_items.scalars().all()
                if not all((it.arrived_qty or 0) >= (it.quantity or 0) for it in sib_list):
                    all_arrived = False
                    break
            if all_arrived:
                target_pos = [po] + same_order_pos
        from datetime import date
        today = date.today()
        for target in target_pos:
            target.status = "全部到货"
            target.debt_amount = 0
            target.arrived_date = today

        for oid_str in order_ids_set:
            o_result = await session.execute(select(Order).where(Order.id == int(oid_str)))
            o = o_result.scalar_one_or_none()
            if not o:
                continue
            if o.status_key not in ("purchasing", "partial_in"):
                continue
            old_label = o.status_label
            new_key = "stocked"
            new_label = get_status_label(new_key)
            new_color = get_status_color(new_key)
            history = o.history or []
            history.append({
                "s": old_label,
                "s2": new_label,
                "c": new_key,
                "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                "detail": "采购单全部到货，自动推进到「已入库」",
            })
            o.status_key = new_key
            o.status_label = new_label
            o.status_color = new_color
            o.history = history

            # ── 自动生成加工单（物料明细） ──
            mat_result = await session.execute(
                select(OrderItem).where(
                    OrderItem.order_id == o.id,
                    OrderItem.procurement_type == "物料",
                )
            )
            material_items = list(mat_result.scalars().all())
            if material_items:
                now = datetime.now(timezone.utc)
                today_str = now.strftime("%Y%m%d")
                seq_result = await session.execute(
                    select(func.count(ProcessingOrder.id)).where(
                        ProcessingOrder.po_no.like(f"JG{today_str}%")
                    )
                )
                seq = (seq_result.scalar() or 0) + 1
                po_no = f"JG{today_str}{seq:03d}"
                processing_order = ProcessingOrder(
                    po_no=po_no, order_id=o.id, order_no=o.order_no or "",
                    customer_name=o.customer_name or "",
                    total_items=len(material_items), status="pending", printed=False,
                )
                session.add(processing_order)
                await session.flush()
                for oi in material_items:
                    session.add(ProcessingOrderItem(
                        processing_order_id=processing_order.id,
                        order_item_id=oi.id, product_name=oi.product_name or "",
                        product_code=oi.product_code or "",
                        width=float(oi.width or 0), height=float(oi.height or 0),
                        qty=float(oi.qty or 1), unit=oi.unit or "",
                        process_desc=oi.process_desc or "",
                    ))
                await session.flush()
                # 推进订单状态：stocked → processing
                old_lbl2 = o.status_label
                new_key2 = "processing"
                new_lbl2 = get_status_label(new_key2)
                new_clr2 = get_status_color(new_key2)
                o.status_key = new_key2
                o.status_label = new_lbl2
                o.status_color = new_clr2
                o.history.append({
                    "s": old_lbl2, "s2": new_lbl2, "c": new_key2,
                    "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                    "detail": f"系统自动生成加工单「{po_no}」，进入加工流程",
                })
    else:
        po.status = "部分到货"

    return inbound_details, None


@router.post("/batch-receive")
async def batch_receive_purchase(
    session: SessionDep, current_user: CurrentUserDep, req: BatchReceiveRequest
):
    """批量收货（一次操作多张采购单）"""
    results = []
    errors = []

    for po_id in req.po_ids:
        po = (await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))).scalar_one_or_none()
        if not po:
            errors.append({"po_id": po_id, "error": "采购单不存在"})
            continue
        if po.status in ("全部到货", "已取消"):
            errors.append({"po_id": po_id, "po_no": po.po_no, "error": f"状态为{po.status}，跳过"})
            continue

        items_result = await session.execute(
            select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == po_id)
        )
        po_items = items_result.scalars().all()

        receive_items = []
        for pi in po_items:
            max_receive = float(pi.quantity or 0) - float(pi.arrived_qty or 0)
            if max_receive > 0:
                receive_items.append(ReceiveItem(
                    product_id=pi.product_id,
                    qty=max_receive,
                    product_name=pi.product_name or "",
                ))

        if not receive_items:
            errors.append({"po_id": po_id, "po_no": po.po_no, "error": "无可收货的明细"})
            continue

        details, err = await _execute_receive(session, current_user, po_id, ReceiveCreate(
            items=receive_items,
            warehouse_id=req.warehouse_id,
        ))
        if err:
            errors.append({"po_id": po_id, "po_no": po.po_no, "error": err["error"]})
        else:
            results.append({"po_id": po_id, "po_no": po.po_no, "items": len(receive_items)})

    await session.flush()
    return success(
        data={"results": results, "errors": errors},
        message=f"成功收货 {len(results)} 单，{len(errors)} 单跳过",
    )


@router.post("/{po_id}/receive")
async def receive_purchase(
    session: SessionDep, current_user: CurrentUserDep, po_id: int, req: ReceiveCreate
):
    """采购收货（分批到货 + 自动更新库存）"""
    inbound_details, err = await _execute_receive(session, current_user, po_id, req)
    if err:
        raise BusinessError(err["error"])
    po = (await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))).scalar_one_or_none()

    await session.flush()
    return success(
        data={"id": po_id, "status": po.status if po else "", "details": inbound_details},
        message=f"已收货 {len(inbound_details)} 项，当前状态：{po.status if po else ''}",
    )


# ─── 收货回退 ─────────────────────────────────────────────────


@router.post("/{po_id}/receive-rollback")
async def rollback_receive(
    session: SessionDep, current_user: CurrentUserDep, po_id: int, req: ReceiveRollbackCreate
):
    """收货回退（反向扣减库存）"""
    result = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("采购单不存在")

    if po.status in ("待采购", "已取消"):
        raise BusinessError(f"采购单状态为{po.status}，没有可回退的收货记录")

    rollback_details = []

    for item in req.items:
        product_id = item.product_id
        qty = float(item.qty or 0)

        # 查询采购明细
        po_item_result = await session.execute(
            select(PurchaseOrderItem).where(
                PurchaseOrderItem.purchase_order_id == po_id,
                PurchaseOrderItem.product_id == product_id,
            )
        )
        po_item = po_item_result.scalar_one_or_none()
        if not po_item:
            continue

        # 如果没有指定回退数量，默认全部回退
        if qty <= 0:
            qty = float(po_item.arrived_qty or 0)
        else:
            qty = min(qty, float(po_item.arrived_qty or 0))

        if qty <= 0:
            continue

        # 扣减采购明细已到货
        po_item.arrived_qty = float(po_item.arrived_qty or 0) - qty

        # 扣减产品库存
        prod_result = await session.execute(select(Product).where(Product.id == product_id))
        prod = prod_result.scalar_one_or_none()
        if prod:
            prod.stock = max(0, float(prod.stock or 0) - qty)

        # 扣减仓库库存
        inv_result = await session.execute(
            select(Inventory).where(
                Inventory.product_id == product_id,
                Inventory.warehouse_id == req.warehouse_id,
            )
        )
        inv = inv_result.scalar_one_or_none()
        if inv:
            qty_before = float(inv.quantity or 0)
            inv.quantity = max(0, qty_before - qty)
        else:
            qty_before = 0

        # 记录库存流水（出库）
        flow = InventoryFlow(
            product_id=product_id,
            warehouse_id=req.warehouse_id,
            flow_type="OUT",
            qty_before=qty_before,
            qty_change=-qty,
            qty_after=max(0, qty_before - qty),
            ref_type="purchase_rollback",
            ref_id=po_id,
            operator_id=current_user.id,
            remark=f"收货回退 {po.po_no}",
        )
        session.add(flow)

        rollback_details.append({
            "product_id": product_id,
            "qty": qty,
        })

    # 确保回退更新已刷新到数据库，再重新计算状态
    await session.flush()

    # 重新计算采购单状态
    po_items_result = await session.execute(
        select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == po_id)
    )
    all_items = po_items_result.scalars().all()
    total_arrived = sum(float(it.arrived_qty or 0) for it in all_items)

    old_status = po.status
    if total_arrived <= 0:
        po.status = "待采购"
    else:
        # 检查是否所有明细都已全部到货
        all_full = all(
            (it.arrived_qty or 0) >= (it.quantity or 0)
            for it in all_items
        )
        po.status = "全部到货" if all_full else "部分到货"

    # ── 检查是否影响订单状态（如果所有关联PO都已回退到无库存状态）──
    order_ids_set = set(
        oid.strip() for oid in (po.order_ids or '').split(',')
        if oid.strip().isdigit()
    )
    if order_ids_set:
        for oid_str in order_ids_set:
            o_result = await session.execute(select(Order).where(Order.id == int(oid_str)))
            o = o_result.scalar_one_or_none()
            if not o:
                continue
            # 如果订单当前是 stocked 状态，检查所有关联PO是否全部已回退
            if o.status_key == "stocked":
                sibling_result = await session.execute(
                    select(PurchaseOrder).where(PurchaseOrder.order_ids != '')
                )
                all_pos = sibling_result.scalars().all()
                same_order_pos = [
                    sib for sib in all_pos
                    if oid_str in (sib.order_ids or '').split(',')
                ]
                # 检查是否所有这些 PO 都没有到货了
                all_zero = True
                for sibling in same_order_pos:
                    sib_items = await session.execute(
                        select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == sibling.id)
                    )
                    sib_list = sib_items.scalars().all()
                    if any(float(it.arrived_qty or 0) > 0 for it in sib_list):
                        all_zero = False
                        break
                if all_zero:
                    # 回退订单状态到 purchasing
                    old_label = o.status_label
                    new_key = "purchasing"
                    new_label = get_status_label(new_key)
                    new_color = get_status_color(new_key)
                    history = o.history or []
                    history.append({
                        "s": old_label,
                        "s2": new_label,
                        "c": new_key,
                        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                        "detail": f"采购单「{po.po_no}」收货已全部回退，自动回退到「采购中」",
                    })
                    o.status_key = new_key
                    o.status_label = new_label
                    o.status_color = new_color
                    o.history = history

    await session.flush()
    return success(
        data={"id": po_id, "status": po.status, "details": rollback_details},
        message=f"已回退 {len(rollback_details)} 项，状态变更为：{po.status}",
    )


# ─── QR码 ──────────────────────────────────────────────────


@router.get("/{po_id}/qrcode")
async def get_po_qrcode(session: SessionDep, current_user: CurrentUserDep, po_id: int):
    """获取采购单QR码图片"""
    result = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("采购单不存在")

    if po.qrcode_base64:
        img_bytes = base64.b64decode(po.qrcode_base64)
    else:
        qr = qrcode.make(po.po_no)
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        img_bytes = buf.getvalue()

    return StreamingResponse(
        io.BytesIO(img_bytes),
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="{po.po_no}.png"'},
    )


@router.get("/scan/{code}")
async def scan_purchase_order(
    session: SessionDep, current_user: CurrentUserDep, code: str
):
    """通过扫描的po_no查找采购单"""
    result = await session.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_no == code)
    )
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError(f"未找到采购单: {code}")

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
            "procurement_type": item.procurement_type,
            "process_desc": item.process_desc or "",
        })

    order_nos = []
    if po.order_ids:
        oids = [int(x.strip()) for x in po.order_ids.split(",") if x.strip().isdigit()]
        if oids:
            from app.domain.order import Order
            o_result = await session.execute(
                select(Order.order_no).where(Order.id.in_(oids))
            )
            order_nos = [r[0] for r in o_result.all()]

    return success(data={
        "id": po.id,
        "po_no": po.po_no,
        "supplier_name": po.supplier_name,
        "supplier_id": po.supplier_id,
        "status": po.status,
        "total_amount": float(po.total_amount),
        "paid_amount": float(po.paid_amount),
        "debt_amount": float(po.debt_amount),
        "order_ids": po.order_ids,
        "order_nos": order_nos,
        "order_date": str(po.order_date) if po.order_date else None,
        "expected_date": str(po.expected_date) if po.expected_date else None,
        "arrived_date": str(po.arrived_date) if po.arrived_date else None,
        "remark": po.remark,
        "po_items": po_items,
    })


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


# ─── 发送采购单给供应商 ──────────────────────────────


@router.post("/{po_id}/share")
async def share_purchase_order(session: SessionDep, current_user: CurrentUserDep, po_id: int):
    """生成采购单分享内容（可用于复制发送给供应商）"""
    result = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise NotFoundError("采购单不存在")

    # Resolve order numbers
    order_nos = []
    if po.order_ids:
        oids = [int(x.strip()) for x in po.order_ids.split(",") if x.strip().isdigit()]
        if oids:
            o_result = await session.execute(
                select(Order.order_no).where(Order.id.in_(oids))
            )
            order_nos = [r[0] for r in o_result.all()]
    order_nos_str = "、".join(order_nos) if order_nos else ""

    def _format_item_line(item):
        """所有项统一: [编码] 名称  数量；成品另起附加行显示尺寸和工艺"""
        code = f"[{item.product_code}]" if item.product_code else ""
        name = item.product_name
        qty = f"{float(item.quantity)} {item.unit}"
        parts = [p for p in [code, name, qty] if p]
        main = "  ".join(parts)
        if item.procurement_type == "成品":
            spec = item.spec or ""
            pdesc = item.process_desc or ""
            extras = []
            if spec:
                extras.append(f"  尺寸：{spec}")
            if pdesc:
                extras.append(f"  工艺：{pdesc}")
            if extras:
                main += "\n" + "\n".join(extras)
        return main

    items_text = ""
    for i, item in enumerate(po.po_items or [], 1):
        line = _format_item_line(item)
        # indent sub-lines
        parts = line.split("\n")
        items_text += f"{i}. {parts[0]}\n"
        for sub in parts[1:]:
            items_text += f"   {sub}\n"

    text = (
        f"【采购单号】{po.po_no}\n"
        f"【供应商】{po.supplier_name}\n"
        f"【联系人】{po.contact}  {po.phone}\n"
        f"【下单日期】{po.order_date or ''}\n"
        f"【关联订单】{order_nos_str}\n"
        f"【明细】\n{items_text}"
    )

    # Also generate a simple HTML version for printing
    has_order_info = bool(order_nos_str)
    has_finished = any((item.procurement_type or "") == "成品" for item in (po.po_items or []))

    html_lines = [
        "<div style='font-family: sans-serif; max-width: 720px; margin: 0 auto; padding: 20px;'>",
        f"<h2 style='text-align:center;'>采购单</h2>",
        f"<table style='width:100%; border-collapse: collapse; margin-bottom: 16px;'>",
        f"<tr><td><strong>单号：</strong>{po.po_no}</td><td><strong>供应商：</strong>{po.supplier_name}</td></tr>",
        f"<tr><td><strong>联系人：</strong>{po.contact} {po.phone}</td><td><strong>下单日期：</strong>{po.order_date or '-'}</td></tr>",
    ]
    if has_order_info:
        html_lines.append(
            f"<tr><td colspan='2'><strong>关联订单：</strong>{order_nos_str}</td></tr>"
        )
    html_lines += [
        "</table>",
        "<table style='width:100%; border-collapse: collapse;' border='1' cellpadding='6'>",
    ]

    # Always use consistent column layout with 规格+工艺 when any 成品 exists
    if has_finished:
        html_lines.append(
            "<tr style='background:#f5f5f5;'><th>序号</th><th>编码</th><th>产品</th><th>规格</th><th>工艺</th><th>数量</th></tr>"
        )
    else:
        html_lines.append(
            "<tr style='background:#f5f5f5;'><th>序号</th><th>编码</th><th>产品</th><th>数量</th></tr>"
        )

    for i, item in enumerate(po.po_items or [], 1):
        code = item.product_code or ""
        name = item.product_name
        qty = f"{float(item.quantity)} {item.unit}"
        if has_finished:
            # Always emit 6 columns, non-成品 leave spec/工艺 empty
            spec = item.spec or "" if item.procurement_type == "成品" else ""
            pdesc = item.process_desc or "" if item.procurement_type == "成品" else ""
            html_lines.append(
                f"<tr><td>{i}</td><td>{code}</td><td>{name}</td>"
                f"<td>{spec}</td><td>{pdesc}</td>"
                f"<td style='text-align:right'>{qty}</td></tr>"
            )
        else:
            html_lines.append(
                f"<tr><td>{i}</td><td>{code}</td><td>{name}</td>"
                f"<td style='text-align:right'>{qty}</td></tr>"
            )
    html_lines.append("</table></div>")

    return success(data={
        "text": text,
        "html": "\n".join(html_lines),
        "po_no": po.po_no,
        "supplier_name": po.supplier_name,
        "total_amount": float(po.total_amount),
        "contact": po.contact,
        "phone": po.phone,
    })


# ─── 获取所有供应商列表（采购单中用） ──────────────────


@router.get("/suppliers/list")
async def list_purchase_suppliers(session: SessionDep, current_user: CurrentUserDep):
    """获取有采购记录的供应商列表（用于层级筛选）"""
    from app.domain.product import Supplier as SupModel

    result = await session.execute(
        select(PurchaseOrder.supplier_id, PurchaseOrder.supplier_name)
        .where(PurchaseOrder.supplier_id.isnot(None))
        .distinct()
        .order_by(PurchaseOrder.supplier_name)
    )
    suppliers = []
    for sid, name in result.all():
        code = ""
        if sid:
            sup = await session.get(SupModel, sid)
            code = sup.code if sup else ""
        suppliers.append({"id": sid, "name": name, "code": code})
    return success(data=suppliers)


# ─── 合并生成（支持选择合并模式） ───────────────────────


@router.post("/generate-merged")
async def generate_merged_purchase_orders(
    session: SessionDep, current_user: CurrentUserDep, req: PurchaseGenerateRequest
):
    """合并生成采购单 - 将所有选定订单的相同供应商合并为一张采购单"""
    if not req.order_ids:
        raise BusinessError("请选择至少一个订单")

    po_nos = await _execute_create_pos(session, req.order_ids, current_user)
    if not po_nos:
        raise BusinessError("选定订单中没有需要采购的商品")
    return success(
        data={"po_nos": po_nos},
        message=f"已生成 {len(po_nos)} 张采购单: {', '.join(po_nos)}",
    )


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
        pt_labels = list(group["sections"].keys())
        remark = f"【{'/'.join(pt_labels)}采购】源自订单 {', '.join(order_nos)}"

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
        # 生成QR码
        try:
            qr_img = qrcode.make(po.po_no)
            buf = io.BytesIO()
            qr_img.save(buf, format="PNG")
            po.qrcode_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception:
            pass  # QR码生成失败不影响主流程
        await session.flush()

        for pt, section in group["sections"].items():
            for m in section["items"]:
                pdescs = m.get("process_descs", [])
                pdesc_str = "；".join(filter(None, pdescs)) if pdescs else ""
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
                    procurement_type=pt,
                    process_desc=pdesc_str,
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
