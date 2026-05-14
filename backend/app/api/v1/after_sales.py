"""
售后管理 API
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep
from app.core.exceptions import NotFoundError
from app.core.response import paginated, success
from app.domain.after_sale import AfterSaleService
from app.domain.order import Order
from app.schemas.after_sale import AfterSaleCreate, AfterSaleUpdate

router = APIRouter(prefix="/api/v1/after-sales", tags=["售后管理"])


def _generate_service_no(today_str: str, seq: int) -> str:
    """生成售后单号：AS{YYYYMMDD}{3位序号}"""
    return f"AS{today_str}{seq:03d}"


@router.get("")
async def list_after_sales(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    status: str | None = Query(None),
    service_type: str | None = Query(None),
    keyword: str | None = Query(None),
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
):
    """售后列表（分页+筛选）"""
    conditions = []
    if status:
        conditions.append(AfterSaleService.status == status)
    if service_type:
        conditions.append(AfterSaleService.service_type == service_type)
    if start_date:
        conditions.append(func.date(AfterSaleService.created_at) >= start_date)
    if end_date:
        conditions.append(func.date(AfterSaleService.created_at) <= end_date)
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(
            or_(
                AfterSaleService.service_no.ilike(kw),
                AfterSaleService.order_no.ilike(kw),
                AfterSaleService.customer_name.ilike(kw),
                AfterSaleService.customer_phone.ilike(kw),
            )
        )

    where = and_(*conditions) if conditions else True
    total = (await session.execute(
        select(func.count()).select_from(AfterSaleService).where(where)
    )).scalar() or 0

    result = await session.execute(
        select(AfterSaleService)
        .where(where)
        .order_by(AfterSaleService.created_at.desc())
        .offset(page.offset)
        .limit(page.page_size)
    )
    items = result.scalars().all()

    return paginated(
        items=[
            {
                "id": s.id,
                "service_no": s.service_no,
                "order_id": s.order_id,
                "order_no": s.order_no,
                "customer_name": s.customer_name,
                "customer_phone": s.customer_phone,
                "service_type": s.service_type,
                "service_type_label": s.service_type_label,
                "description": s.description,
                "status": s.status,
                "handler_id": s.handler_id,
                "handler_name": s.handler_name,
                "resolution": s.resolution,
                "resolved_at": str(s.resolved_at)[:19] if s.resolved_at else None,
                "remark": s.remark,
                "created_at": str(s.created_at)[:19] if s.created_at else "",
                "updated_at": str(s.updated_at)[:19] if s.updated_at else "",
            }
            for s in items
        ],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.get("/stats")
async def get_after_sale_stats(session: SessionDep, current_user: CurrentUserDep):
    """售后统计（待处理/处理中/已完成数量 + 类型分布）"""
    pending = (await session.execute(
        select(func.count()).select_from(AfterSaleService).where(AfterSaleService.status == "待处理")
    )).scalar() or 0

    processing = (await session.execute(
        select(func.count()).select_from(AfterSaleService).where(AfterSaleService.status == "处理中")
    )).scalar() or 0

    completed = (await session.execute(
        select(func.count()).select_from(AfterSaleService).where(
            AfterSaleService.status.in_(["已处理", "已关闭"])
        )
    )).scalar() or 0

    total = (await session.execute(
        select(func.count()).select_from(AfterSaleService)
    )).scalar() or 0

    # 类型分布
    type_rows = (await session.execute(
        select(AfterSaleService.service_type, AfterSaleService.service_type_label, func.count().label("cnt"))
        .group_by(AfterSaleService.service_type, AfterSaleService.service_type_label)
    )).all()
    by_type = {}
    for t, label, cnt in type_rows:
        by_type[t] = {"label": label, "count": cnt}

    return success(data={
        "pending_count": pending,
        "processing_count": processing,
        "completed_count": completed,
        "total_count": total,
        "by_type": by_type,
    })


@router.get("/{after_sale_id}")
async def get_after_sale(session: SessionDep, current_user: CurrentUserDep, after_sale_id: int):
    """售后详情"""
    result = await session.execute(select(AfterSaleService).where(AfterSaleService.id == after_sale_id))
    s = result.scalar_one_or_none()
    if not s:
        raise NotFoundError("售后单不存在")

    return success(data={
        "id": s.id,
        "service_no": s.service_no,
        "order_id": s.order_id,
        "order_no": s.order_no,
        "customer_name": s.customer_name,
        "customer_phone": s.customer_phone,
        "service_type": s.service_type,
        "service_type_label": s.service_type_label,
        "description": s.description,
        "status": s.status,
        "handler_id": s.handler_id,
        "handler_name": s.handler_name,
        "resolution": s.resolution,
        "resolved_at": str(s.resolved_at)[:19] if s.resolved_at else None,
        "remark": s.remark,
        "created_at": str(s.created_at)[:19] if s.created_at else "",
        "updated_at": str(s.updated_at)[:19] if s.updated_at else "",
    })


@router.post("")
async def create_after_sale(session: SessionDep, current_user: CurrentUserDep, req: AfterSaleCreate):
    """创建售后单（手动或由订单异常处理自动触发）"""
    # 如关联订单，自动填充客户信息
    customer_name = req.customer_name
    customer_phone = req.customer_phone
    order_no = req.order_no

    if req.order_id:
        result = await session.execute(select(Order).where(Order.id == req.order_id))
        order = result.scalar_one_or_none()
        if order:
            customer_name = customer_name or order.customer_name
            customer_phone = customer_phone or order.customer_phone
            order_no = order_no or order.order_no

    # 生成售后单号
    now = datetime.now(timezone.utc).astimezone()
    today_str = now.strftime("%Y%m%d")
    seq_result = await session.execute(
        select(func.count(AfterSaleService.id)).where(
            AfterSaleService.service_no.like(f"AS{today_str}%")
        )
    )
    seq = (seq_result.scalar() or 0) + 1
    service_no = _generate_service_no(today_str, seq)

    after_sale = AfterSaleService(
        service_no=service_no,
        order_id=req.order_id,
        order_no=order_no,
        customer_name=customer_name,
        customer_phone=customer_phone,
        service_type=req.service_type,
        service_type_label=req.service_type_label or req.service_type,
        description=req.description,
        status="待处理",
        remark=req.remark,
    )
    session.add(after_sale)
    await session.flush()

    return success(data={"id": after_sale.id, "service_no": service_no}, message="售后单创建成功")


@router.put("/{after_sale_id}")
async def update_after_sale(
    session: SessionDep, current_user: CurrentUserDep, after_sale_id: int, req: AfterSaleUpdate
):
    """更新售后单（处理/关闭）"""
    result = await session.execute(select(AfterSaleService).where(AfterSaleService.id == after_sale_id))
    s = result.scalar_one_or_none()
    if not s:
        raise NotFoundError("售后单不存在")

    update_data = req.model_dump(exclude_none=True)

    # 如果状态变为已处理，记录处理时间和处理人
    if update_data.get("status") == "已处理" and s.status != "已处理":
        update_data["resolved_at"] = datetime.now(timezone.utc).astimezone()
        if not update_data.get("handler_name"):
            update_data["handler_name"] = current_user.name

    for field, value in update_data.items():
        setattr(s, field, value)
    await session.flush()

    return success(data={"id": after_sale_id}, message="售后单更新成功")


@router.delete("/{after_sale_id}")
async def delete_after_sale(session: SessionDep, current_user: CurrentUserDep, after_sale_id: int):
    """删除售后单"""
    result = await session.execute(select(AfterSaleService).where(AfterSaleService.id == after_sale_id))
    s = result.scalar_one_or_none()
    if not s:
        raise NotFoundError("售后单不存在")

    await session.delete(s)
    await session.flush()
    return success(message="售后单已删除")
