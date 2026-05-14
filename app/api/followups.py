# app/api/followups.py
# 客户跟进记录 API（V4.0 合入）
# 独立拆分自 customers_v4.py，专注跟进记录的 CRUD
from datetime import datetime, date

from fastapi import APIRouter, Body, Path, Query
from sqlalchemy import and_, func, select

from app.core.response import success_response, error_response
from app.database import async_session
from app.models import Customer, FollowupRecord

router = APIRouter(prefix="/api/followups", tags=["客户跟进"])


def _parse_date(val) -> date | None:
    if not val:
        return None
    if isinstance(val, date):
        return val
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(val), fmt).date()
        except ValueError:
            continue
    return None


# ─── 列表（支持分页+客户筛选）────────────────────────────────────────────────
@router.get("", response_model=dict)
async def list_followups(
    customer_id: int | None = Query(None, alias="customer_id", description="客户ID"),
    followup_type: str | None = Query(None, description="跟进类型：电话/微信/上门"),
    keyword: str | None = Query(None, description="搜索跟进内容关键字"),
    date_from: str | None = Query(None, alias="date_from"),
    date_to: str | None = Query(None, alias="date_to"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """跟进记录列表（全局查询 or 按客户查询）"""
    async with async_session() as session:
        conditions = []

        if customer_id:
            conditions.append(FollowupRecord.customer_id == customer_id)

        if followup_type:
            conditions.append(FollowupRecord.type == followup_type)

        if keyword:
            kw = f"%{keyword}%"
            conditions.append(FollowupRecord.content.ilike(kw))

        if date_from:
            try:
                conditions.append(FollowupRecord.created_at >= datetime.strptime(date_from, "%Y-%m-%d"))
            except ValueError:
                pass

        if date_to:
            try:
                conditions.append(FollowupRecord.created_at <= datetime.strptime(date_to + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
            except ValueError:
                pass

        where_clause = and_(*conditions) if conditions else True

        r = await session.execute(select(func.count(FollowupRecord.id)).where(where_clause))
        total = r.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            select(FollowupRecord)
            .where(where_clause)
            .order_by(FollowupRecord.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(query)
        records = result.scalars().all()

        # 批量查询客户名称（减少 N+1）
        customer_ids = list({r.customer_id for r in records if r.customer_id})
        customer_map = {}
        if customer_ids:
            cr = await session.execute(
                select(Customer.id, Customer.name).where(Customer.id.in_(customer_ids))
            )
            customer_map = {row[0]: row[1] for row in cr.fetchall()}

        return success_response(
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [
                    {
                        "id": fr.id,
                        "customer_id": fr.customer_id,
                        "customer_name": customer_map.get(fr.customer_id, ""),
                        "type": fr.type or "",
                        "content": fr.content or "",
                        "next_date": str(fr.next_date) if fr.next_date else "",
                        "operator_id": fr.operator_id,
                        "created_at": str(fr.created_at)[:19] if fr.created_at else "",
                    }
                    for fr in records
                ],
            }
        )


# ─── 客户跟进记录 ────────────────────────────────────────────────────────────
@router.get("/customer/{customer_id}", response_model=dict)
async def list_customer_followups(customer_id: int = Path(...)):
    """获取指定客户的跟进记录列表"""
    async with async_session() as session:
        # 验证客户存在
        r = await session.execute(
            select(Customer).where(
                and_(Customer.id == customer_id, Customer.is_deleted == False)
            )
        )
        if not r.scalar_one_or_none():
            return error_response("客户不存在")

        r = await session.execute(
            select(FollowupRecord)
            .where(FollowupRecord.customer_id == customer_id)
            .order_by(FollowupRecord.created_at.desc())
        )
        records = r.scalars().all()

        return success_response(
            data={
                "items": [
                    {
                        "id": fr.id,
                        "type": fr.type or "",
                        "content": fr.content or "",
                        "next_date": str(fr.next_date) if fr.next_date else "",
                        "operator_id": fr.operator_id,
                        "created_at": str(fr.created_at)[:19] if fr.created_at else "",
                    }
                    for fr in records
                ]
            }
        )


@router.post("", response_model=dict)
async def create_followup(req: dict = Body(...)):
    """
    新增跟进记录
    Body: { customer_id, type, content, next_date, operator_id }
    """
    async with async_session() as session:
        customer_id = req.get("customer_id")
        if not customer_id:
            return error_response("customer_id 不能为空")

        # 验证客户存在
        r = await session.execute(
            select(Customer).where(
                and_(Customer.id == customer_id, Customer.is_deleted == False)
            )
        )
        c = r.scalar_one_or_none()
        if not c:
            return error_response("客户不存在")

        fr = FollowupRecord(
            customer_id=customer_id,
            type=req.get("type", "电话"),
            content=req.get("content", ""),
            next_date=_parse_date(req.get("next_date")),
            operator_id=req.get("operator_id"),
        )
        session.add(fr)

        # 更新客户下次跟进时间
        if req.get("next_date"):
            c.next_followup_date = _parse_date(req["next_date"])

        # 追加跟进历史摘要（JSON 字段，仅保留最近20条）
        import json
        history = json.loads(getattr(c, "followup_history", "[]") or "[]")
        history.insert(
            0,
            {
                "type": req.get("type", "电话"),
                "content": str(req.get("content", ""))[:50],
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            },
        )
        c.followup_history = json.dumps(history[:20], ensure_ascii=False)

        # 更新最后联系时间
        c.last_contact_at = datetime.now().isoformat()

        await session.commit()
        await session.refresh(fr)

        return success_response(
            data={
                "id": fr.id,
                "customer_id": fr.customer_id,
                "type": fr.type,
                "content": fr.content,
                "next_date": str(fr.next_date) if fr.next_date else "",
                "created_at": str(fr.created_at)[:19] if fr.created_at else "",
            }
        )


@router.put("/{followup_id}", response_model=dict)
async def update_followup(followup_id: int = Path(...), req: dict = Body(...)):
    """编辑跟进记录"""
    async with async_session() as session:
        r = await session.execute(
            select(FollowupRecord).where(FollowupRecord.id == followup_id)
        )
        fr = r.scalar_one_or_none()
        if not fr:
            return error_response("跟进记录不存在")

        for field in ["type", "content", "next_date", "operator_id"]:
            if field in req:
                if field == "next_date":
                    setattr(fr, field, _parse_date(req[field]))
                else:
                    setattr(fr, field, req[field])

        await session.commit()
        return success_response(data={"id": followup_id})


@router.delete("/{followup_id}", response_model=dict)
async def delete_followup(followup_id: int = Path(...)):
    """删除跟进记录"""
    async with async_session() as session:
        r = await session.execute(
            select(FollowupRecord).where(FollowupRecord.id == followup_id)
        )
        fr = r.scalar_one_or_none()
        if not fr:
            return error_response("跟进记录不存在")

        await session.delete(fr)
        await session.commit()
        return success_response(message="删除成功")