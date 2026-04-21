# app/api/installation_orders.py
# V3.0 安装单 API
from fastapi import APIRouter, Query, Body, Path, Header, HTTPException
from app.database import async_session
from app.models import InstallationOrder, Order, InstallerAccount
from app.schemas import CommonResponse
from sqlalchemy import select, func, and_
from datetime import datetime, date
from typing import Optional

router = APIRouter(prefix="/api/installation-orders", tags=["V3.0 安装单"])


@router.get("", response_model=dict)
async def list_installation_orders(
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    installer_id: Optional[int] = Query(None),
    scheduled_from: Optional[str] = Query(None, alias="scheduled_from"),
    scheduled_to: Optional[str] = Query(None, alias="scheduled_to"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """安装单列表（支持筛选）"""
    async with async_session() as session:
        conditions = []
        if status:
            conditions.append(InstallationOrder.status == status)
        if installer_id:
            conditions.append(InstallationOrder.installer_id == installer_id)
        if keyword:
            kw = f"%{keyword}%"
            conditions.append(
                (InstallationOrder.ins_no.ilike(kw))
                | (InstallationOrder.customer_name.ilike(kw))
                | (InstallationOrder.customer_phone.ilike(kw))
                | (InstallationOrder.order_no.ilike(kw))
            )
        if scheduled_from:
            try:
                d = datetime.strptime(scheduled_from, "%Y-%m-%d").date()
                conditions.append(InstallationOrder.scheduled_date >= d)
            except Exception:
                pass
        if scheduled_to:
            try:
                d = datetime.strptime(scheduled_to, "%Y-%m-%d").date()
                conditions.append(InstallationOrder.scheduled_date <= d)
            except Exception:
                pass

        where_clause = and_(*conditions) if conditions else True

        r = await session.execute(select(func.count(InstallationOrder.id)).where(where_clause))
        total = r.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            select(InstallationOrder)
            .where(where_clause)
            .order_by(InstallationOrder.scheduled_date.asc(), InstallationOrder.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(query)
        items = result.scalars().all()

        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": io.id,
                    "ins_no": io.ins_no or "",
                    "order_id": io.order_id,
                    "order_no": io.order_no or "",
                    "customer_name": io.customer_name or "",
                    "customer_phone": io.customer_phone or "",
                    "address": io.address or "",
                    "product_details": io.product_details or {},
                    "measure_summary": io.measure_summary or "",
                    "install_requirements": io.install_requirements or "",
                    "scheduled_date": str(io.scheduled_date) if io.scheduled_date else "",
                    "installer_id": io.installer_id,
                    "installer_name": io.installer_name or "",
                    "install_time_slot": io.install_time_slot or "",
                    "status": io.status or "待分配",
                    "install_photo": io.install_photo or [],
                    "receivable_amount": float(io.receivable_amount or 0),
                    "received_amount": float(io.received_amount or 0),
                    "unpaid_amount": float(io.unpaid_amount or 0),
                    "remark": io.remark or "",
                    "created_at": str(io.created_at)[:19] if io.created_at else "",
                }
                for io in items
            ],
        }


@router.get("/{ins_id}", response_model=dict)
async def get_installation_order(ins_id: int = Path(...)):
    """安装单详情"""
    async with async_session() as session:
        r = await session.execute(select(InstallationOrder).where(InstallationOrder.id == ins_id))
        io = r.scalar_one_or_none()
        if not io:
            raise HTTPException(status_code=404, detail="安装单不存在")

        return {
            "success": True,
            "data": {
                "id": io.id,
                "ins_no": io.ins_no or "",
                "order_id": io.order_id,
                "order_no": io.order_no or "",
                "customer_name": io.customer_name or "",
                "customer_phone": io.customer_phone or "",
                "address": io.address or "",
                "product_details": io.product_details or {},
                "measure_summary": io.measure_summary or "",
                "install_requirements": io.install_requirements or "",
                "scheduled_date": str(io.scheduled_date) if io.scheduled_date else "",
                "installer_id": io.installer_id,
                "installer_name": io.installer_name or "",
                "install_time_slot": io.install_time_slot or "",
                "status": io.status or "待分配",
                "install_photo": io.install_photo or [],
                "customer_signature": io.customer_signature or "",
                "confirmed_at": str(io.confirmed_at)[:19] if io.confirmed_at else "",
                "receivable_amount": float(io.receivable_amount or 0),
                "received_amount": float(io.received_amount or 0),
                "unpaid_amount": float(io.unpaid_amount or 0),
                "remark": io.remark or "",
                "created_at": str(io.created_at)[:19] if io.created_at else "",
            },
        }


