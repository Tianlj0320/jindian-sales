"""
生产反馈模型
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base, TimestampMixin


class ProductionFeedback(Base, TimestampMixin):
    """生产反馈"""

    __tablename__ = "production_feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feedback_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, comment="反馈编号")

    # 关联
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="订单ID")
    order_no: Mapped[str] = mapped_column(String(30), default="", comment="订单号")
    purchase_order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="采购单ID")

    # 反馈内容
    feedback_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="类型: quality/defect/shortage")
    description: Mapped[str] = mapped_column(Text, default="", comment="问题描述")
    photos: Mapped[list | None] = mapped_column(JSON, default=list, comment="图片列表")

    # 处理
    status: Mapped[str] = mapped_column(String(20), default="待处理", comment="状态: 待处理/处理中/已解决")
    resolver: Mapped[str] = mapped_column(String(50), default="", comment="处理人")
    resolution: Mapped[str] = mapped_column(Text, default="", comment="处理方案")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="解决时间")
