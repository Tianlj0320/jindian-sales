"""
生产反馈 API
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep
from app.core.exceptions import NotFoundError
from app.core.response import paginated, success
from app.domain.production import ProductionFeedback
from app.schemas.production import ProductionFeedbackCreate, ProductionFeedbackUpdate

router = APIRouter(prefix="/api/v1/production", tags=["生产反馈"])


@router.get("/feedbacks")
async def list_feedbacks(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    order_id: int | None = Query(None),
    feedback_type: str | None = Query(None),
    status: str | None = Query(None),
):
    """生产反馈列表"""
    conditions = []
    if order_id:
        conditions.append(ProductionFeedback.order_id == order_id)
    if feedback_type:
        conditions.append(ProductionFeedback.feedback_type == feedback_type)
    if status:
        conditions.append(ProductionFeedback.status == status)

    where = and_(*conditions) if conditions else True
    total = (await session.execute(
        select(func.count()).select_from(ProductionFeedback).where(where)
    )).scalar() or 0

    result = await session.execute(
        select(ProductionFeedback)
        .where(where)
        .order_by(ProductionFeedback.created_at.desc())
        .offset(page.offset)
        .limit(page.page_size)
    )
    items = result.scalars().all()

    return paginated(
        items=[
            {
                "id": f.id,
                "feedback_no": f.feedback_no,
                "order_id": f.order_id,
                "order_no": f.order_no,
                "purchase_order_id": f.purchase_order_id,
                "feedback_type": f.feedback_type,
                "description": f.description,
                "photos": f.photos or [],
                "status": f.status,
                "resolver": f.resolver,
                "resolution": f.resolution,
                "resolved_at": str(f.resolved_at)[:19] if f.resolved_at else None,
                "created_at": str(f.created_at)[:19] if f.created_at else None,
            }
            for f in items
        ],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.get("/feedbacks/{feedback_id}")
async def get_feedback(session: SessionDep, current_user: CurrentUserDep, feedback_id: int):
    """生产反馈详情"""
    result = await session.execute(select(ProductionFeedback).where(ProductionFeedback.id == feedback_id))
    f = result.scalar_one_or_none()
    if not f:
        raise NotFoundError("反馈记录不存在")

    return success(data={
        "id": f.id,
        "feedback_no": f.feedback_no,
        "order_id": f.order_id,
        "order_no": f.order_no,
        "purchase_order_id": f.purchase_order_id,
        "feedback_type": f.feedback_type,
        "description": f.description,
        "photos": f.photos or [],
        "status": f.status,
        "resolver": f.resolver,
        "resolution": f.resolution,
        "resolved_at": str(f.resolved_at)[:19] if f.resolved_at else None,
        "created_at": str(f.created_at)[:19] if f.created_at else None,
    })


@router.post("/feedbacks")
async def create_feedback(session: SessionDep, current_user: CurrentUserDep, req: ProductionFeedbackCreate):
    """创建生产反馈"""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y%m%d")

    # 生成反馈编号
    seq_r = await session.execute(
        select(func.count(ProductionFeedback.id)).where(
            ProductionFeedback.feedback_no.like(f"FB{today_str}%")
        )
    )
    seq = (seq_r.scalar() or 0) + 1
    feedback_no = f"FB{today_str}{seq:03d}"

    feedback = ProductionFeedback(
        feedback_no=feedback_no,
        order_id=req.order_id,
        order_no=req.order_no,
        feedback_type=req.feedback_type,
        description=req.description,
        photos=req.photos,
        status="待处理",
    )
    session.add(feedback)
    await session.flush()

    return success(data={"id": feedback.id, "feedback_no": feedback_no}, message="反馈已提交")


@router.put("/feedbacks/{feedback_id}")
async def update_feedback(
    session: SessionDep, current_user: CurrentUserDep, feedback_id: int, req: ProductionFeedbackUpdate
):
    """更新生产反馈"""
    result = await session.execute(select(ProductionFeedback).where(ProductionFeedback.id == feedback_id))
    f = result.scalar_one_or_none()
    if not f:
        raise NotFoundError("反馈记录不存在")

    update_data = req.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(f, key, value)

    # 如果状态变为已解决，记录解决时间
    if req.status == "已解决" and f.resolved_at is None:
        f.resolved_at = datetime.now(timezone.utc)

    await session.flush()
    return success(data={"id": feedback_id}, message="反馈已更新")


@router.get("/stats")
async def get_production_stats(session: SessionDep, current_user: CurrentUserDep):
    """生产统计（待处理数量等）"""
    total = (await session.execute(select(func.count(ProductionFeedback.id)))).scalar() or 0
    pending = (await session.execute(
        select(func.count(ProductionFeedback.id)).where(ProductionFeedback.status == "待处理")
    )).scalar() or 0
    processing = (await session.execute(
        select(func.count(ProductionFeedback.id)).where(ProductionFeedback.status == "处理中")
    )).scalar() or 0

    return success(data={
        "total": total,
        "pending": pending,
        "processing": processing,
        "resolved": total - pending - processing,
    })