@router.post("", response_model=CommonResponse)
async def create_installation_order(req: dict = Body(...)):
    """
    手动创建安装单（通常由生产完成后自动生成，也可手动创建）

    Body:
    {
        "order_id": 1,
        "scheduled_date": "2026-05-01",
        "installer_id": 1,
        "install_time_slot": "09:00-12:00",
        "install_requirements": "小心墙壁...",
        "remark": ""
    }
    """
    INS_NO_PREFIX = "INS"

    async with async_session() as session:
        # 生成安装单号
        today_str = datetime.now().strftime("%Y%m%d")
        seq_r = await session.execute(
            select(func.count(InstallationOrder.id)).where(
                InstallationOrder.ins_no.like(f"{INS_NO_PREFIX}{today_str}%")
            )
        )
        seq = (seq_r.scalar() or 0) + 1
        ins_no = f"{INS_NO_PREFIX}{today_str}{seq:03d}"

        # 读取关联订单信息
        order_id = req.get("order_id")
        order_no = ""
        customer_name = ""
        customer_phone = ""
        address = ""
        product_details = {}
        measure_summary = ""

        if order_id:
            r = await session.execute(select(Order).where(Order.id == order_id))
            order = r.scalar_one_or_none()
            if order:
                order_no = order.order_no or ""
                customer_name = order.customer_name or ""
                customer_phone = order.customer_phone or ""
                address = getattr(order, "install_address", "") or order.address or ""
                measure_summary = getattr(order, "measure_data", "") or ""

        # 安装工姓名
        installer_name = ""
        if req.get("installer_id"):
            r = await session.execute(
                select(InstallerAccount.name).where(InstallerAccount.id == req["installer_id"])
            )
            installer_name = r.scalar() or ""

        scheduled_date = None
        if req.get("scheduled_date"):
            scheduled_date = datetime.strptime(req["scheduled_date"], "%Y-%m-%d").date()

        io = InstallationOrder(
            ins_no=ins_no,
            order_id=order_id,
            order_no=order_no,
            customer_name=customer_name,
            customer_phone=customer_phone,
            address=address,
            product_details=product_details,
            measure_summary=measure_summary,
            install_requirements=req.get("install_requirements", ""),
            scheduled_date=scheduled_date,
            installer_id=req.get("installer_id"),
            installer_name=installer_name,
            install_time_slot=req.get("install_time_slot", ""),
            status="待分配",
            receivable_amount=req.get("receivable_amount", 0),
            remark=req.get("remark", ""),
        )
        session.add(io)
        await session.commit()
        await session.refresh(io)

        return CommonResponse(
            success=True,
            data={"id": io.id, "ins_no": io.ins_no, "status": io.status},
        )


@router.patch("/{ins_id}", response_model=CommonResponse)
async def update_installation_order(
    ins_id: int = Path(...),
    req: dict = Body(...),
):
    """
    更新安装单（分配安装工/确认安装/验收等）

    Body:
    {
        "status": "已分配",
        "installer_id": 1,
        "scheduled_date": "2026-05-01",
        "install_time_slot": "09:00-12:00",
        "install_photo": ["url1"],
        "customer_signature": "base64...",
        "received_amount": 500,
        "remark": ""
    }
    """
    async with async_session() as session:
        r = await session.execute(select(InstallationOrder).where(InstallationOrder.id == ins_id))
        io = r.scalar_one_or_none()
        if not io:
            return CommonResponse(success=False, error="安装单不存在")

        # 更新安装工姓名
        if "installer_id" in req and req["installer_id"]:
            r = await session.execute(
                select(InstallerAccount.name).where(InstallerAccount.id == req["installer_id"])
            )
            io.installer_name = r.scalar() or ""
            io.installer_id = req["installer_id"]

        if "status" in req:
            io.status = req["status"]
            if req["status"] == "已验收":
                io.confirmed_at = datetime.now()

        if "scheduled_date" in req and req["scheduled_date"]:
            io.scheduled_date = datetime.strptime(req["scheduled_date"], "%Y-%m-%d").date()

        if "install_time_slot" in req:
            io.install_time_slot = req["install_time_slot"]

        if "install_photo" in req:
            io.install_photo = req["install_photo"]

        if "customer_signature" in req:
            io.customer_signature = req["customer_signature"]

        if "install_requirements" in req:
            io.install_requirements = req["install_requirements"]

        if "received_amount" in req:
            io.received_amount = req["received_amount"]
            io.unpaid_amount = float(io.receivable_amount or 0) - float(req["received_amount"] or 0)

        if "remark" in req:
            io.remark = req["remark"]

        # 更新关联订单状态
        if req.get("status") == "已验收" and io.order_id:
            r = await session.execute(select(Order).where(Order.id == io.order_id))
            order = r.scalar_one_or_none()
            if order:
                order.status = "已验收"
                order.status_key = "installed"

        await session.commit()
        return CommonResponse(success=True, data={"id": ins_id, "status": io.status})


