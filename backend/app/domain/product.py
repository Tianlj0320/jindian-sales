"""
产品/面料/供应商模型
"""

from __future__ import annotations

from sqlalchemy import DECIMAL, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base, TimestampMixin


class ProductCategory(Base, TimestampMixin):
    """产品分类"""

    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="分类名称")
    code: Mapped[str] = mapped_column(String(20), default="", comment="分类编码")
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("product_categories.id"), nullable=True, comment="父分类ID")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注")

    children = relationship("ProductCategory", backref="parent", remote_side=[id])


class Supplier(Base, TimestampMixin):
    """供应商"""

    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), default="", comment="供应商编码")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="供应商名称")
    type: Mapped[str] = mapped_column(String(20), default="布艺", comment="类型: 成品/布艺/配件")
    contact: Mapped[str] = mapped_column(String(50), default="", comment="联系人")
    phone: Mapped[str] = mapped_column(String(20), default="", comment="联系电话")
    address: Mapped[str] = mapped_column(String(300), default="", comment="地址")
    delivery_days: Mapped[int] = mapped_column(Integer, default=7, comment="交期(天)")
    payment_terms: Mapped[str] = mapped_column(String(200), default="", comment="付款条件")
    qq: Mapped[str] = mapped_column(String(30), default="", comment="QQ号")
    wechat: Mapped[str] = mapped_column(String(50), default="", comment="微信号")
    bank_account: Mapped[str] = mapped_column(String(50), default="", comment="收款账号")
    bank_name: Mapped[str] = mapped_column(String(100), default="", comment="开户银行")
    payee: Mapped[str] = mapped_column(String(50), default="", comment="收款人")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注")


class Product(Base, TimestampMixin):
    """产品/面料"""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), default="", index=True, comment="产品编码")
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="产品名称")
    product_type: Mapped[str] = mapped_column(String(20), default="面料", comment="类型: 面料/辅料/成品")
    classification: Mapped[str] = mapped_column(String(20), default="", comment="分类: 定高/定宽/配件")

    # 分类关联
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("product_categories.id"), nullable=True, comment="分类ID")
    supplier_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=True, comment="供应商ID")

    # 规格
    model: Mapped[str] = mapped_column(String(50), default="", comment="型号")
    material: Mapped[str] = mapped_column(String(50), default="", comment="材质")
    color: Mapped[str] = mapped_column(String(50), default="", comment="颜色")
    pattern: Mapped[str] = mapped_column(String(50), default="", comment="花型")
    width: Mapped[int] = mapped_column(Integer, default=280, comment="门幅(cm)")
    standard_width: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="门幅(m)")
    weight: Mapped[int] = mapped_column(Integer, default=0, comment="克重(g/㎡)")
    fold_ratio: Mapped[float] = mapped_column(default=2.0, comment="褶皱系数")
    unit: Mapped[str] = mapped_column(String(10), default="米", comment="单位")
    calc_type: Mapped[str] = mapped_column(String(20), default="per_meter", comment="计价方式: per_meter/per_square/per_window/fixed")

    # 加工类型
    processing_type_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("processing_types.id"), nullable=True, comment="加工类型ID"
    )

    # 价格体系
    cost_price: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="成本价")
    min_price: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="最低售价")
    selling_price: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="销售单价")

    # 库存
    stock: Mapped[int] = mapped_column(Integer, default=0, comment="当前库存")
    safety_stock: Mapped[int] = mapped_column(Integer, default=0, comment="安全库存预警值")

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否上架")
    series: Mapped[str] = mapped_column(String(100), default="", comment="系列")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注")

    # 关系
    supplier = relationship("Supplier", lazy="joined")
    category = relationship("ProductCategory", lazy="joined")
    processing_type = relationship("ProcessingType", lazy="selectin")
