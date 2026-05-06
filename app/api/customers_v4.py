# app/api/customers_v4.py
# V4.0 客户管理扩展 API（跟进记录 + 沉睡客户提醒）
import json
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Body, Header, Path, Query
from sqlalchemy import and_, func, select, update

from app.core.response import success_response, error_response
from app.database import async_session
from app.models import Customer, FollowupRecord, Order

router = APIRouter(prefix="/api/v4/customers", tags=["V4.0 客户管理"])


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


# ─── 客户 CRUD ────────────────────────────────────────────────────────────────


@router.get("", response_model=dict)
async def list_customers_v4(
    keyword: str | None = Query(None, description="搜索：姓名/电话"),
    customer_type: str | None = Query(None, description="客户类型: retail/project/designer"),
    level: str | None = Query(None, description="客户等级: A/B/C"),
    tags: str | None = Query(None, description="标签（逗号分隔）"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """V4.0 客户列表（支持标签筛选）"""
    async with async_session() as session:
        conditions = [Customer.is_deleted == False]

        if keyword:
            kw = f"%{keyword}%"
            conditions.append(
                (Customer.name.ilike(kw)) | (Customer.phone.ilike(kw))
            )
        if customer_type:
            conditions.append(Customer.customer_type == customer_type)
        if level:
            conditions.append(Customer.level == level)
        if tags:
            # JSON 数组标签筛选：SQLite json_each
            for tag in tags.split(","):
                tag = tag.strip()
                if tag:
                    conditions.append(
                        Customer.tags.like(f'%"{tag}"%')
                    )

        where_clause = and_(*conditions)

        # 总数
        r = await session.execute(
            select(func.count(Customer.id)).where(where_clause)
        )
        total = r.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            select(Customer)
            .where(where_clause)
            .order_by(Customer.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(query)
        customers = result.scalars().all()

        return success_response(
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [
                    {
                        "id": c.id,
                        "name": c.name or "",
                        "phone": c.phone or "",
                        "customer_type": getattr(c, "customer_type", "retail") or "retail",
                        "level": getattr(c, "level", "C") or "C",
                        "address": c.address or "",
                        "community": c.community or "",
                        "source": c.source or "",
                        "salesperson": c.salesperson or "",
                        "tags": json.loads(getattr(c, "tags", "[]") or "[]"),
                        "total_orders": getattr(c, "total_orders", 0) or 0,
                        "total_amount": float(getattr(c, "total_amount", 0) or 0),
                        "debt": float(c.debt or 0),
                        "next_followup_date": str(getattr(c, "next_followup_date", "") or ""),
                        "measure_status": getattr(c, "measure_status", "pending") or "pending",
                        "created_at": str(c.created_at)[:19] if c.created_at else "",
                    }
                    for c in customers
                ],
            }
        )


@router.post("")
async def create_customer_v4(req: dict = Body(...)):
    """V4.0 新建客户"""
    async with async_session() as session:
        # 检查手机号重复
        if req.get("phone"):
            r = await session.execute(
                select(Customer).where(
                    and_(Customer.phone == req["phone"], Customer.is_deleted == False)
                )
            )
            if r.scalar_one_or_none():
                return error_response("该手机号已存在")

        tags = req.get("tags", [])
        if isinstance(tags, list):
            tags = json.dumps(tags, ensure_ascii=False)

        customer = Customer(
            name=req.get("name", ""),
            phone=req.get("phone", ""),
            type=req.get("type", "零售"),
            address=req.get("address", ""),
            community=req.get("community", ""),
            source=req.get("source", ""),
            salesperson=req.get("salesperson", ""),
            debt=req.get("debt", 0),
        )

        session.add(customer)
        await session.commit()
        await session.refresh(customer)

        return success_response(
            data={
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
            }
        )



# ─── 沉睡客户提醒 ────────────────────────────────────────────────────────────


@router.get("/sleeping", response_model=dict)
async def list_sleeping_customers(
    days: int = Query(30, ge=7, description="超过多少天未跟进视为沉睡"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    沉睡客户提醒：
    - 最近一次跟进时间距今超过 `days` 天
    - 或从未跟进但客户创建时间较久
    """
    async with async_session() as session:
        today = date.today()
        cutoff = today

        # 子查询：最新跟进时间
        subq = (
            select(
                FollowupRecord.customer_id,
                func.max(FollowupRecord.created_at).label("last_followup"),
            )
            .group_by(FollowupRecord.customer_id)
            .subquery()
        )

        # 有跟进记录但超过 cutoff 天数未跟进视为沉睡
        cutoff_date = (datetime.now() - timedelta(days=days)).date()
        
        r = await session.execute(
            select(func.count(Customer.id))
            .join(subq, Customer.id == subq.c.customer_id)
            .where(
                and_(
                    Customer.is_deleted == False,
                    subq.c.last_followup < cutoff_date,
                )
            )
        )
        total = r.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            select(Customer)
            .join(subq, Customer.id == subq.c.customer_id)
            .where(
                and_(
                    Customer.is_deleted == False,
                    subq.c.last_followup < cutoff_date,
                )
            )
            .order_by(subq.c.last_followup.asc())
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(query)
        customers = result.scalars().all()

        return success_response(
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "days_threshold": days,
                "items": [
                    {
                        "id": c.id,
                        "name": c.name or "",
                        "phone": c.phone or "",
                        "customer_type": getattr(c, "customer_type", "retail") or "retail",
                        "level": getattr(c, "level", "C") or "C",
                        "salesperson": c.salesperson or "",
                        "total_orders": getattr(c, "total_orders", 0) or 0,
                        "total_amount": float(getattr(c, "total_amount", 0) or 0),
                        "debt": float(c.debt or 0),
                        "next_followup_date": str(getattr(c, "next_followup_date", "") or ""),
                        "last_contact_at": getattr(c, "last_contact_at", "") or "",
                        "last_order_date": "",  # 可关联 orders 表补充
                    }
                    for c in customers
                ],
            }
        )
@router.get("/{customer_id}", response_model=dict)
async def get_customer_v4(customer_id: int = Path(...)):
    """V4.0 客户详情"""
    async with async_session() as session:
        r = await session.execute(
            select(Customer).where(
                and_(Customer.id == customer_id, Customer.is_deleted == False)
            )
        )
        c = r.scalar_one_or_none()
        if not c:
            return error_response("客户不存在")

        return success_response(
            data={
                "id": c.id,
                "name": c.name or "",
                "phone": c.phone or "",
                "customer_type": getattr(c, "customer_type", "retail") or "retail",
                "type": c.type or "",
                "level": getattr(c, "level", "C") or "C",
                "address": c.address or "",
                "community": c.community or "",
                "source": c.source or "",
                "salesperson": c.salesperson or "",
                "salesperson_id": getattr(c, "salesperson_id", None),
                "tags": json.loads(getattr(c, "tags", "[]") or "[]"),
                "total_orders": getattr(c, "total_orders", 0) or 0,
                "total_amount": float(getattr(c, "total_amount", 0) or 0),
                "debt": float(c.debt or 0),
                "next_followup_date": str(getattr(c, "next_followup_date", "") or ""),
                "followup_history": json.loads(getattr(c, "followup_history", "[]") or "[]"),
                "measure_status": getattr(c, "measure_status", "pending") or "pending",
                "credit_limit": float(getattr(c, "credit_limit", 0) or 0),
                "created_at": str(c.created_at)[:19] if c.created_at else "",
            }
        )


@router.put("/{customer_id}")
async def update_customer_v4(customer_id: int = Path(...), req: dict = Body(...)):
    """V4.0 更新客户"""
    async with async_session() as session:
        r = await session.execute(
            select(Customer).where(
                and_(Customer.id == customer_id, Customer.is_deleted == False)
            )
        )
        c = r.scalar_one_or_none()
        if not c:
            return error_response("客户不存在")

        for field in [
            "name", "phone", "customer_type", "type", "level",
            "address", "community", "source", "salesperson",
            "measure_status", "credit_limit",
        ]:
            if field in req:
                setattr(c, field, req[field])

        if "tags" in req:
            c.tags = json.dumps(req["tags"], ensure_ascii=False) if isinstance(req["tags"], list) else req["tags"]

        if "next_followup_date" in req:
            c.next_followup_date = _parse_date(req["next_followup_date"])

        if "followup_history" in req:
            c.followup_history = (
                json.dumps(req["followup_history"], ensure_ascii=False)
                if isinstance(req["followup_history"], list)
                else req["followup_history"]
            )

        if "debt" in req:
            c.debt = req["debt"]

        await session.commit()
        return success_response(data={"id": customer_id})


@router.delete("/{customer_id}", response_model=dict)
async def delete_customer_v4(customer_id: int = Path(...)):
    """
    V4.0 软删除客户（is_deleted=True，不物理删除）
    """
    async with async_session() as session:
        r = await session.execute(
            select(Customer).where(
                and_(Customer.id == customer_id, Customer.is_deleted == False)
            )
        )
        c = r.scalar_one_or_none()
        if not c:
            return error_response("客户不存在")

        c.is_deleted = True
        c.deleted_at = datetime.now()
        await session.commit()
        return success_response(data={"id": customer_id})


# ─── 跟进记录 ────────────────────────────────────────────────────────────────


@router.get("/{customer_id}/followup", response_model=dict)
async def list_followup_records(customer_id: int = Path(...)):
    """获取客户跟进记录"""
    async with async_session() as session:
        # 验证客户存在
        r = await session.execute(
            select(Customer).where(Customer.id == customer_id)
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


@router.post("/{customer_id}/followup")
async def add_followup_record(customer_id: int = Path(...), req: dict = Body(...)):
    """添加跟进记录"""
    async with async_session() as session:
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

        # 追加跟进历史（JSON 摘要）
        history = json.loads(getattr(c, "followup_history", "[]") or "[]")
        history.insert(
            0,
            {
                "type": req.get("type", "电话"),
                "content": req.get("content", "")[:50],
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            },
        )
        # 只保留最近 20 条
        c.followup_history = json.dumps(history[:20], ensure_ascii=False)

        # 更新 last_contact_at
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


