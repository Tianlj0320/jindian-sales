# app/api/installations_v4.py
# V4.0 安装单管理 API（独立于V3，使用installation_orders表）
from datetime import datetime, date

from fastapi import APIRouter, Body, Header, Path, Query
from sqlalchemy import and_, func, select, update

from app.api.auth import verify_token
from app.core.response import success_response, error_response
from app.database import async_session
from app.models import InstallationOrder, InstallerAccount, Order

router = APIRouter(prefix="/api/v4/installations", tags=["V4.0 安装单管理"])



def _str_date(val) -> str:
    if not val:
        return ""
    if isinstance(val, (date, datetime)):
        return val.strftime("%Y-%m-%d")
    return str(val)[:10]


def _str_dt(val) -> str:
    if not val:
        return ""
    return val.strftime("%Y-%m-%d %H:%M:%S") if isinstance(val, datetime) else str(val)[:19]


# ─── 创建安装单 ────────────────────────────────────────────────────────────────
@router.post("")
async def create_installation(
    req: dict = Body(...),
):
    """POST /api/v4/installations - 创建安装单"""
    async with async_session() as session:
        # 生成 ins_no
        today_str = datetime.now().strftime("%Y%m%d")
        r = await session.execute(
            select(func.count(InstallationOrder.id)).where(
                InstallationOrder.ins_no.like(f"INS{today_str}%")
            )
        )
        seq = (r.scalar() or 0) + 1
        ins_no = f"INS{today_str}{seq:03d}"

        scheduled_date = None
        if req.get("scheduled_date"):
            try:
                scheduled_date = datetime.strptime(str(req["scheduled_date"])[:10], "%Y-%m-%d").date()
            except Exception:
                pass

        install_time_slot = req.get("install_time_slot", "")

        io = InstallationOrder(
            ins_no=ins_no,
            order_id=req.get("order_id"),
            scheduled_date=scheduled_date,
            install_time_slot=install_time_slot,
            installer_id=req.get("installer_id"),
            address=req.get("address", ""),
            customer_phone=req.get("customer_phone", ""),

            customer_name=req.get("customer_name", ""),
            status=req.get("status", "待派工"),
            remark=req.get("remark", ""),
        )
        session.add(io)
        await session.commit()
        await session.refresh(io)

        return success_response(data={"id": io.id, "ins_no": io.ins_no, "status": io.status})


# ─── 安装单列表 ────────────────────────────────────────────────────────────────
@router.get("", response_model=dict)
async def list_installations(
    status: str | None = Query(None),
    installer_id: int | None = Query(None, alias="installer_id"),
    date_from: str | None = Query(None, alias="date_from"),
    date_to: str | None = Query(None, alias="date_to"),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """GET /api/v4/installations - 安装单列表"""
    async with async_session() as session:
        conditions = []
        if status:
            conditions.append(InstallationOrder.status == status)
        if installer_id:
            conditions.append(InstallationOrder.installer_id == installer_id)
        if date_from:
            try:
                conditions.append(InstallationOrder.scheduled_date >= datetime.strptime(date_from, "%Y-%m-%d").date())
            except Exception:
                pass
        if date_to:
            try:
                conditions.append(InstallationOrder.scheduled_date <= datetime.strptime(date_to, "%Y-%m-%d").date())
            except Exception:
                pass
        if keyword:
            kw = f"%{keyword}%"
            conditions.append(
                (InstallationOrder.ins_no.ilike(kw))
                | (InstallationOrder.address.ilike(kw))
                | (InstallationOrder.customer_phone.ilike(kw))
            )

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

        return success_response(
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [
                    {
                        "id": io.id,
                        "ins_no": io.ins_no or "",
                        "order_id": io.order_id,
                        "scheduled_date": _str_date(io.scheduled_date),
                        "install_time_slot": io.install_time_slot or "",
                                                "installer_id": io.installer_id,
                        "address": io.address or "",
                        "customer_phone": io.customer_phone or "",
                        "status": io.status or "待派工",
                        "remark": io.remark or "",
                        "confirmed_at": _str_dt(io.confirmed_at),
                                                "customer_signature": io.customer_signature or "",
                        "created_at": _str_dt(io.created_at),
                    }
                    for io in items
                ],
            }
        )


# ─── 安装单详情 ────────────────────────────────────────────────────────────────

