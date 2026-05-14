"""
财务管理 API
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep
from app.core.exceptions import NotFoundError, BusinessError
from app.core.response import paginated, success
from app.domain.customer import Customer
from app.domain.deposit import Deposit
from app.domain.finance import FinanceExpense, FinancePayable, FinanceReceivable
from app.domain.order import Order
from app.domain.purchase import PurchaseOrder
from app.schemas.finance import ExpenseCreate, ExpenseUpdate, PayPayment, ReceivePayment

router = APIRouter(prefix="/api/v1/finance", tags=["财务管理"])


# ══════════════════════════════════════════════════════════════
# 应收款
# ══════════════════════════════════════════════════════════════


@router.get("/receivables")
async def list_receivables(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    status: str | None = Query(None),
    keyword: str | None = Query(None),
):
    """应收款列表"""
    conditions = []
    if status:
        conditions.append(FinanceReceivable.status == status)
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(FinanceReceivable.customer_name.ilike(kw))

    where = and_(*conditions) if conditions else True
    total = (await session.execute(
        select(func.count()).select_from(FinanceReceivable).where(where)
    )).scalar() or 0

    result = await session.execute(
        select(FinanceReceivable)
        .where(where)
        .order_by(FinanceReceivable.created_at.desc())
        .offset(page.offset)
        .limit(page.page_size)
    )
    items = result.scalars().all()

    return paginated(
        items=[
            {
                "id": r.id,
                "order_id": r.order_id,
                "order_no": r.order_no,
                "customer_name": r.customer_name,
                "total_amount": float(r.total_amount),
                "received_amount": float(r.received_amount),
                "unpaid_amount": float(r.unpaid_amount),
                "status": r.status,
                "due_date": str(r.due_date) if r.due_date else None,
                "remark": r.remark,
                "created_at": str(r.created_at)[:19] if r.created_at else "",
            }
            for r in items
        ],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/receive")
async def receive_payment(session: SessionDep, current_user: CurrentUserDep, req: ReceivePayment):
    """收款确认"""
    result = await session.execute(select(Order).where(Order.id == req.order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError("订单不存在")

    # 更新订单收款
    order.received = float(order.received or 0) + req.amount
    order.debt = max(0, float(order.amount or 0) - float(order.received or 0))

    # 如果收款类型为定金，同步更新订单定金和定金记录
    if req.payment_type == "定金":
        order.deposit = float(order.deposit or 0) + req.amount

        # 客户定金余额更新
        if order.customer_id:
            c_result = await session.execute(
                select(Customer).where(Customer.id == order.customer_id, Customer.is_deleted == 0)
            )
            customer = c_result.scalar_one_or_none()
            if customer:
                current_balance = float(getattr(customer, "deposit_balance", 0))
                new_balance = current_balance + req.amount
                customer.deposit_balance = new_balance

                # 创建定金记录
                deposit = Deposit(
                    customer_id=order.customer_id,
                    order_id=req.order_id,
                    amount=req.amount,
                    balance=new_balance,
                    payment_method=req.method,
                    received_at=date.today(),
                    operator_id=current_user.id,
                    operator_name=current_user.name,
                    remark=req.remark or f"订单{order.order_no}定金",
                )
                session.add(deposit)

    # 查找或创建应收记录
    recv_result = await session.execute(
        select(FinanceReceivable).where(FinanceReceivable.order_id == req.order_id)
    )
    recv = recv_result.scalar_one_or_none()
    if recv:
        recv.received_amount = float(recv.received_amount or 0) + req.amount
        recv.unpaid_amount = max(0, float(recv.total_amount) - float(recv.received_amount))
        if recv.unpaid_amount <= 0:
            recv.status = "已结清"
        else:
            recv.status = "部分收款"
    else:
        recv = FinanceReceivable(
            order_id=req.order_id,
            order_no=order.order_no or "",
            customer_name=order.customer_name or "",
            total_amount=float(order.amount or 0),
            received_amount=req.amount,
            unpaid_amount=max(0, float(order.amount or 0) - req.amount),
            status="已结清" if req.amount >= float(order.amount or 0) else "部分收款",
        )
        session.add(recv)

    await session.flush()
    return success(data={
        "order_id": req.order_id,
        "amount": req.amount,
        "payment_type": req.payment_type,
    }, message="收款登记成功")


@router.get("/receivables/{order_id}/payments")
async def get_order_payments(session: SessionDep, current_user: CurrentUserDep, order_id: int):
    """获取订单的全部收款明细（含定金）"""
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError("订单不存在")

    # 应收记录
    recv_result = await session.execute(
        select(FinanceReceivable).where(FinanceReceivable.order_id == order_id)
    )
    recv = recv_result.scalar_one_or_none()

    # 定金记录（优先按订单关联，再按客户关联）
    deposits = []
    if order.customer_id:
        dep_cond = [Deposit.customer_id == order.customer_id]
        # 如果有order_id关联的定金，也包含进来
        dep_result = await session.execute(
            select(Deposit)
            .where(*dep_cond)
            .order_by(Deposit.created_at.desc())
        )
        deposits = [
            {
                "id": d.id,
                "amount": float(d.amount),
                "balance": float(d.balance),
                "payment_method": d.payment_method,
                "received_at": str(d.received_at) if d.received_at else None,
                "operator_name": d.operator_name,
                "remark": d.remark,
                "created_at": str(d.created_at)[:19] if d.created_at else "",
            }
            for d in dep_result.scalars().all()
            if d.order_id is None or d.order_id == order_id
        ]

    # 组装付款明细（基于订单收款变动记录）
    # 由于当前系统未存储逐笔收款明细，从订单和应收记录推导
    payments = []
    total_received = float(order.received or 0)
    if total_received > 0:
        # 有定金记录时优先展示
        for d in deposits:
            if float(d["amount"]) > 0:
                payments.append({
                    "type": "定金",
                    "amount": float(d["amount"]),
                    "method": d["payment_method"],
                    "date": d["received_at"],
                    "remark": d["remark"],
                    "source": "deposit",
                })
        # 如果定金总额小于已收，差额作为其他收款
        deposit_total = sum(p["amount"] for p in payments if p["source"] == "deposit")
        if total_received > deposit_total:
            payments.append({
                "type": "收款",
                "amount": total_received - deposit_total,
                "method": "",
                "date": None,
                "remark": "综合收款（含进度款/尾款）",
                "source": "receivable",
            })

    return success(data={
        "order_id": order.id,
        "order_no": order.order_no or "",
        "customer_name": order.customer_name or "",
        "customer_id": order.customer_id,
        "total_amount": float(order.amount or 0),
        "received_amount": total_received,
        "unpaid_amount": float(order.debt or 0),
        "deposit_amount": float(order.deposit or 0),
        "receivable_status": recv.status if recv else ("已结清" if total_received >= float(order.amount or 0) else "未收款"),
        "payments": payments,
        "deposits": deposits,
    })


# ══════════════════════════════════════════════════════════════
# 应付款
# ══════════════════════════════════════════════════════════════


@router.get("/payables")
async def list_payables(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    status: str | None = Query(None),
):
    """应付款列表"""
    conditions = []
    if status:
        conditions.append(FinancePayable.status == status)

    where = and_(*conditions) if conditions else True
    total = (await session.execute(
        select(func.count()).select_from(FinancePayable).where(where)
    )).scalar() or 0

    result = await session.execute(
        select(FinancePayable)
        .where(where)
        .order_by(FinancePayable.created_at.desc())
        .offset(page.offset)
        .limit(page.page_size)
    )
    items = result.scalars().all()

    return paginated(
        items=[
            {
                "id": p.id,
                "ref_type": p.ref_type,
                "ref_id": p.ref_id,
                "supplier_name": p.supplier_name,
                "total_amount": float(p.total_amount),
                "paid_amount": float(p.paid_amount),
                "unpaid_amount": float(p.unpaid_amount),
                "status": p.status,
                "due_date": str(p.due_date) if p.due_date else None,
                "remark": p.remark,
                "created_at": str(p.created_at)[:19] if p.created_at else "",
            }
            for p in items
        ],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/pay")
async def pay_payment(session: SessionDep, current_user: CurrentUserDep, req: PayPayment):
    """付款确认"""
    result = await session.execute(
        select(FinancePayable).where(
            FinancePayable.ref_type == req.ref_type,
            FinancePayable.ref_id == req.ref_id,
        )
    )
    pay = result.scalar_one_or_none()
    if pay:
        pay.paid_amount = float(pay.paid_amount or 0) + req.amount
        pay.unpaid_amount = max(0, float(pay.total_amount) - float(pay.paid_amount))
        pay.status = "已结清" if pay.unpaid_amount <= 0 else "部分付款"
    else:
        pay = FinancePayable(
            ref_type=req.ref_type,
            ref_id=req.ref_id,
            total_amount=req.amount,
            paid_amount=req.amount,
            unpaid_amount=0,
            status="已结清",
        )
        session.add(pay)

    # 更新采购单付款
    if req.ref_type == "purchase":
        po_result = await session.execute(
            select(PurchaseOrder).where(PurchaseOrder.id == req.ref_id)
        )
        po = po_result.scalar_one_or_none()
        if po:
            po.paid_amount = float(po.paid_amount or 0) + req.amount
            po.debt_amount = max(0, float(po.total_amount) - float(po.paid_amount))

    await session.flush()
    return success(data={"ref_id": req.ref_id, "amount": req.amount}, message="付款登记成功")


# ══════════════════════════════════════════════════════════════
# 费用管理
# ══════════════════════════════════════════════════════════════


@router.get("/expenses")
async def list_expenses(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    category: str | None = Query(None),
    year: int | None = Query(None),
    month: int | None = Query(None),
):
    """费用列表"""
    conditions = []
    if category:
        conditions.append(FinanceExpense.category == category)
    if year and month:
        conditions.append(func.strftime("%Y-%m", FinanceExpense.expense_date) == f"{year}-{month:02d}")

    where = and_(*conditions) if conditions else True
    total = (await session.execute(
        select(func.count()).select_from(FinanceExpense).where(where)
    )).scalar() or 0

    result = await session.execute(
        select(FinanceExpense)
        .where(where)
        .order_by(FinanceExpense.expense_date.desc())
        .offset(page.offset)
        .limit(page.page_size)
    )
    items = result.scalars().all()

    return paginated(
        items=[
            {
                "id": e.id,
                "category": e.category,
                "amount": float(e.amount),
                "expense_date": str(e.expense_date),
                "operator_id": e.operator_id,
                "remark": e.remark,
                "created_at": str(e.created_at)[:19] if e.created_at else "",
            }
            for e in items
        ],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/expenses")
async def create_expense(session: SessionDep, current_user: CurrentUserDep, req: ExpenseCreate):
    """创建费用记录"""
    expense_date = datetime.strptime(req.expense_date, "%Y-%m-%d").date() if req.expense_date else date.today()
    expense = FinanceExpense(
        category=req.category,
        amount=req.amount,
        expense_date=expense_date,
        operator_id=current_user.id,
        remark=req.remark,
    )
    session.add(expense)
    await session.flush()
    return success(data={"id": expense.id}, message="费用记录创建成功")


@router.put("/expenses/{expense_id}")
async def update_expense(
    session: SessionDep, current_user: CurrentUserDep, expense_id: int, req: ExpenseUpdate
):
    """更新费用记录"""
    result = await session.execute(select(FinanceExpense).where(FinanceExpense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise NotFoundError("费用记录不存在")

    update_data = req.model_dump(exclude_none=True)
    if "expense_date" in update_data and update_data["expense_date"]:
        from datetime import date
        try:
            update_data["expense_date"] = date.fromisoformat(update_data["expense_date"])
        except ValueError:
            pass

    for field, value in update_data.items():
        setattr(expense, field, value)
    await session.flush()
    return success(data={"id": expense_id}, message="费用记录更新成功")


@router.delete("/expenses/{expense_id}")
async def delete_expense(session: SessionDep, current_user: CurrentUserDep, expense_id: int):
    """删除费用记录"""
    result = await session.execute(select(FinanceExpense).where(FinanceExpense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise NotFoundError("费用记录不存在")

    await session.delete(expense)
    await session.flush()
    return success(message="费用记录已删除")


# ══════════════════════════════════════════════════════════════
# 财务摘要
# ══════════════════════════════════════════════════════════════


@router.get("/summary")
async def get_finance_summary(session: SessionDep, current_user: CurrentUserDep):
    """财务摘要"""
    today = date.today()
    month_start = today.replace(day=1)

    # 应收汇总
    recv_data = (await session.execute(
        select(
            func.coalesce(func.sum(FinanceReceivable.total_amount), 0),
            func.coalesce(func.sum(FinanceReceivable.received_amount), 0),
            func.coalesce(func.sum(FinanceReceivable.unpaid_amount), 0),
        )
    )).first()
    total_receivable, total_received, total_unpaid = (
        float(recv_data[0] or 0),
        float(recv_data[1] or 0),
        float(recv_data[2] or 0),
    )

    # 应付汇总
    pay_data = (await session.execute(
        select(
            func.coalesce(func.sum(FinancePayable.total_amount), 0),
            func.coalesce(func.sum(FinancePayable.paid_amount), 0),
            func.coalesce(func.sum(FinancePayable.unpaid_amount), 0),
        )
    )).first()
    total_payable, total_paid, total_unpaid_payable = (
        float(pay_data[0] or 0),
        float(pay_data[1] or 0),
        float(pay_data[2] or 0),
    )

    # 本月收款（计算订单本月收款变化较复杂，简化为查询本月创建的应收）
    month_received = (await session.execute(
        select(func.coalesce(func.sum(FinanceReceivable.received_amount), 0))
        .where(func.date(FinanceReceivable.created_at) >= month_start)
    )).scalar() or 0

    # 本月费用
    month_expense = (await session.execute(
        select(func.coalesce(func.sum(FinanceExpense.amount), 0))
        .where(
            FinanceExpense.expense_date >= month_start,
            FinanceExpense.expense_date <= today,
        )
    )).scalar() or 0

    return success(data={
        "total_receivable": total_receivable,
        "total_received": total_received,
        "total_unpaid": total_unpaid,
        "total_payable": total_payable,
        "total_paid": total_paid,
        "total_unpaid_payable": total_unpaid_payable,
        "month_received": float(month_received),
        "month_paid": 0,
        "month_expense": float(month_expense),
    })


@router.get("/monthly-report")
async def get_monthly_report(
    session: SessionDep,
    current_user: CurrentUserDep,
    year: int | None = Query(None, description="年份，默认当前年份"),
):
    """月度财务报表：按月统计收入/支出/利润"""
    target_year = year or date.today().year

    # 月度收款统计（按 created_at 月份分组）
    recv_rows = (await session.execute(
        select(
            func.strftime("%m", FinanceReceivable.created_at).label("mon"),
            func.coalesce(func.sum(FinanceReceivable.received_amount), 0),
            func.count(FinanceReceivable.id),
        )
        .where(
            func.strftime("%Y", FinanceReceivable.created_at) == str(target_year),
        )
        .group_by("mon")
        .order_by("mon")
    )).all()

    # 月度费用统计（按 expense_date 月份分组）
    exp_rows = (await session.execute(
        select(
            func.strftime("%m", FinanceExpense.expense_date).label("mon"),
            func.coalesce(func.sum(FinanceExpense.amount), 0),
            func.count(FinanceExpense.id),
        )
        .where(
            func.strftime("%Y", FinanceExpense.expense_date) == str(target_year),
        )
        .group_by("mon")
        .order_by("mon")
    )).all()

    recv_map = {r.mon: {"amount": float(r[1]), "count": r[2]} for r in recv_rows}
    exp_map = {e.mon: {"amount": float(e[1]), "count": e[2]} for e in exp_rows}

    months = []
    for m in range(1, 13):
        mon = f"{m:02d}"
        revenue = recv_map.get(mon, {}).get("amount", 0)
        expense = exp_map.get(mon, {}).get("amount", 0)
        months.append({
            "month": f"{target_year}-{mon}",
            "revenue": revenue,
            "expense": expense,
            "net_profit": round(revenue - expense, 2),
            "revenue_count": recv_map.get(mon, {}).get("count", 0),
            "expense_count": exp_map.get(mon, {}).get("count", 0),
        })

    # 汇总
    total_revenue = sum(m["revenue"] for m in months)
    total_expense = sum(m["expense"] for m in months)

    return success(data={
        "year": target_year,
        "months": months,
        "total_revenue": total_revenue,
        "total_expense": total_expense,
        "total_net_profit": round(total_revenue - total_expense, 2),
    })
