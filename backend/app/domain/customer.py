"""
客户与跟进记录模型
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import JSON, Column, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base, SoftDeleteMixin, TimestampMixin


class Customer(Base, TimestampMixin, SoftDeleteMixin):
    """客户"""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="客户姓名")
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True, comment="联系电话")
    type: Mapped[str] = mapped_column(String(20), default="retail", comment="客户类型: retail/project/designer")
    source: Mapped[str] = mapped_column(String(50), default="", comment="客户来源")
    level: Mapped[str] = mapped_column(String(10), default="C", comment="客户等级: A/B/C")

    address: Mapped[str] = mapped_column(String(300), default="", comment="地址")
    community: Mapped[str] = mapped_column(String(100), default="", comment="小区")
    salesperson_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="负责导购ID")
    salesperson_name: Mapped[str] = mapped_column(String(50), default="", comment="负责导购姓名")

    # 统计字段
    total_orders: Mapped[int] = mapped_column(Integer, default=0, comment="累计订单数")
    total_amount: Mapped[float] = mapped_column(default=0.0, comment="累计金额")
    debt: Mapped[float] = mapped_column(default=0.0, comment="当前欠款")

    # 跟进
    next_followup_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="下次跟进日期")
    last_contact_at: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="最后联系时间")

    tags: Mapped[list] = mapped_column(JSON, default=list, comment="标签列表")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注")


class FollowupRecord(Base, TimestampMixin):
    """客户跟进记录"""

    __tablename__ = "followup_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="客户ID")
    type: Mapped[str] = mapped_column(String(20), default="电话", comment="跟进方式: 电话/微信/上门")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="跟进内容")
    result: Mapped[str] = mapped_column(String(100), default="", comment="跟进结果")
    next_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="下次跟进日期")
    operator_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="操作人ID")