@router.get("/schedule", response_model=dict)
async def installation_schedule(
    date_from: str = Query(..., alias="date_from"),
    date_to: str = Query(..., alias="date_to"),
    installer_id: int | None = Query(None, alias="installer_id"),
):
    """GET /api/v4/installations/schedule - 排班视图（日历格式）"""
    async with async_session() as session:
        conditions = []
        try:
            conditions.append(InstallationOrder.scheduled_date >= datetime.strptime(date_from, "%Y-%m-%d").date())
            conditions.append(InstallationOrder.scheduled_date <= datetime.strptime(date_to, "%Y-%m-%d").date())
        except Exception:
            return error_response("日期格式错误，请使用 YYYY-MM-DD")

        if installer_id:
            conditions.append(InstallationOrder.installer_id == installer_id)

        where_clause = and_(*conditions)

        query = (
            select(InstallationOrder)
            .where(where_clause)
            .order_by(InstallationOrder.scheduled_date.asc(), InstallationOrder.install_time_slot.asc())
        )
        result = await session.execute(query)
        items = result.scalars().all()

        # 按日期分组
        schedule: dict[str, list] = {}
        for io in items:
            d = _str_date(io.scheduled_date)
            if d not in schedule:
                schedule[d] = []
            schedule[d].append({
                "id": io.id,
                "ins_no": io.ins_no or "",
                "order_id": io.order_id,
                "install_time_slot": io.install_time_slot or "",
                "installer_id": io.installer_id,
                                "address": io.address or "",
                "customer_phone": io.customer_phone or "",
                "status": io.status or "待派工",
                "remark": io.remark or "",
            })

        return success_response(data={"date_from": date_from, "date_to": date_to, "schedule": schedule})


# ─── 更新安装单信息 ────────────────────────────────────────────────────────────

@router.get("/{ins_id}", response_model=dict)
async def get_installation(
    ins_id: int = Path(...),
):
    """GET /api/v4/installations/{id} - 安装单详情"""
    async with async_session() as session:
        r = await session.execute(select(InstallationOrder).where(InstallationOrder.id == ins_id))
        io = r.scalar_one_or_none()
        if not io:
            return error_response("安装单不存在")

        return success_response(
            data={
                "id": io.id,
                "ins_no": io.ins_no or "",
                "order_id": io.order_id,
                "scheduled_date": _str_date(io.scheduled_date),
                "install_time_slot": io.install_time_slot or "",
                                "installer_id": io.installer_id,
                "address": io.address or "",
                "customer_phone": io.customer_phone or "",
                "status": io.status or "待派工",
                "remark": io.remark or "",
                "confirmed_at": _str_dt(io.confirmed_at),
                                "customer_signature": io.customer_signature or "",
                "created_at": _str_dt(io.created_at),
                "updated_at": _str_dt(io.updated_at),
            }
        )


# ─── 派工 ──────────────────────────────────────────────────────────────────────
@router.put("/{ins_id}/dispatch")
async def dispatch_installation(
    ins_id: int = Path(...),
    req: dict = Body(...),
):
    """PUT /api/v4/installations/{id}/dispatch - 派工（指定安装工/班组）"""
    async with async_session() as session:
        r = await session.execute(select(InstallationOrder).where(InstallationOrder.id == ins_id))
        io = r.scalar_one_or_none()
        if not io:
            return error_response("安装单不存在")

        if req.get("installer_id"):
            io.installer_id = req["installer_id"]

        io.status = "dispatched"  # 使用V4状态常量

        if req.get("scheduled_date"):
            try:
                io.scheduled_date = datetime.strptime(str(req["scheduled_date"])[:10], "%Y-%m-%d").date()
            except Exception:
                pass
        if req.get("install_time_slot"):
            io.install_time_slot = req["install_time_slot"]

        await session.commit()

        return success_response(data={"id": io.id, "status": io.status, "installer_id": io.installer_id})


# ─── 更新状态 ──────────────────────────────────────────────────────────────────
@router.put("/{ins_id}/status")
async def update_installation_status(
    ins_id: int = Path(...),
    req: dict = Body(...),
):
    """PUT /api/v4/installations/{id}/status - 更新状态（上门中/已完成/有问题）"""
    async with async_session() as session:
        r = await session.execute(select(InstallationOrder).where(InstallationOrder.id == ins_id))
        io = r.scalar_one_or_none()
        if not io:
            return error_response("安装单不存在")

        new_status = req.get("status")
        if not new_status:
            return error_response("status不能为空")

        io.status = new_status

        if new_status == "上门中" and not io.confirmed_at:
            io.confirmed_at = datetime.now()
        if new_status == "已完成":
            io.confirmed_at = datetime.now()
        if "note" in req:
            io.remark = req["note"]
        if "quality_score" in req:
            io.quality_score = req["quality_score"]
        if "signature_image" in req:
            io.signature_image = req["signature_image"]

        await session.commit()
        return success_response(data={"id": ins_id, "status": io.status})


# ─── 排班视图（日历格式）────────────────────────────────────────────────────────
@router.put("/{ins_id}")
async def update_installation(
    ins_id: int = Path(...),
    req: dict = Body(...),
):
    """PUT /api/v4/installations/{id} - 更新安装单信息"""
    async with async_session() as session:
        r = await session.execute(select(InstallationOrder).where(InstallationOrder.id == ins_id))
        io = r.scalar_one_or_none()
        if not io:
            return error_response("安装单不存在")

        for field in ("address", "contact_phone", "note", "install_time_slot"):
            if field in req:
                setattr(io, field, req[field])

        if "scheduled_date" in req:
            try:
                io.scheduled_date = datetime.strptime(str(req["scheduled_date"])[:10], "%Y-%m-%d").date()
            except Exception:
                pass

        await session.commit()
        return success_response(data={"id": ins_id})
