# app/api/orders.py
from fastapi import APIRouter, Query, Path, Body
from app.database import async_session
from app.models import Order, OrderItem, InstallTask, Customer, Employee, Product, PurchaseOrder, InstallationOrder
from app.api.purchase_orders import split_order_to_purchase_orders
from app.api.installation_orders import auto_generate_installation_order as _auto_gen_install
from app.schemas import (
    OrderListResponse, OrderResponse,
    OrderListItem, OrderDetailData, CommonResponse
)
from sqlalchemy import select, func, and_
from datetime import datetime, date
from typing import Optional
import json

router = APIRouter(prefix="/api/orders", tags=["订单管理"])


# ─── 订单状态12态映射（V3.0）────────────────────────────────────────────────
ORDER_STATUS_MAP = {
    "created":              {"label": "待确认",      "color": "#909399"},
    "confirmed":           {"label": "已确认",      "color": "#409eff"},
    "split":               {"label": "已拆分",      "color": "#7c3aed"},  # V3.0 采购拆分
    "purchasing":           {"label": "采购中",       "color": "#f59e0b"},  # V3.0
    "stocked":             {"label": "已到货",       "color": "#10b981"},
    "processing":          {"label": "生产中",       "color": "#f97316"},
    "production_exception":{"label": "生产异常",    "color": "#ef4444"},  # V3.0
    "completed":           {"label": "已完成",       "color": "#6366f1"},
    "install_order_generated": {"label": "安装单已生成","color": "#8b5cf6"},  # V3.0
    "shipped":             {"label": "已发货",       "color": "#06b6d4"},  # V3.0
    "installed":           {"label": "已安装",       "color": "#1a3a5c"},
    "accepted":            {"label": "已验收",       "color": "#059669"},
    "cancelled":           {"label": "已取消",       "color": "#d9d9d9"},
}

STATUS_STEPS = [
    "created", "confirmed", "split", "purchasing",
    "stocked", "processing", "production_exception", "completed",
    "install_order_generated", "shipped", "installed", "accepted"
]


def get_next_status(current_key: str) -> Optional[str]:
    """获取下一个状态"""
    try:
        idx = STATUS_STEPS.index(current_key)
        if idx < len(STATUS_STEPS) - 1:
            return STATUS_STEPS[idx + 1]
    except ValueError:
        pass
    return None


