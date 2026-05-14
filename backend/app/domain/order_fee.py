"""
订单费用模型
"""

from __future__ import annotations

from sqlalchemy import DECIMAL, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base, TimestampMixin


class OrderFee(Base, TimestampMixin):
    """订单附加费用（量尺费、安装费、运费等）"""

    __tablename__ = "order_fees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True, comment="订单ID")
    fee_type: Mapped[str] = mapped_column(String(30), nullable=False, comment="费用类型 code（字典 order_fee_type）")
    fee_type_label: Mapped[str] = mapped_column(String(50), default="", comment="费用类型显示名")
    amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="金额")
    remark: Mapped[str] = mapped_column(String(200), default="", comment="备注")
    operator_name: Mapped[str] = mapped_column(String(50), default="", comment="操作人")
