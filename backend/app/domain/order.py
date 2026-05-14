"""
订单与订单明细模型
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import DECIMAL, JSON, Boolean, Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base, TimestampMixin


class Order(Base, TimestampMixin):
    """销售订单"""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True, comment="订单号")
    order_type: Mapped[str] = mapped_column(String(20), default="窗帘", comment="订单类型: 窗帘/墙布/硬包/岩板/全屋")

    # 客户信息
    customer_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("customers.id"), nullable=True, comment="客户ID")
    customer_name: Mapped[str] = mapped_column(String(50), default="", comment="客户姓名")
    customer_phone: Mapped[str] = mapped_column(String(20), default="", comment="客户电话")

    # 销售信息
    salesperson_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="导购ID")
    salesperson_name: Mapped[str] = mapped_column(String(50), default="", comment="导购姓名")

    # 金额
    quote_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="标价金额")
    discount_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="优惠金额")
    round_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="抹零金额")
    amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="实付金额")
    received: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="已收款")
    debt: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="欠款")
    deposit: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="定金金额")
    discount_reason: Mapped[str] = mapped_column(String(200), default="", comment="折扣原因")

    # 日期
    order_date: Mapped[str] = mapped_column(String(20), default="", comment="下单日期")
    delivery_date: Mapped[str] = mapped_column(String(20), default="", comment="交货日期")
    delivery_method: Mapped[str] = mapped_column(String(20), default="上门安装", comment="交货方式")

    # 状态
    status_key: Mapped[str] = mapped_column(String(30), default="initial", index=True, comment="状态key")
    status_label: Mapped[str] = mapped_column(String(30), default="待量尺", comment="状态名称")
    status_color: Mapped[str] = mapped_column(String(20), default="#909399", comment="状态颜色")

    # 内容
    content: Mapped[str] = mapped_column(String(500), default="", comment="订单内容概述")
    remark: Mapped[str] = mapped_column(String(500), default="", comment="备注")

    # 安装信息
    install_address: Mapped[str] = mapped_column(String(300), default="", comment="安装地址")
    install_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="安装日期")
    install_time_slot: Mapped[str] = mapped_column(String(20), default="", comment="安装时段")

    # 测量数据
    measure_data: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="测量数据")
    install_requirements: Mapped[str] = mapped_column(Text, default="", comment="安装要求")

    # 历史记录
    history: Mapped[list | None] = mapped_column(JSON, default=list, comment="状态变更历史")

    # 补单关联
    parent_order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("orders.id"), nullable=True, comment="原订单ID（补单专用）")
    orig_order_no: Mapped[str] = mapped_column(String(30), default="", comment="原订单号（补单专用）")

    # 关系
    items = relationship("OrderItem", back_populates="order", lazy="selectin",
                         cascade="all, delete-orphan",
                         order_by="OrderItem.id")


class OrderItem(Base, TimestampMixin):
    """订单明细"""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)

    # 商品信息
    item_type: Mapped[str] = mapped_column(String(20), default="窗帘", comment="类型: 窗帘/窗纱/软包/硬包")
    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="产品ID")
    product_name: Mapped[str] = mapped_column(String(200), default="", comment="产品名称")
    product_code: Mapped[str] = mapped_column(String(50), default="", comment="产品编码")
    supplier_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="供应商ID")

    # 规格
    room: Mapped[str] = mapped_column(String(50), default="", comment="房间")
    width: Mapped[float] = mapped_column(DECIMAL(8, 2), default=0, comment="宽度(m)")
    height: Mapped[float] = mapped_column(DECIMAL(8, 2), default=0, comment="高度(m)")
    fold_ratio: Mapped[float] = mapped_column(DECIMAL(4, 2), default=2.0, comment="褶皱倍数")
    unit: Mapped[str] = mapped_column(String(10), default="米", comment="单位")

    # 价格
    unit_price: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="单价")
    qty: Mapped[float] = mapped_column(DECIMAL(10, 2), default=1, comment="数量")
    discount: Mapped[float] = mapped_column(DECIMAL(4, 2), default=1.0, comment="折扣率")
    amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="金额")
    final_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0, comment="折后金额")

    # 工艺
    open_type: Mapped[str] = mapped_column(String(20), default="", comment="开合方式")
    style_code: Mapped[str] = mapped_column(String(20), default="", comment="款式编码")
    process_desc: Mapped[str] = mapped_column(String(200), default="", comment="工艺描述")
    classification: Mapped[str] = mapped_column(String(20), default="", comment="定高/定宽")
    material_type: Mapped[str] = mapped_column(String(20), default="主料", comment="主料/辅料")
    procurement_type: Mapped[str] = mapped_column(String(10), default="物料", comment="采购类型: 物料/成品/辅料")
    is_purchase: Mapped[bool] = mapped_column(Boolean, default=True, comment="订单级是否采购覆盖: False=跳过此明细不生成采购单")
    calc_type: Mapped[str] = mapped_column(String(20), default="per_meter", comment="计价方式")
    panel_count: Mapped[float] = mapped_column(DECIMAL(8, 2), default=0, comment="幅数")
    note: Mapped[str] = mapped_column(Text, default="", comment="备注")

    # 关系
    order = relationship("Order", back_populates="items")
