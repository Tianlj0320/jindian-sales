"""
财务管理模型
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import DECIMAL, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base, TimestampMixin


class FinanceReceivable(Base, TimestampMixin):
    """应收款记录"""

    __tablename__ = "finance_receivables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False, comment="订单ID")
    order_no: Mapped[str] = mapped_column(String(30), default="", comment="订单号")
    customer_name: Mapped[str] = mapped_column(String(50), default="", comment="客户名")

    total_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="应收总额")
    received_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="已收金额")
    unpaid_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="未收金额")

    status: Mapped[str] = mapped_column(String(20), default="待收款", comment="状态: 待收款/部分收款/已结清")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="到期日")
    remark: Mapped[str] = mapped_column(String(300), default="", comment="备注")


class FinancePayable(Base, TimestampMixin):
    """应付款记录"""

    __tablename__ = "finance_payables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ref_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="关联类型: purchase/installation")
    ref_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="关联ID")
    supplier_name: Mapped[str] = mapped_column(String(100), default="", comment="供应商名")

    total_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="应付总额")
    paid_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="已付金额")
    unpaid_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="未付金额")

    status: Mapped[str] = mapped_column(String(20), default="待付款", comment="状态: 待付款/部分付款/已结清")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="到期日")
    remark: Mapped[str] = mapped_column(String(300), default="", comment="备注")


class FinanceExpense(Base, TimestampMixin):
    """运营费用记录"""

    __tablename__ = "finance_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False, comment="费用类型: 房租/水电/工资/办公/其他")
    amount: Mapped[float] = mapped_column(DECIMAL(12, 2), nullable=False, comment="金额")
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, comment="费用日期")
    operator_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="经办人ID")
    remark: Mapped[str] = mapped_column(String(300), default="", comment="备注")
