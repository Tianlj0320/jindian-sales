"""
仓库与库存模型
"""

from __future__ import annotations

from sqlalchemy import DECIMAL, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base, TimestampMixin


class Warehouse(Base, TimestampMixin):
    """仓库"""

    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="仓库名称")
    code: Mapped[str] = mapped_column(String(20), default="", comment="仓库编码")
    address: Mapped[str] = mapped_column(String(300), default="", comment="仓库地址")
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否启用")
    warehouse_type: Mapped[str] = mapped_column(String(20), default="main", comment="仓库类型: main=主仓库, auxiliary=辅料仓, finished=成品仓")
    remark: Mapped[str] = mapped_column(String(200), default="", comment="备注")


class Inventory(Base, TimestampMixin):
    """库存（每个仓库每个产品一条记录）"""

    __tablename__ = "inventories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False, index=True, comment="产品ID")
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False, comment="仓库ID")
    quantity: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="当前库存数量")
    safety_stock: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="安全库存")

    # 三级分类：区域 → 货架 → 库位
    zone: Mapped[str] = mapped_column(String(50), default="", comment="存放区域（一级）")
    shelf: Mapped[str] = mapped_column(String(50), default="", comment="货架（二级）")
    bin: Mapped[str] = mapped_column(String(50), default="", comment="库位（三级）")

    product = relationship("Product", lazy="joined")


class WarehouseStorage(Base, TimestampMixin):
    """仓库存储位置定义（三级分类：区域 → 货架 → 库位）"""

    __tablename__ = "warehouse_storage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True, comment="所属仓库")
    level: Mapped[int] = mapped_column(Integer, nullable=False, comment="层级: 1=区域, 2=货架, 3=库位")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="名称")
    code: Mapped[str] = mapped_column(String(30), default="", comment="编码")
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="父级ID")
    remark: Mapped[str] = mapped_column(String(200), default="", comment="备注")


class InventoryFlow(Base, TimestampMixin):
    """库存流水记录"""

    __tablename__ = "inventory_flows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False, index=True, comment="产品ID")
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False, comment="仓库ID")
    flow_type: Mapped[str] = mapped_column(String(10), nullable=False, comment="类型: IN/OUT/TRANSFER/ADJUST")
    qty_before: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="变动前数量")
    qty_change: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="变动数量")
    qty_after: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0, comment="变动后数量")
    ref_type: Mapped[str] = mapped_column(String(20), default="", comment="关联类型: order/purchase/adjust")
    ref_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="关联ID")
    operator_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="操作人ID")
    remark: Mapped[str] = mapped_column(Text, default="", comment="备注")
