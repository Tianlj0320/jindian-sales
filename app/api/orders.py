# app/api/orders.py
from fastapi import APIRouter, Query, Path, Body
from app.database import async_session
from app.models import Order, InstallTask, Customer, Employee, Product
from app.schemas import (
    OrderListResponse, OrderResponse,
    OrderListItem, OrderDetailData, CommonResponse
)
from sqlalchemy import select, func, and_
from datetime import datetime, date
from typing import Optional
import json

router = APIRouter(prefix="/api/orders", tags=["订单管理"])


# ─── 订单状态8态映射 ─────────────────────────────────────────────────────────
ORDER_STATUS_MAP = {
    "created":     {"label": "待确认",    "color": "#909399"},
    "confirmed":  {"label": "已核单",    "color": "#409eff"},
    "measured":   {"label": "已测量",    "color": "#67c23a"},
    "stocked":    {"label": "已备货",    "color": "#e6a23c"},
    "processing": {"label": "加工中",    "color": "#f56c6c"},
    "install":    {"label": "待安装",    "color": "#9c27b0"},
    "installed":  {"label": "已安装",    "color": "#1a3a5c"},
    "completed": {"label": "已完成",    "color": "#222222"},
    "cancelled": {"label": "已取消",    "color": "#d9d9d9"},
}

STATUS_STEPS = [
    "created", "confirmed", "measured", "stocked",
    "processing", "install", "installed", "completed"
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
            conditions.append(func.date(Order.created_at) >= date(year, 1, 1))
            conditions.append(func.date(Order.created_at) < date(year + 1, 1, 1))
        if month and year:
            from datetime import date
            m_start = date(year, month, 1)
            import calendar
            m_end = date(year, month, calendar.monthrange(year, month)[1])
            conditions.append(func.date(Order.created_at) >= m_start)
            conditions.append(func.date(Order.created_at) <= m_end)

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
        quote_amount = sum(
            float(i.get("price", 0)) * int(i.get("qty", 0))
            for i in items
        )
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

        # 交货日期缺省：接单日+14天
        order_date = req.get("order_date") or datetime.now().strftime("%Y-%m-%d")
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
            install_address=req.get("install_address", ""),
            install_date=req.get("install_date") or None,
            install_time_slot=req.get("install_time_slot", ""),
        )

        session.add(order)
        await session.commit()
        await session.refresh(order)

        # 如果有安装日期，创建安装任务
        if req.get("install_date") and req.get("install_date") != "":
            install_task = InstallTask(
                order_id=order.id,
                order_no=order_no,
                installer_id=req.get("installer_id"),
                install_date=datetime.strptime(req.get("install_date"), "%Y-%m-%d").date(),
                install_time_slot=req.get("install_time_slot", ""),
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

        return CommonResponse(success=True, data={
            "id": order_id,
            "status_key": new_status_key,
            "status_label": new_label,
            "status_color": new_color
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
            o.install_date = datetime.strptime(req["install_date"], "%Y-%m-%d").date() if req["install_date"] else None

        if "received" in req:
            o.received = float(req["received"])
            o.debt = max(0, float(o.amount or 0) - float(req["received"]))

        # 重新计算金额
        items = req.get("items")
        if items is not None:
            o.items = items
            quote = sum(float(i.get("price", 0)) * int(i.get("qty", 0)) for i in items)
            o.quote_amount = quote
            o.amount = max(0, quote - float(o.discount_amount or 0) - float(o.round_amount or 0))
            o.debt = max(0, float(o.amount or 0) - float(o.received or 0))

        await session.commit()
        return CommonResponse(success=True, data={"id": order_id})
