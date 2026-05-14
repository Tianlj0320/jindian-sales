"""
售后管理模型
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DECIMAL, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base, TimestampMixin


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

    # 处理状态
    status: Mapped[str] = mapped_column(String(20), default="待处理", comment="状态: 待处理/处理中/已处理/已关闭")
    handler_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="处理人ID")
    handler_name: Mapped[str] = mapped_column(String(50), default="", comment="处理人姓名")
    resolution: Mapped[str] = mapped_column(Text, default="", comment="处理结果说明")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="处理完成时间")

    # 备注
    remark: Mapped[str] = mapped_column(String(500), default="", comment="备注")
