# app/api/track.py

from fastapi import APIRouter, Query, Request
from sqlalchemy import select

from app.core.config import STORE_PHONE
from app.database import async_session
from app.models import CustomerProgressQueryLog, Order
from app.schemas import NextStep, OrderItem, StatusHistoryItem, TrackResponse, TrackResponseData

router = APIRouter(prefix="/api/track", tags=["客户进度查询"])

# 8态进度定义
STATUS_STEPS = [
    {"key": "created", "label": "订单已录入", "step": 0},
    {"key": "confirmed", "label": "已核单确认", "step": 1},
    {"key": "measured", "label": "已测量", "step": 2},
    {"key": "stocked", "label": "已备货", "step": 3},
    {"key": "processing", "label": "加工中", "step": 4},
    {"key": "install", "label": "待安装", "step": 5},
    {"key": "installed", "label": "已安装", "step": 6},
    {"key": "completed", "label": "已完成", "step": 7},
]


def mask_phone(phone: str) -> str:
    """脱敏手机号，保留前3后4位"""
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]


def mask_phone_last4(phone: str) -> str:
    """脱敏手机号，显示末4位"""
    if not phone:
        return ""
    return "****" + phone[-4:]


@router.get("", response_model=TrackResponse)
async def query_order_progress(
    request: Request,
    order_no: str = Query(..., description="订单编号"),
    phone_hint: str = Query(..., description="手机号后4位"),
):
    """
    客户扫码查询订单进度
    - 输入：订单号 + 手机号后4位
    - 输出：订单进度状态、当前步骤、下一步计划
    """
    # 记录查询日志
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")[:500]

    async with async_session() as session:
        # 查找订单
        result = await session.execute(select(Order).where(Order.order_no == order_no))
        order = result.scalar_one_or_none()

        if not order:
            return TrackResponse(success=False, error="订单号或手机号不正确，请核对后重新查询")

        # 校验手机号后4位
        if not order.customer_phone or not order.customer_phone.endswith(phone_hint):
            # 记录查询失败日志
            log = CustomerProgressQueryLog(
                order_no=order_no,
                phone_hint=phone_hint,
                ip_address=client_ip,
                user_agent=user_agent,
            )
            session.add(log)
            await session.commit()
            return TrackResponse(success=False, error="订单号或手机号不正确，请核对后重新查询")

        # 写入查询日志
        log = CustomerProgressQueryLog(
            order_no=order_no, phone_hint=phone_hint, ip_address=client_ip, user_agent=user_agent
        )
        session.add(log)

        # 计算进度
        current_step_index = 0
        for i, s in enumerate(STATUS_STEPS):
            if s["key"] == order.status_key:
                current_step_index = i
                break

        # 构建历史
        status_history = []
        for i, s in enumerate(STATUS_STEPS):
            is_current = i == current_step_index
            # 查找历史记录中的时间
            hist_time = None
            if order.history and isinstance(order.history, list):
                for h in order.history:
                    if isinstance(h, dict) and h.get("s2") == s["label"]:
                        hist_time = h.get("time")
                        break

            status_history.append(
                StatusHistoryItem(
                    step=i,
                    key=s["key"],
                    label=s["label"],
                    time=hist_time,
                    done=i < current_step_index,
                    is_current=is_current,
                )
            )

        # 下一步
        next_step_data = None
        if current_step_index < 7 and order.status_key not in ("completed", "cancelled"):
            next_key = STATUS_STEPS[current_step_index]["key"]
            if order.status_key == "install" and order.install_date:
                next_step_data = NextStep(
                    type="install",
                    label="安装",
                    date=str(order.install_date) if order.install_date else None,
                    time_slot=order.install_time_slot,
                    installer_name=None,  # 需关联 installer_account 查询
                    installer_phone_masked=None,
                )

        # 解析订单明细
        order_items = []
        if order.items and isinstance(order.items, list):
            for item in order.items:
                if isinstance(item, dict):
                    order_items.append(
                        OrderItem(
                            room=item.get("room", item.get("name", "")),
                            product=item.get("product", item.get("name", "")),
                            qty=item.get("qty", 1),
                        )
                    )

        # 获取当前状态中文名
        status_label = STATUS_STEPS[current_step_index]["label"]
        for s in STATUS_STEPS:
            if s["key"] == order.status_key:
                status_label = s["label"]
                break

        await session.commit()

        return TrackResponse(
            success=True,
            data=TrackResponseData(
                order_no=order.order_no,
                customer_name=order.customer_name or "",
                customer_phone_masked=mask_phone(order.customer_phone or ""),
                order_type=order.order_type or "窗帘",
                amount=float(order.amount or 0),
                received=float(order.received or 0),
                status_key=order.status_key or "created",
                status_label=status_label,
                progress_step=current_step_index,
                progress_total=len(STATUS_STEPS),
                status_history=status_history,
                next_step=next_step_data,
                order_items=order_items,
                store_phone=STORE_PHONE,
            ),
        )
