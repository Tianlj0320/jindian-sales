"""
售后管理 API
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select

from app.api.deps import CurrentUserDep, PageDep, SessionDep
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import paginated, success
from app.domain.after_sale import (
    AFTER_SALE_STATUS,
    TERMINAL_STATUSES,
    AfterSaleService,
    can_transition_after_sale,
)
from app.domain.finance import FinanceExpense, FinancePayable, FinanceReceivable
from app.domain.order import Order
from app.schemas.after_sale import AfterSaleCreate, AfterSaleUpdate

router = APIRouter(prefix="/api/v1/after-sales", tags=["售后管理"])


def _generate_service_no(today_str: str, seq: int) -> str:
    return f"AS{today_str}{seq:03d}"


def _service_to_dict(s: AfterSaleService) -> dict:
    return {
        "id": s.id,
        "service_no": s.service_no,
        "order_id": s.order_id,
        "order_no": s.order_no,
        "customer_name": s.customer_name,
        "customer_phone": s.customer_phone,
        "service_type": s.service_type,
        "service_type_label": s.service_type_label,
        "description": s.description,
        "priority": s.priority,
        "source": s.source,
        "status": s.status,
        "handler_id": s.handler_id,
        "handler_name": s.handler_name,
        "resolution": s.resolution,
        "resolved_type": s.resolved_type,
        "resolved_at": str(s.resolved_at)[:19] if s.resolved_at else None,
        "reviewer_name": s.reviewer_name,
        "review_remark": s.review_remark,
        "reviewed_at": str(s.reviewed_at)[:19] if s.reviewed_at else None,
        "rejected_at": str(s.rejected_at)[:19] if s.rejected_at else None,
        "closed_at": str(s.closed_at)[:19] if s.closed_at else None,
        "order_hold": bool(s.order_hold),
        "customer_confirmed": bool(s.customer_confirmed),
        "customer_confirmed_at": str(s.customer_confirmed_at)[:19] if s.customer_confirmed_at else None,
        "refund_amount": float(s.refund_amount or 0),
        "compensation_amount": float(s.compensation_amount or 0),
        "rework_cost": float(s.rework_cost or 0),
        "remark": s.remark,
        "created_at": str(s.created_at)[:19] if s.created_at else "",
        "updated_at": str(s.updated_at)[:19] if s.updated_at else "",
    }


# ─── 列表 ───────────────────────────────────────────────────


@router.get("")
async def list_after_sales(
    session: SessionDep,
    page: PageDep,
    current_user: CurrentUserDep,
    status: str | None = Query(None),
    service_type: str | None = Query(None),
    keyword: str | None = Query(None),
    priority: str | None = Query(None),
    order_hold: bool | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
):
    """售后列表（分页+筛选）"""
    conditions = []
    if status:
        conditions.append(AfterSaleService.status == status)
    if service_type:
        conditions.append(AfterSaleService.service_type == service_type)
    if priority:
        conditions.append(AfterSaleService.priority == priority)
    if order_hold is not None:
        conditions.append(AfterSaleService.order_hold == order_hold)
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
        items=[_service_to_dict(s) for s in items],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.get("/stats")
async def get_after_sale_stats(session: SessionDep, current_user: CurrentUserDep):
    """售后统计"""
    pending_review = (await session.execute(
        select(func.count()).select_from(AfterSaleService).where(AfterSaleService.status == "待审核")
    )).scalar() or 0
    pending = (await session.execute(
        select(func.count()).select_from(AfterSaleService).where(AfterSaleService.status == "待处理")
    )).scalar() or 0
    processing = (await session.execute(
        select(func.count()).select_from(AfterSaleService).where(
            AfterSaleService.status.in_(["处理中", "待客户确认"])
        )
    )).scalar() or 0
    completed = (await session.execute(
        select(func.count()).select_from(AfterSaleService).where(
            AfterSaleService.status.in_(["已完成", "已关闭"])
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
        "pending_review_count": pending_review,
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
    return success(data=_service_to_dict(s))


# ─── 创建 ───────────────────────────────────────────────────


@router.post("")
async def create_after_sale(session: SessionDep, current_user: CurrentUserDep, req: AfterSaleCreate):
    """创建售后单"""
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
        priority=req.priority or "normal",
        source=req.source or "manual",
        order_hold=req.order_hold,
        status="待审核",
        remark=req.remark,
    )
    session.add(after_sale)
    await session.flush()

    return success(data={"id": after_sale.id, "service_no": service_no}, message="售后单创建成功")


# ─── 更新（含状态机验证） ─────────────────────────────────


@router.put("/{after_sale_id}")
async def update_after_sale(
    session: SessionDep, current_user: CurrentUserDep, after_sale_id: int, req: AfterSaleUpdate
):
    """更新售后单（审核/处理/关闭）"""
    result = await session.execute(select(AfterSaleService).where(AfterSaleService.id == after_sale_id))
    s = result.scalar_one_or_none()
    if not s:
        raise NotFoundError("售后单不存在")

    update_data = req.model_dump(exclude_none=True)
    now = datetime.now(timezone.utc).astimezone()
    old_status = s.status
    new_status = update_data.get("status", old_status)

    # ── 状态转移验证 ──
    if new_status != old_status:
        if not can_transition_after_sale(old_status, new_status):
            raise BusinessError(f"不允许从「{old_status}」转移到「{new_status}」")

        # 各状态转移的额外校验和副作用
        if new_status == "待处理" and old_status == "待审核":
            # 审核通过
            update_data["reviewer_name"] = update_data.get("reviewer_name") or current_user.name
            update_data["reviewed_at"] = now

        elif new_status == "已关闭" and old_status == "待审核":
            # 审核驳回
            update_data["rejected_at"] = now
            update_data["closed_at"] = now

        elif new_status == "处理中":
            # 指派处理人
            if not update_data.get("handler_name"):
                update_data["handler_name"] = current_user.name

        elif new_status == "待客户确认":
            # 完成处理，填写方案
            update_data["resolved_at"] = now
            if not update_data.get("handler_name"):
                update_data["handler_name"] = current_user.name

        elif new_status == "已完成":
            if old_status == "待客户确认":
                # 客户确认
                update_data["customer_confirmed"] = True
                update_data["customer_confirmed_at"] = now

            await _process_financials(session, s, update_data, now)

        elif new_status == "已关闭" and old_status != "待审核":
            update_data["closed_at"] = now

    # ── 更新字段 ──
    for field, value in update_data.items():
        setattr(s, field, value)
    await session.flush()

    return success(data={"id": after_sale_id}, message="售后单更新成功")


async def _process_financials(
    session, s: AfterSaleService, update_data: dict, now: datetime
):
    """售后完结时处理财务联动"""
    refund = float(update_data.get("refund_amount") or s.refund_amount or 0)
    compensation = float(update_data.get("compensation_amount") or s.compensation_amount or 0)
    rework = float(update_data.get("rework_cost") or s.rework_cost or 0)

    if refund > 0 and s.order_id:
        # 从订单已收中扣减退款
        order_result = await session.execute(select(Order).where(Order.id == s.order_id))
        o = order_result.scalar_one_or_none()
        if o:
            o.received = max(0, float(o.received or 0) - refund)
            o.debt = max(0, float(o.amount or 0) - float(o.received or 0))
            # 更新应收记录
            recv_result = await session.execute(
                select(FinanceReceivable).where(FinanceReceivable.order_id == s.order_id)
            )
            recv = recv_result.scalar_one_or_none()
            if recv:
                recv.received_amount = max(0, float(recv.received_amount or 0) - refund)
                recv.unpaid_amount = float(recv.total_amount or 0) - float(recv.received_amount or 0)
                recv.status = "部分收款" if recv.unpaid_amount > 0 else "已结清"

    if compensation > 0:
        # 创建应付（赔偿给客户，用虚拟供应商或特殊标记）
        payable = FinancePayable(
            ref_type="after_sale",
            ref_id=s.id,
            supplier_name=f"售后赔偿-{s.customer_name}",
            total_amount=compensation,
            paid_amount=0,
            unpaid_amount=compensation,
            status="待付款",
            remark=f"售后单 {s.service_no} 赔偿",
        )
        session.add(payable)

    if rework > 0:
        expense = FinanceExpense(
            category="其他",
            amount=rework,
            expense_date=now.date(),
            operator_id=None,
            remark=f"售后返工-{s.service_no}",
        )
        session.add(expense)


# ─── 删除 ───────────────────────────────────────────────────


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
