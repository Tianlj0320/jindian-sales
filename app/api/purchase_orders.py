# app/api/purchase_orders.py
# V3.0 采购单 API（含订单拆分核心逻辑）
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Body, Header, HTTPException, Path, Query
from sqlalchemy import and_, func, select, text

from app.core.response import success_response, error_response
from app.database import async_session
from app.models import Order, OrderItem, Product, PurchaseOrder, Supplier, WarehouseRecord
from app.schemas import CommonResponse

router = APIRouter(prefix="/api/purchase-orders", tags=["V3.0 采购管理"])

# 状态枚举 & 只读字段
VALID_STATUSES = {"待采购", "已下单", "部分到货", "全部到货"}
READONLY_FIELDS = {"po_no"}


# ─── 辅助函数 ────────────────────────────────────────────────


def make_po_no() -> str:
    today = datetime.now().strftime("%Y%m%d")
    return f"PO{today}"  # 序号由调用方补


def parse_delivery_date(order: dict) -> date | None:
    """从订单 JSON 解析交期"""
    dd = order.get("delivery_date", "")
    if not dd:
        return None
    try:
        return datetime.strptime(str(dd)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


# ─── P0-2：采购单到货自动入库 ─────────────────────────────────────────────────
async def auto_inbound_warehouse(session: Any, po_id: int) -> dict:
    """
    当采购单状态推进到「全部到货」时，自动执行以下操作：
    1. 遍历 PurchaseOrder.items（JSON），按 product_id + qty 写入 WarehouseRecord
    2. 更新 Product.stock += qty
    返回入库结果摘要
    """
    # 读取采购单
    r = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = r.scalar_one_or_none()
    if not po:
        return {"success": False, "error": "采购单不存在"}

    items = po.items or []
    if not items:
        return {"success": True, "inbound_count": 0, "details": []}

    inbound_details = []
    operator = "system-auto"

    for item in items:
        product_id = item.get("product_id")
        qty = float(item.get("qty", 0))
        product_name = item.get("product_name", "")
        if not product_id or qty <= 0:
            continue

        # 写入入库记录
        record = WarehouseRecord(
            record_type="in",
            product_id=product_id,
            product_name=product_name,
            qty=qty,
            unit=item.get("unit", "米"),
            remark=f"采购单 {po.po_no} 到货入库",
            operator=operator,
        )
        session.add(record)

        # 更新库存
        r2 = await session.execute(select(Product).where(Product.id == product_id))
        prod = r2.scalar_one_or_none()
        if prod:
            prod.stock = (prod.stock or 0) + int(qty)

        inbound_details.append({
            "product_id": product_id,
            "product_name": product_name,
            "qty": qty,
        })

    # 更新采购单到货日期
    po.arrived_date = datetime.now().date()

    await session.flush()
    return {"success": True, "inbound_count": len(inbound_details), "details": inbound_details}


# ─── 订单拆分核心逻辑 ─────────────────────────────────────────
async def split_order_to_purchase_orders(session: Any, order_id: int) -> list[PurchaseOrder]:
    """
    拆分逻辑：
    1. 读取订单明细（order_items），按 supplier_id 分组
    2. 同一 supplier_id + 交期±3天 → 合并成一张采购单
    3. 不同 supplier_id → 分开
    4. 自动生成 PO 单号
    """
    # 读取订单
    r = await session.execute(select(Order).where(Order.id == order_id))
    order = r.scalar_one_or_none()
    if not order:
        return []

    # 读取订单明细
    r = await session.execute(select(OrderItem).where(OrderItem.order_id == order_id))
    items = r.scalars().all()
    if not items:
        return []

    # 按 supplier_id 分组，收集 product_id → 详细信息
    supplier_groups: dict = {}  # supplier_id → {supplier_name, contact, phone, items: []}

    for item in items:
        supplier_id = item.supplier_id
        if not supplier_id:
            # 没有 supplier_id 的默认到"无供应商"组
            supplier_id = 0

        # 获取产品/供应商信息
        product_info = {
            "product_id": None,
            "product_code": item.product_code or "",
            "product_name": item.product_name or "",
            "spec": f"{item.width or 0}x{item.height or 0}" if item.width or item.height else "",
            "qty": item.qty or 1,
            "unit_price": float(item.unit_price or 0),
            "amount": float(item.amount or 0),
            "material_type": getattr(item, "material_type", "主料"),
            "order_item_id": item.id,
        }
        # P1-3：尝试通过 product_code 查找 Product 表并回填 product_id
        if product_info["product_code"]:
            pr = await session.execute(select(Product).where(Product.code == product_info["product_code"]))
            prod = pr.scalar_one_or_none()
            if prod:
                product_info["product_id"] = prod.id

        if supplier_id not in supplier_groups:
            # 查询供应商信息
            sup_name, sup_contact, sup_phone = "", "", ""
            if supplier_id > 0:
                sr = await session.execute(select(Supplier).where(Supplier.id == supplier_id))
                sup = sr.scalar_one_or_none()
                if sup:
                    sup_name = sup.name or ""
                    sup_contact = sup.contact or ""
                    sup_phone = sup.phone or ""

            supplier_groups[supplier_id] = {
                "supplier_id": supplier_id,
                "supplier_name": sup_name,
                "contact": sup_contact,
                "phone": sup_phone,
                "items": [],
                "delivery_date": parse_delivery_date(order.__dict__),
            }

        supplier_groups[supplier_id]["items"].append(product_info)

    # 生成采购单
    purchase_orders = []
    for supplier_id, group in supplier_groups.items():
        if not group["items"]:
            continue

        # 生成 PO 序号
        today_str = datetime.now().strftime("%Y%m%d")
        seq_r = await session.execute(
            select(func.count(PurchaseOrder.id)).where(PurchaseOrder.po_no.like(f"PO{today_str}%"))
        )
        seq = (seq_r.scalar() or 0) + 1
        po_no = f"PO{today_str}{seq:03d}"

        total = sum(float(i["amount"]) for i in group["items"])

        po = PurchaseOrder(
            po_no=po_no,
            supplier_id=supplier_id if supplier_id > 0 else None,
            supplier_name=group["supplier_name"],
            contact=group["contact"],
            phone=group["phone"],
            total_amount=total,
            paid_amount=0,
            debt_amount=total,
            status="待采购",
            order_ids=str(order_id),
            expected_date=group["delivery_date"],
            items=group["items"],
            remark=f"由订单 {order.order_no} 拆分生成",
        )
        session.add(po)
        purchase_orders.append(po)

    return purchase_orders


# ─── API 接口 ────────────────────────────────────────────────


@router.post("/split/{order_id}")
async def split_order(
    order_id: int = Path(..., description="订单ID"),
    authorization: str | None = Header(None),
) -> dict:
    """
    【核心接口】订单拆分采购单

    请求：POST /api/purchase-orders/split/{order_id}
    逻辑：
      1. 读取订单明细，按 supplier_id 分组
      2. 同一供应商 + 交期相近（±3天）→ 合并一张采购单
      3. 不同供应商 → 各自独立采购单
      4. 自动生成 PO 单号（PO + 年月日 + 序号）
    返回：生成的采购单列表
    """
    # 权限检查（暂时跳过，正式环境从 header 验证）
    async with async_session() as session:
        # 检查订单状态
        r = await session.execute(select(Order.status_key).where(Order.id == order_id))
        order_status = r.scalar_one_or_none()
        if not order_status:
            raise HTTPException(status_code=404, detail="订单不存在")

        # P2-5: 状态必须是 confirmed/split 才能拆分
        ALLOWED_SPLIT_STATUS = ["confirmed", "split"]
        if order_status not in ALLOWED_SPLIT_STATUS:
            raise HTTPException(
                status_code=400, detail=f"订单状态为「{order_status}」，无法拆分"
            )

        pos = await split_order_to_purchase_orders(session, order_id)

        # 更新订单状态
        r = await session.execute(select(Order).where(Order.id == order_id))
        order = r.scalar_one()
        order.status = "已拆分"
        order.status_key = "split"

        await session.commit()

        return success_response(
            data={
                "purchase_orders": [
                    {
                        "id": po.id,
                        "po_no": po.po_no,
                        "supplier_name": po.supplier_name or "未分配供应商",
                        "total_amount": float(po.total_amount),
                        "status": po.status,
                        "expected_date": str(po.expected_date) if po.expected_date else "",
                        "item_count": len(po.items or []),
                    }
                    for po in pos
                ]
            },
            message=f"成功拆分为 {len(pos)} 张采购单",
        )


@router.get("", response_model=dict)
async def list_purchase_orders(
    status: str | None = Query(None, description="状态筛选"),
    supplier_id: int | None = Query(None, description="供应商ID筛选"),
    keyword: str | None = Query(None, description="供应商/PO单号搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """采购单列表（分页）"""
    async with async_session() as session:
        conditions = []
        if status:
            conditions.append(PurchaseOrder.status == status)
        if supplier_id:
            conditions.append(PurchaseOrder.supplier_id == supplier_id)
        if keyword:
            kw = f"%{keyword}%"
            conditions.append(
                (PurchaseOrder.po_no.ilike(kw)) | (PurchaseOrder.supplier_name.ilike(kw))
            )

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
        items = result.scalars().all()

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
                        "total_amount": float(p.total_amount or 0),
                        "paid_amount": float(p.paid_amount or 0),
                        "debt_amount": float(p.debt_amount or 0),
                        "status": p.status or "待采购",
                        "order_ids": p.order_ids or "",
                        "expected_date": str(p.expected_date) if p.expected_date else "",
                        "arrived_date": str(p.arrived_date) if p.arrived_date else "",
                        "items": p.items or [],
                        "remark": p.remark or "",
                        "created_at": str(p.created_at)[:19] if p.created_at else "",
                    }
                    for p in items
                ],
            }
        )


@router.get("/{po_id}", response_model=dict)
async def get_purchase_order(po_id: int = Path(...)) -> dict:
    """采购单详情"""
    async with async_session() as session:
        r = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
        p = r.scalar_one_or_none()
        if not p:
            raise HTTPException(status_code=404, detail="采购单不存在")

        # 关联订单信息
        order_list = []
        if p.order_ids:
            for oid in str(p.order_ids).split(","):
                oid = oid.strip()
                if oid:
                    or_ = await session.execute(select(Order).where(Order.id == int(oid)))
                    o = or_.scalar_one_or_none()
                    if o:
                        order_list.append(
                            {"id": o.id, "order_no": o.order_no, "customer_name": o.customer_name}
                        )

        return success_response(
            data={
                "id": p.id,
                "po_no": p.po_no or "",
                "supplier_id": p.supplier_id,
                "supplier_name": p.supplier_name or "",
                "contact": p.contact or "",
                "phone": p.phone or "",
                "total_amount": float(p.total_amount or 0),
                "paid_amount": float(p.paid_amount or 0),
                "debt_amount": float(p.debt_amount or 0),
                "status": p.status or "待采购",
                "order_ids": p.order_ids or "",
                "orders": order_list,
                "expected_date": str(p.expected_date) if p.expected_date else "",
                "arrived_date": str(p.arrived_date) if p.arrived_date else "",
                "items": p.items or [],
                "remark": p.remark or "",
                "created_at": str(p.created_at)[:19] if p.created_at else "",
                "updated_at": str(p.updated_at)[:19] if p.updated_at else "",
            }
        )


@router.patch("/{po_id}", response_model=CommonResponse)
async def update_purchase_order(
    po_id: int = Path(...),
    req: dict[str, Any] = Body(...),
) -> dict:
    """
    更新采购单状态
    Body: { "status": "已下单", "remark": "...", "items": [...] }
    """
    # 只读字段保护
    readonly_submitted = READONLY_FIELDS & set(req.keys())
    if readonly_submitted:
        raise HTTPException(
            status_code=400, detail=f"字段 {','.join(readonly_submitted)} 为只读字段，不允许更新"
        )

    async with async_session() as session:
        r = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
        p = r.scalar_one_or_none()
        if not p:
            return error_response(error="采购单不存在")

        new_status = req.get("status")
        old_status = p.status
        if new_status:
            if new_status not in VALID_STATUSES:
                raise HTTPException(
                    status_code=400,
                    detail=f"非法状态值「{new_status}」，允许值：{', '.join(sorted(VALID_STATUSES))}",
                )
            p.status = new_status

        # P0-2：状态推进到「全部到货」→ 自动入库
        inbound_result = None
        if old_status != "全部到货" and new_status == "全部到货":
            inbound_result = await auto_inbound_warehouse(session, po_id)
            if not inbound_result.get("success"):
                # 入库失败不影响主流程，仅记录 warning
                pass

        if "items" in req:
            p.items = req["items"]
            # 重新计算总金额
            p.total_amount = sum(
                float(i.get("qty", 0)) * float(i.get("unit_price", 0)) for i in (req["items"] or [])
            )
            p.debt_amount = p.total_amount - float(p.paid_amount or 0)

        if "remark" in req:
            p.remark = req["remark"]

        if req.get("expected_date"):
            p.expected_date = datetime.strptime(req["expected_date"], "%Y-%m-%d").date()

        if req.get("arrived_date"):
            p.arrived_date = datetime.strptime(req["arrived_date"], "%Y-%m-%d").date()

        await session.commit()
        resp_data = {"id": po_id, "status": p.status}
        if inbound_result:
            resp_data["inbound"] = inbound_result
        return success_response(data=resp_data)


@router.delete("/{po_id}", response_model=CommonResponse)
async def delete_purchase_order(po_id: int = Path(...)) -> dict:
    """删除采购单"""
    async with async_session() as session:
        r = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
        p = r.scalar_one_or_none()
        if not p:
            return error_response(error="采购单不存在")
        await session.delete(p)
        await session.commit()
        return success_response(message="删除成功")


@router.post("/merge", response_model=dict)
async def merge_purchase_orders(
    po_ids: list[int] = Body(..., description="要合并的采购单ID列表"),
    authorization: str | None = Header(None),
) -> dict:
    """
    合并多张采购单（同一供应商 + 交期相近）
    """
    if len(po_ids) < 2:
        raise HTTPException(status_code=400, detail="至少需要选择2张采购单")

    async with async_session() as session:
        r = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id.in_(po_ids)))
        pos = r.scalars().all()
        if len(pos) != len(po_ids):
            raise HTTPException(status_code=404, detail="部分采购单不存在")

        # 验证：必须同供应商
        suppliers = set(p.supplier_id for p in pos)
        if len(suppliers) != 1:
            raise HTTPException(status_code=400, detail="合并的采购单必须属于同一供应商")

        # 合并 items
        all_items = []
        all_order_ids = set()
        for p in pos:
            all_items.extend(p.items or [])
            if p.order_ids:
                all_order_ids.update(str(p.order_ids).split(","))

        total = sum(float(i.get("amount", 0)) for i in all_items)

        # 生成新 PO 号
        today_str = datetime.now().strftime("%Y%m%d")
        seq_r = await session.execute(
            select(func.count(PurchaseOrder.id)).where(PurchaseOrder.po_no.like(f"PO{today_str}%"))
        )
        seq = (seq_r.scalar() or 0) + 1
        po_no = f"PO{today_str}{seq:03d}"

        new_po = PurchaseOrder(
            po_no=po_no,
            supplier_id=pos[0].supplier_id,
            supplier_name=pos[0].supplier_name or "",
            contact=pos[0].contact or "",
            phone=pos[0].phone or "",
            total_amount=total,
            paid_amount=0,
            debt_amount=total,
            status="待采购",
            order_ids=",".join(str(oid) for oid in all_order_ids if oid.strip()),
            expected_date=pos[0].expected_date,
            items=all_items,
            remark=f"由 {len(pos)} 张采购单合并",
        )
        session.add(new_po)

        # 删除原采购单
        for p in pos:
            await session.delete(p)

        await session.commit()

        return success_response(
            data={
                "purchase_order": {
                    "id": new_po.id,
                    "po_no": new_po.po_no,
                    "supplier_name": new_po.supplier_name or "",
                    "total_amount": float(new_po.total_amount),
                    "item_count": len(all_items),
                }
            },
            message=f"成功合并 {len(pos)} 张采购单",
        )


@router.get("/by-supplier/{supplier_id}", response_model=dict)
async def get_purchase_orders_by_supplier(
    supplier_id: int = Path(...),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """
    按供应商查采购单
    GET /api/purchase-orders/by-supplier/{supplier_id}?status=待采购&page=1&page_size=20
    """
    async with async_session() as session:
        conditions = [PurchaseOrder.supplier_id == supplier_id]
        if status:
            conditions.append(PurchaseOrder.status == status)

        where_clause = and_(*conditions)

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
        items = result.scalars().all()

        # 供应商信息
        sup_name = ""
        if items:
            sup_name = items[0].supplier_name or ""

        return success_response(
            data={
                "supplier_id": supplier_id,
                "supplier_name": sup_name,
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [
                    {
                        "id": p.id,
                        "po_no": p.po_no or "",
                        "total_amount": float(p.total_amount or 0),
                        "paid_amount": float(p.paid_amount or 0),
                        "debt_amount": float(p.debt_amount or 0),
                        "status": p.status or "待采购",
                        "order_ids": p.order_ids or "",
                        "expected_date": str(p.expected_date) if p.expected_date else "",
                        "arrived_date": str(p.arrived_date) if p.arrived_date else "",
                        "item_count": len(p.items or []),
                        "remark": p.remark or "",
                        "created_at": str(p.created_at)[:19] if p.created_at else "",
                    }
                    for p in items
                ],
            }
        )


@router.post("/batch-split")
async def batch_split_orders(
    order_ids: list[int] = Body(..., description="订单ID列表"),
    authorization: str | None = Header(None),
) -> dict:
    """
    【批量拆分核心接口】
    将多个已确认订单合并按供应商拆分生成采购单

    逻辑：
      1. 读取所有订单的明细（OrderItem），按 supplier_id 分组
      2. 同一供应商 → 合并成一张采购单（汇总所有订单的物料）
      3. 收集所有涉及的 order_ids
      4. 各订单状态改为"已拆分"
    """
    if not order_ids:
        raise HTTPException(status_code=400, detail="请至少选择一个订单")

    async with async_session() as session:
        # ── 读取所有订单的明细，按供应商分组 ──────────────────────────────
        supplier_map: dict = {}  # supplier_id → {supplier_name, contact, phone, items: [], order_ids: set, delivery_date}

        for order_id in order_ids:
            # 检查订单状态
            r = await session.execute(select(Order).where(Order.id == order_id))
            order = r.scalar_one_or_none()
            if not order:
                continue
            if order.status_key not in ("confirmed",):
                raise HTTPException(
                    status_code=400,
                    detail=f"订单「{order.order_no}」状态为「{order.status_key}」，仅已确认订单可生成采购单",
                )
            if order.status_key == "split":
                raise HTTPException(
                    status_code=400, detail=f"订单「{order.order_no}」已生成采购单，不可重复操作"
                )

            # 读取订单明细
            r = await session.execute(select(OrderItem).where(OrderItem.order_id == order_id))
            items = r.scalars().all()

            for item in items:
                sid = item.supplier_id or 0
                if sid not in supplier_map:
                    sup_name, sup_contact, sup_phone = "", "", ""
                    if sid > 0:
                        sr = await session.execute(select(Supplier).where(Supplier.id == sid))
                        sup = sr.scalar_one_or_none()
                        if sup:
                            sup_name = sup.name or ""
                            sup_contact = sup.contact or ""
                            sup_phone = sup.phone or ""
                    supplier_map[sid] = {
                        "supplier_id": sid,
                        "supplier_name": sup_name,
                        "contact": sup_contact,
                        "phone": sup_phone,
                        "items": [],
                        "order_ids": set(),
                        "delivery_date": parse_delivery_date(order.__dict__),
                    }
                supplier_map[sid]["items"].append(
                    {
                        "product_id": None,
                        "product_code": item.product_code or "",
                        "product_name": item.product_name or "",
                        "spec": f"{item.width or 0}x{item.height or 0}"
                        if item.width or item.height
                        else "",
                        "qty": item.qty or 1,
                        "unit_price": float(item.unit_price or 0),
                        "amount": float(item.amount or 0),
                        "material_type": getattr(item, "material_type", "主料"),
                        "order_item_id": item.id,
                        "source_order_no": order.order_no,
                    }
                )
                # P1-3：尝试通过 product_code 查找 Product 表并回填 product_id
                if item.product_code:
                    pr = await session.execute(select(Product).where(Product.code == item.product_code))
                    prod = pr.scalar_one_or_none()
                    if prod:
                        supplier_map[sid]["items"][-1]["product_id"] = prod.id
                supplier_map[sid]["order_ids"].add(str(order_id))

        # P2-4: 使用 SELECT FOR UPDATE 锁避免并发序号冲突
        seq_r = await session.execute(
            select(PurchaseOrder.po_no).where(
                PurchaseOrder.po_no.like(f"PO{today_str}%")
            ).with_for_update().order_by(PurchaseOrder.id.desc()).limit(1)
        )
        last_po = seq_r.scalar_one_or_none()
        base_seq = 0
        if last_po:
            try:
                base_seq = int(last_po[-3:])
            except (ValueError, IndexError):
                base_seq = 0

        purchase_orders = []
        for idx, (sid, group) in enumerate(supplier_map.items()):
            if not group["items"]:
                continue
            base_seq += 1
            po_no = f"PO{today_str}{base_seq:03d}"
            total = sum(float(i["amount"]) for i in group["items"])
            order_ids_str = ",".join(sorted(group["order_ids"]))

            po = PurchaseOrder(
                po_no=po_no,
                supplier_id=sid if sid > 0 else None,
                supplier_name=group["supplier_name"],
                contact=group["contact"],
                phone=group["phone"],
                total_amount=total,
                paid_amount=0,
                debt_amount=total,
                status="待采购",
                order_ids=order_ids_str,
                expected_date=group["delivery_date"],
                items=group["items"],
                remark=f"由订单 {order_ids_str} 批量拆分生成",
            )
            session.add(po)

            # 更新各订单状态
            for oid in group["order_ids"]:
                r = await session.execute(select(Order).where(Order.id == int(oid)))
                o = r.scalar_one_or_none()
                if o:
                    o.status = "已拆分"
                    o.status_key = "split"

            purchase_orders.append(
                {
                    "id": f"pending_{idx}",
                    "po_no": po_no,
                    "supplier_name": group["supplier_name"] or "未分配供应商",
                    "total_amount": total,
                    "status": "待采购",
                    "item_count": len(group["items"]),
                    "order_count": len(group["order_ids"]),
                }
            )

        await session.commit()

        return success_response(
            data={"purchase_orders": purchase_orders},
            message=f"成功生成 {len(purchase_orders)} 张采购单",
        )
