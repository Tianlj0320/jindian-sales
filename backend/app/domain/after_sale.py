"""
售后管理模型
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DECIMAL, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base, TimestampMixin

# 售后状态常量
AFTER_SALE_STATUS = frozenset({
    "待审核", "待处理", "处理中", "待客户确认", "已完成", "已关闭",
})

# 有效状态转移
VALID_TRANSITIONS: dict[str, set[str]] = {
    "待审核": {"待处理", "已关闭"},
    "待处理": {"处理中", "已完成", "已关闭"},
    "处理中": {"待客户确认", "已关闭"},
    "待客户确认": {"已完成", "处理中", "已关闭"},
    "已完成": set(),
    "已关闭": set(),
}

# 终态
TERMINAL_STATUSES: frozenset = frozenset({"已完成", "已关闭"})


def can_transition_after_sale(from_status: str, to_status: str) -> bool:
    """判断售后状态转移是否合法"""
    allowed = VALID_TRANSITIONS.get(from_status, set())
    return to_status in allowed


class AfterSaleService(Base, TimestampMixin):
    """售后工单"""

    __tablename__ = "after_sale_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, comment="售后单号 AS{YYYYMMDD}{seq}")

    # 关联订单
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="订单ID")
    order_no: Mapped[str] = mapped_column(String(30), default="", comment="订单号")

    # 客户信息
    customer_name: Mapped[str] = mapped_column(String(50), default="", comment="客户姓名")
    customer_phone: Mapped[str] = mapped_column(String(20), default="", comment="联系电话")

    # 售后内容
    service_type: Mapped[str] = mapped_column(String(30), nullable=False, comment="售后类型 code（字典 after_sale_category）")
    service_type_label: Mapped[str] = mapped_column(String(50), default="", comment="类型显示名")
    description: Mapped[str] = mapped_column(Text, default="", comment="问题描述")
    priority: Mapped[str] = mapped_column(String(10), default="normal", comment="优先级: urgent/high/normal/low")
    source: Mapped[str] = mapped_column(String(20), default="manual", comment="来源: manual/order/production/installation")

    # 审核
    reviewer_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="审核人ID")
    reviewer_name: Mapped[str] = mapped_column(String(50), default="", comment="审核人姓名")
    review_remark: Mapped[str] = mapped_column(Text, default="", comment="审核意见")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="审核时间")
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="驳回时间")

    # 处理
    status: Mapped[str] = mapped_column(String(20), default="待审核", comment="状态: 待审核/待处理/处理中/待客户确认/已完成/已关闭")
    handler_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="处理人ID")
    handler_name: Mapped[str] = mapped_column(String(50), default="", comment="处理人姓名")
    resolution: Mapped[str] = mapped_column(Text, default="", comment="处理结果说明")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="处理完成时间")
    resolved_type: Mapped[str] = mapped_column(String(20), default="", comment="处理方案: refund/replacement/rework/return/other")

    # 过程控制
    order_hold: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否阻塞关联订单推进")
    customer_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, comment="客户是否已确认")
    customer_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="客户确认时间")
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="关闭时间")

    # 财务关联
    refund_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="退款金额")
    compensation_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="赔偿金额")
    rework_cost: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="返工费用")

    # 备注
    remark: Mapped[str] = mapped_column(String(500), default="", comment="备注")
