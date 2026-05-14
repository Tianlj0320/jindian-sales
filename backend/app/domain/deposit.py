"""
定金管理模型
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import DECIMAL, Column, Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base, TimestampMixin


class Deposit(Base, TimestampMixin):
    """定金记录"""

    __tablename__ = "deposits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="客户ID")
    amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, default=0, comment="金额（正=收定金，负=抵扣）")
    balance: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, default=0, comment="余额")
    payment_method: Mapped[str] = mapped_column(String(20), default="", comment="收款方式")
    received_at: Mapped[date | None] = mapped_column(Date, nullable=True, comment="收款日期")
    operator_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="操作人ID")
    operator_name: Mapped[str] = mapped_column(String(50), default="", comment="操作人姓名")
    remark: Mapped[str] = mapped_column(Text, default="", comment="备注")
