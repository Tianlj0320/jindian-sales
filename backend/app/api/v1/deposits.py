"""
定金管理 API
"""

from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import paginated, success
from app.domain.customer import Customer
from app.domain.deposit import Deposit
from app.schemas.deposit import DepositCreate

router = APIRouter(prefix="/api/v1/deposits", tags=["定金管理"])


@router.post("")
async def create_deposit(session: SessionDep, current_user: CurrentUserDep, req: DepositCreate):
    """创建定金记录"""
    # 验证客户存在
    result = await session.execute(
        select(Customer).where(Customer.id == req.customer_id, Customer.is_deleted == 0)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("客户不存在")

    amount = float(req.amount)
    if amount <= 0:
        raise BusinessError("定金金额必须大于0")

    # 处理日期
    received_at = None
    if req.received_at:
        try:
            received_at = date.fromisoformat(req.received_at)
        except ValueError:
            received_at = date.today()
    else:
        received_at = date.today()

    # 计算新余额
    current_balance = float(getattr(customer, "deposit_balance", 0))
    new_balance = current_balance + amount

    # 更新客户定金余额
    customer.deposit_balance = new_balance

    # 创建定金记录
    deposit = Deposit(
        customer_id=req.customer_id,
        amount=amount,
        balance=new_balance,
        payment_method=req.payment_method,
        received_at=received_at,
        operator_id=current_user.id,
        operator_name=current_user.name,
        remark=req.remark,
    )
    session.add(deposit)
    await session.flush()

    return success(data={
        "id": deposit.id,
        "customer_id": deposit.customer_id,
        "amount": float(deposit.amount),
        "balance": float(deposit.balance),
        "payment_method": deposit.payment_method,
        "received_at": str(deposit.received_at) if deposit.received_at else None,
        "operator_name": deposit.operator_name,
        "remark": deposit.remark,
        "created_at": str(deposit.created_at)[:19] if deposit.created_at else "",
    }, message="定金记录创建成功")


@router.get("")
async def list_deposits(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    customer_id: int | None = Query(None, description="客户ID"),
    start_date: str | None = Query(None, description="开始日期"),
    end_date: str | None = Query(None, description="结束日期"),
    keyword: str | None = Query(None, description="搜索关键词"),
):
    """定金列表（分页+筛选）"""
    conditions = []

    if customer_id:
        conditions.append(Deposit.customer_id == customer_id)
    if start_date:
        conditions.append(Deposit.received_at >= start_date)
    if end_date:
        conditions.append(Deposit.received_at <= end_date)
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(or_(
            Deposit.remark.ilike(kw),
            Deposit.payment_method.ilike(kw),
            Deposit.operator_name.ilike(kw),
        ))

    where = and_(*conditions) if conditions else True

    total = (await session.execute(
        select(func.count()).select_from(Deposit).where(where)
    )).scalar() or 0

    result = await session.execute(
        select(Deposit)
        .where(where)
        .order_by(Deposit.created_at.desc())
        .offset(page.offset)
        .limit(page.page_size)
    )
    deposits = result.scalars().all()

    items = [
        {
            "id": d.id,
            "customer_id": d.customer_id,
            "amount": float(d.amount),
            "balance": float(d.balance),
            "payment_method": d.payment_method or "",
            "received_at": str(d.received_at) if d.received_at else None,
            "operator_id": d.operator_id,
            "operator_name": d.operator_name or "",
            "remark": d.remark or "",
            "created_at": str(d.created_at)[:19] if d.created_at else "",
            "updated_at": str(d.updated_at)[:19] if d.updated_at else "",
        }
        for d in deposits
    ]

    return paginated(items=items, total=total, page=page.page, page_size=page.page_size)


@router.get("/{deposit_id}")
async def get_deposit(session: SessionDep, current_user: CurrentUserDep, deposit_id: int):
    """定金详情"""
    result = await session.execute(select(Deposit).where(Deposit.id == deposit_id))
    d = result.scalar_one_or_none()
    if not d:
        raise NotFoundError("定金记录不存在")

    return success(data={
        "id": d.id,
        "customer_id": d.customer_id,
        "amount": float(d.amount),
        "balance": float(d.balance),
        "payment_method": d.payment_method or "",
        "received_at": str(d.received_at) if d.received_at else None,
        "operator_id": d.operator_id,
        "operator_name": d.operator_name or "",
        "remark": d.remark or "",
        "created_at": str(d.created_at)[:19] if d.created_at else "",
        "updated_at": str(d.updated_at)[:19] if d.updated_at else "",
    })


@router.get("/customer/{customer_id}/balance")
async def get_customer_deposit_balance(session: SessionDep, current_user: CurrentUserDep, customer_id: int):
    """获取客户定金余额 + 历史记录"""
    result = await session.execute(
        select(Customer).where(Customer.id == customer_id, Customer.is_deleted == 0)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("客户不存在")

    balance = float(getattr(customer, "deposit_balance", 0))

    # 查询历史记录
    history_result = await session.execute(
        select(Deposit)
        .where(Deposit.customer_id == customer_id)
        .order_by(Deposit.created_at.desc())
        .limit(50)
    )
    records = history_result.scalars().all()

    return success(data={
        "customer_id": customer_id,
        "customer_name": customer.name,
        "customer_phone": customer.phone,
        "balance": balance,
        "records": [
            {
                "id": r.id,
                "amount": float(r.amount),
                "balance": float(r.balance),
                "payment_method": r.payment_method or "",
                "received_at": str(r.received_at) if r.received_at else None,
                "operator_name": r.operator_name or "",
                "remark": r.remark or "",
                "created_at": str(r.created_at)[:19] if r.created_at else "",
            }
            for r in records
        ],
    })