@router.get("", response_model=OrderListResponse)
async def list_orders(
    status_key: Optional[str] = Query(None, description="状态key筛选"),
    order_type: Optional[str] = Query(None, description="订单类型"),
    keyword: Optional[str] = Query(None, description="搜索：订单号/客户名"),
    year: Optional[int] = Query(None, description="年筛选"),
    month: Optional[int] = Query(None, description="月筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """订单列表（支持筛选+分页+年月）"""
    async with async_session() as session:
        query = select(Order)
        conditions = []

        if status_key:
            conditions.append(Order.status_key == status_key)
        if order_type:
            conditions.append(Order.order_type == order_type)
        if keyword:
            kw = f"%{keyword}%"
            conditions.append(
                (Order.order_no.ilike(kw)) |
                (Order.customer_name.ilike(kw))
            )
        if year:
            from datetime import date
            conditions.append(Order.order_date >= f"{year}-01-01")
            conditions.append(Order.order_date < f"{year+1}-01-01")
        if month and year:
            from datetime import date
            m_start = f"{year}-{month:02d}-01"
            import calendar
            m_end_day = calendar.monthrange(year, month)[1]
            m_end = f"{year}-{month:02d}-{m_end_day:02d}"
            conditions.append(Order.order_date >= m_start)
            conditions.append(Order.order_date <= m_end)

        if conditions:
            query = query.where(and_(*conditions))

        # 总数
        count_result = await session.execute(
            select(func.count()).select_from(Order).where(and_(*conditions)) if conditions else select(func.count()).select_from(Order)
        )
        total = count_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        query = query.order_by(Order.created_at.desc()).offset(offset).limit(page_size)
        result = await session.execute(query)
        orders = result.scalars().all()

        items = []
        for o in orders:
            status_info = ORDER_STATUS_MAP.get(o.status_key, {})
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
                "status_key": o.status_key or "created",
                "status_label": status_info.get("label", o.status or ""),
                "status_color": status_info.get("color", "#909399"),
                "order_date": o.order_date or "",
                "delivery_date": o.delivery_date or "",
                "salesperson": o.salesperson or "",
                "install_date": str(o.install_date) if o.install_date else "",
                "items": o.items or []
            })

        await session.commit()
        return OrderListResponse(
            success=True,
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int = Path(..., description="订单ID")):
    """订单详情"""
    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        o = result.scalar_one_or_none()
        if not o:
            return OrderResponse(success=False, error="订单不存在")

        status_info = ORDER_STATUS_MAP.get(o.status_key, {})
        return OrderResponse(success=True, data={
            "id": o.id,
            "order_no": o.order_no,
            "customer_id": o.customer_id,
            "customer_name": o.customer_name or "",
            "customer_phone": o.customer_phone or "",
            "order_type": o.order_type or "",
            "status_key": o.status_key or "created",
            "status_label": status_info.get("label", ""),
            "status_color": status_info.get("color", "#909399"),
            "amount": float(o.amount or 0),
            "quote_amount": float(o.quote_amount or 0),
            "discount_amount": float(o.discount_amount or 0),
            "round_amount": float(o.round_amount or 0),
            "received": float(o.received or 0),
            "debt": float(o.debt or 0),
            "order_date": o.order_date or "",
            "delivery_date": o.delivery_date or "",
            "delivery_method": o.delivery_method or "",
            "content": o.content or "",
            "salesperson": o.salesperson or "",
            
            "history": o.history or [],
            "items": o.items or [],
            "install_address": o.install_address or "",
            "install_date": str(o.install_date) if o.install_date else "",
            "install_time_slot": o.install_time_slot or "",
            "created_at": str(o.created_at) if o.created_at else ""
        })


@router.post("", response_model=CommonResponse)
async def create_order(req: dict = Body(...)):
    """新建订单"""
    async with async_session() as session:
        today = datetime.now().strftime("%Y%m%d")

        # 查当日最大流水号
        seq_result = await session.execute(
            select(func.count(Order.id))
            .where(Order.order_no.like(f"{today}%"))
        )
        seq = (seq_result.scalar() or 0) + 1
        order_no = f"{today}{seq:03d}"

        items = req.get("items", [])
        materials = req.get("materials", [])
        quote_amount = (sum(float(i.get("amount", 0)) for i in items)
                     + sum(float(m.get("amount", 0)) for m in materials))
        discount = float(req.get("discount_amount", 0))
        round_amt = float(req.get("round_amount", 0))
        amount = max(0, quote_amount - discount - round_amt)
        received = float(req.get("received", 0))

        # 查找客户信息
        customer_id = req.get("customer_id")
        customer_name = req.get("customer_name", "")
        customer_phone = req.get("customer_phone", "")
        if customer_id:
            cr = await session.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            c = cr.scalar_one_or_none()
            if c:
                customer_name = c.name
                customer_phone = c.phone

        # 交货日期缺省：接单日+14天（支持多种日期格式）
        order_date_raw = req.get("order_date") or datetime.now().strftime("%Y-%m-%d")
        # 统一转换为 YYYY-MM-DD
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d"):
            try:
                order_date = datetime.strptime(order_date_raw, fmt).strftime("%Y-%m-%d")
                break
            except ValueError:
                continue
        else:
            order_date = datetime.now().strftime("%Y-%m-%d")
        delivery_date = req.get("delivery_date")
        if not delivery_date:
            d = datetime.strptime(order_date, "%Y-%m-%d")
            d = d.replace(day=min(d.day + 14, 28))
            delivery_date = d.strftime("%Y-%m-%d")

        history = [{
            "s": "创建订单",
            "s2": "待确认",
            "c": "pending",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
        }]

        order = Order(
            order_no=order_no,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            order_type=req.get("order_type", "窗帘"),
            status="待确认",
            status_key="created",
            status_color="#909399",
            quote_amount=quote_amount,
            discount_amount=discount,
            round_amount=round_amt,
            amount=amount,
            received=received,
            debt=max(0, amount - received),
            order_date=order_date,
            delivery_date=delivery_date,
            delivery_method=req.get("delivery_method", "上门安装"),
            content=req.get("content", ""),
            salesperson=req.get("salesperson", ""),
            history=history,
            items=items,
        )

        # 处理 install_date（转换为 Python date 对象）
        install_date_val = None
        install_date_raw = req.get("install_date")
        if install_date_raw:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d"):
                try:
                    install_date_val = datetime.strptime(install_date_raw, fmt).date()
                    break
                except ValueError:
                    continue
        order.install_date = install_date_val

        session.add(order)
        await session.commit()
        await session.refresh(order)

        # ── V3.0：为每个明细创建 OrderItem 记录（含供应商信息）───────────────
        for item in items:
            product_id = item.get("product_id")
            supplier_id = None
            material_type = item.get("material_type", "主料")
            if product_id:
                pr = await session.execute(select(Product).where(Product.id == product_id))
                prod = pr.scalar_one_or_none()
                if prod:
                    supplier_id = prod.supplier_id
            oi = OrderItem(
                order_id=order.id,
                item_type=item.get("product_type", "窗帘"),
                room=item.get("room", ""),
                category=item.get("category", ""),
                product_name=item.get("product_name", ""),
                product_code=item.get("product_code", ""),
                width=item.get("width"),
                height=item.get("height"),
                fold_ratio=item.get("fold_ratio") or 2.0,
                unit=item.get("unit", "米"),
                unit_price=item.get("unit_price", item.get("price", 0)),
                qty=item.get("qty", 1),
                discount=item.get("discount", 1.0),
                amount=item.get("amount", 0),
                final_amount=item.get("final_amount", item.get("amount", 0)),
                open_type=item.get("open_type", ""),
                style_code=item.get("style_code", ""),
                process_desc=item.get("process_desc", ""),
                is_custom=item.get("is_custom", 1),
                note=item.get("note", ""),
                supplier_id=supplier_id,
                material_type=material_type,
            )
            session.add(oi)
        await session.commit()

        # 如果有安装日期，创建安装任务
        _install_date = None
        _id_raw = req.get("install_date")
        if _id_raw:
            for _fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d"):
                try:
                    _install_date = datetime.strptime(_id_raw, _fmt).date()
                    break
                except ValueError:
                    continue
        if _install_date:
            install_task = InstallTask(
                order_id=order.id,
                order_no=order_no,
                installer_id=req.get("installer_id"),
                install_date=_install_date,
                install_time_slot=req.get("install_time_slot") or "",
                address=req.get("install_address", ""),
                customer_name=customer_name,
                customer_phone=customer_phone,
                raw_customer_phone=customer_phone,
                order_content=req.get("content", ""),
                priority="normal",
                status="pending",
                navigate_url=f"https://uri.amap.com/search?keyword={req.get('install_address','')}" if req.get("install_address") else None
            )
            session.add(install_task)
            await session.commit()

        return CommonResponse(success=True, data={"id": order.id, "order_no": order_no})


@router.put("/{order_id}/status", response_model=CommonResponse)
async def update_order_status(
    order_id: int,
    new_status_key: str = Body(..., embed=True)
):
    """更新订单状态"""
    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        o = result.scalar_one_or_none()
        if not o:
            return CommonResponse(success=False, error="订单不存在")

        if new_status_key not in ORDER_STATUS_MAP:
            return CommonResponse(success=False, error=f"无效状态：{new_status_key}")

        old_key = o.status_key
        old_label = ORDER_STATUS_MAP.get(old_key, {}).get("label", o.status)
        new_label = ORDER_STATUS_MAP[new_status_key]["label"]
        new_color = ORDER_STATUS_MAP[new_status_key]["color"]

        o.status_key = new_status_key
        o.status = new_label
        o.status_color = new_color

        # 追加历史
        history = o.history or []
        history.append({
            "s": old_label,
            "s2": new_label,
            "c": new_status_key,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        o.history = history

        # 如果变成已完成，同时更新欠款=0
        if new_status_key == "completed":
            o.debt = 0

        await session.commit()

        # ─── V3.0 订单流程联动 ───────────────────────────────────────────
        auto_action_msg = None

        # 订单确认（confirmed）→ 仅记录状态，采购单由采购管理手动生成
        if new_status_key == "confirmed":
            auto_action_msg = "订单已确认，请在采购管理中生成采购单"

        # 订单生产完成（completed）→ 自动生成安装单
        if new_status_key == "completed":
            try:
                from sqlalchemy import select as sa_select
                r = await session.execute(sa_select(InstallationOrder).where(InstallationOrder.order_id == order_id))
                existing_ins = r.scalar_one_or_none()
                if not existing_ins:
                    # 生成安装单
                    INS_NO_PREFIX = "INS"
                    today_str = datetime.now().strftime("%Y%m%d")
                    seq_r = await session.execute(
                        select(func.count(InstallationOrder.id)).where(
                            InstallationOrder.ins_no.like(f"{INS_NO_PREFIX}{today_str}%")
                        )
                    )
                    seq = (seq_r.scalar() or 0) + 1
                    ins_no = f"{INS_NO_PREFIX}{today_str}{seq:03d}"
                    ins = InstallationOrder(
                        ins_no=ins_no,
                        order_id=o.id,
                        order_no=o.order_no or "",
                        customer_name=o.customer_name or "",
                        customer_phone=o.customer_phone or "",
                        address=o.install_address or "",
                        product_details=o.items or {},
                        measure_summary=str(getattr(o, "measure_data", "") or ""),
                        install_requirements=getattr(o, "install_requires", "") or "",
                        status="待分配",
                    )
                    session.add(ins)
                    await session.flush()
                    o.status_key = "install_order_generated"
                    o.status = "安装单已生成"
                    o.status_color = ORDER_STATUS_MAP["install_order_generated"]["color"]
                    history = o.history or []
                    history.append({"s": "已完成", "s2": "安装单已生成", "c": "install_order_generated", "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    o.history = history
                    await session.commit()
                    auto_action_msg = f"已自动生成安装单 {ins_no}"
            except Exception as e:
                auto_action_msg = f"生成安装单失败：{str(e)}"

        return CommonResponse(success=True, data={
            "id": order_id,
            "status_key": new_status_key,
            "status_label": new_label,
            "status_color": new_color,
            "auto_action": auto_action_msg,
        })


@router.put("/{order_id}", response_model=CommonResponse)
async def update_order(
    order_id: int,
    req: dict = Body(...)
):
    """编辑订单"""
    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        o = result.scalar_one_or_none()
        if not o:
            return CommonResponse(success=False, error="订单不存在")

        # 更新字段
        for field in ["customer_name", "customer_phone", "order_type",
                       "delivery_method", "content", "salesperson",
                       "install_address", "install_time_slot"]:
            if field in req:
                setattr(o, field, req[field])

        if "install_date" in req:
            install_date_raw = req.get("install_date")
            if install_date_raw:
                for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d"):
                    try:
                        o.install_date = datetime.strptime(install_date_raw, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    o.install_date = None
            else:
                o.install_date = None

        if "received" in req:
            o.received = float(req["received"])
            o.debt = max(0, float(o.amount or 0) - float(req["received"]))

        # 重新计算金额
        items = req.get("items")
        if items is not None:
            o.items = items
            quote = sum(float(i.get("unit_price", i.get("price", 0))) * int(i.get("qty", 0)) for i in items)
            o.quote_amount = quote
            o.amount = max(0, quote - float(o.discount_amount or 0) - float(o.round_amount or 0))
            o.debt = max(0, float(o.amount or 0) - float(o.received or 0))
            # ── 同步更新 OrderItem 记录 ─────────────────────────────────────
            # 删除旧的
            del_r = await session.execute(
                select(OrderItem).where(OrderItem.order_id == order_id)
            )
            old_items = del_r.scalars().all()
            for oi in old_items:
                await session.delete(oi)
            # 创建新的
            for item in items:
                product_id = item.get("product_id")
                supplier_id = None
                if product_id:
                    pr = await session.execute(select(Product).where(Product.id == product_id))
                    prod = pr.scalar_one_or_none()
                    if prod:
                        supplier_id = prod.supplier_id
                oi = OrderItem(
                    order_id=order_id,
                    item_type=item.get("product_type", "窗帘"),
                    room=item.get("room", ""),
                    category=item.get("category", ""),
                    product_name=item.get("product_name", ""),
                    product_code=item.get("product_code", ""),
                    width=item.get("width"),
                    height=item.get("height"),
                    fold_ratio=item.get("fold_ratio") or 2.0,
                    unit=item.get("unit", "米"),
                    unit_price=item.get("unit_price", item.get("price", 0)),
                    qty=item.get("qty", 1),
                    discount=item.get("discount", 1.0),
                    amount=item.get("amount", 0),
                    final_amount=item.get("final_amount", item.get("amount", 0)),
                    open_type=item.get("open_type", ""),
                    style_code=item.get("style_code", ""),
                    process_desc=item.get("process_desc", ""),
                    is_custom=item.get("is_custom", 1),
                    note=item.get("note", ""),
                    supplier_id=supplier_id,
                    material_type=item.get("material_type", "主料"),
                )
                session.add(oi)

        await session.commit()
        return CommonResponse(success=True, data={"id": order_id})


@router.delete("/{order_id}", response_model=CommonResponse)
async def delete_order(order_id: int = Path(...)):
    """删除订单"""
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        o = result.scalar_one_or_none()
        if not o:
            return CommonResponse(success=False, error="订单不存在")
        # 删除关联的 OrderItem 记录
        items_result = await session.execute(select(OrderItem).where(OrderItem.order_id == order_id))
        for item in items_result.scalars().all():
            await session.delete(item)
        await session.delete(o)
        await session.commit()
        return CommonResponse(success=True, data={"id": order_id})
