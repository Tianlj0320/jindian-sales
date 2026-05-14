"""
客户管理 API
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep
from app.core.exceptions import NotFoundError
from app.core.response import success, paginated
from app.domain.customer import Customer, FollowupRecord
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse, FollowupCreate, FollowupUpdate

router = APIRouter(prefix="/api/v1/customers", tags=["客户管理"])


@router.get("/search")
async def search_customers(
    session: SessionDep,
    current_user: CurrentUserDep,
    keyword: str = Query("", description="搜索关键词"),
):
    """客户搜索（轻量级，用于下拉提示）"""
    conditions = [Customer.is_deleted == 0]
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(or_(Customer.name.ilike(kw), Customer.phone.ilike(kw)))

    where = and_(*conditions)
    result = await session.execute(
        select(Customer).where(where).order_by(Customer.updated_at.desc()).limit(15)
    )
    customers = result.scalars().all()
    return success(data=[
        {
            "id": c.id,
            "name": c.name,
            "phone": c.phone,
            "address": c.address,
            "community": c.community,
            "level": c.level,
        }
        for c in customers
    ])


@router.get("")
async def list_customers(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    keyword: str | None = Query(None, description="搜索关键词"),
    customer_type: str | None = Query(None, description="客户类型"),
):
    """客户列表（分页+搜索+筛选）"""
    conditions = [Customer.is_deleted == 0]

    if keyword:
        kw = f"%{keyword}%"
        conditions.append(or_(Customer.name.ilike(kw), Customer.phone.ilike(kw)))
    if customer_type:
        conditions.append(Customer.type == customer_type)

    where = and_(*conditions) if conditions else True

    # 总数
    count_q = select(func.count()).select_from(Customer).where(where)
    total = (await session.execute(count_q)).scalar() or 0

    # 分页
    query = (
        select(Customer)
        .where(where)
        .order_by(Customer.created_at.desc())
        .offset(page.offset)
        .limit(page.page_size)
    )
    result = await session.execute(query)
    customers = result.scalars().all()

    items = [
        {
            "id": c.id,
            "name": c.name,
            "phone": c.phone,
            "type": c.type,
            "source": c.source,
            "level": c.level,
            "address": c.address,
            "community": c.community,
            "salesperson_name": c.salesperson_name,
            "total_orders": c.total_orders,
            "total_amount": float(c.total_amount),
            "debt": float(c.debt),
            "next_followup_date": str(c.next_followup_date) if c.next_followup_date else None,
            "last_contact_at": c.last_contact_at,
            "tags": c.tags or [],
            "remark": c.remark,
            "created_at": str(c.created_at)[:19] if c.created_at else "",
        }
        for c in customers
    ]

    return paginated(items=items, total=total, page=page.page, page_size=page.page_size)


@router.get("/{customer_id}")
async def get_customer(session: SessionDep, current_user: CurrentUserDep, customer_id: int):
    """客户详情"""
    result = await session.execute(
        select(Customer).where(Customer.id == customer_id, Customer.is_deleted == 0)
    )
    c = result.scalar_one_or_none()
    if not c:
        raise NotFoundError("客户不存在")

    return success(data={
        "id": c.id,
        "name": c.name,
        "phone": c.phone,
        "type": c.type,
        "source": c.source,
        "level": c.level,
        "address": c.address,
        "community": c.community,
        "salesperson_name": c.salesperson_name,
        "total_orders": c.total_orders,
        "total_amount": float(c.total_amount),
        "debt": float(c.debt),
        "next_followup_date": str(c.next_followup_date) if c.next_followup_date else None,
        "last_contact_at": c.last_contact_at,
        "tags": c.tags or [],
        "remark": c.remark,
        "created_at": str(c.created_at)[:19] if c.created_at else "",
    })


@router.post("")
async def create_customer(session: SessionDep, current_user: CurrentUserDep, req: CustomerCreate):
    """创建客户"""
    customer = Customer(
        name=req.name,
        phone=req.phone,
        type=req.type,
        source=req.source,
        address=req.address,
        community=req.community,
        level=req.level,
        salesperson_id=current_user.id,
        salesperson_name=current_user.name,
        remark=req.remark,
    )
    session.add(customer)
    await session.flush()
    return success(data={"id": customer.id}, message="客户创建成功")


@router.put("/{customer_id}")
async def update_customer(
    session: SessionDep, current_user: CurrentUserDep, customer_id: int, req: CustomerUpdate
):
    """更新客户"""
    result = await session.execute(
        select(Customer).where(Customer.id == customer_id, Customer.is_deleted == 0)
    )
    c = result.scalar_one_or_none()
    if not c:
        raise NotFoundError("客户不存在")

    update_data = req.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(c, field, value)

    await session.flush()
    return success(data={"id": customer_id}, message="客户更新成功")


@router.delete("/{customer_id}")
async def delete_customer(session: SessionDep, current_user: CurrentUserDep, customer_id: int):
    """删除客户（软删除）"""
    result = await session.execute(
        select(Customer).where(Customer.id == customer_id, Customer.is_deleted == 0)
    )
    c = result.scalar_one_or_none()
    if not c:
        raise NotFoundError("客户不存在")

    c.is_deleted = 1
    await session.flush()
    return success(message="客户已删除")


# ── 客户跟进 ──────────────────────────────────────────────────


@router.get("/{customer_id}/followups")
async def list_followups(session: SessionDep, current_user: CurrentUserDep, customer_id: int):
    """跟进记录列表"""
    result = await session.execute(
        select(FollowupRecord)
        .where(FollowupRecord.customer_id == customer_id)
        .order_by(FollowupRecord.created_at.desc())
    )
    records = result.scalars().all()
    return success(data=[
        {
            "id": r.id,
            "type": r.type,
            "content": r.content,
            "result": r.result,
            "next_date": str(r.next_date) if r.next_date else None,
            "operator_id": r.operator_id,
            "created_at": str(r.created_at)[:19] if r.created_at else "",
        }
        for r in records
    ])


@router.post("/{customer_id}/followups")
async def create_followup(
    session: SessionDep, current_user: CurrentUserDep, customer_id: int, req: FollowupCreate
):
    """创建跟进记录"""
    result = await session.execute(
        select(Customer).where(Customer.id == customer_id, Customer.is_deleted == 0)
    )
    c = result.scalar_one_or_none()
    if not c:
        raise NotFoundError("客户不存在")

    from datetime import date
    next_date = None
    if req.next_date:
        try:
            next_date = date.fromisoformat(req.next_date)
        except ValueError:
            pass

    record = FollowupRecord(
        customer_id=customer_id,
        type=req.type,
        content=req.content,
        result=req.result,
        next_date=next_date,
        operator_id=current_user.id,
    )
    session.add(record)

    # 更新客户最后联系时间和下次跟进日期
    c.last_contact_at = str(date.today())
    if next_date:
        c.next_followup_date = next_date

    await session.flush()
    return success(data={"id": record.id}, message="跟进记录创建成功")


@router.put("/{customer_id}/followups/{record_id}")
async def update_followup(
    session: SessionDep, current_user: CurrentUserDep, customer_id: int, record_id: int, req: FollowupUpdate
):
    """更新跟进记录"""
    result = await session.execute(
        select(FollowupRecord).where(
            FollowupRecord.id == record_id,
            FollowupRecord.customer_id == customer_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise NotFoundError("跟进记录不存在")

    update_data = req.model_dump(exclude_none=True)
    if "next_date" in update_data and update_data["next_date"]:
        from datetime import date
        try:
            update_data["next_date"] = date.fromisoformat(update_data["next_date"])
        except ValueError:
            del update_data["next_date"]

    for field, value in update_data.items():
        setattr(record, field, value)

    await session.flush()
    return success(data={"id": record_id}, message="跟进记录更新成功")