@router.post("/auto-generate/{order_id}", response_model=CommonResponse)
async def auto_generate_installation_order(
    order_id: int = Path(...),
    authorization: str = Header(None),
):
    """
    【自动生成安装单】
    触发条件：订单状态变为"已完成"/"生产完成"时自动调用
    根据订单信息自动创建安装单
    """
    INS_NO_PREFIX = "INS"

    async with async_session() as session:
        # 检查是否已有安装单
        r = await session.execute(
            select(InstallationOrder).where(InstallationOrder.order_id == order_id)
        )
        existing = r.scalar_one_or_none()
        if existing:
            return CommonResponse(success=False, error=f"订单已有安装单 {existing.ins_no}")

        # 读取订单
        r = await session.execute(select(Order).where(Order.id == order_id))
        order = r.scalar_one_or_none()
        if not order:
            return CommonResponse(success=False, error="订单不存在")

        # 生成安装单号
        today_str = datetime.now().strftime("%Y%m%d")
        seq_r = await session.execute(
            select(func.count(InstallationOrder.id)).where(
                InstallationOrder.ins_no.like(f"{INS_NO_PREFIX}{today_str}%")
            )
        )
        seq = (seq_r.scalar() or 0) + 1
        ins_no = f"{INS_NO_PREFIX}{today_str}{seq:03d}"

        # 解析测量数据
        measure_summary = ""
        try:
            md = order.measure_data
            if isinstance(md, str):
                md = md
            measure_summary = str(md) if md else ""
        except Exception:
            measure_summary = ""

        io = InstallationOrder(
            ins_no=ins_no,
            order_id=order.id,
            order_no=order.order_no or "",
            customer_name=order.customer_name or "",
            customer_phone=order.customer_phone or "",
            address=getattr(order, "install_address", "") or order.address or "",
            product_details=order.items or {},  # 订单明细作为安装产品
            measure_summary=measure_summary,
            install_requirements=getattr(order, "install_requires", "") or "",
            status="待分配",
        )
        session.add(io)

        # 更新订单状态
        order.status = "安装单已生成"
        order.status_key = "install_order_generated"

        await session.commit()
        await session.refresh(io)

        return CommonResponse(
            success=True,
            data={"id": io.id, "ins_no": io.ins_no, "status": io.status},
        )


@router.post("/{ins_id}/confirm", response_model=CommonResponse)
async def confirm_installation(
    ins_id: int = Path(...),
    req: dict = Body(...),
):
    """
    确认安装（安装情况 + 收款情况）

    Body:
    {
        "status": "已验收",
        "install_photo": ["url1"],
        "customer_signature": "base64...",
        "received_amount": 500,
        "confirm_result": "通过",
        "remark": ""
    }
    """
    async with async_session() as session:
        r = await session.execute(select(InstallationOrder).where(InstallationOrder.id == ins_id))
        io = r.scalar_one_or_none()
        if not io:
            return CommonResponse(success=False, error="安装单不存在")

        if "status" in req:
            io.status = req["status"]
            if req["status"] in ("已验收", "已安装"):
                io.confirmed_at = datetime.now()

        if "install_photo" in req:
            io.install_photo = req["install_photo"]

        if "customer_signature" in req:
            io.customer_signature = req["customer_signature"]

        if "received_amount" in req:
            io.received_amount = req["received_amount"]
            io.unpaid_amount = float(io.receivable_amount or 0) - float(req["received_amount"] or 0)

        if "remark" in req:
            io.remark = req["remark"]

        # 更新关联订单状态 → 已验收
        if req.get("status") == "已验收" and io.order_id:
            r = await session.execute(select(Order).where(Order.id == io.order_id))
            order = r.scalar_one_or_none()
            if order:
                order.status = "已验收"
                order.status_key = "accepted"
                order.status_color = "#059669"
                history = order.history or []
                history.append({
                    "s": order.status,
                    "s2": "已验收",
                    "c": "accepted",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                order.history = history

        await session.commit()
        return CommonResponse(
            success=True,
            data={
                "id": ins_id,
                "status": io.status,
                "received_amount": float(io.received_amount or 0),
                "unpaid_amount": float(io.unpaid_amount or 0),
                "confirmed_at": str(io.confirmed_at)[:19] if io.confirmed_at else "",
            },
        )
