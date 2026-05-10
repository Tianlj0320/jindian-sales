"""
采购单模型
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import DECIMAL, JSON, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base, TimestampMixin


class PurchaseOrder(Base, TimestampMixin):
    """采购单"""

    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    po_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, comment="采购单号")

    # 供应商
    supplier_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=True, comment="供应商ID")
    supplier_name: Mapped[str] = mapped_column(String(100), default="", comment="供应商名称")
    contact: Mapped[str] = mapped_column(String(50), default="", comment="联系人")
    phone: Mapped[str] = mapped_column(String(20), default="", comment="联系电话")
    bank_account: Mapped[str] = mapped_column(String(50), default="", comment="收款账号")
    bank_name: Mapped[str] = mapped_column(String(100), default="", comment="开户银行")
    payee: Mapped[str] = mapped_column(String(50), default="", comment="收款人")
    qq: Mapped[str] = mapped_column(String(30), default="", comment="QQ")
    wechat: Mapped[str] = mapped_column(String(50), default="", comment="微信")

    # 关联订单
    order_ids: Mapped[str] = mapped_column(String(500), default="", comment="关联订单ID(逗号分隔)")

    # 金额
    total_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="总金额")
    paid_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="已付款")
    debt_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="未付款")

    # 状态
    status: Mapped[str] = mapped_column(String(30), default="待采购", comment="状态: 待采购/已下单/部分到货/全部到货/已取消")

    # 日期
    order_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="下单日期")
    expected_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="预计到货")
    arrived_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="实际到货")

    # 内容
    remark: Mapped[str] = mapped_column(String(500), default="", comment="备注")

    # 明细（JSON冗余）
    items: Mapped[list | None] = mapped_column(JSON, default=list, comment="采购明细列表")

    # 关系
    po_items = relationship("PurchaseOrderItem", back_populates="purchase_order", lazy="selectin",
                            cascade="all, delete-orphan")


class PurchaseOrderItem(Base, TimestampMixin):
    """采购单明细"""

    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    purchase_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # 商品
    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="产品ID")
    product_name: Mapped[str] = mapped_column(String(200), default="", comment="产品名称")
    product_code: Mapped[str] = mapped_column(String(50), default="", comment="产品编码")
    spec: Mapped[str] = mapped_column(String(100), default="", comment="规格描述")

    # 数量价格
    quantity: Mapped[float] = mapped_column(DECIMAL(10, 2), default=1, comment="采购数量")
    unit: Mapped[str] = mapped_column(String(10), default="米", comment="单位")
    unit_price: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="单价")
    subtotal: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="小计")

    # 到货
    arrived_qty: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="已到货数量")
    material_type: Mapped[str] = mapped_column(String(20), default="主料", comment="主料/辅料")
    remark: Mapped[str] = mapped_column(String(200), default="", comment="备注")

    # 关系
    purchase_order = relationship("PurchaseOrder", back_populates="po_items")
