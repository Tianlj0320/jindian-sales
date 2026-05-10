"""
加工类型与辅料规则模型
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base, TimestampMixin


class ProcessingType(Base, TimestampMixin):
    """加工类型（如：常规窗帘、罗马杆窗帘、电动窗帘、百叶帘等）"""

    __tablename__ = "processing_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="加工类型名称")
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, comment="编码")
    description: Mapped[str] = mapped_column(String(200), default="", comment="描述")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")

    # 关系
    rules = relationship("ProcessingMaterialRule", back_populates="processing_type",
                         cascade="all, delete-orphan",
                         order_by="ProcessingMaterialRule.sort_order")


class ProcessingMaterialRule(Base, TimestampMixin):
    """加工辅料规则 —— 每个加工类型下需要哪些辅料及计算方式"""

    __tablename__ = "processing_material_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    processing_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("processing_types.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # 辅料信息
    material_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="辅料名称")
    default_product_name: Mapped[str] = mapped_column(String(200), default="", comment="默认产品名称")
    product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("products.id"), nullable=True, comment="关联产品ID")
    unit: Mapped[str] = mapped_column(String(10), default="米", comment="单位")

    # 数量计算方式
    # formula 是一个表达式，可用变量: width(主料宽m), height(主料高m), qty(主料数量), fold_ratio(倍率)
    # 如: "width" "width * qty" "1" "width * 1.1 + 0.2"
    qty_formula: Mapped[str] = mapped_column(String(100), default="1", comment="数量计算公式")
    unit_price: Mapped[float] = mapped_column(default=0, comment="默认单价")

    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否必选")

    # 关系
    processing_type = relationship("ProcessingType", back_populates="rules")
