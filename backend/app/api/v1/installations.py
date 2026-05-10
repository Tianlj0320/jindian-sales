"""
安装管理 API
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import paginated, success
from app.domain.installation import (
    InstallationOrder,
    InstallTeam,
    InstallTeamMember,
    Installer,
)
from app.domain.order import Order
from app.schemas.installation import (
    InstallationOrderCreate,
    InstallTeamCreate,
    InstallTeamUpdate,
    InstallerCreate,
    InstallerUpdate,
)

router = APIRouter(prefix="/api/v1/installations", tags=["安装管理"])


# ══════════════════════════════════════════════════════════════
# 安装队
# ══════════════════════════════════════════════════════════════


@router.get("/teams")
async def list_teams(session: SessionDep, current_user: CurrentUserDep):
    """安装队列表"""
    result = await session.execute(
        select(InstallTeam).where(InstallTeam.is_active == True).order_by(InstallTeam.id)
    )
    teams = result.scalars().all()

    items = []
    for t in teams:
        count = (await session.execute(
            select(func.count()).select_from(InstallTeamMember).where(InstallTeamMember.team_id == t.id)
        )).scalar() or 0
        items.append({
            "id": t.id,
            "name": t.name,
            "leader_name": t.leader_name,
            "leader_phone": t.leader_phone,
            "is_active": t.is_active,
            "member_count": count,
        })

    return success(data=items)


@router.post("/teams")
async def create_team(session: SessionDep, current_user: CurrentUserDep, req: InstallTeamCreate):
    """创建安装队"""
    team = InstallTeam(**req.model_dump())
    session.add(team)
    await session.flush()
    return success(data={"id": team.id}, message="安装队创建成功")


@router.put("/teams/{team_id}")
async def update_team(
    session: SessionDep, current_user: CurrentUserDep, team_id: int, req: InstallTeamUpdate
):
    """更新安装队"""
    result = await session.execute(select(InstallTeam).where(InstallTeam.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise NotFoundError("安装队不存在")

    for field, value in req.model_dump(exclude_none=True).items():
        setattr(team, field, value)
    await session.flush()
    return success(data={"id": team_id}, message="安装队更新成功")


@router.delete("/teams/{team_id}")
async def delete_team(session: SessionDep, current_user: CurrentUserDep, team_id: int):
    """删除安装队（软删除）"""
    result = await session.execute(select(InstallTeam).where(InstallTeam.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise NotFoundError("安装队不存在")

    team.is_active = False
    await session.flush()
    return success(message="安装队已禁用")


# ══════════════════════════════════════════════════════════════
# 安装工
# ══════════════════════════════════════════════════════════════


@router.get("/installers")
async def list_installers(session: SessionDep, current_user: CurrentUserDep):
    """安装工列表"""
    result = await session.execute(
        select(Installer).where(Installer.is_active == True).order_by(Installer.id)
    )
    installers = result.scalars().all()
    return success(data=[
        {"id": i.id, "name": i.name, "phone": i.phone, "is_active": i.is_active}
        for i in installers
    ])


@router.post("/installers")
async def create_installer(session: SessionDep, current_user: CurrentUserDep, req: InstallerCreate):
    """创建安装工"""
    if req.password:
        from app.core.security import hash_password
        password_hash = hash_password(req.password)
    else:
        password_hash = None

    installer = Installer(
        name=req.name,
        phone=req.phone,
        password_hash=password_hash,
    )
    session.add(installer)
    await session.flush()
    return success(data={"id": installer.id}, message="安装工创建成功")


@router.put("/installers/{installer_id}")
async def update_installer(
    session: SessionDep, current_user: CurrentUserDep, installer_id: int, req: InstallerUpdate
):
    """更新安装工"""
    result = await session.execute(select(Installer).where(Installer.id == installer_id))
    inst = result.scalar_one_or_none()
    if not inst:
        raise NotFoundError("安装工不存在")

    for field, value in req.model_dump(exclude_none=True).items():
        setattr(inst, field, value)
    await session.flush()
    return success(data={"id": installer_id}, message="安装工更新成功")


@router.delete("/installers/{installer_id}")
async def delete_installer(session: SessionDep, current_user: CurrentUserDep, installer_id: int):
    """删除安装工（软删除）"""
    result = await session.execute(select(Installer).where(Installer.id == installer_id))
    inst = result.scalar_one_or_none()
    if not inst:
        raise NotFoundError("安装工不存在")

    inst.is_active = False
    await session.flush()
    return success(message="安装工已禁用")


# ══════════════════════════════════════════════════════════════
# 安装单
# ══════════════════════════════════════════════════════════════


@router.get("/orders")
async def list_installation_orders(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    status: str | None = Query(None),
    keyword: str | None = Query(None),
):
    """安装单列表"""
    conditions = []
    if status:
        conditions.append(InstallationOrder.status == status)
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(
            or_(InstallationOrder.customer_name.ilike(kw), InstallationOrder.ins_no.ilike(kw))
        )

    where = and_(*conditions) if conditions else True
    total = (await session.execute(
        select(func.count()).select_from(InstallationOrder).where(where)
    )).scalar() or 0

    result = await session.execute(
        select(InstallationOrder)
        .where(where)
        .order_by(InstallationOrder.created_at.desc())
        .offset(page.offset)
        .limit(page.page_size)
    )
    orders = result.scalars().all()

    items = []
    for o in orders:
        items.append({
            "id": o.id,
            "ins_no": o.ins_no,
            "order_id": o.order_id,
            "order_no": o.order_no,
            "customer_name": o.customer_name,
            "customer_phone": o.customer_phone,
            "address": o.address,
            "team_id": o.team_id,
            "installer_id": o.installer_id,
            "installer_name": o.installer_name,
            "scheduled_date": str(o.scheduled_date) if o.scheduled_date else None,
            "install_time_slot": o.install_time_slot,
            "status": o.status,
            "labor_cost": float(o.labor_cost),
            "material_cost": float(o.material_cost),
            "total_cost": float(o.total_cost),
            "quality_score": o.quality_score,
            "receivable_amount": float(o.receivable_amount),
            "received_amount": float(o.received_amount),
            "unpaid_amount": float(o.unpaid_amount),
            "remark": o.remark,
            "created_at": str(o.created_at)[:19] if o.created_at else "",
        })

    return paginated(items=items, total=total, page=page.page, page_size=page.page_size)


@router.get("/orders/{ins_id}")
async def get_installation_order(session: SessionDep, current_user: CurrentUserDep, ins_id: int):
    """安装单详情"""
    result = await session.execute(select(InstallationOrder).where(InstallationOrder.id == ins_id))
    ins = result.scalar_one_or_none()
    if not ins:
        raise NotFoundError("安装单不存在")

    return success(data={
        "id": ins.id,
        "ins_no": ins.ins_no,
        "order_id": ins.order_id,
        "order_no": ins.order_no,
        "customer_name": ins.customer_name,
        "customer_phone": ins.customer_phone,
        "address": ins.address,
        "product_details": ins.product_details or {},
        "measure_summary": ins.measure_summary,
        "install_requirements": ins.install_requirements,
        "team_id": ins.team_id,
        "installer_id": ins.installer_id,
        "installer_name": ins.installer_name,
        "scheduled_date": str(ins.scheduled_date) if ins.scheduled_date else None,
        "install_time_slot": ins.install_time_slot,
        "status": ins.status,
        "labor_cost": float(ins.labor_cost),
        "material_cost": float(ins.material_cost),
        "total_cost": float(ins.total_cost),
        "quality_score": ins.quality_score,
        "install_photos": ins.install_photos or [],
        "customer_signature": ins.customer_signature,
        "actual_start_time": str(ins.actual_start_time)[:19] if ins.actual_start_time else None,
        "actual_end_time": str(ins.actual_end_time)[:19] if ins.actual_end_time else None,
        "confirmed_at": str(ins.confirmed_at)[:19] if ins.confirmed_at else None,
        "receivable_amount": float(ins.receivable_amount),
        "received_amount": float(ins.received_amount),
        "unpaid_amount": float(ins.unpaid_amount),
        "remark": ins.remark,
        "created_at": str(ins.created_at)[:19] if ins.created_at else "",
    })


@router.post("/orders")
async def create_installation_order(
    session: SessionDep, current_user: CurrentUserDep, req: InstallationOrderCreate
):
    """创建安装单（手动）"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    seq = (await session.execute(
        select(func.count(InstallationOrder.id)).where(
            InstallationOrder.ins_no.like(f"INS{today}%")
        )
    )).scalar() or 0
    ins_no = f"INS{today}{seq + 1:03d}"

    # 获取订单信息
    order_result = await session.execute(select(Order).where(Order.id == req.order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise NotFoundError("订单不存在")

    from datetime import date
    scheduled = None
    if req.scheduled_date:
        try:
            scheduled = datetime.strptime(req.scheduled_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    ins = InstallationOrder(
        ins_no=ins_no,
        order_id=req.order_id,
        order_no=order.order_no or "",
        customer_name=order.customer_name or "",
        customer_phone=order.customer_phone or "",
        address=order.install_address or "",
        product_details={},
        install_requirements=order.install_requirements or "",
        status="待分配",
        team_id=req.team_id,
        installer_id=req.installer_id,
        scheduled_date=scheduled,
        install_time_slot=req.install_time_slot,
        labor_cost=req.labor_cost,
        material_cost=req.material_cost,
        total_cost=req.labor_cost + req.material_cost,
        receivable_amount=order.amount or 0,
        received_amount=order.received or 0,
        unpaid_amount=order.debt or 0,
        remark=req.remark,
    )
    session.add(ins)
    await session.flush()
    return success(data={"id": ins.id, "ins_no": ins_no}, message="安装单创建成功")


@router.put("/orders/{ins_id}/status")
async def update_installation_status(
    session: SessionDep, current_user: CurrentUserDep, ins_id: int, status: str = Query(...),
):
    """更新安装单状态"""
    result = await session.execute(select(InstallationOrder).where(InstallationOrder.id == ins_id))
    ins = result.scalar_one_or_none()
    if not ins:
        raise NotFoundError("安装单不存在")

    ins.status = status
    if status == "安装中":
        ins.actual_start_time = datetime.now(timezone.utc)
    elif status == "已完成":
        ins.actual_end_time = datetime.now(timezone.utc)

    await session.flush()
    return success(data={"id": ins_id, "status": status}, message="安装单状态已更新")
