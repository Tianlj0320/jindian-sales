# app/api/production_feedback.py
# V3.0 生产反馈 API
from datetime import datetime

from fastapi import APIRouter, Body, HTTPException, Path, Query
from sqlalchemy import and_, func, select

from app.core.response import success_response, error_response
from app.database import async_session
from app.models import Order, ProductionFeedback

router = APIRouter(prefix="/api/production-feedback", tags=["V3.0 生产反馈"])


@router.post("", response_model=CommonResponse)
async def create_feedback(req: dict = Body(...)):
    """
    创建生产反馈单

    Body:
    {
        "order_id": 1,
        "purchase_order_id": 1,   # 可选
        "feedback_type": "quality",  # quality / defect / shortage
        "description": "面料有色差",
        "photos": ["url1", "url2"]
    }
    """
    # 校验常量
    VALID_FEEDBACK_TYPES = {"quality", "defect", "shortage"}
    FEEDBACK_TYPES = {"quality": "质量", "defect": "残次", "shortage": "米数不足"}
    FEEDBACK_NO_PREFIX = "FB"

    # 1. order_id 必填校验
    if not req.get("order_id"):
        raise HTTPException(status_code=400, detail="order_id 为必填字段")

    # 2. feedback_type 枚举校验
    feedback_type = req.get("feedback_type", "quality")
    if feedback_type not in VALID_FEEDBACK_TYPES:
        raise HTTPException(
            status_code=400, detail=f"feedback_type 非法，允许值: {list(VALID_FEEDBACK_TYPES)}"
        )

    # 3. 订单存在性校验
    async with async_session() as session:
        r = await session.execute(select(Order.id).where(Order.id == req["order_id"]))
        if r.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="订单不存在")

        # 生成反馈单号
        today_str = datetime.now().strftime("%Y%m%d")
        seq_r = await session.execute(
            select(func.count(ProductionFeedback.id)).where(
                ProductionFeedback.feedback_no.like(f"{FEEDBACK_NO_PREFIX}{today_str}%")
            )
        )
        seq = (seq_r.scalar() or 0) + 1
        feedback_no = f"{FEEDBACK_NO_PREFIX}{today_str}{seq:03d}"

        # 关联订单号
        order_no = ""
        if req.get("order_id"):
            r2 = await session.execute(select(Order.order_no).where(Order.id == req["order_id"]))
            order_no = r2.scalar() or ""

        fb = ProductionFeedback(
            feedback_no=feedback_no,
            order_id=req.get("order_id"),
            order_no=order_no,
            purchase_order_id=req.get("purchase_order_id"),
            feedback_type=feedback_type,
            description=req.get("description", ""),
            photos=req.get("photos", []),
            status="待处理",
        )
        session.add(fb)
        await session.commit()
        await session.refresh(fb)

        return success_response(
            data={
                "id": fb.id,
                "feedback_no": fb.feedback_no,
                "feedback_type_label": FEEDBACK_TYPES.get(fb.feedback_type, fb.feedback_type),
            }
        )


@router.get("", response_model=dict)
async def list_feedbacks(
    status: str | None = Query(None),
    feedback_type: str | None = Query(None, alias="feedback_type"),
    order_id: int | None = Query(None),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """生产反馈列表"""
    FEEDBACK_TYPES = {"quality": "质量", "defect": "残次", "shortage": "米数不足"}

    async with async_session() as session:
        conditions = []
        if status:
            conditions.append(ProductionFeedback.status == status)
        if feedback_type:
            conditions.append(ProductionFeedback.feedback_type == feedback_type)
        if order_id is not None:
            conditions.append(ProductionFeedback.order_id == order_id)
        if keyword:
            kw = f"%{keyword}%"
            conditions.append(
                (ProductionFeedback.feedback_no.ilike(kw))
                | (ProductionFeedback.order_no.ilike(kw))
                | (ProductionFeedback.description.ilike(kw))
            )

        where_clause = and_(*conditions) if conditions else True

        r = await session.execute(select(func.count(ProductionFeedback.id)).where(where_clause))
        total = r.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            select(ProductionFeedback)
            .where(where_clause)
            .order_by(ProductionFeedback.created_at.desc())
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
                        "id": fb.id,
                        "feedback_no": fb.feedback_no or "",
                        "order_id": fb.order_id,
                        "order_no": fb.order_no or "",
                        "purchase_order_id": fb.purchase_order_id,
                        "feedback_type": fb.feedback_type or "",
                        "feedback_type_label": FEEDBACK_TYPES.get(fb.feedback_type, fb.feedback_type),
                        "description": fb.description or "",
                        "photos": fb.photos or [],
                        "status": fb.status or "待处理",
                        "resolver": fb.resolver or "",
                        "resolution": fb.resolution or "",
                        "resolved_at": str(fb.resolved_at)[:19] if fb.resolved_at else "",
                        "created_at": str(fb.created_at)[:19] if fb.created_at else "",
                    }
                    for fb in items
                ],
            }
        )


@router.get("/{fb_id}", response_model=dict)
async def get_feedback(fb_id: int = Path(...)):
    """反馈详情"""
    async with async_session() as session:
        r = await session.execute(select(ProductionFeedback).where(ProductionFeedback.id == fb_id))
        fb = r.scalar_one_or_none()
        if not fb:
            raise HTTPException(status_code=404, detail="反馈不存在")

        FEEDBACK_TYPES = {"quality": "质量", "defect": "残次", "shortage": "米数不足"}

        return success_response(
            data={
                "id": fb.id,
                "feedback_no": fb.feedback_no or "",
                "order_id": fb.order_id,
                "order_no": fb.order_no or "",
                "purchase_order_id": fb.purchase_order_id,
                "feedback_type": fb.feedback_type or "",
                "feedback_type_label": FEEDBACK_TYPES.get(fb.feedback_type, fb.feedback_type),
                "description": fb.description or "",
                "photos": fb.photos or [],
                "status": fb.status or "待处理",
                "resolver": fb.resolver or "",
                "resolution": fb.resolution or "",
                "resolved_at": str(fb.resolved_at)[:19] if fb.resolved_at else "",
                "created_at": str(fb.created_at)[:19] if fb.created_at else "",
            }
        )


@router.patch("/{fb_id}", response_model=CommonResponse)
async def update_feedback(
    fb_id: int = Path(...),
    req: dict = Body(...),
):
    """更新反馈（处理结果）"""
    # 状态枚举和状态机常量
    VALID_STATUSES = {"待处理", "已处理", "已解决"}
    STATUS_ORDER = {"待处理": 0, "已处理": 1, "已解决": 2}

    async with async_session() as session:
        r = await session.execute(select(ProductionFeedback).where(ProductionFeedback.id == fb_id))
        fb = r.scalar_one_or_none()
        if not fb:
            return error_response(error="反馈不存在")

        # 状态值校验
        if "status" in req:
            new_status = req["status"]
            if new_status not in VALID_STATUSES:
                return error_response(error=f"状态值非法，允许值: {list(VALID_STATUSES)}")
            # 状态机规则：不允许回退（已解决 → 待处理/已处理）
            old_order = STATUS_ORDER.get(fb.status, 0)
            new_order = STATUS_ORDER.get(new_status, 0)
            if old_order > new_order and fb.status == "已解决":
                return error_response(error="状态不可回退，当前状态为已解决")
            fb.status = new_status

        if "resolution" in req:
            fb.resolution = req["resolution"]
        if "resolver" in req:
            fb.resolver = req["resolver"]
            if req.get("status") == "已解决":
                fb.resolved_at = datetime.now()

        await session.commit()
        return success_response(data={"id": fb_id})
