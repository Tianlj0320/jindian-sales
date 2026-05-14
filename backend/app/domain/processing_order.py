"""加工单管理模型"""
from __future__ import annotations

from sqlalchemy import Boolean, DECIMAL, ForeignKey, Integer, String, TIMESTAMP, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base, TimestampMixin


class ProcessingOrder(Base, TimestampMixin):
    """加工单"""

    __tablename__ = "processing_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    po_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="加工单号")
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False, comment="来源订单")
    order_no: Mapped[str] = mapped_column(String(30), default="", comment="订单号")
    customer_name: Mapped[str] = mapped_column(String(50), default="", comment="客户名")
    warehouse_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=True, comment="加工仓库")
    processing_factory: Mapped[str] = mapped_column(String(100), default="", comment="加工厂名称")
    total_items: Mapped[int] = mapped_column(Integer, default=0, comment="明细条数")
    total_process_fee: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="加工费总额")
    status: Mapped[str] = mapped_column(String(20), default="pending", comment="状态: pending/processing/completed")
    printed: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已打印")
    remark: Mapped[str] = mapped_column(Text, default="", comment="备注")
    completed_at: Mapped[str | None] = mapped_column(TIMESTAMP, nullable=True, comment="完成时间")

    # 关系
    items = relationship(
        "ProcessingOrderItem",
        back_populates="processing_order",
        cascade="all, delete-orphan",
        order_by="ProcessingOrderItem.id",
    )


class ProcessingOrderItem(Base, TimestampMixin):
    """加工单明细"""

    __tablename__ = "processing_order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    processing_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("processing_orders.id"), nullable=False, comment="加工单ID"
    )
    order_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("order_items.id"), nullable=False, comment="来源订单明细ID"
    )
    product_name: Mapped[str] = mapped_column(String(200), default="", comment="产品名称")
    product_code: Mapped[str] = mapped_column(String(100), default="", comment="产品编码")
    width: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="宽度")
    height: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="高度")
    qty: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="加工数量")
    unit: Mapped[str] = mapped_column(String(20), default="", comment="单位")
    process_desc: Mapped[str] = mapped_column(Text, default="", comment="工艺描述")
    process_fee_unit: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="加工单价")
    process_fee_subtotal: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="加工费小计")
    checked: Mapped[bool] = mapped_column(Boolean, default=False, comment="仓库验收勾选")
    remark: Mapped[str] = mapped_column(Text, default="", comment="备注")

    # 关系
    processing_order = relationship("ProcessingOrder", back_populates="items")
